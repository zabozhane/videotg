from __future__ import annotations

import logging

from aiohttp import web

from videobot.config.settings import Settings

logger = logging.getLogger(__name__)


async def health(_request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def run_health_server(settings: Settings) -> web.AppRunner:
    app = web.Application()
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=settings.health_host, port=settings.health_port)
    await site.start()
    logger.info("Healthcheck listening on %s:%s", settings.health_host, settings.health_port)
    return runner


async def stop_health_server(runner: web.AppRunner | None) -> None:
    if runner is None:
        return
    await runner.cleanup()
