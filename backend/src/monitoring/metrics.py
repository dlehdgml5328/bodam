"""Prometheus metrics registry."""

from __future__ import annotations

from prometheus_client import REGISTRY, Counter, Histogram, generate_latest

# # -> 살려?
# from fastapi import FastAPI, Response
# app = FastAPI()

REQUEST_COUNT = Counter("bodam_requests_total", "Total HTTP requests", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("bodam_request_duration_seconds", "Request latency", ["path"])


def export_metrics() -> bytes:
    return generate_latest(REGISTRY)

# @app.get("/")
# def hello():
#     REQUESTS.inc()   # 카운터 +1
#     return {"msg": "hello"}

# @app.get("/metrics")
# def metrics():
#     return Response(generate_latest(), media_type="text/plain")



__all__ = ["REQUEST_COUNT", "REQUEST_LATENCY", "export_metrics"]

# # ---- 1022 새로운 파일로 대체 ---- 아래로 쭉
# import time
# from fastapi import APIRouter, Response, Request, FastAPI
# from prometheus_client import (
#     Counter, Histogram, Gauge,
#     generate_latest, CONTENT_TYPE_LATEST
# )

# router = APIRouter(tags=["Monitoring"])

# # ---- 메트릭 정의 ----
# REQUEST_COUNT = Counter(
#     "fastapi_request_count",
#     "Total request count",
#     ["method", "endpoint", "status_code"],
# )
# REQUEST_LATENCY = Histogram(
#     "fastapi_request_latency_seconds",
#     "Request latency in seconds",
#     ["endpoint"],
# )
# ALIVE = Gauge("fastapi_app_alive", "If app is alive: 1")
# ALIVE.set(1)

# # ---- /metrics 엔드포인트 ----
# @router.get("/metrics")
# def metrics():
#     return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# # ---- 앱에 미들웨어를 붙이는 헬퍼 ----1022
# def attach_metrics_middleware(app: FastAPI):
#     @app.middleware("http")
#     async def prometheus_middleware(request: Request, call_next):
#         start = time.time()
#         response = await call_next(request)
#         duration = time.time() - start

#         REQUEST_COUNT.labels(
#             request.method, request.url.path, str(response.status_code)
#         ).inc()
#         REQUEST_LATENCY.labels(request.url.path).observe(duration)
#         return response
