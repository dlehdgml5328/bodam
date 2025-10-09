# Implementation Plan: Redis 분리 배포 및 Celery 운영 환경

**Branch**: `002-cache-redis-queue` | **Date**: 2025-10-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/home/donghee/bodam/specs/002-cache-redis-queue/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   ✅ Loaded successfully
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   ✅ Project Type: Web (backend + frontend)
   ✅ All clarifications resolved in research.md
3. Fill the Constitution Check section
   ⚠️  Constitution file is template - using default principles
4. Evaluate Constitution Check section
   ✅ No violations (infrastructure changes only)
5. Execute Phase 0 → research.md
   ✅ Completed: Redis/Celery K8s deployment patterns researched
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
   ✅ Completed: All design artifacts generated
7. Re-evaluate Constitution Check section
   ✅ PASS - No new violations
8. Plan Phase 2 → Describe task generation approach
   ✅ Described below
9. STOP - Ready for /tasks command
   ✅ Plan complete
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

Redis를 **Cache용**과 **Queue용**으로 분리하여 K8s에 배포하고, Celery Worker/Beat/Flower를 K8s 환경으로 이전합니다. 현재 docker-compose 단일 Redis 인스턴스는 캐시 장애가 작업 큐에 영향을 주는 단일 장애점(SPOF)이므로, 독립적인 인스턴스로 분리하여 안정성과 성능을 향상시킵니다.

**주요 변경 사항**:
- Redis Cache: Deployment (메모리 전용, LRU eviction)
- Redis Queue: StatefulSet + PVC (AOF+RDB, noeviction)
- Celery Worker: Deployment + HPA (2-10 replicas)
- Celery Beat: Deployment (replicas=1, Recreate)
- Flower: Deployment + Ingress + Basic Auth
- Redis Exporter 확장 (Cache/Queue 각각)
- AlertManager 규칙 추가 (작업 큐 모니터링)

## Technical Context
**Language/Version**: Python 3.11+ (Backend)
**Primary Dependencies**: FastAPI, Celery, Redis, Kubernetes (K8s), Prometheus
**Storage**: Redis (메모리 캐시 및 작업 큐), PostgreSQL (애플리케이션 데이터), K8s PersistentVolume (Redis Queue 데이터 지속성)
**Testing**: pytest (단위 테스트), kubectl (K8s 리소스 테스트), redis-cli (Redis 헬스체크)
**Target Platform**: K8s cluster (Linux)
**Project Type**: web (backend + frontend, 이 기능은 backend 인프라 변경)
**Performance Goals**: Redis Cache 응답 시간 < 10ms p95, Celery Worker 처리량 100+ tasks/min
**Constraints**: Queue Redis 데이터 손실 < 1초 (AOF everysec), Beat 단일 인스턴스 보장
**Scale/Scope**: Redis Cache 512MB, Queue Redis 1GB 메모리 + 5GB PVC, Worker 2-10 replicas (HPA)

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**기본 원칙 검증**:

1. **Library-First**: ✅ PASS
   - 인프라 변경으로 새로운 라이브러리 작성 없음
   - 표준 K8s 리소스 및 공식 Redis/Celery 이미지 사용

2. **CLI Interface**: ✅ PASS
   - kubectl 명령어로 모든 리소스 관리
   - redis-cli로 헬스체크 수행

3. **Test-First**: ✅ PASS
   - K8s 리소스 배포 후 헬스체크 테스트 실행
   - Celery 작업 통합 테스트 포함 (quickstart.md 참조)

4. **Integration Testing**: ✅ PASS
   - Redis 연결 테스트, Celery 작업 실행 테스트
   - Prometheus 메트릭 수집 검증

5. **Observability**: ✅ PASS
   - Redis Exporter로 메트릭 수집
   - Prometheus + AlertManager 통합
   - Flower 대시보드 제공

**결론**: 모든 기본 원칙 통과. 인프라 변경으로 애플리케이션 코드 변경 최소화.

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 2: Web application (현재 프로젝트 구조)
backend/
├── src/
│   ├── models/
│   ├── services/
│   ├── api/
│   └── workers/          # Celery 작업 정의
└── tests/
    ├── integration/
    └── unit/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

infra/
├── k8s/
│   ├── backend/
│   ├── frontend/
│   ├── monitoring/
│   ├── redis/           # 이번 기능에서 추가
│   │   ├── cache/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   ├── configmap.yaml
│   │   │   └── exporter.yaml
│   │   └── queue/
│   │       ├── statefulset.yaml
│   │       ├── service.yaml
│   │       ├── configmap.yaml
│   │       ├── exporter.yaml
│   │       └── backup-cronjob.yaml
│   └── celery/          # 이번 기능에서 추가
│       ├── worker-deployment.yaml
│       ├── worker-hpa.yaml
│       ├── beat-deployment.yaml
│       ├── flower-deployment.yaml
│       ├── flower-service.yaml
│       └── flower-ingress.yaml
└── monitoring/
    └── alertmanager-rules.yaml  # 확장 예정
```

**Structure Decision**: Option 2 (Web application). 이번 기능은 인프라 구성 변경으로 `infra/k8s/redis/` 및 `infra/k8s/celery/` 디렉토리 추가.

## Phase 0: Outline & Research

**완료된 리서치 작업** (`research.md` 참조):

1. **K8s에서 Redis 분리 배포 (Cache/Queue)**:
   - Cache Redis: Deployment (메모리 전용, LRU eviction)
   - Queue Redis: StatefulSet + PVC (AOF+RDB, noeviction)
   - 고가용성: 현재 단일 인스턴스 (향후 Sentinel/Cluster 업그레이드)

2. **Redis 백업 정책**:
   - Queue Redis: AOF (everysec) + RDB 스냅샷 (1시간마다)
   - K8s CronJob으로 매일 새벽 2시 S3 백업
   - 백업 보관: 7일 (일일), 4주 (주간)

3. **Celery Worker/Beat/Flower K8s 배포**:
   - Worker: Deployment + HPA (2-10 replicas, CPU 70%)
   - Beat: Deployment (replicas=1, Recreate 전략)
   - Flower: Deployment + Basic Auth + Ingress 제한

4. **작업 큐 라우팅**:
   - `critical` 큐: 결제 처리 (높은 우선순위)
   - `celery` 큐: 일반 작업 (알림 발송)
   - `batch` 큐: 크롤링, 분석 (낮은 우선순위)

5. **모니터링 및 알림**:
   - redis-exporter: Cache/Queue 각각 배포
   - Celery Custom Exporter: Flower API 스크래핑
   - AlertManager: Redis 메모리, 작업 큐 길이, Worker 상태

**Output**: `research.md` (완료)

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

**완료된 설계 작업**:

1. **Data Model** (`data-model.md`):
   - 운영 엔티티 정의 (인프라 리소스)
   - Redis 인스턴스: Cache Redis, Queue Redis
   - Celery 컴포넌트: Worker, Beat, Flower
   - 모니터링 리소스: Redis Exporter, Celery Exporter
   - 백업 리소스: CronJob

2. **K8s 리소스 계약** (`contracts/README.md`):
   - Redis Cache Service: `redis-cache-service:6379`
   - Redis Queue Service: `redis-queue-service:6379`
   - 환경 변수 계약: `REDIS_CACHE_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
   - Celery 작업 큐 라우팅: `critical`, `celery`, `batch`
   - 모니터링 계약: Prometheus 메트릭, AlertManager 규칙
   - 백업 및 복구 계약: S3 백업, RDB 복구 절차

3. **Quickstart Guide** (`quickstart.md`):
   - Step-by-step 배포 가이드 (9단계)
   - Redis Cache/Queue 배포
   - Celery Worker/Beat/Flower 배포
   - 모니터링 설정
   - 통합 테스트 시나리오
   - Troubleshooting 가이드

4. **CLAUDE.md 업데이트**:
   - 이미 프로젝트 루트에 존재 (`/home/donghee/bodam/CLAUDE.md`)
   - 이 기능 후 업데이트 예정 (Redis/Celery K8s 배포 기술 스택 추가)

**Output**: `data-model.md`, `contracts/README.md`, `quickstart.md` (모두 완료)

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:

1. **K8s YAML 작성 태스크** (각 리소스별 독립 파일):
   - Redis Cache: Deployment, Service, ConfigMap, Exporter [P]
   - Redis Queue: StatefulSet, Service, ConfigMap, Exporter, Backup CronJob [P]
   - Celery Worker: Deployment, HPA [P]
   - Celery Beat: Deployment [P]
   - Flower: Deployment, Service, Ingress [P]
   - Secrets: flower-auth, aws-credentials

2. **환경 변수 업데이트**:
   - Backend `.env.example` 업데이트 (REDIS_CACHE_URL, CELERY_BROKER_URL)
   - Backend Deployment 환경 변수 추가

3. **테스트 작성**:
   - Redis 헬스체크 테스트 (cache, queue)
   - Celery 작업 실행 통합 테스트
   - Prometheus 메트릭 수집 검증 테스트

4. **배포 및 검증**:
   - kubectl apply로 리소스 배포
   - 헬스체크 실행
   - Flower 대시보드 접속 확인
   - 기존 docker-compose redis 중단

5. **모니터링 설정**:
   - AlertManager 규칙 추가 (Redis 메모리, 작업 큐 길이)
   - Prometheus ServiceMonitor 업데이트

**Ordering Strategy**:
- Secrets/ConfigMaps 먼저 생성 (의존성)
- Redis 배포 → Celery 배포 순서
- 각 컴포넌트별 YAML은 병렬 작성 가능 [P]
- 배포는 순차적 실행 (Redis → Backend → Celery)

**Estimated Output**: 약 25개 태스크 (K8s YAML 12개 + 테스트 5개 + 배포/검증 8개)

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (해당 없음 - 모든 원칙 통과)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
