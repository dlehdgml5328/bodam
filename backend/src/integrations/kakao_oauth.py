"""Kakao OAuth client helper."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlencode

KAKAO_AUTH_BASE = "https://kauth.kakao.com/oauth/authorize"


@dataclass
class KakaoOAuthSettings:
    client_id: str
    redirect_uri: str
    response_type: str = "code"

    @classmethod
    def from_env(cls) -> "KakaoOAuthSettings":
        return cls(
            client_id=os.getenv("KAKAO_CLIENT_ID", "test"),
            redirect_uri=os.getenv("KAKAO_REDIRECT_URI", "http://localhost:8000/auth/kakao"),
        )


def build_authorize_url(state: str, settings: KakaoOAuthSettings | None = None) -> str:
    settings = settings or KakaoOAuthSettings.from_env()
    query = urlencode(
        {
            "client_id": settings.client_id,
            "redirect_uri": settings.redirect_uri,
            "response_type": settings.response_type,
            "state": state,
        }
    )
    return f"{KAKAO_AUTH_BASE}?{query}"


__all__ = ["build_authorize_url", "KakaoOAuthSettings"]
