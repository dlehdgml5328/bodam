"""Runtime configuration for cache layers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

# Load env if dotenv available (mirrors other config modules)
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - optional dependency
    pass


@dataclass(frozen=True)
class CacheSettings:
    """Settings for standard Redis cache and semantic cache."""

    cache_url: str = os.getenv("REDIS_CACHE_URL", "redis://redis-cache-service:6379/0")
    semantic_url: str = os.getenv(
        "REDIS_SEMANTIC_URL", "redis://redis-semantic-service:6379/0"
    )
    default_cache_ttl_seconds: int = int(os.getenv("CACHE_DEFAULT_TTL", "300"))
    default_semantic_ttl_seconds: int = int(os.getenv("SEMANTIC_CACHE_TTL", "3600"))
    embed_provider: str = os.getenv("EMBED_PROVIDER", "together")
    embed_model: str = os.getenv("EMBED_MODEL", "text-embedding-3-small")
    embed_dimension: int = int(os.getenv("EMBED_DIM", "1536"))
    embed_timeout_seconds: float = float(os.getenv("EMBED_TIMEOUT_SECONDS", "10"))
    embed_fallback_provider: str | None = os.getenv("EMBED_FALLBACK_PROVIDER")


@lru_cache
def get_cache_settings() -> CacheSettings:
    return CacheSettings()


__all__ = ["CacheSettings", "get_cache_settings"]
