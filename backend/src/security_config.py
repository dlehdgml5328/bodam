"""Security configuration values."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class SecuritySettings:
    cookie_domain: str | None = os.getenv("COOKIE_DOMAIN") or None
    cookie_secure: bool = os.getenv("COOKIE_SECURE", "true").lower() == "true"
    cookie_samesite: str = os.getenv("COOKIE_SAMESITE", "None")
    allowed_origins: List[str] = field(
        default_factory=lambda: os.getenv(
            "ALLOWED_ORIGINS", "https://app.bodam.example"
        ).split(",")
    )
    jwt_secret: str = os.getenv("JWT_SECRET") or os.getenv("JWT_SECRET_KEY", "change-me-secret")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_private_key: str | None = os.getenv("JWT_PRIVATE_KEY")
    jwt_public_key: str | None = os.getenv("JWT_PUBLIC_KEY")
    access_token_ttl_minutes: int = int(os.getenv("ACCESS_TOKEN_TTL", "15"))  # 15분 (SECURITY.md 기준)
    refresh_token_ttl_minutes: int = int(os.getenv("REFRESH_TOKEN_TTL", "10080"))  # 7일 = 10080분
    password_reset_token_minutes: int = int(os.getenv("PASSWORD_RESET_TOKEN_TTL", "30"))

    def __post_init__(self) -> None:
        """Validate JWT configuration after initialization."""
        if self.jwt_algorithm.startswith("RS") or self.jwt_algorithm.startswith("ES"):
            if not self.jwt_private_key or not self.jwt_public_key:
                raise ValueError(
                    f"JWT algorithm {self.jwt_algorithm} requires both "
                    "JWT_PRIVATE_KEY and JWT_PUBLIC_KEY environment variables"
                )
        elif self.jwt_algorithm.startswith("HS"):
            if len(self.jwt_secret) < 32:
                raise ValueError(
                    "JWT_SECRET must be at least 32 characters long for HMAC algorithms"
                )

    @property
    def jwt_signing_key(self) -> str:
        """Get the appropriate signing key based on algorithm."""
        if self.jwt_algorithm.startswith("RS") or self.jwt_algorithm.startswith("ES"):
            return self.jwt_private_key or ""
        else:
            return self.jwt_secret

    @property
    def jwt_verifying_key(self) -> str:
        """Get the appropriate verifying key based on algorithm."""
        if self.jwt_algorithm.startswith("RS") or self.jwt_algorithm.startswith("ES"):
            return self.jwt_public_key or ""
        else:
            return self.jwt_secret


@lru_cache
def get_security_settings() -> SecuritySettings:
    return SecuritySettings()


__all__ = ["SecuritySettings", "get_security_settings"]
