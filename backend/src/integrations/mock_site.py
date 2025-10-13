"""Client helpers for the mock fire station site."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://dlehdgml5328.github.io/mock-fire-station-site"
INCIDENTS_PATH = "data/incidents.json"


def _root_dir() -> Path:
    return Path(__file__).resolve().parents[3]


def load_local_incidents() -> list[dict[str, Any]]:
    """Load bundled mock incidents as a local fallback."""
    path = _root_dir() / "mock-site" / "data" / "incidents.json"
    if not path.exists():
        logger.warning("[MockSite] Local incident file missing: %s", path)
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.error("[MockSite] Failed to parse local incident file: %s", exc)
        return []
    if not isinstance(data, list):
        logger.error("[MockSite] Local incident file has invalid structure")
        return []
    return data


class MockFireNewsClient:
    """HTTP client for retrieving incidents from the mock fire site."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float = 5.0,
    ) -> None:
        raw_base = base_url or os.getenv("MOCK_SITE_BASE_URL", DEFAULT_BASE_URL)
        self.base_url = raw_base.rstrip("/")
        self.timeout = timeout

    async def fetch_incidents(self) -> list[dict[str, Any]]:
        url = f"{self.base_url}/{INCIDENTS_PATH}"
        logger.debug("[MockSite] Fetching incidents from %s", url)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            payload = response.json()

        if not isinstance(payload, list):
            raise ValueError("Incident payload is not a list")
        return payload


__all__ = ["MockFireNewsClient", "load_local_incidents"]
