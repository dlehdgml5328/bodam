"""Prometheus metrics registry."""

from __future__ import annotations

from prometheus_client import Counter, Histogram, REGISTRY, generate_latest

REQUEST_COUNT = Counter("bodam_requests_total", "Total HTTP requests", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("bodam_request_duration_seconds", "Request latency", ["path"])


def export_metrics() -> bytes:
    return generate_latest(REGISTRY)


__all__ = ["REQUEST_COUNT", "REQUEST_LATENCY", "export_metrics"]
