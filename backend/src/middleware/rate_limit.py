"""Simple in-memory rate limiting middleware for development."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Naive token bucket rate limiter keyed by client IP."""

    def __init__(self, app, *, requests_per_minute: int = 60) -> None:  # type: ignore[override]
        super().__init__(app)
        self._requests_per_minute = requests_per_minute
        self._hits = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        client_ip = request.client.host if request.client else "anonymous"
        window_start = time.time() - 60
        self._hits[client_ip] = [ts for ts in self._hits[client_ip] if ts >= window_start]

        if len(self._hits[client_ip]) >= self._requests_per_minute:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"},
            )

        self._hits[client_ip].append(time.time())
        return await call_next(request)


__all__ = ["RateLimitMiddleware"]
