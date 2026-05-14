from __future__ import annotations

import asyncio
import logging
import signal
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

from videobot.app_lifecycle.health import run_health_server, stop_health_server
from videobot.config.settings import get_settings
from videobot.logging_setup.init_logging import setup_logging
from videobot.telegram_bot.handlers import build_router

logger = logging.getLogger(__name__)


async def run_app() -> None:
    settings = get_settings()
    setup_logging(settings)
    settings.temp_dir.mkdir(parents=True, exist_ok=True)

    bot = Bot(
        token=settings.bot_token,
        session=AiohttpSession(timeout=float(settings.telegram_api_session_timeout_seconds)),
    )
    dp = Dispatcher()
    sem = asyncio.Semaphore(settings.max_concurrent_downloads)
    dp.include_router(build_router(settings, sem))

    wh = await bot.get_webhook_info()
    if wh.url:
        logger.info("Webhook was set (%s), removing for polling", wh.url)
    await bot.delete_webhook(drop_pending_updates=False)

    health_runner: Any = None
    stop_event = asyncio.Event()

    def _request_shutdown() -> None:
        logger.info("Shutdown requested")
        stop_event.set()

    loop = asyncio.get_running_loop()
    signals = (signal.SIGINT, signal.SIGTERM)
    for sig in signals:
        try:
            loop.add_signal_handler(sig, _request_shutdown)
        except NotImplementedError:
            pass

    try:
        health_runner = await run_health_server(settings)
        poll_task = asyncio.create_task(dp.start_polling(bot), name="polling")
        wait_task = asyncio.create_task(stop_event.wait(), name="stop-wait")
        done, pending = await asyncio.wait(
            {poll_task, wait_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        for t in pending:
            t.cancel()
        for t in done:
            if t is poll_task and not t.cancelled():
                exc = t.exception()
                if exc:
                    logger.error("Polling ended with error: %s", exc)
        await asyncio.gather(*pending, return_exceptions=True)
    finally:
        for sig in signals:
            try:
                loop.remove_signal_handler(sig)
            except NotImplementedError:
                pass
        await stop_health_server(health_runner)
        await bot.session.close()
        logger.info("Shutdown complete")


def main() -> None:
    asyncio.run(run_app())
