"""Re-encode downloaded video so Telegram clients decode video track reliably."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def transcode_for_telegram(src: Path, *, ffmpeg_timeout_s: float = 1800.0) -> Path:
    """
    H.264 Main + yuv420p + AAC + faststart for Telegram inline playback.
    Удаляет исходник при успехе; при ошибке возвращает исходный путь.
    """
    if not src.is_file():
        return src
    if shutil.which("ffmpeg") is None:
        logger.warning("ffmpeg не найден в PATH, пропускаю перекодировку для Telegram")
        return src

    out = src.with_name(f"{src.stem}.tg{src.suffix}")
    if out == src:
        out = src.with_name(f"{src.stem}.tg.mp4")

    last_err: subprocess.CalledProcessError | None = None

    cmd_with_audio = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "warning",
        "-i",
        str(src),
        "-map",
        "0:v:0",
        "-map",
        "0:a:0",
        "-c:v",
        "libx264",
        "-threads",
        "0",
        "-profile:v",
        "main",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        str(out),
    ]
    cmd_video_only = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "warning",
        "-i",
        str(src),
        "-map",
        "0:v:0",
        "-an",
        "-c:v",
        "libx264",
        "-threads",
        "0",
        "-profile:v",
        "main",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-movflags",
        "+faststart",
        str(out),
    ]

    for cmd in (cmd_with_audio, cmd_video_only):
        try:
            subprocess.run(
                cmd,
                check=True,
                timeout=ffmpeg_timeout_s,
                capture_output=True,
                text=True,
            )
            break
        except subprocess.CalledProcessError as exc:
            last_err = exc
            out.unlink(missing_ok=True)
            continue
        except subprocess.TimeoutExpired:
            out.unlink(missing_ok=True)
            logger.warning("Перекодировка: превышен таймаут ffmpeg")
            return src
    else:
        logger.warning(
            "Перекодировка для Telegram не удалась, отправляю исходник. stderr=%s",
            (last_err.stderr or "")[:800] if last_err else "",
        )
        return src

    try:
        src.unlink()
    except OSError as exc:
        logger.warning("Не удалось удалить исходник после перекодировки: %s", exc)
    logger.info("Видео перекодировано для Telegram: %s", out.name)
    return out
