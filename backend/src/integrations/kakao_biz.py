"""Kakao Business API client."""

from __future__ import annotations

import os
from dataclasses import dataclass

import httpx


@dataclass
class KakaoBizSettings:
    api_key: str
    base_url: str = "https://api.kakao.com"

    @classmethod
    def from_env(cls) -> "KakaoBizSettings":
        return cls(
            api_key=os.getenv("KAKAO_BIZ_API_KEY", "test"),
            base_url=os.getenv("KAKAO_BIZ_BASE_URL", cls.base_url),
        )


class KakaoBizClient:
    def __init__(self, settings: KakaoBizSettings | None = None) -> None:
        self._settings = settings or KakaoBizSettings.from_env()
        self._client = httpx.AsyncClient(
            base_url=self._settings.base_url,
            headers={"Authorization": f"KakaoAK {self._settings.api_key}"},
        )

    async def send_notification(self, to: str, template_id: str, variables: dict) -> dict:
        # Placeholder call
        return {"to": to, "template_id": template_id, "status": "queued"}

    async def close(self) -> None:
        await self._client.aclose()


__all__ = ["KakaoBizClient", "KakaoBizSettings"]
