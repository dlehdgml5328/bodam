"""JWT authentication middleware placeholder."""

from __future__ import annotations

import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Extracts bearer tokens and attaches them to request state."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1]
        elif "bodam_session" in request.cookies:
            token = request.cookies["bodam_session"]

        request.state.token = token
        logger.debug("Auth token resolved: %s", "set" if token else "missing")
        response = await call_next(request)
        return response


__all__ = ["AuthMiddleware"]
