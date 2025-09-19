"""Google OAuth client helper."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlencode

GOOGLE_AUTH_BASE = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://openidconnect.googleapis.com/v1/userinfo"


@dataclass
class GoogleOAuthSettings:
    client_id: str
    client_secret: str
    redirect_uri: str
    scope: str = "openid email profile"

    @classmethod
    def from_env(cls) -> "GoogleOAuthSettings":
        return cls(
            client_id=os.getenv("GOOGLE_CLIENT_ID", "test"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET", "test"),
            redirect_uri=os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google"),
        )


def build_authorize_url(state: str, settings: GoogleOAuthSettings | None = None) -> str:
    settings = settings or GoogleOAuthSettings.from_env()
    query = urlencode(
        {
            "client_id": settings.client_id,
            "redirect_uri": settings.redirect_uri,
            "response_type": "code",
            "scope": settings.scope,
            "state": state,
        }
    )
    return f"{GOOGLE_AUTH_BASE}?{query}"


__all__ = ["build_authorize_url", "GoogleOAuthSettings"]
