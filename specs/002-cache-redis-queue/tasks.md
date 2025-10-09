# Tasks: Redis 분리 배포 및 Celery 운영 환경

**Input**: Design documents from `/home/donghee/bodam/specs/002-cache-redis-queue/`
**Prerequisites**: plan.md (✅), research.md (✅), data-model.md (✅), contracts/ (✅), quickstart.md (✅)

## Execution Flow (main)
```
1. Load plan.md from feature directory
   ✅ Loaded: K8s 인프라 변경, Redis 분리, Celery 배포
2. Load optional design documents:
   ✅ data-model.md: Redis Cache, Queue, Celery Worker/Beat/Flower
   ✅ contracts/: K8s 리소스 계약, 환경 변수 계약
   ✅ research.md: StatefulSet vs Deployment, 백업 정책, HPA
3. Generate tasks by category:
   ✅ Setup: K8s 디렉토리 생성, Secrets
   ✅ Tests: Redis 헬스체크, Celery 작업 실행 테스트
   ✅ Core: K8s YAML 작성 (Redis, Celery)
   ✅ Integration: Backend 환경 변수 업데이트, 모니터링
   ✅ Polish: 백업 검증, 문서화
4. Apply task rules:
   ✅ K8s YAML 파일 (독립적) = [P]
   ✅ 배포 순서 (의존성) = 순차
5. Number tasks sequentially (T001-T030)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   ✅ All contracts have tests
   ✅ All entities have K8s resources
9. Return: SUCCESS (30 tasks ready for execution)
```

---

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

---

## Phase 3.1: Setup (사전 준비)

- [x] **T001** K8s 디렉토리 구조 생성 ✅
  - 생성: `infra/k8s/redis/cache/`, `infra/k8s/redis/queue/`, `infra/k8s/celery/`
  - 확인: 디렉토리 존재 여부

- [x] **T002** K8s Secrets 생성 스크립트 작성 ✅
  - 파일: `infra/k8s/scripts/create-secrets.sh`
  - 내용: Flower Basic Auth 비밀번호, AWS credentials (백업용)
  - 실행 권한 부여: `chmod +x`

- [x] **T003** [P] Backend 환경 변수 예시 파일 업데이트 ✅
  - 파일: `backend/.env.example`
  - 추가: `REDIS_CACHE_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
  - 기존 `REDIS_URL` 주석 처리 또는 제거

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Redis 헬스체크 테스트

- [x] **T004** [P] Redis Cache 헬스체크 테스트 ✅
  - 파일: `backend/tests/integration/test_redis_cache_health.py`
  - 테스트:
    - Redis Cache Service에 연결 (`redis-cache-service:6379`)
    - `PING` 명령 → `PONG` 응답 확인
    - DB 0 접근 가능 확인
  - 예상 결과: **FAIL** (Redis Cache 미배포)

- [x] **T005** [P] Redis Queue 헬스체크 및 PVC 테스트 ✅
  - 파일: `backend/tests/integration/test_redis_queue_health.py`
  - 테스트:
    - Redis Queue Service에 연결 (`redis-queue-service:6379`)
    - `PING` 명령 → `PONG` 응답 확인
    - DB 0 (Broker), DB 1 (Result Backend) 접근 확인
    - PVC 마운트 확인 (kubectl로 PVC Bound 상태 확인)
  - 예상 결과: **FAIL** (Redis Queue 미배포)

### Celery 통합 테스트

- [x] **T006** [P] Celery Worker 작업 실행 테스트 ✅
  - 파일: `backend/tests/integration/test_celery_worker.py`
  - 테스트:
    - `health_check` 작업 실행 (`worker.health_check.delay()`)
    - 결과 확인: `"ok"` 반환
    - 작업 완료 시간 < 5초
  - 예상 결과: **FAIL** (Celery Worker 미배포)

- [x] **T007** [P] Celery Beat 스케줄 테스트 ✅
  - 파일: `backend/tests/integration/test_celery_beat.py`
  - 테스트:
    - Beat 스케줄 정의 확인 (`celery_app.conf.beat_schedule`)
    - `crawl-news-every-30min` 스케줄 존재 확인
    - Beat Pod가 정확히 1개 실행 중인지 확인 (kubectl)
  - 예상 결과: **FAIL** (Celery Beat 미배포)

- [x] **T008** [P] Flower 웹 UI 접속 테스트 ✅
  - 파일: `backend/tests/integration/test_flower_ui.py`
  - 테스트:
    - Flower 접속 (`https://bodam.example.com/flower` 또는 port-forward)
    - Basic Auth 인증 성공 (`admin:{password}`)
    - Worker 목록 조회 API (`/flower/api/workers`) 응답 확인
  - 예상 결과: **FAIL** (Flower 미배포)

### 백업 테스트

- [x] **T009** [P] Redis Queue 백업 CronJob 테스트 ✅
  - 파일: `backend/tests/integration/test_redis_backup.py`
  - 테스트:
    - CronJob 수동 실행 (`kubectl create job --from=cronjob/redis-queue-backup`)
    - RDB 파일 생성 확인 (`/data/dump.rdb` 존재)
    - S3 업로드 확인 (모킹 또는 실제 S3)
  - 예상 결과: **FAIL** (백업 CronJob 미생성)

---

## Phase 3.3: Core Implementation (K8s YAML 작성)

### Redis Cache 리소스

- [x] **T010** [P] Redis Cache ConfigMap 작성 ✅
  - 파일: `infra/k8s/redis/cache/configmap.yaml`
  - 내용:
    - `maxmemory 512mb`
    - `maxmemory-policy allkeys-lru`
    - `save ""` (백업 없음)
    - `appendonly no`

- [x] **T011** [P] Redis Cache Deployment 작성 ✅
  - 파일: `infra/k8s/redis/cache/deployment.yaml`
  - 내용:
    - Image: `redis:7.2-alpine`
    - ConfigMap 마운트
    - Resources: 256Mi request, 512Mi limit
    - Liveness/Readiness Probe

- [x] **T012** [P] Redis Cache Service 작성 ✅
  - 파일: `infra/k8s/redis/cache/service.yaml`
  - 내용:
    - Type: ClusterIP
    - Port: 6379
    - Selector: `app: redis-cache`

- [x] **T013** [P] Redis Cache Exporter Deployment 작성 ✅
  - 파일: `infra/k8s/redis/cache/exporter.yaml`
  - 내용:
    - Image: `oliver006/redis_exporter:latest`
    - Env: `REDIS_ADDR=redis://redis-cache-service:6379`
    - Service (metrics port 9121)
    - ServiceMonitor (Prometheus 스크래핑)

### Redis Queue 리소스

- [x] **T014** [P] Redis Queue ConfigMap 작성 ✅
  - 파일: `infra/k8s/redis/queue/configmap.yaml`
  - 내용:
    - `maxmemory 1gb`
    - `maxmemory-policy noeviction`
    - `appendonly yes`
    - `appendfsync everysec`
    - `save 3600 1`

- [x] **T015** [P] Redis Queue StatefulSet 작성 ✅
  - 파일: `infra/k8s/redis/queue/statefulset.yaml`
  - 내용:
    - Image: `redis:7.2-alpine`
    - ConfigMap 마운트
    - PVC Template (5Gi)
    - Resources: 512Mi request, 1Gi limit

- [x] **T016** [P] Redis Queue Headless Service 작성 ✅
  - 파일: `infra/k8s/redis/queue/service.yaml`
  - 내용:
    - Type: ClusterIP
    - `clusterIP: None` (Headless)
    - Port: 6379

- [x] **T017** [P] Redis Queue Exporter Deployment 작성 ✅
  - 파일: `infra/k8s/redis/queue/exporter.yaml`
  - 내용: Cache Exporter와 동일하되 `REDIS_ADDR=redis://redis-queue-service:6379`

- [x] **T018** [P] Redis Queue 백업 CronJob 작성 ✅
  - 파일: `infra/k8s/redis/queue/backup-cronjob.yaml`
  - 내용:
    - Schedule: `0 2 * * *` (매일 새벽 2시)
    - Job: `redis-cli BGSAVE` → S3 업로드
    - AWS credentials Secret 참조

### Celery 리소스

- [x] **T019** [P] Celery Worker Deployment 작성 ✅
  - 파일: `infra/k8s/celery/worker-deployment.yaml`
  - 내용:
    - Image: `{your-registry}/bodam-backend:latest`
    - Command: `celery -A src.worker.celery_app worker --loglevel=info --concurrency=4`
    - Env: `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `DATABASE_URL`
    - Resources: 256Mi request, 512Mi limit

- [x] **T020** [P] Celery Worker HPA 작성 ✅
  - 파일: `infra/k8s/celery/worker-hpa.yaml`
  - 내용:
    - minReplicas: 2, maxReplicas: 10
    - targetCPUUtilizationPercentage: 70
    - scaleUp/scaleDown stabilizationWindow

- [x] **T021** [P] Celery Beat Deployment 작성 ✅
  - 파일: `infra/k8s/celery/beat-deployment.yaml`
  - 내용:
    - replicas: 1 (고정)
    - strategy: Recreate
    - Command: `celery -A src.worker.celery_app beat --loglevel=info`

- [x] **T022** [P] Flower Deployment 작성 ✅
  - 파일: `infra/k8s/celery/flower-deployment.yaml`
  - 내용:
    - Command: `celery -A src.worker.celery_app flower --port=5555 --url_prefix=/flower --basic_auth=admin:$(FLOWER_PASSWORD)`
    - Env: `FLOWER_PASSWORD` (Secret 참조)

- [x] **T023** [P] Flower Service 작성 ✅
  - 파일: `infra/k8s/celery/flower-service.yaml`
  - 내용:
    - Type: ClusterIP
    - Port: 5555

- [x] **T024** [P] Flower Ingress 작성 ✅
  - 파일: `infra/k8s/celery/flower-ingress.yaml`
  - 내용:
    - Path: `/flower`
    - Annotation: `nginx.ingress.kubernetes.io/whitelist-source-range: "10.0.0.0/8"`
    - Backend: flower-service:5555

### 모니터링 리소스

- [x] **T025** [P] AlertManager Celery 알림 규칙 추가 ✅
  - 파일: `infra/monitoring/alertmanager-celery-rules.yaml`
  - 내용:
    - `CeleryWorkerDown`: Worker Pod down > 5분
    - `CeleryTaskQueueTooLong`: 대기 작업 > 1000개, 10분
    - Slack 알림 설정

---

## Phase 3.4: Integration (배포 및 설정)

- [x] **T026** Backend Deployment 환경 변수 업데이트 ✅
  - 파일: `infra/k8s/backend/deployment.yaml` (기존 파일 수정)
  - 변경:
    - `REDIS_URL` → `REDIS_CACHE_URL=redis://redis-cache-service:6379/0`
    - `CELERY_BROKER_URL=redis://redis-queue-service:6379/0` 추가
    - `CELERY_RESULT_BACKEND=redis://redis-queue-service:6379/1` 추가
  - 의존성: T010-T012 완료 후 (Redis Cache 배포 후)

- [x] **T027** K8s 리소스 배포 (순서 중요) ✅
  1. Secrets 생성 (`kubectl apply -f infra/k8s/scripts/create-secrets.sh`)
  2. Redis Cache 배포 (`kubectl apply -f infra/k8s/redis/cache/`)
  3. Redis Queue 배포 (`kubectl apply -f infra/k8s/redis/queue/`)
  4. Celery Worker/Beat/Flower 배포 (`kubectl apply -f infra/k8s/celery/`)
  5. AlertManager 규칙 배포 (`kubectl apply -f infra/monitoring/alertmanager-celery-rules.yaml`)
  6. Backend Deployment 재시작 (`kubectl rollout restart deployment/backend`)
  - 각 단계마다 Pod 상태 확인 (`kubectl get pods -w`)

- [x] **T028** Backend 애플리케이션 코드 환경 변수 참조 업데이트 ✅
  - 파일: `backend/src/config/settings.py` (또는 유사 파일)
  - 변경:
    - `REDIS_URL` 참조 → `REDIS_CACHE_URL`로 변경
    - Celery 설정에서 `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` 사용 확인
  - 의존성: T003 완료 후

---

## Phase 3.5: Polish (검증 및 문서화)

- [ ] **T029** 통합 테스트 전체 실행 및 검증
  - 실행: `pytest backend/tests/integration/test_redis_*.py backend/tests/integration/test_celery_*.py -v`
  - 확인:
    - T004-T009 모든 테스트 **PASS**
    - Redis Cache/Queue 정상 작동
    - Celery Worker 작업 처리 성공
    - Flower UI 접속 가능
    - 백업 CronJob 실행 성공
  - 의존성: T027 완료 후 (모든 리소스 배포 후)

- [ ] **T030** 마이그레이션 문서 작성 및 docker-compose Redis 중단
  - 파일: `docs/migration/002-redis-celery-k8s.md`
  - 내용:
    - 마이그레이션 전후 비교
    - 환경 변수 변경 사항
    - 롤백 절차
  - 실행: `docker-compose down redis` (기존 Redis 중단)
  - 확인: Backend API가 K8s Redis로만 정상 작동하는지 검증

---

## Dependencies (의존성 그래프)

```
Setup (T001-T003)
  ↓
Tests (T004-T009) [P]  ← 모든 테스트는 병렬 실행 가능
  ↓
K8s YAML 작성 (T010-T025) [P]  ← 대부분 병렬 가능
  ↓
T026 Backend 환경 변수 업데이트
  ↓
T027 K8s 리소스 배포 (순차 실행)
  ↓
T028 Backend 코드 업데이트
  ↓
T029 통합 테스트 검증
  ↓
T030 마이그레이션 완료 및 문서화
```

**주요 차단 관계**:
- T004-T009 (테스트)는 T027 (배포) 완료 후 PASS로 전환
- T010-T025 (YAML 작성)는 독립적이므로 병렬 가능
- T026 (환경 변수)는 T010-T012 (Redis Cache) 완료 필요
- T027 (배포)는 모든 YAML 작성 완료 필요
- T029 (검증)는 T027 (배포) 완료 필요

---

## Parallel Execution Examples

### 예시 1: 테스트 작성 (T004-T009)
```bash
# 6개 테스트 파일을 동시에 작성 (독립적)
claude code "Write Redis Cache health check test in backend/tests/integration/test_redis_cache_health.py" &
claude code "Write Redis Queue health check test in backend/tests/integration/test_redis_queue_health.py" &
claude code "Write Celery Worker task execution test in backend/tests/integration/test_celery_worker.py" &
claude code "Write Celery Beat schedule test in backend/tests/integration/test_celery_beat.py" &
claude code "Write Flower web UI access test in backend/tests/integration/test_flower_ui.py" &
claude code "Write Redis Queue backup CronJob test in backend/tests/integration/test_redis_backup.py" &
wait
```

### 예시 2: Redis K8s YAML 작성 (T010-T013, T014-T018)
```bash
# Redis Cache 리소스 4개 파일 동시 작성
claude code "Write Redis Cache ConfigMap in infra/k8s/redis/cache/configmap.yaml" &
claude code "Write Redis Cache Deployment in infra/k8s/redis/cache/deployment.yaml" &
claude code "Write Redis Cache Service in infra/k8s/redis/cache/service.yaml" &
claude code "Write Redis Cache Exporter in infra/k8s/redis/cache/exporter.yaml" &
wait

# Redis Queue 리소스 5개 파일 동시 작성
claude code "Write Redis Queue ConfigMap in infra/k8s/redis/queue/configmap.yaml" &
claude code "Write Redis Queue StatefulSet in infra/k8s/redis/queue/statefulset.yaml" &
claude code "Write Redis Queue Service in infra/k8s/redis/queue/service.yaml" &
claude code "Write Redis Queue Exporter in infra/k8s/redis/queue/exporter.yaml" &
claude code "Write Redis Queue backup CronJob in infra/k8s/redis/queue/backup-cronjob.yaml" &
wait
```

### 예시 3: Celery K8s YAML 작성 (T019-T024)
```bash
# Celery 리소스 6개 파일 동시 작성
claude code "Write Celery Worker Deployment in infra/k8s/celery/worker-deployment.yaml" &
claude code "Write Celery Worker HPA in infra/k8s/celery/worker-hpa.yaml" &
claude code "Write Celery Beat Deployment in infra/k8s/celery/beat-deployment.yaml" &
claude code "Write Flower Deployment in infra/k8s/celery/flower-deployment.yaml" &
claude code "Write Flower Service in infra/k8s/celery/flower-service.yaml" &
claude code "Write Flower Ingress in infra/k8s/celery/flower-ingress.yaml" &
wait
```

---

## Notes

### TDD 원칙 준수
- **T004-T009** 테스트는 반드시 먼저 작성하고 **FAIL** 확인
- K8s 리소스 배포 (T027) 후 테스트가 **PASS**로 전환되는지 검증

### 병렬 실행 가능 태스크
- **[P]** 표시: 독립적인 파일 작성 → 동시 실행 가능
- K8s YAML 파일은 대부분 독립적이므로 병렬 작성 가능

### 순차 실행 필수 태스크
- **T027** 배포는 순서 중요:
  1. Secrets → 2. Redis Cache → 3. Redis Queue → 4. Celery → 5. Backend 재시작
- **T029** 통합 테스트는 모든 배포 완료 후 실행

### 커밋 전략
- 각 Phase 완료 후 커밋
  - Phase 3.1 완료 → `git commit -m "Setup: K8s 디렉토리 및 Secrets 스크립트"`
  - Phase 3.2 완료 → `git commit -m "Tests: Redis 및 Celery 통합 테스트 (FAIL)"`
  - Phase 3.3 완료 → `git commit -m "K8s YAML: Redis Cache/Queue, Celery 리소스"`
  - Phase 3.4 완료 → `git commit -m "Deployment: K8s 리소스 배포 완료"`
  - Phase 3.5 완료 → `git commit -m "Validation: 통합 테스트 PASS, 마이그레이션 완료"`

---

## Validation Checklist
*GATE: Checked before task execution*

- [x] All contracts have corresponding tests (T004-T009)
- [x] All entities have K8s resources (T010-T024)
- [x] All tests come before implementation (T004-T009 → T010-T025)
- [x] Parallel tasks truly independent (독립 파일)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task

---

## 실행 순서 요약

1. **Setup** (T001-T003): 디렉토리 생성, Secrets 스크립트, 환경 변수 예시
2. **Tests First** (T004-T009): 6개 통합 테스트 작성 (병렬) → 모두 FAIL 확인
3. **Core** (T010-T025): 16개 K8s YAML 작성 (대부분 병렬)
4. **Integration** (T026-T028): 환경 변수 업데이트, 배포, 코드 수정
5. **Polish** (T029-T030): 테스트 PASS 확인, 마이그레이션 완료

**예상 소요 시간**: 4-6시간 (병렬 실행 시)

**최종 목표**: docker-compose Redis 중단 후 K8s Redis/Celery로 완전 이전, 모든 테스트 PASS
