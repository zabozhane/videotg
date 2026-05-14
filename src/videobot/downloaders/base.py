from __future__ import annotations

import asyncio
import logging
import random
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from videobot.config.settings import Settings
from videobot.downloaders.exceptions import DownloadFailed, SizeExceededError

logger = logging.getLogger(__name__)


def _describe_exception(exc: BaseException) -> str:
    if isinstance(exc, TimeoutError):
        return "Превышен таймаут загрузки (DOWNLOAD_TIMEOUT_SECONDS)."
    msg = str(exc).strip()
    if msg:
        return _truncate_for_user(msg, 900)
    return _truncate_for_user(type(exc).__name__, 200)


def _truncate_for_user(text: str, max_len: int) -> str:
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _parse_cookies_from_browser(spec: str) -> tuple[str, str | None, str | None, str | None]:
    """Match yt-dlp CLI parsing for --cookies-from-browser (see yt_dlp/__init__.py)."""
    import re

    from yt_dlp.cookies import SUPPORTED_BROWSERS, SUPPORTED_KEYRINGS

    spec = spec.strip()
    mobj = re.fullmatch(
        r"""(?x)
            (?P<name>[^+:]+)
            (?:\s*\+\s*(?P<keyring>[^:]+))?
            (?:\s*:\s*(?!:)(?P<profile>.+?))?
            (?:\s*::\s*(?P<container>.+))?
        """,
        spec,
    )
    if mobj is None:
        raise ValueError(f"некорректный YTDLP_COOKIES_FROM_BROWSER: {spec!r}")
    browser_name, keyring, profile, container = mobj.group(
        "name",
        "keyring",
        "profile",
        "container",
    )
    browser_name = browser_name.lower()
    if browser_name not in SUPPORTED_BROWSERS:
        raise ValueError(
            f"браузер {browser_name!r} не поддержан yt-dlp; например: chrome, brave, firefox"
        )
    if keyring is not None:
        keyring = keyring.upper()
        if keyring not in SUPPORTED_KEYRINGS:
            raise ValueError(f"keyring {keyring!r} не поддержан yt-dlp")
    return (browser_name, profile, keyring, container)


def _pick_merged_media(out_dir: Path, stem: str) -> Path | None:
    """After yt-dlp+DASH merge, prefer {stem}.mp4; never return transient .m4a fragments."""
    merged = out_dir / f"{stem}.mp4"
    if merged.is_file():
        return merged
    exts = {".mp4", ".webm", ".mkv", ".mov", ".m4v"}
    pool: list[Path] = []
    for p in out_dir.glob(f"{stem}.*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in exts:
            continue
        low = p.name.lower()
        if low.endswith(".part") or low.endswith(".temp") or low.endswith(".ytdl"):
            continue
        pool.append(p)
    if not pool:
        return None
    return max(pool, key=lambda p: p.stat().st_size)


class BaseDownloader(ABC):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @abstractmethod
    def _ytdlp_format_selector(self) -> str:
        """yt-dlp -f format string for this platform."""

    async def download(self, url: str) -> Path:
        self._settings.temp_dir.mkdir(parents=True, exist_ok=True)
        stem = f"dl_{uuid.uuid4().hex}"
        out_dir = self._settings.temp_dir
        max_bytes = int(self._settings.max_video_size_mb * 1024 * 1024)

        last_err: BaseException | None = None
        for attempt in range(1, self._settings.download_retries + 1):
            try:
                path = await asyncio.wait_for(
                    asyncio.to_thread(
                        self._sync_download,
                        url,
                        out_dir,
                        stem,
                        max_bytes,
                    ),
                    timeout=self._settings.download_timeout_seconds,
                )
                self._assert_size(path, max_bytes)
                return path
            except SizeExceededError:
                raise
            except Exception as exc:  # noqa: BLE001 — aggregate for retry
                last_err = exc
                logger.warning("Download attempt %s failed: %s", attempt, exc)
                self._cleanup_stem(out_dir, stem)
                if attempt < self._settings.download_retries:
                    await asyncio.sleep(_backoff_seconds(attempt))
                else:
                    break

        reason = _describe_exception(last_err) if last_err else "неизвестная ошибка"
        raise DownloadFailed(
            f"Не удалось скачать после {self._settings.download_retries} попыток: {reason}",
            last_err,
        )

    def _assert_size(self, path: Path, max_bytes: int) -> None:
        if not path.is_file():
            raise DownloadFailed(f"Expected file missing: {path}")
        size = path.stat().st_size
        if size > max_bytes:
            self._safe_unlink(path)
            raise SizeExceededError(
                f"Файл {size} байт превышает лимит {max_bytes} байт "
                f"({self._settings.max_video_size_mb} МБ)"
            )

    @staticmethod
    def _safe_unlink(path: Path) -> None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass

    @staticmethod
    def _cleanup_stem(out_dir: Path, stem: str) -> None:
        for p in out_dir.glob(f"{stem}.*"):
            BaseDownloader._safe_unlink(p)

    def _sync_download(self, url: str, out_dir: Path, stem: str, max_bytes: int) -> Path:
        import yt_dlp

        outtmpl = str(out_dir / f"{stem}.%(ext)s")
        opts: dict[str, Any] = {
            "format": self._ytdlp_format_selector(),
            "outtmpl": outtmpl,
            "merge_output_format": "mp4",
            "max_filesize": max_bytes,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "retries": 2,
            "fragment_retries": 2,
            "ignoreerrors": False,
        }

        browser_spec = self._settings.ytdlp_cookies_from_browser
        if browser_spec:
            try:
                opts["cookiesfrombrowser"] = _parse_cookies_from_browser(browser_spec)
                logger.debug("yt-dlp cookiesfrombrowser=%s", browser_spec)
            except ValueError as exc:
                logger.warning("%s", exc)
        else:
            cf = self._settings.ytdlp_cookiefile
            if cf is not None:
                if cf.is_file():
                    opts["cookiefile"] = str(cf.resolve())
                else:
                    logger.warning("YTDLP_COOKIEFILE задан, но файл не найден: %s", cf)

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        picked = _pick_merged_media(out_dir, stem)
        if picked is None:
            raise DownloadFailed("yt-dlp не создал итоговый видеофайл после склейки")
        return picked

    async def download_safe(self, url: str) -> Path:
        """Same as download; alias for clarity in callers."""
        return await self.download(url)


def _backoff_seconds(attempt: int) -> float:
    base = float(min(2 ** (attempt - 1), 30))
    return base + float(random.uniform(0, 0.5))
