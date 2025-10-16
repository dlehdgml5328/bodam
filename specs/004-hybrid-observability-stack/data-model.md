# Data Model: 하이브리드 관측성 스택

**Feature**: 004-hybrid-observability-stack
**Date**: 2025-10-16
**Status**: Complete

## 개요

이 문서는 하이브리드 관측성 스택에서 사용되는 데이터 모델을 정의합니다. spec.md의 Key Entities를 기반으로 구현 가능한 수준으로 상세화했습니다.

---

## 1. ErrorEvent (에러 이벤트)

### 목적
중요한 에러를 PostgreSQL에 저장하고 pgvector를 사용하여 유사 에러를 검색합니다 (FR-015, FR-016).

### Schema

```python
# backend/src/models/error_event.py
from sqlalchemy import Column, Integer, String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from datetime import datetime

class ErrorEvent(Base):
    __tablename__ = "error_events"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Timestamp
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Error Details
    level = Column(String(10), nullable=False, index=True)  # error, critical
    message = Column(Text, nullable=False)
    traceback = Column(Text, nullable=True)

    # Service Context
    service = Column(String(50), nullable=False, index=True)  # backend, celery, kong
    endpoint = Column(String(255), nullable=True)  # /api/donations
    method = Column(String(10), nullable=True)  # GET, POST
    status_code = Column(Integer, nullable=True)  # 500, 503

    # OpenTelemetry Context
    trace_id = Column(String(32), nullable=True, index=True)  # 16진수 32자
    span_id = Column(String(16), nullable=True)  # 16진수 16자

    # Additional Context (JSON)
    context = Column(JSONB, nullable=True)
    # 예시: {"user_id": 123, "request_id": "abc", "ip": "1.2.3.4"}

    # Vector Embedding (384 dimensions, all-MiniLM-L6-v2)
    embedding = Column(Vector(384), nullable=True)

    # Resolution Status
    resolution_status = Column(
        String(20),
        nullable=False,
        default="new",
        index=True
    )  # new, analyzing, resolved, ignored

    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)  # admin username
    resolution_notes = Column(Text, nullable=True)

    # Indexes
    __table_args__ = (
        Index('ix_error_events_timestamp_level', 'timestamp', 'level'),
        Index('ix_error_events_service_timestamp', 'service', 'timestamp'),
        # ivfflat index for vector similarity (생성 시 수동)
        # CREATE INDEX ON error_events USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
    )
```

### 필드 설명

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `id` | Integer | ✅ | Primary Key |
| `timestamp` | DateTime | ✅ | 에러 발생 시각 (UTC) |
| `level` | String(10) | ✅ | error, critical |
| `message` | Text | ✅ | 에러 메시지 |
| `traceback` | Text | ❌ | Python 스택 트레이스 |
| `service` | String(50) | ✅ | backend, celery, kong |
| `endpoint` | String(255) | ❌ | API 엔드포인트 |
| `method` | String(10) | ❌ | HTTP 메서드 |
| `status_code` | Integer | ❌ | HTTP 상태 코드 |
| `trace_id` | String(32) | ❌ | OpenTelemetry Trace ID |
| `span_id` | String(16) | ❌ | OpenTelemetry Span ID |
| `context` | JSONB | ❌ | 추가 컨텍스트 (user_id, request_id 등) |
| `embedding` | Vector(384) | ❌ | 유사도 검색용 임베딩 |
| `resolution_status` | String(20) | ✅ | new, analyzing, resolved, ignored |
| `resolved_at` | DateTime | ❌ | 해결 시각 |
| `resolved_by` | String(100) | ❌ | 해결한 관리자 |
| `resolution_notes` | Text | ❌ | 해결 방법 메모 |

### 상태 전이

```
new (생성)
  ↓
analyzing (Llama 분석 중)
  ↓
resolved (해결됨) or ignored (무시)
```

### Validation Rules

1. `level`은 "error" 또는 "critical"만 허용
2. `resolution_status`는 "new", "analyzing", "resolved", "ignored"만 허용
3. `message`는 최소 1자 이상
4. `embedding`은 384차원 벡터 (null 허용, 비동기 생성)
5. `trace_id`는 32자 16진수 (OpenTelemetry 형식)

### 인덱스 전략

```sql
-- 시간 + 레벨 복합 인덱스 (최근 에러 조회)
CREATE INDEX ix_error_events_timestamp_level ON error_events (timestamp DESC, level);

-- 서비스 + 시간 (서비스별 에러 조회)
CREATE INDEX ix_error_events_service_timestamp ON error_events (service, timestamp DESC);

-- Trace ID (트레이스 연동)
CREATE INDEX ix_error_events_trace_id ON error_events (trace_id);

-- Vector Similarity (ivfflat, 수동 생성)
CREATE INDEX ix_error_events_embedding ON error_events
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

---

## 2. LoadTestRun (부하 테스트 실행 기록)

### 목적
K6 부하 테스트 실행 이력을 저장하고 성능 추이를 분석합니다 (FR-017, FR-019).

### Schema

```python
# backend/src/models/load_test_run.py
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

class LoadTestRun(Base):
    __tablename__ = "load_test_runs"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Test Identification
    test_id = Column(String(100), nullable=False, unique=True, index=True)
    # 예시: "k6-200vu-2025-10-16-17-30-00"

    scenario_name = Column(String(100), nullable=False)
    # 예시: "moderate-200vu", "stress-500vu"

    # Timing
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Test Configuration
    target_vu = Column(Integer, nullable=False)  # Virtual Users
    stages_config = Column(JSONB, nullable=True)
    # 예시: [{"duration": "1m", "target": 50}, {"duration": "3m", "target": 200}]

    # Results Summary
    total_requests = Column(Integer, nullable=True)
    failed_requests = Column(Integer, nullable=True)
    requests_per_second = Column(Float, nullable=True)

    # Latency Metrics (milliseconds)
    latency_p50 = Column(Float, nullable=True)
    latency_p95 = Column(Float, nullable=True)
    latency_p99 = Column(Float, nullable=True)
    latency_avg = Column(Float, nullable=True)
    latency_min = Column(Float, nullable=True)
    latency_max = Column(Float, nullable=True)

    # Pass/Fail Status
    status = Column(String(20), nullable=False, default="running")
    # running, passed, failed, aborted

    passed_thresholds = Column(Boolean, nullable=True)
    # K6 thresholds 통과 여부 (p95 < 500ms 등)

    # Error Details (실패 시)
    error_message = Column(Text, nullable=True)

    # Full Results (JSON)
    results_json = Column(JSONB, nullable=True)
    # K6 summary.json 전체 저장

    # Metadata
    executor = Column(String(100), nullable=True)  # 실행한 사용자/시스템
    tags = Column(JSONB, nullable=True)
    # 예시: {"environment": "staging", "version": "v1.2.3"}

    # Prometheus Time Range (메트릭 조회용)
    prometheus_start = Column(Integer, nullable=True)  # Unix timestamp
    prometheus_end = Column(Integer, nullable=True)
```

### 필드 설명

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `id` | Integer | ✅ | Primary Key |
| `test_id` | String(100) | ✅ | 고유 테스트 ID (unique) |
| `scenario_name` | String(100) | ✅ | 시나리오 이름 |
| `start_time` | DateTime | ✅ | 테스트 시작 시각 |
| `end_time` | DateTime | ❌ | 테스트 종료 시각 |
| `duration_seconds` | Float | ❌ | 소요 시간 (초) |
| `target_vu` | Integer | ✅ | 목표 Virtual Users |
| `stages_config` | JSONB | ❌ | K6 stages 설정 |
| `total_requests` | Integer | ❌ | 총 요청 수 |
| `failed_requests` | Integer | ❌ | 실패한 요청 수 |
| `requests_per_second` | Float | ❌ | 초당 요청 수 (RPS) |
| `latency_p50` | Float | ❌ | p50 지연시간 (ms) |
| `latency_p95` | Float | ❌ | p95 지연시간 (ms) |
| `latency_p99` | Float | ❌ | p99 지연시간 (ms) |
| `latency_avg` | Float | ❌ | 평균 지연시간 (ms) |
| `latency_min` | Float | ❌ | 최소 지연시간 (ms) |
| `latency_max` | Float | ❌ | 최대 지연시간 (ms) |
| `status` | String(20) | ✅ | running, passed, failed, aborted |
| `passed_thresholds` | Boolean | ❌ | K6 thresholds 통과 여부 |
| `error_message` | Text | ❌ | 실패 사유 |
| `results_json` | JSONB | ❌ | K6 summary.json 전체 |
| `executor` | String(100) | ❌ | 실행자 (admin, CI/CD) |
| `tags` | JSONB | ❌ | 메타데이터 태그 |
| `prometheus_start` | Integer | ❌ | Prometheus 쿼리 시작 (Unix timestamp) |
| `prometheus_end` | Integer | ❌ | Prometheus 쿼리 종료 (Unix timestamp) |

### 상태 전이

```
running (실행 중)
  ↓
passed (성공) or failed (실패) or aborted (중단)
```

### Validation Rules

1. `status`는 "running", "passed", "failed", "aborted"만 허용
2. `target_vu`는 1 이상 (K6는 최소 1 VU 필요)
3. `end_time`은 `start_time` 이후여야 함
4. `duration_seconds` = `end_time - start_time` (자동 계산)
5. `latency_p95` < 500ms이면 `passed_thresholds = True` (spec.md 기준)

### 인덱스 전략

```sql
-- 시작 시간 (최근 테스트 조회)
CREATE INDEX ix_load_test_runs_start_time ON load_test_runs (start_time DESC);

-- test_id (고유 조회)
CREATE UNIQUE INDEX ix_load_test_runs_test_id ON load_test_runs (test_id);

-- 시나리오별 조회
CREATE INDEX ix_load_test_runs_scenario_status ON load_test_runs (scenario_name, status);
```

---

## 3. 관측성 데이터 (외부 저장)

### 3.1 Metric (Prometheus TSDB)

**저장 위치**:
- 로컬: Prometheus PersistentVolume (3일)
- 원격: Grafana Cloud (14일)

**데이터 형식** (Prometheus exposition format):
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/donations",status="2xx"} 1234

# HELP http_request_duration_seconds HTTP request latency
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",endpoint="/api/donations",le="0.1"} 95
http_request_duration_seconds_sum{method="GET",endpoint="/api/donations"} 123.45
http_request_duration_seconds_count{method="GET",endpoint="/api/donations"} 1000
```

**속성**:
- Metric Name: `http_requests_total`
- Labels: `method`, `endpoint`, `status`
- Value: Counter 또는 Gauge 또는 Histogram
- Timestamp: 자동 (scrape 시각)

### 3.2 Log (Loki Storage)

**저장 위치**:
- 로컬: Loki PersistentVolume (3일)
- 원격: Grafana Cloud (14일)

**데이터 형식** (JSON):
```json
{
  "timestamp": "2025-10-16T17:30:15.123Z",
  "level": "error",
  "message": "Database connection timeout",
  "service": "backend",
  "trace_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "span_id": "a1b2c3d4e5f6g7h8",
  "endpoint": "/api/donations",
  "method": "POST",
  "user_id": 123,
  "error_type": "TimeoutError"
}
```

**속성**:
- Timestamp: ISO 8601 (UTC)
- Level: debug, info, warning, error, critical
- Labels: `service`, `level`, `trace_id`
- Structured Fields: JSON 형태

### 3.3 Trace (Tempo Storage)

**저장 위치**:
- 로컬: Tempo PersistentVolume (2일)
- 원격: Grafana Cloud (14일)

**데이터 형식** (OpenTelemetry):
```json
{
  "traceId": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "spans": [
    {
      "spanId": "a1b2c3d4e5f6g7h8",
      "parentSpanId": null,
      "name": "POST /api/donations",
      "kind": "SERVER",
      "startTime": 1697471415123000000,
      "endTime": 1697471415523000000,
      "duration": 400000000,
      "attributes": {
        "http.method": "POST",
        "http.url": "/api/donations",
        "http.status_code": 201
      },
      "status": {"code": "OK"}
    },
    {
      "spanId": "b2c3d4e5f6g7h8i9",
      "parentSpanId": "a1b2c3d4e5f6g7h8",
      "name": "SELECT donations",
      "kind": "CLIENT",
      "startTime": 1697471415200000000,
      "endTime": 1697471415350000000,
      "duration": 150000000,
      "attributes": {
        "db.system": "postgresql",
        "db.statement": "SELECT * FROM donations WHERE id = $1"
      },
      "status": {"code": "OK"}
    }
  ]
}
```

**속성**:
- Trace ID: 32자 16진수
- Span ID: 16자 16진수
- Duration: 나노초 (1e9 = 1초)
- Attributes: Key-Value 메타데이터

---

## 4. 관계 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│                      PostgreSQL (bodam DB)                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ErrorEvent                          LoadTestRun             │
│  ├─ id                               ├─ id                   │
│  ├─ timestamp                        ├─ test_id              │
│  ├─ message                          ├─ start_time           │
│  ├─ trace_id ─────────┐              ├─ latency_p95          │
│  ├─ embedding (vector)│              ├─ status               │
│  └─ resolution_status │              └─ results_json         │
│                       │                                       │
└───────────────────────┼───────────────────────────────────────┘
                        │
                        │ trace_id 참조
                        │
┌───────────────────────┼───────────────────────────────────────┐
│                       │     Tempo (Trace Storage)             │
│                       └──→  Trace ID로 Span 조회              │
│                                                                │
│  Trace                                                         │
│  ├─ traceId: "a1b2c3d4..."                                    │
│  └─ spans[]                                                    │
│      ├─ spanId                                                 │
│      ├─ duration                                               │
│      └─ attributes                                             │
│                                                                │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│              Prometheus (Metric Storage)                       │
│                                                                 │
│  http_requests_total{endpoint="/api/donations",status="5xx"}   │
│  http_request_duration_seconds{endpoint="/api/donations"}      │
│  db_connections_active                                          │
│  http_client_waiting_requests{host="gemini"}                   │
│                                                                 │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                 Loki (Log Storage)                              │
│                                                                 │
│  {service="backend", level="error", trace_id="a1b2c3d4..."}    │
│  message: "Database connection timeout"                        │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## 5. 데이터 흐름

### ErrorEvent 생성 흐름

```
1. FastAPI에서 5XX 에러 발생
   ↓
2. Middleware가 에러 캡처
   ↓
3. Celery Task 트리거: log_error_event.delay(error_data)
   ↓
4. Celery Worker:
   - ErrorAnalyzer.create_embedding(message + traceback)
   - ErrorEvent 생성 및 저장
   ↓
5. PostgreSQL: error_events 테이블에 저장
   ↓
6. Llama 쿼리 시:
   - ObservabilityAgent.find_similar_errors(error_message)
   - pgvector cosine_distance 검색
   - 유사 에러 5개 반환
```

### LoadTestRun 생성 흐름

```
1. K6 테스트 시작
   ↓
2. Backend API: POST /api/load-tests
   - LoadTestRun 생성 (status="running")
   - prometheus_start = now()
   ↓
3. K6 실행 중:
   - statsd → Prometheus 실시간 전송
   ↓
4. K6 완료:
   - summary.json 생성
   ↓
5. Backend API: PUT /api/load-tests/{test_id}
   - status = "passed" or "failed"
   - latency_p95, results_json 업데이트
   - prometheus_end = now()
   ↓
6. Grafana 대시보드:
   - LoadTestRun 조회
   - prometheus_start ~ prometheus_end 범위 메트릭 시각화
```

---

## 6. 스토리지 예상 크기

### ErrorEvent

```
예상:
- 평상시: 하루 10개 에러 (트래픽 적음)
- 부하 테스트 시: 하루 100개 에러
- 행 크기: ~2KB (message + traceback + embedding)
- 월 저장: 100개 × 30일 = 3,000개 = 6MB

1년 후: ~72MB (삭제 정책 없음)
```

### LoadTestRun

```
예상:
- 주 2회 부하 테스트
- 행 크기: ~10KB (results_json 포함)
- 월 저장: 8개 = 80KB

1년 후: ~960KB (거의 무시 가능)
```

### 총 PostgreSQL 추가 용량

```
1년 후: ~73MB (ErrorEvent + LoadTestRun)
→ 기존 bodam DB 대비 무시 가능한 수준
```

---

## 7. 마이그레이션 스크립트

### Alembic Migration

```python
# backend/alembic/versions/004_add_observability_tables.py
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

### pgvector Extension 설치

```sql
-- PostgreSQL에서 실행 (Alembic 전에)
CREATE EXTENSION IF NOT EXISTS vector;

-- ivfflat 인덱스 생성 (데이터 추가 후 수동 실행)
CREATE INDEX ix_error_events_embedding ON error_events
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

---

## 결론

**Phase 1 Data Model 완료**:
- ✅ ErrorEvent: pgvector 유사도 검색
- ✅ LoadTestRun: K6 결과 저장
- ✅ 외부 저장소: Prometheus, Loki, Tempo (문서화)
- ✅ Alembic Migration 스크립트
- ✅ 예상 스토리지: 1년 후 ~73MB

**다음 단계**: Contracts 생성 (Prometheus, Loki, Tempo, K6, Llama API 스펙)
