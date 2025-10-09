"""Integration tests for Flower monitoring UI (T008)."""

from __future__ import annotations

import pytest
import httpx

FLOWER_API_URL = "https://bodam.example.com/flower/api/workers"
FLOWER_AUTH = ("admin", "admin123")

pytestmark = pytest.mark.asyncio


async def test_flower_ui_workers_endpoint_accessible() -> None:
    """Flower API should be reachable with basic auth."""
    async with httpx.AsyncClient(auth=FLOWER_AUTH, verify=False, timeout=5.0) as client:
        try:
            response = await client.get(FLOWER_API_URL)
        except Exception as exc:  # pragma: no cover - fail fast until infra exists
            pytest.fail(f"Flower API request failed: {exc}")

    assert response.status_code == 200, "Flower API did not return HTTP 200"
    assert isinstance(response.json(), dict), "Flower API did not return JSON data"
