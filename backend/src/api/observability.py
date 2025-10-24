"""
Observability API - Prometheus metrics endpoint
FR-001, FR-004: 14 core metrics 노출
"""
from fastapi import APIRouter
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.responses import Response

router = APIRouter()

# 14 Core Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=[0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4],
)

http_request_size_bytes = Histogram(
    "http_request_size_bytes",
    "HTTP request size",
    ["method", "endpoint"],
)

http_response_size_bytes = Histogram(
    "http_response_size_bytes",
    "HTTP response size",
    ["method", "endpoint"],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests in progress",
    ["method", "endpoint"],
)

db_connection_pool_size = Gauge(
    "db_connection_pool_size",
    "DB pool size",
    ["service"],
)

db_connection_pool_in_use = Gauge(
    "db_connection_pool_in_use",
    "DB connections in use",
    ["service"],
)

db_connection_pool_available = Gauge(
    "db_connection_pool_available",
    "DB connections available",
    ["service"],
)

db_connection_pool_waiting = Gauge(
    "db_connection_pool_waiting",
    "Requests waiting for DB connection",
    ["service"],
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "DB query duration",
    ["query_type"],
)

http_client_pool_size = Gauge(
    "http_client_pool_size",
    "HTTP client pool size",
    ["host"],
)

http_client_pool_in_use = Gauge(
    "http_client_pool_in_use",
    "HTTP client connections in use",
    ["host"],
)

http_client_waiting_requests = Gauge(
    "http_client_waiting_requests",
    "Requests waiting for HTTP connection",
    ["host"],
)

celery_tasks_total = Counter(
    "celery_tasks_total",
    "Total Celery tasks",
    ["task_name", "status"],
)

# --- 시나리오 테스트용 신규 메트릭 ---

# 1) 동시 기부 Race 재현용
bodam_donation_duplicate_total = Counter(
    "bodam_donation_duplicate_total",
    "Total duplicate donation creation attempts detected",
    ["fire_station_id"],
)

# 2) 결제 멱등성 테스트용
bodam_payment_idempotency_key_hit_total = Counter(
    "bodam_payment_idempotency_key_hit_total",
    "Total payment confirmation requests hitting the idempotency key cache",
)

# 1) DB Deadlock 감지용
db_deadlocks_total = Counter(
    "db_deadlocks_total",
    "Total database deadlocks detected",
    ["transaction_name"],
)

@router.get("/metrics")
def metrics():
    """FR-001, FR-004: Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
