# Implementation Plan: DB 커넥션 풀과 HTTP 커넥션 풀 설정

**Branch**: `003-db-http` | **Date**: 2025-10-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/home/eugene/bodam/specs/003-db-http/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 8. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
시스템은 데이터베이스와 외부 HTTP 서비스에 대한 연결 풀을 설정하여 성능을 최적화하고 리소스 고갈을 방지합니다. SQLAlchemy의 async engine 연결 풀과 httpx/aiohttp의 HTTP 클라이언트 연결 풀을 구성하여, 높은 부하 상황에서도 안정적인 연결 관리를 제공합니다.

## Technical Context
**Language/Version**: Python 3.11+
**Primary Dependencies**: SQLAlchemy 2.0 (async), httpx 0.25+, asyncpg, aiohttp 3.9+
**Storage**: PostgreSQL (existing)
**Testing**: pytest, pytest-asyncio, pytest-cov
**Target Platform**: Linux server (Docker + Kubernetes)
**Project Type**: web (backend + frontend)
**Performance Goals**:
- 응답 시간: 5초 이내 (평균)
- 동시 요청: 100개 처리 가능
- TPS (Transactions Per Second): 환경에 따라 가변 (초기 목표 50 TPS)
- 연결 타임아웃: 일반 API 4초, 결제 API 3분
- 읽기 타임아웃: 일반 API 8초, 결제 API 3분

**Constraints**:
- 메모리 사용량: 70% 이하 유지 (초과 시 알람)
- DB 연결 풀: 기본 10개, 최대 100개 (overflow 포함)
- HTTP 연결 풀: 호스트당 최대 20개, 전체 최대 100개
- 대기 시간: 0.4초
- 재시도: 최대 2회, 간격 4초 (멱등성 보장 시에만)

**Scale/Scope**:
- 기존 서비스에 추가되는 인프라 개선 작업
- 모니터링: Prometheus + Grafana + Loki (추후 구현)
- 알람: AlertManager (추후 구현)
- 성능 테스트: K6 (추후 구현)

**User-Provided Implementation Details**:
1. **DB 커넥션 풀 설정**:
   - pool_size: 10 (기본 연결 수)
   - max_overflow: 20 (추가 확장 가능 연결 수, 총 최대 30개)
   - pool_recycle: 3600초 (1시간 후 연결 재활용)
   - pool_pre_ping: True (연결 유효성 검증)
   - pool_timeout: 0.4초 (대기 시간)
   - 연결 풀 가득 시: 추가 연결 생성 (max_overflow 내에서) + 경고 알람

2. **HTTP 커넥션 풀 설정**:
   - 전체 최대 연결: 100개
   - 호스트당 최대 연결: 20개
   - Keep-Alive 타임아웃: 60초
   - 연결 타임아웃:
     * 일반 API: 4초
     * 결제 API: 180초 (3분)
   - 읽기 타임아웃:
     * 일반 API: 8초
     * 결제 API: 180초 (3분)
   - 소켓 타임아웃: 10초
   - 호출 타임아웃: 10초

3. **재시도 정책**:
   - 재시도 허용 조건:
     * 단순 조회 (GET 요청)
     * 연결 타임아웃 발생 시
     * 멱등성이 보장된 변경 요청 (PUT, DELETE with idempotency key)
   - 재시도 제외:
     * 결제 시스템 API
     * 상태 변경 API (멱등성 미보장 시)
   - 최대 재시도 횟수: 2회
   - 재시도 간격: 4초 (exponential backoff 미적용, 고정 간격)

4. **모니터링 & 알람** (추후 구현 예정):
   - 연결 풀 메트릭: 활성 연결 수, 대기 중인 요청 수, 연결 풀 사용률
   - 알람 조건:
     * 메모리 사용량 70% 초과
     * DB 연결 풀 90% 사용 (확장 필요 경고)
     * 네트워크 장애
     * 리소스 부족 (CPU, 메모리)
   - 도구: Prometheus + Grafana + Loki + AlertManager + K6

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Compliance Analysis
The constitution template is generic and not filled out for this project. Proceeding with standard best practices:

**✅ TDD Principles**:
- Tests will be written first for connection pool configuration
- Contract tests for pool behavior (max connections, timeout, retry logic)
- Integration tests for pool usage under load

**✅ Library-First Approach**:
- Connection pool configuration will be centralized in `backend/src/database/connection.py` and `backend/src/integrations/http_client.py`
- Reusable across all API endpoints and services
- Clear separation: config layer → connection layer → service layer

**✅ Observability**:
- Structured logging for connection pool events
- Metrics endpoints for monitoring (ready for Prometheus integration)
- Clear error messages for troubleshooting

**✅ Simplicity**:
- Use existing SQLAlchemy and httpx features (no custom pool implementation)
- Configuration via environment variables (existing pattern)
- No new architectural layers introduced

**No constitutional violations detected.**

## Project Structure

### Documentation (this feature)
```
specs/003-db-http/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
backend/
├── src/
│   ├── database/
│   │   ├── connection.py        # DB pool configuration (modify)
│   │   └── pool_metrics.py      # Pool monitoring (new)
│   ├── integrations/
│   │   ├── http_client.py       # HTTP client factory (new)
│   │   └── retry_policy.py      # Retry logic (new)
│   ├── config.py                # Environment settings (modify)
│   └── monitoring/
│       └── metrics.py           # Metrics collection (modify)
└── tests/
    ├── contract/
    │   ├── test_db_pool_contract.py
    │   └── test_http_pool_contract.py
    ├── integration/
    │   ├── test_db_pool_integration.py
    │   ├── test_http_pool_integration.py
    │   └── test_retry_integration.py
    └── unit/
        ├── test_pool_config.py
        └── test_retry_policy.py
```

**Structure Decision**: Option 2 (Web application - backend + frontend). This feature only affects the backend.

## Phase 0: Outline & Research

### Research Tasks
1. **SQLAlchemy Async Pool Configuration**:
   - Research: SQLAlchemy 2.0 async engine pool parameters
   - Research: Best practices for pool_size, max_overflow, pool_recycle
   - Research: Connection health checks with pool_pre_ping
   - Research: Pool event hooks for monitoring

2. **HTTP Client Connection Pooling**:
   - Research: httpx AsyncClient connection pooling capabilities
   - Research: aiohttp ClientSession pooling (alternative)
   - Decision: Choose between httpx and aiohttp
   - Research: Per-host connection limits
   - Research: Keep-Alive and connection reuse

3. **Retry Strategies**:
   - Research: Idempotency patterns for API retries
   - Research: httpx/aiohttp retry mechanisms (tenacity library)
   - Research: Circuit breaker patterns (optional for future)

4. **Monitoring & Metrics**:
   - Research: SQLAlchemy pool events for metrics collection
   - Research: httpx/aiohttp connection pool stats
   - Research: Prometheus Python client integration
   - Research: Custom metrics for Grafana dashboards

5. **Performance Testing**:
   - Research: K6 for load testing connection pools
   - Research: Locust as alternative
   - Research: pytest-benchmark for micro-benchmarks

**Output**: [research.md](./research.md) 완료

## Phase 1: Design & Contracts

**Prerequisites**: research.md 완료됨

### Phase 1 산출물

1. **data-model.md**:
   - 설정 엔티티: DatabasePoolConfig, HttpClientConfig, HttpTimeoutConfig, RetryPolicyConfig
   - 모니터링 엔티티: PoolMetrics, HttpRequestMetrics, AlertRule (추후 구현)
   - 상태 전이: DB 연결 상태, HTTP 연결 상태
   - 검증 규칙 및 데이터 흐름

2. **contracts/** 디렉토리:
   - `db-pool-config.yaml`: DB 연결 풀 설정 계약서
   - `http-client-config.yaml`: HTTP 클라이언트 연결 풀 설정 계약서

3. **quickstart.md**:
   - 7단계 빠른 시작 가이드
   - 의존성 설치 → 환경 변수 → DB 테스트 → HTTP 테스트 → 부하 테스트
   - 트러블슈팅 가이드

4. **CLAUDE.md 업데이트**:
   - 새로운 기술 스택 추가: httpx 0.25+, tenacity 8.2+
   - 최근 변경사항 업데이트: 003-db-http 기능 추가

**Output**: 모든 Phase 1 산출물 생성 완료

### Constitution Check 재평가

Phase 1 디자인 검토 결과:

**✅ TDD 준수**:
- Contract tests 계획됨 (test_db_pool_contract.py, test_http_pool_contract.py)
- Integration tests 계획됨 (quickstart.md의 테스트 시나리오)

**✅ Library-First 준수**:
- 기존 SQLAlchemy, httpx 라이브러리 활용
- 재사용 가능한 http_client.py, retry_policy.py 모듈 설계

**✅ Observability 준수**:
- Pool events로 메트릭 수집 계획
- Prometheus 연동 준비 (추후 구현)

**✅ Simplicity 준수**:
- 커스텀 풀 구현 없음
- 환경 변수 기반 설정 (기존 패턴 유지)

**No new constitutional violations. Phase 1 approved.**

## Phase 2: Task Planning Approach

*이 섹션은 /tasks 명령어가 수행할 작업을 설명합니다. /plan 명령어는 tasks.md를 생성하지 않습니다.*

### Task 생성 전략

**TDD 순서**:
1. Contract tests 먼저 작성 (실패해야 함)
2. 구현 코드 작성 (테스트 통과)
3. Integration tests 작성
4. Refactoring (필요 시)

**의존성 순서**:
1. Config 설정 추가 (config.py)
2. DB 연결 풀 설정 (connection.py 수정)
3. HTTP 클라이언트 팩토리 (http_client.py 신규)
4. 재시도 정책 (retry_policy.py 신규)
5. 모니터링 메트릭 (pool_metrics.py 신규, 추후 구현 표시)
6. 통합 테스트 실행

**병렬 실행 가능 태스크** [P]:
- Config 필드 추가와 Contract tests는 병렬 가능
- DB pool 설정과 HTTP client 설정은 독립적이므로 병렬 가능
- 각 모듈의 unit tests는 병렬 실행 가능

### 예상 태스크 목록 (25-30개)

**Phase 0: 환경 준비** (T001-T003):
- T001: httpx, tenacity 의존성 추가 및 설치
- T002: 환경 변수 .env.example 업데이트
- T003: CLAUDE.md 검증 (자동 업데이트됨)

**Phase 1: Config 설정** (T004-T006) [P]:
- T004: config.py에 DB 연결 풀 설정 필드 추가
- T005: config.py에 HTTP 연결 풀 설정 필드 추가
- T006: config.py에 재시도 정책 설정 필드 추가

**Phase 2: TDD - Contract Tests 작성** (T007-T009) [P]:
- T007: test_db_pool_contract.py 작성 (실패)
- T008: test_http_pool_contract.py 작성 (실패)
- T009: test_retry_policy_contract.py 작성 (실패)

**Phase 3: DB 연결 풀 구현** (T010-T013):
- T010: connection.py 수정 (pool 설정 추가)
- T011: pool_metrics.py 스텁 생성 (추후 구현 표시)
- T012: test_db_pool_contract.py 실행 (통과 확인)
- T013: test_db_pool_integration.py 작성 및 실행

**Phase 4: HTTP 클라이언트 구현** (T014-T018):
- T014: http_client.py 생성 (AsyncClient 팩토리)
- T015: retry_policy.py 생성 (tenacity 데코레이터)
- T016: test_http_pool_contract.py 실행 (통과 확인)
- T017: test_retry_policy_contract.py 실행 (통과 확인)
- T018: test_http_pool_integration.py 작성 및 실행

**Phase 5: 통합** (T019-T022):
- T019: 기존 코드에서 http_client 사용하도록 리팩토링 (예: integrations/toss_payments.py)
- T020: 기존 코드에서 retry_policy 적용 (예: integrations/naver_news.py)
- T021: test_retry_integration.py 작성 및 실행
- T022: quickstart.md 1-4단계 실행 및 검증

**Phase 6: 부하 테스트** (T023-T025):
- T023: K6 부하 테스트 스크립트 작성
- T024: K6 테스트 실행 (100 VUs)
- T025: 성능 결과 분석 및 튜닝

**Phase 7: 문서화 및 정리** (T026-T028):
- T026: 모든 테스트 실행 (pytest --cov)
- T027: ARCHITECTURE.md 업데이트 (연결 풀 섹션 추가)
- T028: README.md 업데이트 (환경 변수 설명 추가)

### 예상 산출물

**코드 파일** (신규 또는 수정):
- `backend/src/config.py` (수정)
- `backend/src/database/connection.py` (수정)
- `backend/src/database/pool_metrics.py` (신규, 스텁)
- `backend/src/integrations/http_client.py` (신규)
- `backend/src/integrations/retry_policy.py` (신규)

**테스트 파일** (신규):
- `backend/tests/contract/test_db_pool_contract.py`
- `backend/tests/contract/test_http_pool_contract.py`
- `backend/tests/contract/test_retry_policy_contract.py`
- `backend/tests/integration/test_db_pool_integration.py`
- `backend/tests/integration/test_http_pool_integration.py`
- `backend/tests/integration/test_retry_integration.py`
- `backend/tests/unit/test_pool_config.py`
- `backend/tests/unit/test_retry_policy.py`

**부하 테스트 파일** (신규):
- `backend/tests/performance/connection_pool_load_test.js`

**문서 파일** (수정):
- `ARCHITECTURE.md`
- `README.md`
- `.env.example`

### 성공 기준

- [ ] 모든 contract tests 통과
- [ ] 모든 integration tests 통과
- [ ] K6 부하 테스트: 95%가 5초 이내, 에러율 1% 미만
- [ ] 코드 커버리지: 80% 이상
- [ ] quickstart.md 검증 완료

**IMPORTANT**: 이 Phase는 /tasks 명령어로 실행됩니다. /plan 명령어는 여기서 중단됩니다.

## Phase 3+: Future Implementation

*이 Phase들은 /plan 명령어 범위를 벗어납니다*

**Phase 3**: Task 실행 (/tasks 명령어가 tasks.md 생성)
**Phase 4**: 구현 (tasks.md 따라 실행)
**Phase 5**: 검증 (테스트 실행, quickstart.md 실행, 성능 검증)

## Complexity Tracking

*Constitution Check에서 위반사항이 있을 경우에만 작성*

**N/A**: 위반사항 없음

## Progress Tracking

*실행 흐름 중 업데이트됨*

**Phase 상태**:
- [x] Phase 0: 연구 완료 (/plan 명령어) ✅
- [x] Phase 1: 설계 완료 (/plan 명령어) ✅
- [x] Phase 2: Task 계획 완료 (/plan 명령어 - 접근 방식만 설명) ✅
- [ ] Phase 3: Tasks 생성 (/tasks 명령어)
- [ ] Phase 4: 구현 완료
- [ ] Phase 5: 검증 통과

**Gate 상태**:
- [x] Initial Constitution Check: PASS ✅
- [x] Post-Design Constitution Check: PASS ✅
- [x] 모든 NEEDS CLARIFICATION 해결됨 ✅
- [x] 복잡도 편차 문서화됨 (N/A) ✅

**생성된 산출물**:
- [x] research.md ✅
- [x] data-model.md ✅
- [x] contracts/db-pool-config.yaml ✅
- [x] contracts/http-client-config.yaml ✅
- [x] quickstart.md ✅
- [x] CLAUDE.md (업데이트됨) ✅

---

## 완료 요약

### /plan 명령어 실행 완료 ✅

**생성된 파일**:
1. `/home/eugene/bodam/specs/003-db-http/plan.md` (이 파일)
2. `/home/eugene/bodam/specs/003-db-http/research.md`
3. `/home/eugene/bodam/specs/003-db-http/data-model.md`
4. `/home/eugene/bodam/specs/003-db-http/contracts/db-pool-config.yaml`
5. `/home/eugene/bodam/specs/003-db-http/contracts/http-client-config.yaml`
6. `/home/eugene/bodam/specs/003-db-http/quickstart.md`
7. `/home/eugene/bodam/CLAUDE.md` (업데이트됨)

**다음 단계**:
- `/tasks` 명령어를 실행하여 tasks.md 생성
- tasks.md를 따라 TDD 방식으로 구현
- quickstart.md로 검증

**Branch**: `003-db-http`
**Status**: Ready for /tasks command

---
*Constitution 기반 - `.specify/memory/constitution.md` 참조*
