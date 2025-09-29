"""Rate limiting middleware with Redis backend."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

import redis.asyncio as redis
from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Rate limit configuration
RATE_LIMITS = {
    "/auth/login": "5/minute",
    "/auth/signup": "3/minute",
    "/auth/password-reset/request": "2/minute",
    "/donations": "10/minute",
    "/api/*": "100/minute",
    "default": "60/minute",
}


class RateLimitExceeded(HTTPException):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, retry_after: int) -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using sliding window algorithm with Redis."""

    def __init__(self, app: Any, redis_url: str = "redis://localhost:6379") -> None:
        super().__init__(app)
        self.redis_client = redis.from_url(redis_url, decode_responses=True)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        # Skip rate limiting for health checks and static files
        if request.url.path in ["/health", "/metrics"] or request.url.path.startswith("/static/"):
            return await call_next(request)

        # Get client identifier (prefer user ID if authenticated, fallback to IP)
        client_id = self._get_client_id(request)
        rate_limit = self._get_rate_limit(request.url.path)

        if rate_limit:
            await self._check_rate_limit(client_id, request.url.path, rate_limit)

        response = await call_next(request)
        return response

    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier for rate limiting."""
        # Try to get user ID from request state (set by auth middleware)
        if hasattr(request.state, "user_id") and request.state.user_id:
            return f"user:{request.state.user_id}"

        # Fallback to IP address
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

        return f"ip:{client_ip}"

    def _get_rate_limit(self, path: str) -> str | None:
        """Get rate limit configuration for the given path."""
        # Exact match first
        if path in RATE_LIMITS:
            return RATE_LIMITS[path]

        # Pattern matching for wildcard routes
        for pattern, limit in RATE_LIMITS.items():
            if pattern.endswith("/*") and path.startswith(pattern[:-2]):
                return limit

        # Default rate limit
        return RATE_LIMITS["default"]

    async def _check_rate_limit(self, client_id: str, path: str, rate_limit: str) -> None:
        """Check if client has exceeded rate limit using sliding window."""
        try:
            limit, period = self._parse_rate_limit(rate_limit)
            key = f"rate_limit:{client_id}:{path}:{period}"

            # Use sliding window counter with Redis
            current_time = int(asyncio.get_event_loop().time())
            window_start = current_time - period

            # Remove old entries and count current requests
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.expire(key, period + 1)

            results = await pipe.execute()
            current_requests = results[1]

            if current_requests >= limit:
                retry_after = period - (current_time % period)
                logger.warning(
                    "Rate limit exceeded for client %s on path %s: %d/%d requests",
                    client_id, path, current_requests, limit
                )
                raise RateLimitExceeded(retry_after)

            # Add current request
            await self.redis_client.zadd(key, {str(current_time): current_time})

            logger.debug(
                "Rate limit check passed for client %s on path %s: %d/%d requests",
                client_id, path, current_requests + 1, limit
            )

        except redis.RedisError as e:
            logger.error("Redis error in rate limiting: %s", e)
            # Allow request to pass through on Redis errors
        except RateLimitExceeded:
            raise
        except Exception as e:
            logger.error("Unexpected error in rate limiting: %s", e)
            # Allow request to pass through on unexpected errors

    def _parse_rate_limit(self, rate_limit: str) -> tuple[int, int]:
        """Parse rate limit string like '5/minute' into (limit, period_seconds)."""
        limit_str, period_str = rate_limit.split("/")
        limit = int(limit_str)

        period_map = {
            "second": 1,
            "minute": 60,
            "hour": 3600,
            "day": 86400,
        }

        period = period_map.get(period_str, 60)  # Default to minute
        return limit, period

    async def close(self) -> None:
        """Close Redis connection."""
        await self.redis_client.aclose()


__all__ = ["RateLimitMiddleware", "RateLimitExceeded", "RATE_LIMITS"]