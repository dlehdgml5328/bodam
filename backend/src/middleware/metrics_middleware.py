"""
Metrics middleware - HTTP metrics 자동 수집
FR-001, FR-004: Status grouping (2xx, 4xx, 5xx)
"""
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from src.api.observability import (
    http_request_duration_seconds,
    http_request_size_bytes,
    http_requests_in_progress,
    http_requests_total,
    http_response_size_bytes,
)


def get_status_group(status_code: int) -> str:
    """Status grouping: 2xx, 4xx, 5xx"""
    if 200 <= status_code < 300:
        return "2xx"
    elif 400 <= status_code < 500:
        return "4xx"
    else:
        return "5xx"


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method
        endpoint = request.url.path

        # Request size
        request_size = int(request.headers.get("content-length", 0))
        http_request_size_bytes.labels(method=method, endpoint=endpoint).observe(request_size)

        # In progress
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

        start_time = time.time()
        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Status grouping
            status = get_status_group(response.status_code)

            # Metrics
            http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
            http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)

            # Response size
            response_size = int(response.headers.get("content-length", 0))
            http_response_size_bytes.labels(method=method, endpoint=endpoint).observe(response_size)

            return response
        finally:
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()
