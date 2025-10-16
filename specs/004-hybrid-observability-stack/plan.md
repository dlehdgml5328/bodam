# 구현 계획: 하이브리드 관측성 스택 (Hybrid Observability Stack)

**Branch**: `wonuk` | **Date**: 2025-10-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/home/eugene/bodam/specs/004-hybrid-observability-stack/spec.md`

## Execution Flow (/plan 명령 범위)
```
1. Feature spec 로드 완료
   → 경로: /home/eugene/bodam/specs/004-hybrid-observability-stack/spec.md
2. Technical Context 작성 완료
   → 프로젝트 타입: Web (FastAPI backend + Next.js frontend)
   → 구조 결정: Option 2 (backend/ + frontend/)
3. Constitution Check 평가 완료
   → 템플릿만 존재, 프로젝트는 기존 구조 유지
4. Phase 0 실행 중 → research.md
5. Phase 1 실행 예정 → contracts, data-model.md, quickstart.md
6. Phase 2 계획 → tasks.md 생성 전략 (STOP, /tasks 명령 대기)
```

## 요약
보담(BoDam) 소방관 커피 기부 플랫폼에 하이브리드 관측성 스택을 구현합니다. 이 시스템은 Prometheus(메트릭), Loki(로그), Tempo(트레이스)를 로컬 Kubernetes 클러스터에 배포하여 3일(메트릭/로그) 또는 2일(트레이스) 동안 빠른 쿼리를 지원하고, Grafana Cloud Free Tier로 Remote Write하여 14일간 장기 보관합니다. Llama AI 어시스턴트가 로컬 관측성 스택을 직접 쿼리(HTTP API)하여 1초 이내 응답을 제공하고, K6 부하 테스트가 200 동시 사용자를 시뮬레이션하며, HPA가 CPU 70%/Memory 80% 기준으로 Backend를 최대 3 replicas까지 자동 확장합니다. 월 비용은 $36(DigitalOcean DOKS)입니다.

## Technical Context
**Language/Version**: Python 3.11+ (Backend), TypeScript/Node.js 18+ (Frontend), JavaScript (K6)
**Primary Dependencies**:
- Backend: FastAPI, SQLAlchemy 2.0 (Async), Celery, OpenTelemetry SDK, prometheus-client, httpx
- Observability: Prometheus, Loki, Promtail, Tempo, Grafana Cloud SDK
- Load Testing: K6
- Infrastructure: Kubernetes (DOKS), Kong Gateway, NGINX

**Storage**:
- Primary: PostgreSQL + pgvector (ErrorEvent with embeddings)
- Cache: Redis
- Local Observability: PersistentVolumes (Prometheus 3d, Loki 3d, Tempo 2d)
- Remote: Grafana Cloud Free Tier (14d retention)

**Testing**: pytest (Backend unit/integration/contract), K6 (load testing), OpenAPI contract tests

**Target Platform**:
- Development: Docker Compose
- Production: Kubernetes (DigitalOcean DOKS, 1 Node 8GB RAM)
- Frontend Deployment: Vercel

**Project Type**: Web (backend/ + frontend/ structure)

**Performance Goals**:
- Observability query latency: < 1s (로컬 데이터)
- Metric collection overhead: < 2% CPU
- Log/Trace collection latency: < 10ms per request
- K6 load test: 200 concurrent users, p95 < 500ms
- AI assistant response: < 1s (Llama 쿼리)

**Constraints**:
- Monthly cost: < $40 (현재 $36 target)
- Local retention: 3d (metrics/logs), 2d (traces)
- Remote retention: 14d (Grafana Cloud Free Tier)
- Grafana Cloud limits: 10K active series, 50GB logs/month, 50GB traces/month
- HPA max replicas: 3 (Backend only)
- Disk space alert: 80% threshold

**Scale/Scope**:
- Application Pods: 5 (Backend, PostgreSQL, Redis, NGINX, Kong)
- Observability Pods: 4 (Prometheus, Loki, Tempo, Promtail DaemonSet)
- Total: 9 Pods (평상시) → 11 Pods (HPA 확장 시)
- Metrics: ~10K series, CPU/Memory/HTTP metrics + custom (donation count, crawler success rate)
- Logs: < 1GB/day (moderate volume)
- Traces: 100% collection (low traffic), sampling 10-30% (high traffic)
- K6 scenarios: 50-500 VU (Virtual Users)

## Constitution Check
*GATE: 템플릿만 존재, 프로젝트는 기존 패턴 따름*

이 프로젝트는 `.specify/memory/constitution.md`가 템플릿만 포함하고 있어 명시적 constitutional 제약이 없습니다. 따라서 기존 bodam 프로젝트 구조와 패턴을 따릅니다:

**기존 패턴 준수**:
- ✅ Web 프로젝트 구조: `backend/` + `frontend/`
- ✅ FastAPI + SQLAlchemy 2.0 async 패턴
- ✅ Kubernetes 배포 (`infra/k8s/`)
- ✅ Docker Compose 로컬 개발
- ✅ pytest 테스트 프레임워크
- ✅ Celery 비동기 작업 처리
- ✅ Kong Gateway + NGINX 구성

**새로운 컴포넌트**:
- Prometheus + Loki + Tempo (관측성 스택)
- Grafana Cloud 통합 (Remote Write)
- OpenTelemetry instrumentation (분산 트레이싱)
- K6 load testing
- Llama 쿼리 인터페이스 (기존 AI 기반 확장)

**복잡도 정당화**:
- Hybrid approach (로컬 + 원격)는 FR-014(1초 쿼리) + NFR-006(비용 $40 미만)을 동시 만족하기 위해 필수
- 3개 관측성 툴(Prometheus, Loki, Tempo)은 각각 다른 데이터 타입(metrics, logs, traces) 처리를 위해 필수

## 프로젝트 구조

### 문서 (이 기능)
```
specs/004-hybrid-observability-stack/
├── spec.md              # 기능 명세서 (완료)
├── plan.md              # 이 파일 (/plan 명령 출력)
├── research.md          # Phase 0 출력 (/plan 명령)
├── data-model.md        # Phase 1 출력 (/plan 명령)
├── quickstart.md        # Phase 1 출력 (/plan 명령)
├── contracts/           # Phase 1 출력 (/plan 명령)
│   ├── prometheus-metrics.yaml          # Prometheus scrape config
│   ├── loki-config.yaml                 # Loki configuration
│   ├── tempo-config.yaml                # Tempo configuration
│   ├── grafana-agent-config.yaml        # Alternative: Grafana Agent
│   ├── k6-scenarios.js                  # K6 test scenarios
│   └── llama-observability-api.yaml     # Llama 쿼리 API contract
└── tasks.md             # Phase 2 출력 (/tasks 명령 - /plan에서 생성 안 함)
```

### 소스 코드 (저장소 루트)
```
bodam/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── observability.py         # /metrics endpoint (Prometheus)
│   │   │   └── llama_query.py           # Llama observability query API
│   │   ├── models/
│   │   │   └── error_event.py           # ErrorEvent model (pgvector)
│   │   ├── services/
│   │   │   ├── observability_agent.py   # Llama → Prometheus/Loki/Tempo
│   │   │   └── error_analyzer.py        # Vector similarity search
│   │   ├── middleware/
│   │   │   └── tracing.py               # OpenTelemetry FastAPI middleware
│   │   └── workers/
│   │       └── error_logger.py          # Celery: 에러 이벤트 저장
│   └── tests/
│       ├── contract/
│       │   ├── test_prometheus_metrics_contract.py
│       │   ├── test_loki_logs_contract.py
│       │   └── test_tempo_traces_contract.py
│       ├── integration/
│       │   ├── test_observability_stack_integration.py
│       │   ├── test_llama_query_integration.py
│       │   └── test_k6_monitoring_integration.py
│       └── unit/
│           └── test_observability_agent.py
│
├── frontend/
│   ├── src/
│   │   └── (기존 구조 유지, 추가 변경 없음)
│
├── infra/k8s/
│   ├── observability/
│   │   ├── prometheus/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   ├── configmap.yaml           # prometheus.yml + remote_write
│   │   │   └── pvc.yaml                 # 3d retention storage
│   │   ├── loki/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   ├── configmap.yaml           # loki.yaml + remote_write
│   │   │   └── pvc.yaml                 # 3d retention storage
│   │   ├── tempo/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   ├── configmap.yaml           # tempo.yaml + remote_write
│   │   │   └── pvc.yaml                 # 2d retention storage
│   │   ├── promtail/
│   │   │   ├── daemonset.yaml           # 각 노드마다 로그 수집
│   │   │   └── configmap.yaml           # promtail.yaml
│   │   └── secrets/
│   │       └── grafana-cloud-secrets.yaml  # API keys
│   ├── backend/
│   │   └── hpa.yaml                     # 기존에 추가: CPU 70%, Mem 80%, max 3
│   └── (기존 kong, nginx 유지)
│
├── tests/load/
│   ├── scenarios/
│   │   ├── baseline-50vu.js             # 50 Virtual Users
│   │   ├── moderate-200vu.js            # 200 VU
│   │   └── stress-500vu.js              # 500 VU
│   └── utils/
│       └── prometheus-reporter.js       # K6 → Prometheus exporter
│
└── docker-compose.dev.yml               # 로컬 개발용 (Prometheus, Loki, Tempo 추가)
```

**구조 결정**: Option 2 (Web application) - backend/ + frontend/ 유지

## Phase 0: 개요 & 리서치

### 1. Technical Context에서 미해결 사항 추출
모든 기술적 결정사항이 사용자와의 논의를 통해 명확히 정의되었습니다. NEEDS CLARIFICATION 항목 없음.

### 2. 리서치 태스크 생성 및 실행

#### 리서치 영역:
1. **Prometheus + Grafana Cloud Remote Write**
   - Prometheus remote_write 설정 베스트 프랙티스
   - Grafana Cloud Free Tier 제한 및 최적화
   - Metric relabeling 및 필터링

2. **Loki + Promtail 구성**
   - Kubernetes 환경에서 Promtail DaemonSet 패턴
   - 로그 파싱 및 구조화 (pipeline stages)
   - Loki retention 및 compaction 설정

3. **Tempo 분산 트레이싱**
   - OpenTelemetry + FastAPI instrumentation
   - Trace context propagation (Kong, NGINX)
   - Tempo storage backend (로컬 filesystem)

4. **K6 + Prometheus 통합**
   - K6 statsd output → Prometheus
   - 실시간 부하 테스트 모니터링
   - K6 Grafana 대시보드

5. **Llama Observability Query Interface**
   - Prometheus HTTP API (PromQL)
   - Loki HTTP API (LogQL)
   - Tempo HTTP API (TraceQL)
   - Python httpx async client patterns

6. **HPA (Horizontal Pod Autoscaler)**
   - Kubernetes HPA v2 (CPU + Memory metrics)
   - Prometheus Adapter (custom metrics)
   - Scale-up/down behavior tuning

7. **PostgreSQL pgvector for ErrorEvent**
   - Vector embedding storage
   - Cosine similarity search
   - Embedding model selection (MiniLM, all-MiniLM-L6-v2)

**Output**: [research.md](research.md) (다음 단계에서 생성)

## Phase 1: 설계 & Contracts

### 1. 엔티티 추출 → data-model.md

**기존 엔티티 (유지)**:
- Donation, FireStation, CrawlJob, CrawledContent (기존 모델)

**새로운 엔티티**:
- **ErrorEvent**: 중요 에러 이벤트 (pgvector embedding)
  - Fields: id, timestamp, level, message, traceback, service, trace_id, span_id, embedding (vector)
  - Relationships: 관련 Trace ID 참조
  - State: new → analyzed → resolved

- **LoadTestRun**: K6 부하 테스트 실행 기록
  - Fields: id, start_time, end_time, target_vu, scenario_name, status, metrics_summary
  - Relationships: Prometheus 메트릭 창 (시간 범위)

**관측성 데이터 (외부 저장)**:
- Metric: Prometheus TSDB (로컬 3d + Grafana Cloud 14d)
- Log: Loki storage (로컬 3d + Grafana Cloud 14d)
- Trace: Tempo storage (로컬 2d + Grafana Cloud 14d)

### 2. API Contracts 생성 → /contracts/

#### A. Prometheus Metrics Endpoint (FastAPI)
```yaml
# contracts/prometheus-metrics.yaml
openapi: 3.0.0
paths:
  /metrics:
    get:
      summary: Prometheus metrics endpoint
      responses:
        '200':
          description: Prometheus exposition format
          content:
            text/plain:
              schema:
                type: string
              example: |
                # HELP http_requests_total Total HTTP requests
                # TYPE http_requests_total counter
                http_requests_total{method="GET",endpoint="/api/donations",status="200"} 1234

                # HELP http_request_duration_seconds HTTP request latency
                # TYPE http_request_duration_seconds histogram
                http_request_duration_seconds_bucket{le="0.1"} 95
                http_request_duration_seconds_sum 123.45
                http_request_duration_seconds_count 1000
```

#### B. Llama Observability Query API (FastAPI)
```yaml
# contracts/llama-observability-api.yaml
openapi: 3.0.0
paths:
  /api/observability/query:
    post:
      summary: Llama가 관측성 데이터 쿼리
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                question:
                  type: string
                  example: "지난 1시간 동안 발생한 에러는?"
                time_range:
                  type: string
                  example: "1h"
                data_sources:
                  type: array
                  items:
                    type: string
                    enum: [metrics, logs, traces]
                  example: ["logs", "traces"]
      responses:
        '200':
          description: 분석 결과
          content:
            application/json:
              schema:
                type: object
                properties:
                  answer:
                    type: string
                  data:
                    type: object
                    properties:
                      logs:
                        type: array
                      traces:
                        type: array
                      similar_errors:
                        type: array
```

#### C. K6 Load Test Scenarios
```javascript
// contracts/k6-scenarios.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';

export let options = {
  stages: [
    { duration: '1m', target: 50 },   // Ramp-up to 50 VU
    { duration: '3m', target: 50 },   // Stay at 50 VU
    { duration: '1m', target: 200 },  // Ramp-up to 200 VU
    { duration: '5m', target: 200 },  // Stay at 200 VU
    { duration: '2m', target: 0 },    // Ramp-down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<500'],  // 95% < 500ms
    'http_req_failed': ['rate<0.01'],     // Error rate < 1%
  },
};

export default function () {
  // Test scenarios for /api/donations, /api/fire-stations, etc.
}
```

#### D. Kubernetes Configs (Contracts)
- `contracts/prometheus-config.yaml`: Prometheus scrape configs + remote_write
- `contracts/loki-config.yaml`: Loki limits + remote_write
- `contracts/tempo-config.yaml`: Tempo receivers + remote_write

### 3. Contract Tests 생성

```python
# tests/contract/test_prometheus_metrics_contract.py
import pytest
import httpx

@pytest.mark.asyncio
async def test_metrics_endpoint_returns_prometheus_format():
    """FR-001: Prometheus 메트릭 엔드포인트가 올바른 포맷 반환"""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8080/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; version=0.0.4"

    # 필수 메트릭 검증
    content = response.text
    assert "http_requests_total" in content
    assert "http_request_duration_seconds" in content
    # 이 테스트는 현재 FAIL (구현 전)
```

```python
# tests/integration/test_llama_query_integration.py
import pytest
from src.services.observability_agent import ObservabilityAgent

@pytest.mark.asyncio
async def test_llama_queries_loki_for_recent_errors():
    """FR-013, FR-014: Llama가 Loki를 쿼리하여 1초 이내 응답"""
    agent = ObservabilityAgent()

    import time
    start = time.time()
    result = await agent.analyze_with_llama("지난 1시간 동안 에러 분석")
    duration = time.time() - start

    assert duration < 1.0  # NFR-001: 1초 이내
    assert "error" in result.lower() or "에러" in result.lower()
    # 이 테스트는 현재 FAIL (구현 전)
```

### 4. 테스트 시나리오 추출 → quickstart.md

User Story → Quickstart 검증 단계:
1. Prometheus가 /metrics 엔드포인트를 스크래핑하는지 확인
2. Loki가 Backend 로그를 수집하는지 확인
3. Tempo가 API 요청 트레이스를 캡처하는지 확인
4. K6 부하 테스트 실행 및 Grafana Cloud 대시보드 확인
5. Llama에게 "CPU 사용량 추이" 질문하여 Prometheus 쿼리 확인
6. HPA가 부하 증가 시 Backend Pod 확장하는지 확인

### 5. Agent Context 업데이트 (CLAUDE.md)

기존 CLAUDE.md에 추가할 내용:
- Observability stack: Prometheus, Loki, Tempo (로컬 + Grafana Cloud)
- OpenTelemetry FastAPI instrumentation
- K6 load testing with Prometheus integration
- Llama observability query interface (Prometheus/Loki/Tempo HTTP APIs)
- HPA configuration (CPU 70%, Memory 80%, max 3 replicas)

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, CLAUDE.md 업데이트

## Phase 2: Task Planning Approach
*이 섹션은 /tasks 명령이 실행할 내용 설명 - /plan에서 실행 안 함*

### 태스크 생성 전략:

#### A. Contract Tests (Phase 1에서 생성됨, FAIL 상태)
- [P] T001: Prometheus /metrics 엔드포인트 contract test
- [P] T002: Loki 로그 수집 contract test
- [P] T003: Tempo 트레이스 캡처 contract test
- [P] T004: K6 시나리오 contract test
- [P] T005: Llama 쿼리 API contract test

#### B. Infrastructure Setup (순차)
- T006: Prometheus Kubernetes manifests (deployment, service, configmap, pvc)
- T007: Loki Kubernetes manifests
- T008: Tempo Kubernetes manifests
- T009: Promtail DaemonSet
- T010: Grafana Cloud secrets 생성
- T011: Remote Write 설정 (Prometheus, Loki, Tempo)
- T012: Docker Compose에 관측성 스택 추가 (로컬 개발용)

#### C. Backend Implementation (TDD 순서)
- [P] T013: ErrorEvent 모델 (pgvector embedding)
- [P] T014: LoadTestRun 모델
- T015: Prometheus /metrics 엔드포인트 구현 (T001 통과)
- T016: OpenTelemetry FastAPI middleware (T003 통과)
- T017: ObservabilityAgent 서비스 (Llama → Prometheus/Loki/Tempo)
- T018: Llama 쿼리 API 구현 (T005 통과)
- T019: ErrorAnalyzer 서비스 (pgvector similarity search)
- T020: Celery worker: 에러 이벤트 자동 저장

#### D. K6 Load Testing
- [P] T021: K6 baseline scenario (50 VU)
- [P] T022: K6 moderate scenario (200 VU)
- [P] T023: K6 stress scenario (500 VU)
- T024: K6 → Prometheus 연동 (statsd exporter)

#### E. HPA & Integration Tests
- T025: Backend HPA manifest (CPU 70%, Memory 80%, max 3)
- T026: Observability stack integration test (Prometheus + Loki + Tempo)
- T027: Llama query integration test (1초 이내 응답)
- T028: K6 + monitoring integration test (부하 테스트 중 메트릭 수집)
- T029: HPA scale-up integration test (CPU 부하 증가 → Pod 증가)
- T030: Network failure resilience test (Remote Write 장애 시 로컬 버퍼링)

#### F. Documentation & Validation
- T031: Quickstart.md 검증 (모든 단계 실행 가능)
- T032: Grafana Cloud 대시보드 스크린샷 및 문서화
- T033: 비용 검증 ($36/월 확인)
- T034: 성능 검증 (NFR-001, NFR-002, NFR-003)

### 순서 전략:
1. **TDD 순서**: Contract tests (T001-T005) → Infrastructure (T006-T012) → Implementation (T013-T020)
2. **의존성 순서**: Models → Services → API → Integration
3. **병렬 실행 [P]**: 독립적인 파일 (contract tests, models, K6 scenarios)

### 예상 출력: 34개의 번호가 부여되고 순서가 정해진 태스크 (tasks.md)

**중요**: 이 단계는 /tasks 명령으로 실행되며, /plan에서는 실행되지 않음

## Phase 3+: 향후 구현
*이 단계들은 /plan 명령 범위 밖*

**Phase 3**: 태스크 실행 (/tasks 명령이 tasks.md 생성)
**Phase 4**: 구현 (tasks.md 실행, constitutional 원칙 준수)
**Phase 5**: 검증 (테스트 실행, quickstart.md 실행, 성능 검증)

## 복잡도 추적
*Constitution Check 위반이 정당화되어야 하는 경우에만 작성*

이 프로젝트는 명시적 constitution이 없으므로 이 섹션은 N/A입니다. 기존 bodam 패턴을 따릅니다.

## 진행 상황 추적
*실행 흐름 중 업데이트되는 체크리스트*

### Phase 상태:
- [ ] Phase 0: Research 완료 (/plan 명령) → 다음 단계
- [ ] Phase 1: Design 완료 (/plan 명령) → 다음 단계
- [ ] Phase 2: Task planning 완료 (/plan 명령 - 전략만 설명) → 다음 단계
- [ ] Phase 3: Tasks 생성됨 (/tasks 명령)
- [ ] Phase 4: 구현 완료
- [ ] Phase 5: 검증 통과

### Gate 상태:
- [x] 초기 Constitution Check: PASS (템플릿만 존재, 기존 패턴 준수)
- [ ] Post-Design Constitution Check: PASS (Phase 1 후 재확인)
- [x] 모든 NEEDS CLARIFICATION 해결됨 (사용자와의 논의 완료)
- [x] 복잡도 편차 문서화됨 (N/A - constitution 없음)

---
*Based on Constitution v[template] - See `.specify/memory/constitution.md`*
