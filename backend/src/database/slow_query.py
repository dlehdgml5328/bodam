"""Slow query logging helper."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from time import perf_counter

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("bodam.db")


@asynccontextmanager
async def slow_query_logger(session: AsyncSession, threshold_ms: float = 200.0):
    start = perf_counter()
    try:
        yield session
    finally:
        duration = (perf_counter() - start) * 1000
        if duration >= threshold_ms:
            logger.warning("Slow DB block detected", extra={"duration_ms": duration})
