"""Naver OAuth client helper."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlencode

NAVER_AUTH_BASE = "https://nid.naver.com/oauth2.0/authorize"


@dataclass
class NaverOAuthSettings:
    client_id: str
    redirect_uri: str
    response_type: str = "code"

    @classmethod
    def from_env(cls) -> "NaverOAuthSettings":
        return cls(
            client_id=os.getenv("NAVER_CLIENT_ID", "test"),
            redirect_uri=os.getenv("NAVER_REDIRECT_URI", "http://localhost:8000/auth/naver"),
        )


def build_authorize_url(state: str, settings: NaverOAuthSettings | None = None) -> str:
    settings = settings or NaverOAuthSettings.from_env()
    query = urlencode(
        {
            "client_id": settings.client_id,
            "redirect_uri": settings.redirect_uri,
            "response_type": settings.response_type,
            "state": state,
        }
    )
    return f"{NAVER_AUTH_BASE}?{query}"


__all__ = ["build_authorize_url", "NaverOAuthSettings"]
