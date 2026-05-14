from __future__ import annotations

import asyncio
import logging
from typing import Any

from aiogram import Bot, F, Router
from aiogram.enums import ChatAction
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from videobot.cleanup_manager.temp_files import managed_temp_path
from videobot.config.settings import Settings
from videobot.downloaders.exceptions import DownloadFailed, SizeExceededError
from videobot.downloaders.factory import downloader_for_platform
from videobot.downloaders.telegram_compat import transcode_for_telegram
from videobot.publisher.publish import publish_video_to_channel
from videobot.validators.urls import VideoPlatform, validate_video_url

logger = logging.getLogger(__name__)


async def _upload_video_heartbeat(bot: Bot, chat_id: int, stop: asyncio.Event) -> None:
    """Telegram chat actions expire ~5s; refresh so the user sees the bot is still working."""
    while not stop.is_set():
        try:
            await bot.send_chat_action(chat_id, ChatAction.UPLOAD_VIDEO)
        except Exception:
            logger.debug("send_chat_action failed", exc_info=True)
        try:
            await asyncio.wait_for(stop.wait(), timeout=4.5)
        except TimeoutError:
            continue


def _first_http_url(text: str) -> str | None:
    for token in text.strip().split():
        if token.startswith(("http://", "https://")):
            return token
    return None


def build_router(settings: Settings, semaphore: asyncio.Semaphore) -> Router:
    router = Router(name="main")

    @router.message(CommandStart())
    async def cmd_start(message: Message) -> None:
        await message.answer(
            "Пришлите ссылку на видео с Instagram, YouTube или Reddit — "
            "бот скачает и опубликует его в канале (см. /help)."
        )

    @router.message(Command("help"))
    async def cmd_help(message: Message) -> None:
        await message.answer(
            "Команды:\n"
            "/start — кратко о боте\n"
            "/help — эта справка\n"
            "/status — состояние\n\n"
            "Отправьте одну ссылку в сообщении. Поддерживаются Instagram (пост/Reels), "
            "YouTube (ролик/Shorts) и Reddit (пост с видео)."
        )

    @router.message(Command("status"))
    async def cmd_status(message: Message) -> None:
        await message.answer("Бот работает, загрузки ограничены семафором конкурентности.")

    @router.message(F.text)
    async def on_text(message: Message, bot: Bot) -> None:
        text = (message.text or "").strip()
        if "http://" not in text and "https://" not in text:
            return
        url = _first_http_url(text)
        if url is None:
            return
        try:
            validated = validate_video_url(url)
        except ValueError as exc:
            await message.answer(str(exc))
            return

        await message.answer(
            "Принял ссылку, начинаю загрузку…\n\n"
            "У Instagram это часто 1–5 минут (скачивание DASH + склейка ffmpeg). "
            "Дождитесь следующего сообщения, не отправляйте ссылку повторно.",
        )

        task = asyncio.create_task(
            _run_pipeline(message, bot, settings, semaphore, validated.url, validated.platform),
            name=f"dl:{message.chat.id}:{message.message_id}",
        )

        def _done(t: asyncio.Task[Any]) -> None:
            try:
                t.result()
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception("Background pipeline failed")

        task.add_done_callback(_done)

    return router


async def _run_pipeline(
    message: Message,
    bot: Bot,
    settings: Settings,
    semaphore: asyncio.Semaphore,
    url: str,
    platform: VideoPlatform,
) -> None:
    async with semaphore:
        stop_hb = asyncio.Event()
        hb_task = asyncio.create_task(
            _upload_video_heartbeat(bot, message.chat.id, stop_hb),
            name=f"hb:{message.chat.id}:{message.message_id}",
        )
        try:
            downloader = downloader_for_platform(platform, settings)
            logger.info("Download start platform=%s chat=%s", platform, message.chat.id)
            try:
                path = await downloader.download(url)
            except SizeExceededError as exc:
                await message.answer(f"Файл слишком большой: {exc}")
                return
            except DownloadFailed as exc:
                await message.answer(str(exc))
                return

            if settings.telegram_reencode_mp4:
                path = await asyncio.to_thread(
                    transcode_for_telegram,
                    path,
                    ffmpeg_timeout_s=min(settings.download_timeout_seconds, 3600.0),
                )

            async with managed_temp_path(path):
                try:
                    await publish_video_to_channel(bot, settings, path)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Publish failed")
                    await message.answer(f"Скачал, но не смог опубликовать в канал: {exc}")
                    return

            await message.answer("Готово: видео отправлено в канал.")
            logger.info("Pipeline OK chat=%s", message.chat.id)
        finally:
            stop_hb.set()
            hb_task.cancel()
            try:
                await hb_task
            except asyncio.CancelledError:
                pass
