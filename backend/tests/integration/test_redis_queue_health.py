"""Integration tests for Redis queue deployment (T005)."""

from __future__ import annotations

import asyncio
import os
import subprocess

import pytest

REDIS_QUEUE_HOST = os.getenv("TEST_REDIS_QUEUE_HOST", "127.0.0.1")
REDIS_QUEUE_PORT = int(os.getenv("TEST_REDIS_QUEUE_PORT", "6379"))
PVC_NAME = "redis-queue-data"

pytestmark = pytest.mark.asyncio


async def _ping_database(db_index: int) -> bytes:
    """Connect to Redis queue, select DB, and issue PING."""
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(REDIS_QUEUE_HOST, REDIS_QUEUE_PORT),
            timeout=2,
        )
    except Exception as exc:  # pragma: no cover - fail fast pre-implementation
        pytest.fail(f"Failed to connect to Redis queue: {exc}")

    try:
        if db_index:
            select_cmd = (
                b"*2\r\n$6\r\nSELECT\r\n$" + str(db_index).encode() + b"\r\n" + str(db_index).encode() + b"\r\n"
            )
            writer.write(select_cmd)
            await writer.drain()
            await asyncio.wait_for(reader.read(64), timeout=2)

        writer.write(b"*1\r\n$4\r\nPING\r\n")
        await writer.drain()
        response = await asyncio.wait_for(reader.read(64), timeout=2)
    finally:
        writer.close()
        await writer.wait_closed()

    return response


async def test_redis_queue_broker_ping() -> None:
    """Redis queue broker (DB 0) must respond with PONG."""
    response = await _ping_database(0)
    assert response.strip() == b"+PONG", "Redis queue broker did not respond with PONG"


async def test_redis_queue_backend_ping() -> None:
    """Redis queue result backend (DB 1) must respond with PONG."""
    response = await _ping_database(1)
    assert response.strip() == b"+PONG", "Redis queue backend did not respond with PONG"


async def test_redis_queue_pvc_is_bound() -> None:
    """Queue Redis must have a bound PVC for data persistence."""
    result = await asyncio.to_thread(
        subprocess.run,
        [
            "kubectl",
            "get",
            "pvc",
            PVC_NAME,
            "-o",
            "jsonpath={.status.phase}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        "kubectl get pvc failed: " + result.stderr.strip()
    )
    assert result.stdout.strip() == "Bound", "Redis queue PVC is not bound"
