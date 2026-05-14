from __future__ import annotations

import asyncio
import logging
import random
from pathlib import Path

from aiogram import Bot
from aiogram.types import FSInputFile

from videobot.config.settings import Settings

logger = logging.getLogger(__name__)


async def publish_video_to_channel(bot: Bot, settings: Settings, video_path: Path) -> None:
    max_bytes = int(settings.max_video_size_mb * 1024 * 1024)
    size = await asyncio.to_thread(lambda: video_path.stat().st_size)
    if size > max_bytes:
        raise ValueError(f"Видео {size} B больше лимита {max_bytes} B")

    last: BaseException | None = None
    for attempt in range(1, settings.upload_retries + 1):
        try:
            await bot.send_video(
                chat_id=settings.telegram_channel_id,
                video=FSInputFile(video_path),
            )
            logger.info("Published %s to channel (attempt %s)", video_path.name, attempt)
            return
        except Exception as exc:  # noqa: BLE001
            last = exc
            logger.warning("Upload attempt %s failed: %s", attempt, exc)
            if attempt < settings.upload_retries:
                await asyncio.sleep(min(2 ** (attempt - 1), 20) + random.uniform(0, 0.3))
    msg = f"Не удалось загрузить в канал после {settings.upload_retries} попыток"
    raise RuntimeError(msg) from last
