"""Security configuration values."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class SecuritySettings:
    cookie_domain: str = os.getenv("COOKIE_DOMAIN", ".bodam.example")
    cookie_secure: bool = os.getenv("COOKIE_SECURE", "true").lower() == "true"
    cookie_samesite: str = os.getenv("COOKIE_SAMESITE", "None")
    allowed_origins: list[str] = os.getenv("ALLOWED_ORIGINS", "https://app.bodam.example").split(",")


__all__ = ["SecuritySettings"]
