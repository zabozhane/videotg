import logging
import os
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Self

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Первый токен из YTDLP_COOKIES_FROM_BROWSER (как у yt-dlp): chrome, chrome:Profile, …
_BROWSER_HEAD = re.compile(r"^([^:+]+)")

# Под ~/.config/… профили с SQLite Cookies (Chrome-семейство на Linux).
_BROWSER_CONFIG_DIRS: dict[str, tuple[str, ...]] = {
    "chrome": ("google-chrome",),
    "chromium": ("chromium",),
    "brave": ("BraveSoftware/Brave-Browser",),
    "edge": ("microsoft-edge",),
    "opera": ("opera", "com.opera.Opera"),
    "vivaldi": ("vivaldi",),
}

# Windows: %LOCALAPPDATA%\…\User Data (или аналог) — профили с Cookies.
_BROWSER_WIN_USERDATA: dict[str, tuple[str, ...]] = {
    "chrome": ("Google/Chrome/User Data",),
    "chromium": ("Chromium/User Data",),
    "brave": ("BraveSoftware/Brave-Browser/User Data",),
    "edge": ("Microsoft/Edge/User Data",),
    "vivaldi": ("Vivaldi/User Data",),
}

# macOS: ~/Library/Application Support/… (те же браузеры, другой корень).
_BROWSER_APP_SUPPORT_DIRS: dict[str, tuple[str, ...]] = {
    "chrome": ("Google/Chrome",),
    "chromium": ("Chromium",),
    "brave": ("BraveSoftware/Brave-Browser",),
    "edge": ("Microsoft Edge",),
    "opera": ("com.operasoftware.Opera",),
    "vivaldi": ("Vivaldi",),
}


def _ytdlp_browser_head(spec: str) -> str | None:
    spec = spec.strip()
    if not spec:
        return None
    m = _BROWSER_HEAD.match(spec)
    return m.group(1).strip().lower() if m else None


def _explicit_browser_profile_dir(spec: str) -> Path | None:
    """yt-dlp: `firefox:/abs/path/to/profile` или `chrome:/abs/path/to/profile`."""
    if ":" not in spec:
        return None
    rest = spec.split(":", 1)[1].strip()
    if not rest.startswith("/"):
        return None
    return Path(rest)


def _browser_cookie_db_at_profile(browser_head: str, profile_dir: Path) -> bool:
    name = browser_head.lower()
    if name == "firefox":
        # Явный путь из .env: достаточно существующего каталога профиля (sqlite может
        # кратковременно отсутствовать при первом старте; не сбрасываем настройку зря).
        return profile_dir.is_dir()
    if name in _BROWSER_CONFIG_DIRS:
        return any(
            p.is_file() and p.name == "Cookies" for p in profile_dir.rglob("Cookies")
        )
    return True


def _browser_cookie_database_likely_present_for_spec(spec: str) -> bool:
    head = _ytdlp_browser_head(spec)
    if not head:
        return True
    explicit = _explicit_browser_profile_dir(spec)
    if explicit is not None:
        return _browser_cookie_db_at_profile(head, explicit)
    return _browser_cookie_database_likely_present(head)


def _browser_cookie_database_likely_present(browser_head: str) -> bool:
    """False на VPS/Docker без профиля браузера — тогда не передаём cookiesfrombrowser в yt-dlp."""
    home = Path.home()
    name = browser_head.lower()
    if name == "firefox":
        if sys.platform == "darwin":
            profiles = home / "Library" / "Application Support" / "Firefox" / "Profiles"
            if profiles.is_dir():
                return any(profiles.glob("**/cookies.sqlite"))
            return False
        mozilla = home / ".mozilla" / "firefox"
        if not mozilla.is_dir():
            return False
        return any(mozilla.glob("**/cookies.sqlite"))
    if name == "safari":
        safari = home / "Library" / "Cookies" / "Cookies.binarycookies"
        return safari.is_file()
    rels = _BROWSER_CONFIG_DIRS.get(name)
    if rels is None:
        return True
    if sys.platform == "darwin":
        app_support = home / "Library" / "Application Support"
        for rel in _BROWSER_APP_SUPPORT_DIRS.get(name, ()):
            base = app_support / Path(rel)
            if base.is_dir() and any(base.glob("**/Cookies")):
                return True
        return False
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA")
        if not local:
            return False
        root = Path(local)
        win_rels = _BROWSER_WIN_USERDATA.get(name)
        if not win_rels:
            return True
        for rel in win_rels:
            base = root / Path(rel)
            if base.is_dir() and any(base.glob("**/Cookies")):
                return True
        return False
    if not sys.platform.startswith("linux"):
        return True
    for rel in rels:
        base = home / ".config" / Path(rel)
        if not base.is_dir():
            continue
        if any(base.glob("**/Cookies")):
            return True
    return False


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = Field(..., description="Telegram Bot API token")
    telegram_channel_id: str = Field(
        ...,
        description="Target channel ID (@username or -100…)",
    )

    max_video_size_mb: float = Field(default=50.0, ge=0.1, le=2000.0)
    temp_dir: Path = Field(default=Path("temp"))
    log_dir: Path = Field(default=Path("logs"))
    log_level: str = Field(default="INFO")

    download_retries: int = Field(default=3, ge=1, le=10)
    download_timeout_seconds: float = Field(default=600.0, ge=30.0)
    upload_retries: int = Field(default=3, ge=1, le=10)
    max_concurrent_downloads: int = Field(default=3, ge=1, le=20)

    health_host: str = Field(default="0.0.0.0")
    health_port: int = Field(default=8080, ge=1, le=65535)

    log_max_bytes: int = Field(default=10 * 1024 * 1024, ge=1024)
    log_backup_count: int = Field(default=5, ge=1, le=50)

    #: Netscape cookies.txt (see yt-dlp README). Strongly recommended for Instagram from a VPS.
    ytdlp_cookiefile: Path | None = Field(
        default=None,
        validation_alias=AliasChoices("YTDLP_COOKIEFILE"),
    )

    #: e.g. "chrome" — yt-dlp reads cookies from the browser (local Mac + Instagram in Chrome).
    ytdlp_cookies_from_browser: str | None = Field(
        default=None,
        validation_alias=AliasChoices("YTDLP_COOKIES_FROM_BROWSER"),
    )

    #: Re-encode to H.264 yuv420p + faststart for Telegram inline playback.
    telegram_reencode_mp4: bool = Field(
        default=True,
        validation_alias=AliasChoices("TELEGRAM_REENCODE_MP4"),
    )

    @field_validator("temp_dir", "log_dir", mode="before")
    @classmethod
    def coerce_path(cls, v: str | Path) -> Path:
        return Path(v).expanduser() if not isinstance(v, Path) else v

    @field_validator("ytdlp_cookiefile", mode="before")
    @classmethod
    def optional_cookie_path(cls, v: str | Path | None) -> Path | None:
        if v is None or v == "":
            return None
        return Path(v).expanduser() if not isinstance(v, Path) else v

    @field_validator("ytdlp_cookies_from_browser", mode="before")
    @classmethod
    def optional_browser_cookies(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s or None

    @model_validator(mode="after")
    def skip_browser_cookies_without_local_db(self) -> Self:
        spec = self.ytdlp_cookies_from_browser
        if not spec:
            return self
        head = _ytdlp_browser_head(spec)
        if head is None:
            return self
        if _browser_cookie_database_likely_present_for_spec(spec):
            return self
        logger.info(
            "YTDLP_COOKIES_FROM_BROWSER=%r: локальная БД cookies не найдена — "
            "отключаем (типично для VPS). Для Instagram задайте YTDLP_COOKIEFILE.",
            spec,
        )
        self.ytdlp_cookies_from_browser = None
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
