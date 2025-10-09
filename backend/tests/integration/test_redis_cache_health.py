"""Integration tests for Redis cache deployment (T004)."""

from __future__ import annotations

import asyncio
import os

import pytest

REDIS_CACHE_HOST = os.getenv("TEST_REDIS_CACHE_HOST", "127.0.0.1")
REDIS_CACHE_PORT = int(os.getenv("TEST_REDIS_CACHE_PORT", "6379"))

pytestmark = pytest.mark.asyncio


async def _send_redis_command(command: bytes) -> bytes:
    """Send a raw Redis command and return the raw response."""
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(REDIS_CACHE_HOST, REDIS_CACHE_PORT),
            timeout=2,
        )
    except Exception as exc:  # pragma: no cover - intentional pre-implementation failure
        pytest.fail(f"Failed to connect to Redis cache: {exc}")

    try:
        writer.write(command)
        await writer.drain()
        response = await asyncio.wait_for(reader.read(1024), timeout=2)
    finally:
        writer.close()
        await writer.wait_closed()

    return response


async def test_redis_cache_health_ping() -> None:
    """Redis cache must respond to a PING command."""
    response = await _send_redis_command(b"*1\r\n$4\r\nPING\r\n")
    assert response.strip() == b"+PONG", "Redis cache did not respond with PONG"


async def test_redis_cache_accepts_commands_on_db0() -> None:
    """Redis cache must accept write commands on database 0."""
    set_response = await _send_redis_command(
        b"*3\r\n$3\r\nSET\r\n$14\r\n__health_check__\r\n$2\r\nok\r\n"
    )
    assert set_response.strip() == b"+OK", "Redis cache failed to store key in DB0"
