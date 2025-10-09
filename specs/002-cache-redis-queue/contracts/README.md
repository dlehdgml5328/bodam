# Contracts: Redis 분리 배포 및 Celery 운영 환경

**Feature**: 002-cache-redis-queue
**Date**: 2025-10-07

## 개요

이 기능은 **인프라 구성 변경**으로, 기존 애플리케이션 API는 변경되지 않습니다.
대신 **K8s 리소스 계약** (Resource Contracts)을 정의합니다.

---

## 1. K8s 리소스 계약

### 1.1 Redis Cache Service

**서비스 명세**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: redis-cache-service
  namespace: default
spec:
  type: ClusterIP
  ports:
  - port: 6379
    targetPort: 6379
    protocol: TCP
  selector:
    app: redis-cache
```

**접근 방법**:
```python
# Backend에서 접근
import redis
cache_client = redis.from_url(os.getenv("REDIS_CACHE_URL"))  # redis://redis-cache-service:6379/0
```

**계약**:
- 항상 `redis-cache-service:6379`로 접근 가능해야 함
- DB 0번 사용 (세션, 캐시)
- 메모리 부족 시 LRU 정책으로 자동 삭제
- **데이터 손실 허용** (Pod 재시작 시 초기화)

---

### 1.2 Redis Queue Service

**서비스 명세**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: redis-queue-service
  namespace: default
spec:
  type: ClusterIP
  clusterIP: None  # Headless service
  ports:
  - port: 6379
    targetPort: 6379
    protocol: TCP
  selector:
    app: redis-queue
```

**접근 방법**:
```python
# Celery 설정
CELERY_BROKER_URL = "redis://redis-queue-service:6379/0"
CELERY_RESULT_BACKEND = "redis://redis-queue-service:6379/1"
```

**계약**:
- 항상 `redis-queue-service:6379`로 접근 가능해야 함
- DB 0번: Broker (작업 큐)
- DB 1번: Result Backend (작업 결과)
- **데이터 지속성 보장** (PVC 마운트, AOF+RDB)
- Pod 재시작 시 데이터 복구됨

---

## 2. 환경 변수 계약

### 2.1 Backend API 환경 변수

**변경 사항**:
```diff
# 기존 (docker-compose)
- REDIS_URL=redis://redis:6379/0
- CELERY_BROKER_URL=redis://redis:6379/0
- CELERY_RESULT_BACKEND=redis://redis:6379/1

# 신규 (K8s)
+ REDIS_CACHE_URL=redis://redis-cache-service:6379/0
+ CELERY_BROKER_URL=redis://redis-queue-service:6379/0
+ CELERY_RESULT_BACKEND=redis://redis-queue-service:6379/1
```

**계약**:
- `REDIS_CACHE_URL`: 세션, 캐시 저장 (기존 `REDIS_URL` 대체)
- `CELERY_BROKER_URL`: Celery Broker (Queue Redis)
- `CELERY_RESULT_BACKEND`: Celery Result Backend (Queue Redis)

**호환성**:
- 기존 코드에서 `REDIS_URL` 사용하는 부분은 `REDIS_CACHE_URL`로 변경 필요

---

### 2.2 Celery Worker 환경 변수

**필수 환경 변수**:
```bash
CELERY_BROKER_URL=redis://redis-queue-service:6379/0
CELERY_RESULT_BACKEND=redis://redis-queue-service:6379/1
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_MAX_TASKS_PER_CHILD=1000
DATABASE_URL=postgresql+psycopg://bodam:bodam@db:5432/bodam  # DB 작업 시 필요
```

**계약**:
- Worker는 Backend API와 동일한 DB 접근 가능해야 함
- `CELERY_WORKER_CONCURRENCY`: 동시 처리 작업 수 (기본 4)
- `CELERY_WORKER_MAX_TASKS_PER_CHILD`: Worker 재시작 주기 (메모리 릭 방지)

---

### 2.3 Flower 환경 변수

**필수 환경 변수**:
```bash
CELERY_BROKER_URL=redis://redis-queue-service:6379/0
CELERY_RESULT_BACKEND=redis://redis-queue-service:6379/1
FLOWER_BASIC_AUTH=admin:${FLOWER_PASSWORD}  # Secret에서 주입
FLOWER_PORT=5555
FLOWER_URL_PREFIX=/flower
```

**계약**:
- Flower는 Celery Worker와 동일한 Redis 접근 가능해야 함
- Basic Auth 필수 (외부 노출 방지)
- Ingress를 통해 `/flower` 경로로 접근

---

## 3. Celery 작업 계약

### 3.1 작업 큐 라우팅

**큐 정의**:
| 큐 이름 | 우선순위 | 용도 | 예시 작업 |
|--------|---------|------|----------|
| `critical` | 높음 | 결제 처리 | `payments.confirm_pending` |
| `celery` | 중간 | 일반 작업 | `notifications.send_email` |
| `batch` | 낮음 | 크롤링, 분석 | `data_collection.crawl_news` |

**라우팅 규칙**:
```python
CELERY_ROUTES = {
    'payments.*': {'queue': 'critical'},
    'notifications.*': {'queue': 'celery'},
    'data_collection.*': {'queue': 'batch'},
    'ai_analyzer.*': {'queue': 'batch'},
    'ranking.*': {'queue': 'batch'},
}
```

**계약**:
- Worker는 모든 큐를 구독해야 함: `--queues=celery,critical,batch`
- `critical` 큐 작업은 최우선 처리
- `batch` 큐 작업은 리소스 여유 시 처리

---

### 3.2 작업 재시도 계약

**기본 재시도 정책**:
```python
@celery_app.task(
    autoretry_for=(NetworkError, TimeoutError),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,  # 지수 백오프
)
def example_task():
    pass
```

**재시도 간격**:
- 1차 재시도: 60초 후
- 2차 재시도: 120초 후
- 3차 재시도: 240초 후
- 최종 실패 시 Sentry 에러 전송

**계약**:
- 네트워크 오류는 자동 재시도
- 3회 재시도 후 실패 시 Dead Letter Queue로 이동 (수동 처리)
- 모든 재시도는 Flower에서 확인 가능

---

## 4. 모니터링 계약

### 4.1 Prometheus 메트릭

**Redis 메트릭** (redis-exporter):
```
# HELP redis_up Redis instance is up
# TYPE redis_up gauge
redis_up{instance="redis-cache-service"} 1

# HELP redis_memory_used_bytes Memory used by Redis
# TYPE redis_memory_used_bytes gauge
redis_memory_used_bytes{instance="redis-cache-service"} 268435456

# HELP redis_connected_clients Number of connected clients
# TYPE redis_connected_clients gauge
redis_connected_clients{instance="redis-cache-service"} 5
```

**Celery 메트릭** (Custom Exporter):
```
# HELP celery_active_tasks Number of active tasks
# TYPE celery_active_tasks gauge
celery_active_tasks{queue="celery"} 5

# HELP celery_pending_tasks Number of pending tasks
# TYPE celery_pending_tasks gauge
celery_pending_tasks{queue="critical"} 120

# HELP celery_failed_tasks_total Total number of failed tasks
# TYPE celery_failed_tasks_total counter
celery_failed_tasks_total{task="send_email"} 3
```

**계약**:
- 모든 메트릭은 `/metrics` 엔드포인트에서 노출
- Prometheus는 30초마다 스크래핑
- 메트릭 보관 기간: 15일

---

### 4.2 AlertManager 규칙

**Redis 알림**:
```yaml
- alert: RedisDown
  expr: redis_up == 0
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Redis {{ $labels.instance }} is down"

- alert: RedisHighMemoryUsage
  expr: redis_memory_used_bytes / redis_memory_max_bytes * 100 > 90
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Redis {{ $labels.instance }} memory usage above 90%"
```

**Celery 알림**:
```yaml
- alert: CeleryWorkerDown
  expr: up{job="celery-worker"} == 0
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Celery Worker is down"

- alert: CeleryTaskQueueTooLong
  expr: celery_pending_tasks > 1000
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Celery queue {{ $labels.queue }} has {{ $value }} pending tasks"
```

**계약**:
- Critical 알림은 Slack `#alerts-critical` 채널로 전송
- Warning 알림은 Slack `#alerts-warning` 채널로 전송
- 알림 중복 방지: 4시간마다 재전송

---

## 5. Flower API 계약

### 5.1 엔드포인트

**Worker 상태 조회**:
```http
GET /flower/api/workers
Authorization: Basic YWRtaW46cGFzc3dvcmQ=

Response:
{
  "worker1@hostname": {
    "status": "online",
    "active": 2,
    "processed": 1523,
    "failed": 3
  }
}
```

**작업 목록 조회**:
```http
GET /flower/api/tasks
Authorization: Basic YWRtaW46cGFzc3dvcmQ=

Response:
{
  "task-id-123": {
    "name": "payments.confirm_pending",
    "state": "SUCCESS",
    "runtime": 2.5,
    "timestamp": "2025-10-07T10:00:00Z"
  }
}
```

**계약**:
- 모든 API 요청은 Basic Auth 필수
- 응답 형식: JSON
- Rate Limit: 100 req/min (Ingress에서 제한)

---

## 6. 백업 및 복구 계약

### 6.1 백업 계약

**자동 백업**:
- 매일 새벽 2시 Queue Redis RDB 파일 백업
- S3 경로: `s3://bodam-backups/redis/{YYYY-MM-DD}/dump.rdb`
- 백업 보관: 7일 (일일), 4주 (주간)

**백업 검증**:
```bash
# 백업 파일 크기 > 0
aws s3 ls s3://bodam-backups/redis/2025-10-07/dump.rdb
```

**계약**:
- 백업 실패 시 AlertManager 알림 발송
- 백업 파일은 암호화되어 저장 (S3 Server-Side Encryption)

---

### 6.2 복구 계약

**복구 절차**:
1. S3에서 백업 파일 다운로드
   ```bash
   aws s3 cp s3://bodam-backups/redis/2025-10-07/dump.rdb /tmp/dump.rdb
   ```

2. Redis Pod의 PVC에 복사
   ```bash
   kubectl cp /tmp/dump.rdb redis-queue-0:/data/dump.rdb
   ```

3. Redis 재시작
   ```bash
   kubectl delete pod redis-queue-0
   ```

**계약**:
- 복구 시간: 최대 10분 (데이터 크기에 따라)
- 복구 후 데이터 검증: `redis-cli DBSIZE`
- 복구 실패 시 이전 백업 파일로 재시도

---

## 7. 테스트 계약

### 7.1 헬스체크

**Redis Cache 헬스체크**:
```bash
redis-cli -h redis-cache-service -p 6379 PING
# Expected: PONG
```

**Redis Queue 헬스체크**:
```bash
redis-cli -h redis-queue-service -p 6379 PING
# Expected: PONG
```

**Celery Worker 헬스체크**:
```bash
celery -A src.worker.celery_app inspect ping
# Expected: {'worker1@hostname': {'ok': 'pong'}}
```

**Flower 헬스체크**:
```bash
curl -u admin:password https://bodam.example.com/flower/api/workers
# Expected: HTTP 200
```

---

### 7.2 통합 테스트

**시나리오 1: 작업 실행 테스트**
```python
# 작업 추가
result = send_donation_receipt.delay(donation_id=123)

# 결과 확인 (최대 30초 대기)
assert result.get(timeout=30) == "success"
```

**시나리오 2: 작업 재시도 테스트**
```python
# 네트워크 오류 시뮬레이션
with patch('requests.post', side_effect=NetworkError):
    result = send_email.delay(email="test@example.com")

# 재시도 확인
assert result.retries > 0
```

**시나리오 3: 스케줄 작업 테스트**
```python
# Beat 스케줄 확인
from celery.schedules import crontab
assert 'crawl-news-every-30min' in celery_app.conf.beat_schedule
```

---

## 8. 마이그레이션 체크리스트

**배포 전 확인**:
- [ ] K8s 클러스터 리소스 충분 (CPU, 메모리, 스토리지)
- [ ] PersistentVolume 사전 프로비저닝 (5Gi)
- [ ] Secrets 생성 (Flower password, AWS credentials)
- [ ] ConfigMaps 생성 (Redis config, Celery config)

**배포 중 확인**:
- [ ] Redis Cache Pod `Running`
- [ ] Redis Queue Pod `Running` + PVC `Bound`
- [ ] Celery Worker Pod `Running` (최소 2개)
- [ ] Celery Beat Pod `Running` (정확히 1개)
- [ ] Flower Pod `Running`
- [ ] Ingress 설정 완료 (`/flower` 경로)

**배포 후 확인**:
- [ ] Backend API가 Redis Cache에 연결 성공
- [ ] Celery 작업 실행 성공 (Flower에서 확인)
- [ ] Beat 스케줄 작업 실행 확인
- [ ] Prometheus 메트릭 수집 확인
- [ ] AlertManager 알림 테스트

---

## 9. 계약 위반 시 대응

### Redis 계약 위반
| 위반 사항 | 증상 | 대응 |
|----------|------|------|
| Cache Redis 다운 | Backend 세션 오류 | Pod 재시작, 캐시 재구축 |
| Queue Redis 다운 | Celery 작업 실패 | Pod 재시작, RDB 복구 |
| 메모리 부족 (Cache) | LRU 삭제 과다 | 메모리 증설 (512MB → 1GB) |
| 메모리 부족 (Queue) | 작업 추가 실패 | Worker 스케일 아웃, 메모리 증설 |

### Celery 계약 위반
| 위반 사항 | 증상 | 대응 |
|----------|------|------|
| Worker 다운 | 작업 대기 증가 | HPA 동작 확인, 수동 스케일 아웃 |
| Beat 중복 실행 | 작업 2배 실행 | replicas=1 확인, Recreate 전략 확인 |
| 작업 3회 재시도 실패 | DLQ 증가 | Sentry 로그 확인, 수동 재처리 |

### 모니터링 계약 위반
| 위반 사항 | 증상 | 대응 |
|----------|------|------|
| Prometheus 스크래핑 실패 | 메트릭 누락 | ServiceMonitor 확인, exporter 재시작 |
| AlertManager 알림 미발송 | 장애 미탐지 | Slack webhook 확인, AlertManager 재시작 |
| Flower 접근 불가 | 모니터링 불가 | Ingress 확인, Basic Auth 확인 |

---

## 10. 참고 문서

- K8s 리소스 정의: `infra/k8s/redis/`, `infra/k8s/celery/`
- 모니터링 설정: `infra/monitoring/`
- Celery 작업 정의: `backend/src/workers/`
- 환경 변수 예시: `backend/.env.example`
