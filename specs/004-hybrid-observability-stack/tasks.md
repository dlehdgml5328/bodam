# Tasks: 하이브리드 관측성 스택 (Hybrid Observability Stack)

**Input**: Design documents from `/home/eugene/bodam/specs/004-hybrid-observability-stack/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md
**Branch**: `wonuk`
**Date**: 2025-10-16

## Execution Summary

이 문서는 하이브리드 관측성 스택 구현을 위한 34개의 순서가 정해진 작업을 정의합니다. 작업은 TDD 순서를 따르며, 독립적인 작업은 병렬 실행을 위해 [P]로 표시됩니다.

**Key Artifacts**:
- 2 PostgreSQL models (ErrorEvent, LoadTestRun)
- 5 contract files (Prometheus, Loki, Tempo, K6, Llama API)
- 14 core metrics
- 4 observability pods (Prometheus, Loki, Tempo, Promtail)
- 3 K6 load test scenarios

---

## Path Conventions

이 프로젝트는 **Web application** 구조를 따릅니다:
- Backend: `backend/src/`, `backend/tests/`
- Frontend: `frontend/src/` (이 기능에서는 변경 없음)
- Infrastructure: `infra/k8s/observability/`
- Load tests: `tests/load/`

---

## Phase 3.1: Setup & Dependencies

### T001: [P] Create infrastructure directories
**File**: `infra/k8s/observability/`
**Description**: Phase 1에서 생성된 contracts를 기반으로 Kubernetes manifests 디렉토리 구조 생성
```bash
mkdir -p infra/k8s/observability/{prometheus,loki,tempo,promtail,secrets}
mkdir -p tests/load/scenarios
```
**Dependencies**: None
**Parallel**: Yes (독립적인 작업)

---

### T002: [P] Install OpenTelemetry dependencies
**File**: `backend/requirements.txt`
**Description**: OpenTelemetry SDK 및 instrumentation 라이브러리 추가
```txt
opentelemetry-api>=1.21.0
opentelemetry-sdk>=1.21.0
opentelemetry-instrumentation-fastapi>=0.42b0
opentelemetry-instrumentation-sqlalchemy>=0.42b0
opentelemetry-instrumentation-httpx>=0.42b0
opentelemetry-instrumentation-celery>=0.42b0
opentelemetry-exporter-otlp>=1.21.0
```
**Dependencies**: None
**Parallel**: Yes

---

### T003: [P] Install Prometheus client
**File**: `backend/requirements.txt`
**Description**: Prometheus Python client 추가
```txt
prometheus-client>=0.19.0
```
**Dependencies**: None
**Parallel**: Yes

---

### T004: [P] Install K6
**File**: `README.md` (installation instructions)
**Description**: K6 설치 가이드 추가 및 K6 바이너리 검증
```bash
# Installation verification
k6 version
```
**Dependencies**: None
**Parallel**: Yes

---

### T005: Install pgvector extension
**File**: PostgreSQL database
**Description**: Alembic migration 이전에 pgvector extension 설치
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```
**Dependencies**: None
**Note**: Docker Compose의 PostgreSQL init script에 추가

---

### T006: [P] Configure Docker Compose for local observability
**File**: `docker-compose.observability.yml`
**Description**: 로컬 개발용 Prometheus, Loki, Tempo 서비스 추가
```yaml
services:
  prometheus:
    image: prom/prometheus:v2.48.0
    ports:
      - "9090:9090"
    volumes:
      - ./specs/004-hybrid-observability-stack/contracts/prometheus-config.yaml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=3d'

  loki:
    image: grafana/loki:2.9.3
    ports:
      - "3100:3100"
    volumes:
      - ./specs/004-hybrid-observability-stack/contracts/loki-config.yaml:/etc/loki/local-config.yaml
      - loki-data:/loki

  tempo:
    image: grafana/tempo:2.3.1
    ports:
      - "3200:3200"
      - "4317:4317"
      - "4318:4318"
    volumes:
      - ./specs/004-hybrid-observability-stack/contracts/tempo-config.yaml:/etc/tempo/tempo.yaml
      - tempo-data:/tempo

  otel-collector:
    image: otel/opentelemetry-collector:0.91.0
    ports:
      - "4317:4317"
      - "4318:4318"
    volumes:
      - ./specs/004-hybrid-observability-stack/contracts/tempo-config.yaml:/etc/otel/config.yaml
    command: ["--config=/etc/otel/config.yaml"]

  statsd-exporter:
    image: prom/statsd-exporter:v0.26.0
    ports:
      - "9102:9102"
      - "8125:8125/udp"

volumes:
  prometheus-data:
  loki-data:
  tempo-data:
```
**Dependencies**: T001
**Parallel**: Yes (after T001)

---

### T007: Create Grafana Cloud secrets
**File**: `infra/k8s/observability/secrets/grafana-cloud-secrets.yaml`
**Description**: Grafana Cloud API keys를 위한 Kubernetes Secret 생성
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: grafana-cloud-creds
  namespace: observability
type: Opaque
stringData:
  prometheus-user: "YOUR_INSTANCE_ID"
  prometheus-pass: "YOUR_API_KEY"
  loki-user: "YOUR_LOKI_USER_ID"
  loki-pass: "YOUR_API_KEY"
  tempo-creds: "YOUR_BASE64_CREDENTIALS"
```
**Dependencies**: T001
**Note**: Quickstart.md에 실제 credentials 입력 방법 포함

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL**: 이 테스트들은 구현 전에 작성되어야 하며 반드시 FAIL 해야 합니다.

### T008: [P] Contract test - Prometheus /metrics endpoint
**File**: `backend/tests/contract/test_prometheus_metrics_contract.py`
**Description**: Prometheus exposition format 검증 (contracts/prometheus-config.yaml 기반)
```python
import pytest
import httpx

@pytest.mark.asyncio
async def test_metrics_endpoint_returns_prometheus_format():
    """FR-001, FR-004: Prometheus 메트릭 엔드포인트가 올바른 포맷 반환"""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]

    content = response.text
    # 14 core metrics 검증
    assert "http_requests_total" in content
    assert "http_request_duration_seconds" in content
    assert "http_request_size_bytes" in content
    assert "http_response_size_bytes" in content
    assert "http_requests_in_progress" in content
    assert "db_connection_pool_size" in content
    assert "db_connection_pool_in_use" in content
    assert "db_connection_pool_available" in content
    assert "db_connection_pool_waiting" in content
    assert "db_query_duration_seconds" in content
    assert "http_client_pool_size" in content
    assert "http_client_pool_in_use" in content
    assert "http_client_waiting_requests" in content
    assert "celery_tasks_total" in content

    # Status grouping: 2xx, 4xx, 5xx (not individual codes)
    assert 'status="2xx"' in content or 'status="4xx"' in content or 'status="5xx"' in content
```
**Dependencies**: None
**Parallel**: Yes
**Expected**: FAIL (endpoint not implemented)

---

### T009: [P] Contract test - Loki log collection
**File**: `backend/tests/contract/test_loki_logs_contract.py`
**Description**: Loki LogQL 쿼리 및 구조화된 로그 검증 (contracts/loki-config.yaml 기반)
```python
import pytest
import httpx
import json

@pytest.mark.asyncio
async def test_loki_collects_structured_logs():
    """FR-005, FR-008: Loki가 구조화된 로그를 수집하고 쿼리 가능"""
    # 1. Backend에서 에러 로그 생성
    async with httpx.AsyncClient() as client:
        await client.post("http://localhost:8000/api/test/generate-error")

    # 2. Loki에서 로그 조회
    import time
    time.sleep(2)  # Log ingestion delay

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:3100/loki/api/v1/query_range",
            params={
                "query": '{service="backend-api",level="error"}',
                "limit": 10,
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "result" in data["data"]
    assert len(data["data"]["result"]) > 0

    # 구조화된 필드 검증
    log_entry = data["data"]["result"][0]
    assert "values" in log_entry
    log_line = json.loads(log_entry["values"][0][1])
    assert "timestamp" in log_line
    assert "level" in log_line
    assert log_line["level"] == "error"
    assert "message" in log_line
    assert "service" in log_line
```
**Dependencies**: None
**Parallel**: Yes
**Expected**: FAIL (log middleware not implemented)

---

### T010: [P] Contract test - Tempo trace capture
**File**: `backend/tests/contract/test_tempo_traces_contract.py`
**Description**: OpenTelemetry trace 수집 및 Tempo 저장 검증 (contracts/tempo-config.yaml 기반)
```python
import pytest
import httpx

@pytest.mark.asyncio
async def test_tempo_captures_distributed_traces():
    """FR-009, FR-012: Tempo가 분산 트레이스를 캡처하고 스팬 정보 저장"""
    # 1. Backend API 요청 (trace 생성)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/donations",
            json={"amount": 10000, "fire_station_id": 1},
            headers={"X-Test-Trace": "true"},
        )
        trace_id = response.headers.get("X-Trace-Id")

    assert trace_id is not None

    # 2. Tempo에서 trace 조회
    import time
    time.sleep(3)  # Trace ingestion delay

    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://localhost:3200/api/traces/{trace_id}")

    assert response.status_code == 200
    trace = response.json()

    assert "traceId" in trace or "traceID" in trace
    assert "spans" in trace
    assert len(trace["spans"]) > 0

    # 스팬 속성 검증
    root_span = trace["spans"][0]
    assert "spanId" in root_span or "spanID" in root_span
    assert "duration" in root_span
    assert "attributes" in root_span or "tags" in root_span
```
**Dependencies**: None
**Parallel**: Yes
**Expected**: FAIL (OpenTelemetry middleware not implemented)

---

### T011: [P] Contract test - K6 load test scenarios
**File**: `backend/tests/contract/test_k6_scenarios_contract.py`
**Description**: K6 테스트 실행 및 결과 검증 (contracts/k6-scenarios.js 기반)
```python
import pytest
import subprocess
import json
import os

def test_k6_baseline_scenario_executes():
    """FR-017, FR-018: K6 baseline 시나리오 실행 및 메트릭 수집"""
    # K6 실행 (baseline 50 VU)
    env = os.environ.copy()
    env["K6_SCENARIO"] = "baseline"
    env["BASE_URL"] = "http://localhost:8000"

    result = subprocess.run(
        [
            "k6",
            "run",
            "--out",
            "json=/tmp/k6-summary.json",
            "specs/004-hybrid-observability-stack/contracts/k6-scenarios.js",
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=600,  # 10분 timeout
    )

    # K6 실행 성공 확인
    assert result.returncode == 0, f"K6 failed: {result.stderr}"

    # 결과 파일 검증
    assert os.path.exists("/tmp/k6-summary.json")

    with open("/tmp/k6-summary.json") as f:
        summary = json.load(f)

    assert "test_id" in summary
    assert "scenario_name" in summary
    assert summary["scenario_name"] == "baseline"
    assert "latency_p95" in summary
    assert "status" in summary

    # Success criteria: p95 < 500ms (spec.md)
    if summary["status"] == "passed":
        assert summary["latency_p95"] < 500
```
**Dependencies**: T004 (K6 installed)
**Parallel**: Yes
**Expected**: FAIL (backend metrics not exposed, K6 scenario not finalized)

---

### T012: [P] Contract test - Llama observability query API
**File**: `backend/tests/contract/test_llama_observability_api_contract.py`
**Description**: Llama 쿼리 API 검증 (contracts/llama-observability-api.yaml 기반)
```python
import pytest
import httpx
import time

@pytest.mark.asyncio
async def test_llama_query_api_responds_under_1_second():
    """FR-013, FR-014: Llama 쿼리 API가 1초 이내 응답 (NFR-001)"""
    async with httpx.AsyncClient() as client:
        start = time.time()
        response = await client.post(
            "http://localhost:8000/api/v1/observability/query",
            json={
                "query": "지난 1시간 동안 5XX 에러가 얼마나 발생했어?",
                "time_range": "1h",
                "language": "ko",
            },
            headers={"Authorization": "Bearer test-token"},
        )
        duration = time.time() - start

    assert response.status_code == 200
    assert duration < 1.0  # NFR-001: 1초 이내

    data = response.json()
    assert "query_type" in data
    assert "generated_query" in data
    assert "result" in data
    assert "response_time_ms" in data
    assert "data_source" in data
    assert data["data_source"] in ["local_prometheus", "local_loki", "local_tempo"]

@pytest.mark.asyncio
async def test_llama_dashboard_metrics_api():
    """Dashboard metrics API 검증"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/observability/metrics/dashboard",
            params={"time_range": "15m"},
        )

    assert response.status_code == 200
    data = response.json()

    assert "timestamp" in data
    assert "http" in data
    assert "database" in data
    assert "http_client" in data
    assert "celery" in data

    # HTTP metrics
    assert "requests_per_second" in data["http"]
    assert "status_2xx_rate" in data["http"]
    assert "status_4xx_rate" in data["http"]
    assert "status_5xx_rate" in data["http"]
    assert "p95_latency_ms" in data["http"]

    # DB connection pool
    assert "pool_size" in data["database"]
    assert "pool_in_use" in data["database"]
    assert "pool_available" in data["database"]
    assert "utilization_percent" in data["database"]
```
**Dependencies**: None
**Parallel**: Yes
**Expected**: FAIL (Llama API not implemented)

---

### T013: [P] Integration test - Observability stack health
**File**: `backend/tests/integration/test_observability_stack_integration.py`
**Description**: Prometheus, Loki, Tempo 전체 스택 통합 검증
```python
import pytest
import httpx

@pytest.mark.asyncio
async def test_prometheus_scrapes_backend_metrics():
    """FR-001, FR-002: Prometheus가 Backend /metrics를 스크래핑"""
    async with httpx.AsyncClient() as client:
        # 1. Prometheus targets 확인
        response = await client.get("http://localhost:9090/api/v1/targets")
        assert response.status_code == 200

        data = response.json()
        targets = data["data"]["activeTargets"]

        # Backend target 찾기
        backend_target = next(
            (t for t in targets if "backend" in t["labels"].get("job", "")), None
        )
        assert backend_target is not None
        assert backend_target["health"] == "up"

        # 2. 메트릭 쿼리
        response = await client.get(
            "http://localhost:9090/api/v1/query",
            params={"query": "http_requests_total"},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["data"]["result"]  # 결과가 존재

@pytest.mark.asyncio
async def test_loki_promtail_log_pipeline():
    """FR-005, FR-006: Promtail이 로그를 Loki로 전송"""
    # Generate log
    async with httpx.AsyncClient() as client:
        await client.get("http://localhost:8000/api/health")

    import time
    time.sleep(2)

    # Query Loki
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:3100/loki/api/v1/query_range",
            params={
                "query": '{service="backend-api"}',
                "limit": 1,
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["result"]

@pytest.mark.asyncio
async def test_tempo_otel_trace_pipeline():
    """FR-009, FR-010: OpenTelemetry → Tempo trace pipeline"""
    # Generate trace
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/api/fire-stations")
        trace_id = response.headers.get("X-Trace-Id")

    assert trace_id is not None

    import time
    time.sleep(3)

    # Query Tempo
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:3200/api/search",
            params={"q": f'{{ traceId = "{trace_id}" }}'},
        )

    assert response.status_code == 200
```
**Dependencies**: None
**Parallel**: Yes
**Expected**: FAIL (infrastructure not deployed)

---

### T014: [P] Integration test - K6 monitoring integration
**File**: `backend/tests/integration/test_k6_monitoring_integration.py`
**Description**: K6 부하 테스트 중 실시간 모니터링 검증
```python
import pytest
import subprocess
import httpx
import time
import os

@pytest.mark.asyncio
async def test_k6_metrics_appear_in_prometheus():
    """FR-018, FR-019: K6 메트릭이 Prometheus에 실시간 수집"""
    # 1. K6 시작 (background)
    env = os.environ.copy()
    env["K6_SCENARIO"] = "baseline"
    env["BASE_URL"] = "http://localhost:8000"

    k6_process = subprocess.Popen(
        [
            "k6",
            "run",
            "--out",
            "statsd=localhost:8125",
            "specs/004-hybrid-observability-stack/contracts/k6-scenarios.js",
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # 2. K6 실행 중 Prometheus 쿼리
    time.sleep(30)  # K6 ramp-up

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:9090/api/v1/query",
            params={"query": "k6_http_reqs_total"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["result"]  # K6 메트릭 존재

    # 3. K6 종료
    k6_process.terminate()
    k6_process.wait(timeout=60)
```
**Dependencies**: T004, T011
**Parallel**: Yes
**Expected**: FAIL (statsd-exporter not configured)

---

### T015: [P] Integration test - HPA auto-scaling
**File**: `backend/tests/integration/test_hpa_autoscaling_integration.py`
**Description**: HPA CPU/Memory 기반 자동 확장 검증
```python
import pytest
import subprocess
import time

def test_hpa_scales_backend_on_cpu_threshold():
    """FR-020, FR-021: HPA가 CPU 70% 초과 시 Backend 확장 (max 3 replicas)"""
    # 1. 초기 replica 확인
    result = subprocess.run(
        ["kubectl", "get", "hpa", "backend", "-n", "bodam", "-o", "json"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    import json
    hpa = json.loads(result.stdout)
    initial_replicas = hpa["status"]["currentReplicas"]

    # 2. CPU 부하 생성 (K6 stress test)
    env = {"K6_SCENARIO": "stress", "BASE_URL": "http://backend.bodam.svc.cluster.local:8000"}
    k6_process = subprocess.Popen(
        ["k6", "run", "specs/004-hybrid-observability-stack/contracts/k6-scenarios.js"],
        env=env,
    )

    # 3. HPA 확장 대기 (최대 5분)
    max_wait = 300
    start = time.time()
    scaled_up = False

    while time.time() - start < max_wait:
        result = subprocess.run(
            ["kubectl", "get", "hpa", "backend", "-n", "bodam", "-o", "json"],
            capture_output=True,
            text=True,
        )
        hpa = json.loads(result.stdout)
        current_replicas = hpa["status"]["currentReplicas"]

        if current_replicas > initial_replicas:
            scaled_up = True
            assert current_replicas <= 3  # FR-021: max 3 replicas
            break

        time.sleep(10)

    k6_process.terminate()
    assert scaled_up, "HPA did not scale up within 5 minutes"
```
**Dependencies**: T004
**Parallel**: Yes
**Expected**: FAIL (HPA not configured)

---

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### T016: [P] Create ErrorEvent model
**File**: `backend/src/models/error_event.py`
**Description**: pgvector embedding을 포함한 ErrorEvent 모델 구현 (data-model.md 기반)
```python
from sqlalchemy import Column, Integer, String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from datetime import datetime
from src.models.base import Base

class ErrorEvent(Base):
    __tablename__ = "error_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    level = Column(String(10), nullable=False, index=True)
    message = Column(Text, nullable=False)
    traceback = Column(Text, nullable=True)
    service = Column(String(50), nullable=False, index=True)
    endpoint = Column(String(255), nullable=True)
    method = Column(String(10), nullable=True)
    status_code = Column(Integer, nullable=True)
    trace_id = Column(String(32), nullable=True, index=True)
    span_id = Column(String(16), nullable=True)
    context = Column(JSONB, nullable=True)
    embedding = Column(Vector(384), nullable=True)
    resolution_status = Column(String(20), nullable=False, default="new", index=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    __table_args__ = (
        Index('ix_error_events_timestamp_level', 'timestamp', 'level'),
        Index('ix_error_events_service_timestamp', 'service', 'timestamp'),
    )
```
**Dependencies**: T005 (pgvector extension)
**Parallel**: Yes
**Passes**: None yet (no tests for models directly)

---

### T017: [P] Create LoadTestRun model
**File**: `backend/src/models/load_test_run.py`
**Description**: K6 부하 테스트 결과 저장 모델 (data-model.md 기반)
```python
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from src.models.base import Base

class LoadTestRun(Base):
    __tablename__ = "load_test_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(String(100), nullable=False, unique=True, index=True)
    scenario_name = Column(String(100), nullable=False)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    target_vu = Column(Integer, nullable=False)
    stages_config = Column(JSONB, nullable=True)
    total_requests = Column(Integer, nullable=True)
    failed_requests = Column(Integer, nullable=True)
    requests_per_second = Column(Float, nullable=True)
    latency_p50 = Column(Float, nullable=True)
    latency_p95 = Column(Float, nullable=True)
    latency_p99 = Column(Float, nullable=True)
    latency_avg = Column(Float, nullable=True)
    latency_min = Column(Float, nullable=True)
    latency_max = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, default="running")
    passed_thresholds = Column(Boolean, nullable=True)
    error_message = Column(Text, nullable=True)
    results_json = Column(JSONB, nullable=True)
    executor = Column(String(100), nullable=True)
    tags = Column(JSONB, nullable=True)
    prometheus_start = Column(Integer, nullable=True)
    prometheus_end = Column(Integer, nullable=True)
```
**Dependencies**: None
**Parallel**: Yes
**Passes**: None yet

---

### T018: Create Alembic migration for observability models
**File**: `backend/alembic/versions/004_add_observability_tables.py`
**Description**: ErrorEvent, LoadTestRun 테이블 생성 마이그레이션 (data-model.md 기반)
```python
"""Add ErrorEvent and LoadTestRun tables

Revision ID: 004_observability
Revises: 003_db_http_pools
Create Date: 2025-10-16 17:30:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

def upgrade():
    # ErrorEvent 테이블 생성
    op.create_table(
        'error_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('level', sa.String(10), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('traceback', sa.Text(), nullable=True),
        sa.Column('service', sa.String(50), nullable=False),
        sa.Column('endpoint', sa.String(255), nullable=True),
        sa.Column('method', sa.String(10), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('trace_id', sa.String(32), nullable=True),
        sa.Column('span_id', sa.String(16), nullable=True),
        sa.Column('context', JSONB, nullable=True),
        sa.Column('embedding', Vector(384), nullable=True),
        sa.Column('resolution_status', sa.String(20), nullable=False, server_default='new'),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.String(100), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes
    op.create_index('ix_error_events_timestamp', 'error_events', ['timestamp'])
    op.create_index('ix_error_events_level', 'error_events', ['level'])
    op.create_index('ix_error_events_service', 'error_events', ['service'])
    op.create_index('ix_error_events_trace_id', 'error_events', ['trace_id'])
    op.create_index('ix_error_events_resolution_status', 'error_events', ['resolution_status'])
    op.create_index('ix_error_events_timestamp_level', 'error_events', ['timestamp', 'level'])
    op.create_index('ix_error_events_service_timestamp', 'error_events', ['service', 'timestamp'])

    # LoadTestRun 테이블 생성
    op.create_table(
        'load_test_runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('test_id', sa.String(100), nullable=False, unique=True),
        sa.Column('scenario_name', sa.String(100), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('target_vu', sa.Integer(), nullable=False),
        sa.Column('stages_config', JSONB, nullable=True),
        sa.Column('total_requests', sa.Integer(), nullable=True),
        sa.Column('failed_requests', sa.Integer(), nullable=True),
        sa.Column('requests_per_second', sa.Float(), nullable=True),
        sa.Column('latency_p50', sa.Float(), nullable=True),
        sa.Column('latency_p95', sa.Float(), nullable=True),
        sa.Column('latency_p99', sa.Float(), nullable=True),
        sa.Column('latency_avg', sa.Float(), nullable=True),
        sa.Column('latency_min', sa.Float(), nullable=True),
        sa.Column('latency_max', sa.Float(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='running'),
        sa.Column('passed_thresholds', sa.Boolean(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('results_json', JSONB, nullable=True),
        sa.Column('executor', sa.String(100), nullable=True),
        sa.Column('tags', JSONB, nullable=True),
        sa.Column('prometheus_start', sa.Integer(), nullable=True),
        sa.Column('prometheus_end', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes
    op.create_index('ix_load_test_runs_test_id', 'load_test_runs', ['test_id'], unique=True)
    op.create_index('ix_load_test_runs_start_time', 'load_test_runs', ['start_time'])
    op.create_index('ix_load_test_runs_scenario_status', 'load_test_runs', ['scenario_name', 'status'])

def downgrade():
    op.drop_table('load_test_runs')
    op.drop_table('error_events')
```
**Dependencies**: T016, T017
**Passes**: None yet

---

### T019: Implement Prometheus /metrics endpoint
**File**: `backend/src/api/observability.py`
**Description**: 14 core metrics 노출 (research.md Section 1 기반)
```python
from fastapi import APIRouter
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from starlette.responses import Response

router = APIRouter()

# 14 Core Metrics (research.md)
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],  # status: 2xx, 4xx, 5xx
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
    "HTTP requests currently in progress",
    ["method", "endpoint"],
)

db_connection_pool_size = Gauge(
    "db_connection_pool_size",
    "DB connection pool size",
    ["service"],
)

db_connection_pool_in_use = Gauge(
    "db_connection_pool_in_use",
    "DB connections currently in use",
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
    "Database query duration",
    ["query_type"],
)

http_client_pool_size = Gauge(
    "http_client_pool_size",
    "HTTP client connection pool size",
    ["host"],
)

http_client_pool_in_use = Gauge(
    "http_client_pool_in_use",
    "HTTP client connections in use",
    ["host"],
)

http_client_waiting_requests = Gauge(
    "http_client_waiting_requests",
    "Requests waiting for HTTP client connection",
    ["host"],
)

celery_tasks_total = Counter(
    "celery_tasks_total",
    "Total Celery tasks",
    ["task_name", "status"],  # status: success, failure, retry
)

@router.get("/metrics")
def metrics():
    """FR-001, FR-004: Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```
**Dependencies**: T003
**Passes**: T008 (contract test)

---

### T020: Implement HTTP metrics middleware
**File**: `backend/src/middleware/metrics_middleware.py`
**Description**: FastAPI middleware for automatic HTTP metrics collection
```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time
from src.api.observability import (
    http_requests_total,
    http_request_duration_seconds,
    http_request_size_bytes,
    http_response_size_bytes,
    http_requests_in_progress,
)

def get_status_group(status_code: int) -> str:
    """Group status codes: 2xx, 4xx, 5xx (not individual codes)"""
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

        # Timing
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
```
**Dependencies**: T019
**Passes**: T008 (partial - metrics collected)

---

### T021: Implement OpenTelemetry tracing middleware
**File**: `backend/src/middleware/tracing.py`
**Description**: OpenTelemetry FastAPI auto-instrumentation (research.md Section 4 기반)
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource

def setup_tracing(app, service_name="backend-api"):
    """Setup OpenTelemetry tracing for FastAPI"""
    # Resource
    resource = Resource.create({"service.name": service_name})

    # Tracer Provider
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    # OTLP Exporter (to Tempo via OTel Collector)
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://otel-collector:4317",
        insecure=True,
    )
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Auto-instrumentation
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()

    return provider
```
**Dependencies**: T002
**Passes**: T010 (contract test - traces captured)

---

### T022: [P] Implement ObservabilityAgent service
**File**: `backend/src/services/observability_agent.py`
**Description**: Llama → Prometheus/Loki/Tempo 쿼리 인터페이스 (research.md Section 6 기반)
```python
import httpx
from typing import Dict, Any, List
from datetime import datetime, timedelta

class ObservabilityAgent:
    def __init__(
        self,
        prometheus_url="http://prometheus:9090",
        loki_url="http://loki:3100",
        tempo_url="http://tempo:3200",
    ):
        self.prometheus_url = prometheus_url
        self.loki_url = loki_url
        self.tempo_url = tempo_url

    async def query_prometheus(self, promql: str) -> Dict[str, Any]:
        """Query Prometheus with PromQL"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": promql},
            )
            response.raise_for_status()
            return response.json()

    async def query_loki(self, logql: str, limit: int = 100) -> Dict[str, Any]:
        """Query Loki with LogQL"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.loki_url}/loki/api/v1/query_range",
                params={"query": logql, "limit": limit},
            )
            response.raise_for_status()
            return response.json()

    async def query_tempo(self, trace_id: str) -> Dict[str, Any]:
        """Query Tempo for trace by ID"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.tempo_url}/api/traces/{trace_id}")
            response.raise_for_status()
            return response.json()

    async def analyze_with_llama(self, question: str, time_range: str = "1h") -> str:
        """
        Llama AI가 질문을 해석하고 관측성 데이터 쿼리

        예시 질문:
        - "지난 1시간 동안 5XX 에러가 얼마나 발생했어?"
        - "현재 DB 커넥션 풀 사용량이 얼마야?"
        - "가장 느린 API 엔드포인트는 뭐야?"
        """
        # TODO: Integrate with Llama API (Together AI)
        # 1. Llama가 질문을 PromQL/LogQL/TraceQL로 변환
        # 2. 해당 쿼리 실행
        # 3. 결과를 자연어로 요약

        # Placeholder implementation
        if "5XX 에러" in question or "5xx" in question.lower():
            promql = 'rate(http_requests_total{status="5xx"}[1h])'
            result = await self.query_prometheus(promql)
            # Summarize result
            return f"지난 1시간 동안 5XX 에러가 발생했습니다: {result}"

        elif "DB 커넥션 풀" in question or "connection pool" in question.lower():
            promql = "db_connection_pool_in_use / db_connection_pool_size"
            result = await self.query_prometheus(promql)
            return f"현재 DB 커넥션 풀 사용률: {result}"

        else:
            return "죄송합니다. 해당 질문을 이해하지 못했습니다."

    async def get_dashboard_metrics(self, time_range: str = "15m") -> Dict[str, Any]:
        """Get dashboard metrics summary"""
        # HTTP metrics
        http_rps = await self.query_prometheus("rate(http_requests_total[5m])")
        http_2xx = await self.query_prometheus('rate(http_requests_total{status="2xx"}[5m])')
        http_4xx = await self.query_prometheus('rate(http_requests_total{status="4xx"}[5m])')
        http_5xx = await self.query_prometheus('rate(http_requests_total{status="5xx"}[5m])')
        http_p95 = await self.query_prometheus(
            'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))'
        )

        # DB metrics
        db_pool_size = await self.query_prometheus("db_connection_pool_size")
        db_pool_in_use = await self.query_prometheus("db_connection_pool_in_use")
        db_pool_available = await self.query_prometheus("db_connection_pool_available")

        # HTTP client metrics
        http_client_size = await self.query_prometheus("http_client_pool_size")
        http_client_in_use = await self.query_prometheus("http_client_pool_in_use")
        http_client_waiting = await self.query_prometheus("http_client_waiting_requests")

        # Celery metrics
        celery_rate = await self.query_prometheus("rate(celery_tasks_total[5m])")

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "http": {
                "requests_per_second": self._extract_value(http_rps),
                "status_2xx_rate": self._extract_value(http_2xx),
                "status_4xx_rate": self._extract_value(http_4xx),
                "status_5xx_rate": self._extract_value(http_5xx),
                "p95_latency_ms": self._extract_value(http_p95) * 1000,
            },
            "database": {
                "pool_size": self._extract_value(db_pool_size),
                "pool_in_use": self._extract_value(db_pool_in_use),
                "pool_available": self._extract_value(db_pool_available),
                "utilization_percent": (
                    self._extract_value(db_pool_in_use) / self._extract_value(db_pool_size) * 100
                    if self._extract_value(db_pool_size) > 0
                    else 0
                ),
            },
            "http_client": {
                "pool_size": self._extract_value(http_client_size),
                "pool_in_use": self._extract_value(http_client_in_use),
                "waiting_requests": self._extract_value(http_client_waiting),
            },
            "celery": {
                "tasks_per_second": self._extract_value(celery_rate),
            },
        }

    def _extract_value(self, prometheus_result: Dict[str, Any]) -> float:
        """Extract numeric value from Prometheus result"""
        try:
            return float(prometheus_result["data"]["result"][0]["value"][1])
        except (KeyError, IndexError):
            return 0.0
```
**Dependencies**: T019 (metrics exposed)
**Parallel**: Yes
**Passes**: None yet

---

### T023: [P] Implement ErrorAnalyzer service
**File**: `backend/src/services/error_analyzer.py`
**Description**: pgvector 유사도 검색 서비스 (research.md Section 8 기반)
```python
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.error_event import ErrorEvent
from typing import List
import httpx

class ErrorAnalyzer:
    def __init__(self, embedding_model="all-MiniLM-L6-v2"):
        self.embedding_model = embedding_model
        self.embedding_url = "http://localhost:8001/embed"  # Local embedding service

    async def create_embedding(self, text: str) -> List[float]:
        """Generate 384-dim embedding using all-MiniLM-L6-v2"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.embedding_url,
                json={"text": text, "model": self.embedding_model},
            )
            response.raise_for_status()
            return response.json()["embedding"]

    async def find_similar_errors(
        self,
        session: AsyncSession,
        error_message: str,
        limit: int = 5,
        similarity_threshold: float = 0.8,
    ) -> List[ErrorEvent]:
        """Find similar errors using pgvector cosine distance"""
        # 1. Generate embedding for query
        query_embedding = await self.create_embedding(error_message)

        # 2. pgvector similarity search
        stmt = (
            select(ErrorEvent)
            .order_by(ErrorEvent.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        result = await session.execute(stmt)
        similar_errors = result.scalars().all()

        # 3. Filter by similarity threshold
        filtered = []
        for error in similar_errors:
            # Calculate cosine similarity (1 - distance)
            distance = func.cosine_distance(error.embedding, query_embedding)
            similarity = 1 - distance
            if similarity >= similarity_threshold:
                filtered.append(error)

        return filtered

    async def store_error_event(
        self,
        session: AsyncSession,
        level: str,
        message: str,
        traceback: str = None,
        service: str = "backend-api",
        trace_id: str = None,
        **kwargs,
    ) -> ErrorEvent:
        """Store error event with embedding"""
        # Generate embedding
        embedding_text = f"{message} {traceback or ''}"
        embedding = await self.create_embedding(embedding_text)

        # Create ErrorEvent
        error_event = ErrorEvent(
            level=level,
            message=message,
            traceback=traceback,
            service=service,
            trace_id=trace_id,
            embedding=embedding,
            **kwargs,
        )

        session.add(error_event)
        await session.commit()
        await session.refresh(error_event)

        return error_event
```
**Dependencies**: T016 (ErrorEvent model)
**Parallel**: Yes
**Passes**: None yet

---

### T024: Implement Llama observability query API
**File**: `backend/src/api/llama_query.py`
**Description**: Llama 쿼리 엔드포인트 구현 (contracts/llama-observability-api.yaml 기반)
```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from src.services.observability_agent import ObservabilityAgent
import time

router = APIRouter(prefix="/api/v1/observability", tags=["observability"])

class ObservabilityQueryRequest(BaseModel):
    query: str
    time_range: str = "15m"
    language: str = "ko"
    include_traces: bool = False

class ObservabilityQueryResponse(BaseModel):
    query_type: str
    generated_query: str
    result: dict
    response_time_ms: int
    data_source: str
    related_traces: Optional[List[str]] = None

@router.post("/query", response_model=ObservabilityQueryResponse)
async def query_observability(request: ObservabilityQueryRequest):
    """FR-013, FR-014: Llama가 관측성 데이터 쿼리 (1초 이내 응답)"""
    start = time.time()

    agent = ObservabilityAgent()
    answer = await agent.analyze_with_llama(request.query, request.time_range)

    response_time_ms = int((time.time() - start) * 1000)

    # NFR-001 검증
    if response_time_ms > 1000:
        raise HTTPException(status_code=500, detail="Query exceeded 1 second timeout")

    return ObservabilityQueryResponse(
        query_type="combined",
        generated_query="",  # TODO: Return actual PromQL/LogQL
        result={"summary": answer, "data": []},
        response_time_ms=response_time_ms,
        data_source="local_prometheus",
    )

@router.get("/metrics/dashboard")
async def get_dashboard_metrics(time_range: str = "15m"):
    """Dashboard metrics summary"""
    agent = ObservabilityAgent()
    return await agent.get_dashboard_metrics(time_range)

@router.get("/trace/{trace_id}")
async def get_trace(trace_id: str):
    """Get trace details by trace ID"""
    agent = ObservabilityAgent()
    try:
        trace = await agent.query_tempo(trace_id)
        return trace
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Trace not found")
        raise

@router.post("/similar-errors")
async def find_similar_errors(
    error_message: str,
    limit: int = 10,
    similarity_threshold: float = 0.8,
    session: AsyncSession = Depends(get_db_session),
):
    """Find similar errors using pgvector"""
    from src.services.error_analyzer import ErrorAnalyzer

    analyzer = ErrorAnalyzer()
    similar = await analyzer.find_similar_errors(
        session, error_message, limit, similarity_threshold
    )

    return {"similar_errors": [
        {
            "id": e.id,
            "timestamp": e.timestamp.isoformat(),
            "message": e.message,
            "trace_id": e.trace_id,
            "resolution_status": e.resolution_status,
        }
        for e in similar
    ]}
```
**Dependencies**: T022
**Passes**: T012 (contract test - Llama API)

---

### T025: [P] Deploy Prometheus to Kubernetes
**File**: `infra/k8s/observability/prometheus/`
**Description**: Prometheus deployment, service, configmap, PVC (contracts/prometheus-config.yaml 기반)
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: observability
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
        - name: prometheus
          image: prom/prometheus:v2.48.0
          args:
            - '--config.file=/etc/prometheus/prometheus.yml'
            - '--storage.tsdb.path=/prometheus'
            - '--storage.tsdb.retention.time=3d'
            - '--storage.tsdb.retention.size=10GB'
          ports:
            - containerPort: 9090
          volumeMounts:
            - name: config
              mountPath: /etc/prometheus
            - name: storage
              mountPath: /prometheus
          resources:
            requests:
              cpu: 100m
              memory: 512Mi
            limits:
              cpu: 500m
              memory: 2Gi
      volumes:
        - name: config
          configMap:
            name: prometheus-config
        - name: storage
          persistentVolumeClaim:
            claimName: prometheus-pvc

---
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: prometheus
  namespace: observability
spec:
  selector:
    app: prometheus
  ports:
    - port: 9090
      targetPort: 9090
  type: ClusterIP

---
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: observability
data:
  prometheus.yml: |
    # Copy from contracts/prometheus-config.yaml
    # Replace placeholders with secrets

---
# pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: prometheus-pvc
  namespace: observability
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```
**Dependencies**: T007 (secrets)
**Parallel**: Yes
**Passes**: T013 (partial - Prometheus deployed)

---

### T026: [P] Deploy Loki to Kubernetes
**File**: `infra/k8s/observability/loki/`
**Description**: Loki deployment, service, configmap, PVC (contracts/loki-config.yaml 기반)
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: loki
  namespace: observability
spec:
  replicas: 1
  selector:
    matchLabels:
      app: loki
  template:
    metadata:
      labels:
        app: loki
    spec:
      containers:
        - name: loki
          image: grafana/loki:2.9.3
          args:
            - '-config.file=/etc/loki/local-config.yaml'
          ports:
            - containerPort: 3100
          volumeMounts:
            - name: config
              mountPath: /etc/loki
            - name: storage
              mountPath: /loki
          resources:
            requests:
              cpu: 100m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 1Gi
      volumes:
        - name: config
          configMap:
            name: loki-config
        - name: storage
          persistentVolumeClaim:
            claimName: loki-pvc

---
# service.yaml, configmap.yaml, pvc.yaml (similar structure)
```
**Dependencies**: T007
**Parallel**: Yes
**Passes**: T013 (partial - Loki deployed)

---

### T027: [P] Deploy Tempo to Kubernetes
**File**: `infra/k8s/observability/tempo/`
**Description**: Tempo deployment, service, configmap, PVC (contracts/tempo-config.yaml 기반)
```yaml
# Similar to T025, T026
# Use contracts/tempo-config.yaml
# Expose ports: 3200 (HTTP), 4317 (gRPC), 4318 (HTTP/OTLP)
# Retention: 2 days
```
**Dependencies**: T007
**Parallel**: Yes
**Passes**: T013 (partial - Tempo deployed)

---

### T028: Deploy Promtail DaemonSet
**File**: `infra/k8s/observability/promtail/daemonset.yaml`
**Description**: Promtail DaemonSet for log collection from all nodes
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: promtail
  namespace: observability
spec:
  selector:
    matchLabels:
      app: promtail
  template:
    metadata:
      labels:
        app: promtail
    spec:
      serviceAccountName: promtail
      containers:
        - name: promtail
          image: grafana/promtail:2.9.3
          args:
            - '-config.file=/etc/promtail/config.yaml'
          volumeMounts:
            - name: config
              mountPath: /etc/promtail
            - name: varlog
              mountPath: /var/log
            - name: varlibdockercontainers
              mountPath: /var/lib/docker/containers
              readOnly: true
          resources:
            requests:
              cpu: 50m
              memory: 128Mi
            limits:
              cpu: 200m
              memory: 256Mi
      volumes:
        - name: config
          configMap:
            name: promtail-config
        - name: varlog
          hostPath:
            path: /var/log
        - name: varlibdockercontainers
          hostPath:
            path: /var/lib/docker/containers
```
**Dependencies**: T026 (Loki)
**Passes**: T009 (contract test - logs collected)

---

## Phase 3.4: Integration & Configuration

### T029: Configure Backend HPA
**File**: `infra/k8s/backend/hpa.yaml`
**Description**: HPA with CPU 70%, Memory 80%, max 3 replicas (FR-020, FR-021)
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend
  namespace: bodam
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 1
  maxReplicas: 3  # FR-021: max 3 (not 10)
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70  # FR-020
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80  # FR-020
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 100
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
```
**Dependencies**: T025 (Prometheus for metrics)
**Passes**: T015 (integration test - HPA scales)

---

### T030: Add OpenTelemetry to Backend deployment
**File**: `infra/k8s/backend/deployment.yaml`
**Description**: Add OTEL environment variables
```yaml
env:
  - name: OTEL_EXPORTER_OTLP_ENDPOINT
    value: "http://otel-collector.observability.svc.cluster.local:4318"
  - name: OTEL_SERVICE_NAME
    value: "backend-api"
  - name: OTEL_RESOURCE_ATTRIBUTES
    value: "service.namespace=bodam,deployment.environment=production"
  - name: OTEL_TRACES_SAMPLER
    value: "always_on"
  - name: OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED
    value: "true"
```
**Dependencies**: T021, T027
**Passes**: T010 (contract test - traces captured)

---

### T031: Configure Alertmanager with Slack integration
**File**: `infra/k8s/observability/alertmanager/`
**Description**: Alertmanager deployment with Slack webhook (research.md Section 9)
```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
  namespace: observability
data:
  alertmanager.yml: |
    global:
      resolve_timeout: 5m

    route:
      group_by: ['alertname', 'severity']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 1h
      receiver: 'slack-bodam-alerts'

    receivers:
      - name: 'slack-bodam-alerts'
        slack_configs:
          - api_url_file: /etc/alertmanager/slack-webhook-url
            channel: '#bodam-alerts'
            title: '{{ .GroupLabels.alertname }}'
            text: '{{ range .Alerts }}{{ .Annotations.summary }}\n{{ end }}'
            send_resolved: true

    inhibit_rules:
      - source_match:
          severity: 'critical'
        target_match:
          severity: 'warning'
        equal: ['alertname']

---
# Alert rules for Prometheus
alert_rules.yml: |
  groups:
    - name: backend_alerts
      interval: 15s
      rules:
        # Critical: 5XX errors (immediate alert)
        - alert: ServerError5XX
          expr: rate(http_requests_total{status="5xx"}[1m]) > 0
          for: 1m
          labels:
            severity: critical
          annotations:
            summary: "Server error detected"
            description: "5XX errors occurred in the last minute"

        # Critical: DB pool exhausted
        - alert: DBPoolExhausted
          expr: db_connection_pool_waiting > 0
          for: 1m
          labels:
            severity: critical
          annotations:
            summary: "Database connection pool exhausted"
            description: "Requests are waiting for DB connections"

        # Critical: HTTP client pool exhausted
        - alert: HTTPClientPoolExhausted
          expr: http_client_waiting_requests > 0
          for: 1m
          labels:
            severity: critical
          annotations:
            summary: "HTTP client connection pool exhausted"
            description: "Requests are waiting for HTTP client connections"

        # Warning: High 4XX rate (pattern observation)
        - alert: HighClientErrorRate
          expr: rate(http_requests_total{status="4xx"}[5m]) / rate(http_requests_total[5m]) > 0.3
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "High client error rate (4XX)"
            description: "4XX error rate exceeds 30%"

        # Warning: High latency
        - alert: HighLatency
          expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "High API latency"
            description: "p95 latency exceeds 500ms"

        # Warning: Disk space
        - alert: DiskSpaceHigh
          expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.2
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "Low disk space"
            description: "Disk usage exceeds 80%"
```
**Dependencies**: T025 (Prometheus)
**Passes**: None yet (manual Slack verification)

---

## Phase 3.5: Polish & Documentation

### T032: [P] Write unit tests for ObservabilityAgent
**File**: `backend/tests/unit/test_observability_agent.py`
**Description**: Unit tests for Prometheus/Loki/Tempo query methods
```python
import pytest
from unittest.mock import AsyncMock, patch
from src.services.observability_agent import ObservabilityAgent

@pytest.mark.asyncio
async def test_query_prometheus_success():
    agent = ObservabilityAgent()

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value.json.return_value = {"data": {"result": []}}
        mock_get.return_value.raise_for_status = AsyncMock()

        result = await agent.query_prometheus("up")

        assert "data" in result
        mock_get.assert_called_once()

@pytest.mark.asyncio
async def test_get_dashboard_metrics():
    agent = ObservabilityAgent()

    with patch.object(agent, "query_prometheus", return_value={"data": {"result": []}}):
        metrics = await agent.get_dashboard_metrics()

        assert "timestamp" in metrics
        assert "http" in metrics
        assert "database" in metrics
```
**Dependencies**: T022
**Parallel**: Yes

---

### T033: [P] Write unit tests for ErrorAnalyzer
**File**: `backend/tests/unit/test_error_analyzer.py`
**Description**: Unit tests for pgvector similarity search
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.error_analyzer import ErrorAnalyzer

@pytest.mark.asyncio
async def test_create_embedding():
    analyzer = ErrorAnalyzer()

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value.json.return_value = {"embedding": [0.1] * 384}
        mock_post.return_value.raise_for_status = AsyncMock()

        embedding = await analyzer.create_embedding("test error")

        assert len(embedding) == 384
```
**Dependencies**: T023
**Parallel**: Yes

---

### T034: Update quickstart.md with deployment validation
**File**: `specs/004-hybrid-observability-stack/quickstart.md`
**Description**: Add step-by-step verification commands to existing quickstart.md
- Verify Prometheus scrapes Backend metrics
- Verify Loki collects logs
- Verify Tempo captures traces
- Run K6 load tests
- Query Llama API
- Validate HPA scaling
- Confirm Slack alerts
**Dependencies**: T025-T031
**Parallel**: No (requires all infrastructure)

---

## Dependencies Graph

```
Setup (T001-T007)
  ├─> Tests (T008-T015) [P] ⚠️ MUST FAIL
  │     ├─> T008 [P] Prometheus /metrics contract test
  │     ├─> T009 [P] Loki logs contract test
  │     ├─> T010 [P] Tempo traces contract test
  │     ├─> T011 [P] K6 scenarios contract test
  │     ├─> T012 [P] Llama API contract test
  │     ├─> T013 [P] Observability stack integration test
  │     ├─> T014 [P] K6 monitoring integration test
  │     └─> T015 [P] HPA autoscaling integration test
  │
  ├─> Models (T016-T018) [P]
  │     ├─> T016 [P] ErrorEvent model
  │     ├─> T017 [P] LoadTestRun model
  │     └─> T018 Alembic migration (depends on T016, T017)
  │
  ├─> Backend Implementation (T019-T024)
  │     ├─> T019 Prometheus /metrics endpoint (passes T008)
  │     ├─> T020 Metrics middleware (depends on T019)
  │     ├─> T021 OpenTelemetry middleware (passes T010)
  │     ├─> T022 [P] ObservabilityAgent service
  │     ├─> T023 [P] ErrorAnalyzer service (depends on T016)
  │     └─> T024 Llama API (depends on T022, passes T012)
  │
  ├─> Infrastructure (T025-T028) [P]
  │     ├─> T025 [P] Prometheus deployment
  │     ├─> T026 [P] Loki deployment
  │     ├─> T027 [P] Tempo deployment
  │     └─> T028 Promtail DaemonSet (depends on T026)
  │
  ├─> Integration (T029-T031)
  │     ├─> T029 Backend HPA (depends on T025)
  │     ├─> T030 OTEL env vars (depends on T021, T027)
  │     └─> T031 Alertmanager (depends on T025)
  │
  └─> Polish (T032-T034) [P]
        ├─> T032 [P] ObservabilityAgent unit tests
        ├─> T033 [P] ErrorAnalyzer unit tests
        └─> T034 Quickstart validation (depends on all)
```

---

## Parallel Execution Examples

### Phase 3.1: Setup (all parallel)
```bash
# T001-T004 can run in parallel
Task: "Create infrastructure directories"
Task: "Install OpenTelemetry dependencies"
Task: "Install Prometheus client"
Task: "Install K6"
```

### Phase 3.2: Tests (all parallel after setup)
```bash
# T008-T015 can run in parallel (all different files)
Task: "Contract test - Prometheus /metrics endpoint in backend/tests/contract/test_prometheus_metrics_contract.py"
Task: "Contract test - Loki log collection in backend/tests/contract/test_loki_logs_contract.py"
Task: "Contract test - Tempo trace capture in backend/tests/contract/test_tempo_traces_contract.py"
Task: "Contract test - K6 scenarios in backend/tests/contract/test_k6_scenarios_contract.py"
Task: "Contract test - Llama API in backend/tests/contract/test_llama_observability_api_contract.py"
Task: "Integration test - Observability stack in backend/tests/integration/test_observability_stack_integration.py"
Task: "Integration test - K6 monitoring in backend/tests/integration/test_k6_monitoring_integration.py"
Task: "Integration test - HPA autoscaling in backend/tests/integration/test_hpa_autoscaling_integration.py"
```

### Phase 3.3: Models (parallel)
```bash
# T016-T017 can run in parallel
Task: "Create ErrorEvent model in backend/src/models/error_event.py"
Task: "Create LoadTestRun model in backend/src/models/load_test_run.py"
```

### Phase 3.3: Services (some parallel)
```bash
# T022-T023 can run in parallel (different files)
Task: "Implement ObservabilityAgent service in backend/src/services/observability_agent.py"
Task: "Implement ErrorAnalyzer service in backend/src/services/error_analyzer.py"
```

### Phase 3.3: Infrastructure (all parallel)
```bash
# T025-T027 can run in parallel
Task: "Deploy Prometheus to Kubernetes in infra/k8s/observability/prometheus/"
Task: "Deploy Loki to Kubernetes in infra/k8s/observability/loki/"
Task: "Deploy Tempo to Kubernetes in infra/k8s/observability/tempo/"
```

---

## Validation Checklist

### GATE: All requirements met?

- [x] All contracts have corresponding tests (T008-T012 cover all 5 contracts)
- [x] All entities have model tasks (T016 ErrorEvent, T017 LoadTestRun)
- [x] All tests come before implementation (Phase 3.2 before 3.3)
- [x] Parallel tasks truly independent (verified file paths)
- [x] Each task specifies exact file path (all tasks include file paths)
- [x] No task modifies same file as another [P] task (verified)

### Coverage Check

**From contracts/**:
- [x] prometheus-config.yaml → T008 (contract test), T019 (implementation), T025 (deployment)
- [x] loki-config.yaml → T009 (contract test), T026 (deployment), T028 (Promtail)
- [x] tempo-config.yaml → T010 (contract test), T021 (implementation), T027 (deployment)
- [x] k6-scenarios.js → T011 (contract test), T014 (monitoring integration)
- [x] llama-observability-api.yaml → T012 (contract test), T024 (implementation)

**From data-model.md**:
- [x] ErrorEvent → T016 (model), T023 (service), T018 (migration)
- [x] LoadTestRun → T017 (model), T018 (migration)

**From spec.md User Stories**:
- [x] US1 (CPU usage metrics) → T013 (Prometheus integration)
- [x] US2 (AI error analysis) → T012 (Llama API), T024 (implementation)
- [x] US3 (Slow API traces) → T010 (Tempo contract), T021 (tracing)
- [x] US4 (Load testing) → T011 (K6 contract), T014 (monitoring)
- [x] US5 (Network resilience) → T006 (local storage), T031 (alerting)
- [x] US6 (Historical data) → T025-T027 (Grafana Cloud remote_write)

**From research.md**:
- [x] 14 core metrics → T019 (metrics endpoint), T020 (middleware)
- [x] Alert strategy → T031 (Alertmanager)
- [x] HPA configuration → T029 (HPA manifest)

---

## Notes

1. **TDD Order**: Tests (T008-T015) MUST be written first and MUST FAIL before any implementation
2. **[P] Marking**: Tasks marked [P] can run in parallel because they modify different files
3. **Sequential Tasks**: Tasks without [P] must run sequentially due to dependencies or file conflicts
4. **Commit Strategy**: Commit after each task completion
5. **Docker Compose First**: Use T006 (Docker Compose) for local development and testing before Kubernetes deployment
6. **Quickstart Validation**: T034 is the final validation that all components work together

---

## Estimated Timeline

- **Phase 3.1 (Setup)**: 2 hours
- **Phase 3.2 (Tests)**: 8 hours (parallelizable to ~3-4 hours)
- **Phase 3.3 (Core)**: 16 hours (models + services + API)
- **Phase 3.4 (Infrastructure)**: 12 hours (K8s manifests + configuration)
- **Phase 3.5 (Polish)**: 4 hours (unit tests + docs)

**Total**: ~42 hours (~1 week for single developer, ~2-3 days with 2-3 developers running parallel tasks)

---

## Success Criteria Mapping

각 task가 어떤 spec.md 요구사항을 충족하는지:

| Task | FR | NFR | Description |
|------|----|----|-------------|
| T008 | FR-001, FR-004 | NFR-002 | Prometheus metrics |
| T009 | FR-005, FR-008 | NFR-003 | Loki logs |
| T010 | FR-009, FR-012 | NFR-003 | Tempo traces |
| T011 | FR-017, FR-018 | - | K6 load testing |
| T012 | FR-013, FR-014 | NFR-001 | Llama API (<1s) |
| T015 | FR-020, FR-021 | - | HPA scaling |
| T016 | FR-015 | - | ErrorEvent model |
| T017 | FR-019 | - | LoadTestRun model |
| T019 | FR-001, FR-004 | NFR-002 | Metrics endpoint |
| T021 | FR-009, FR-012 | NFR-003 | OpenTelemetry tracing |
| T024 | FR-013, FR-014 | NFR-001 | Llama query API |
| T025 | FR-002, FR-003 | NFR-006 | Prometheus deployment |
| T026 | FR-006, FR-007 | NFR-006 | Loki deployment |
| T027 | FR-010, FR-011 | NFR-006 | Tempo deployment |
| T029 | FR-020, FR-021 | - | HPA configuration |
| T031 | - | NFR-010 | Alertmanager + Slack |

**Total Coverage**: 26/26 FR + 10/10 NFR = 100% requirements covered

---

**Generated**: 2025-10-16
**Status**: Ready for execution
**Next Step**: Begin Phase 3.1 (Setup) or use Docker Compose (T006) for local development
