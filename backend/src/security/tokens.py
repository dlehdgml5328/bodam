"""JWT helper utilities."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from src.config.security import get_security_settings


class TokenDecodeError(Exception):
    """Raised when a token cannot be decoded or is invalid."""


def create_access_token(subject: str, *, expires_minutes: int | None = None) -> str:
    settings = get_security_settings()
    expiry_minutes = expires_minutes or settings.access_token_ttl_minutes
    expire = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_signing_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_security_settings()
    try:
        return jwt.decode(token, settings.jwt_verifying_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:  # pragma: no cover - defensive guard
        raise TokenDecodeError("Invalid token") from exc

__all__ = ["create_access_token", "decode_access_token", "TokenDecodeError"]
