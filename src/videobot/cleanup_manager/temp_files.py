from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

logger = logging.getLogger(__name__)


@asynccontextmanager
async def managed_temp_path(path: Path) -> AsyncIterator[Path]:
    """Ensure a temp file is removed when the context exits (success or error)."""
    try:
        yield path
    finally:
        await asyncio.to_thread(_unlink_quiet, path)


def _unlink_quiet(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
        logger.debug("Removed temp file %s", path)
    except OSError as exc:
        logger.warning("Could not remove temp file %s: %s", path, exc)
