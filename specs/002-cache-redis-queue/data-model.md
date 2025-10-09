# Data Model: Redis 분리 배포 및 Celery 운영 환경

**Feature**: 002-cache-redis-queue
**Date**: 2025-10-07

## 개요

이 기능은 인프라 구성 변경으로 애플리케이션 데이터 모델 변경은 없습니다.
대신 **운영 엔티티** (인프라 리소스)를 정의합니다.

---

## 1. Redis 인스턴스 (운영 엔티티)

### 1.1 Cache Redis Instance

**목적**: 세션, API 응답 캐시, 인증 토큰 등 임시 데이터 저장

**속성**:
| 속성 | 타입 | 설명 | 기본값 |
|-----|------|------|--------|
| namespace | string | K8s 네임스페이스 | `default` |
| service_name | string | K8s Service 이름 | `redis-cache` |
| port | int | 서비스 포트 | `6379` |
| maxmemory | string | 최대 메모리 | `512MB` |
| maxmemory_policy | string | 메모리 정책 | `allkeys-lru` |
| persistence | boolean | 데이터 지속성 | `false` |

**K8s 리소스**:
- Deployment: `redis-cache` (replicas: 1)
- Service: `redis-cache-service`
- ConfigMap: `redis-cache-config`

**환경 변수**:
```bash
REDIS_CACHE_URL=redis://redis-cache-service:6379/0
```

---

### 1.2 Queue Redis Instance

**목적**: Celery Broker 및 Result Backend

**속성**:
| 속성 | 타입 | 설명 | 기본값 |
|-----|------|------|--------|
| namespace | string | K8s 네임스페이스 | `default` |
| service_name | string | K8s Service 이름 | `redis-queue` |
| port | int | 서비스 포트 | `6379` |
| maxmemory | string | 최대 메모리 | `1GB` |
| maxmemory_policy | string | 메모리 정책 | `noeviction` |
| persistence | object | 지속성 설정 | (아래 참조) |
| persistence.aof | boolean | AOF 활성화 | `true` |
| persistence.appendfsync | string | AOF fsync 주기 | `everysec` |
| persistence.rdb_enabled | boolean | RDB 활성화 | `true` |
| persistence.save | string | RDB 저장 조건 | `3600 1` (1시간마다) |

**K8s 리소스**:
- StatefulSet: `redis-queue` (replicas: 1)
- Service: `redis-queue-service` (Headless)
- PersistentVolumeClaim: `redis-queue-data-redis-queue-0` (5Gi)
- ConfigMap: `redis-queue-config`

**환경 변수**:
```bash
CELERY_BROKER_URL=redis://redis-queue-service:6379/0
CELERY_RESULT_BACKEND=redis://redis-queue-service:6379/1
```

**데이터 구조** (Redis 내부):
```
# Broker (DB 0)
celery (list): 기본 큐
critical (list): 결제 처리 큐
batch (list): 크롤링 큐

# Result Backend (DB 1)
celery-task-meta-{task_id} (hash): 작업 결과
```

---

## 2. Celery 컴포넌트 (운영 엔티티)

### 2.1 Celery Worker

**목적**: 비동기 작업 실행

**속성**:
| 속성 | 타입 | 설명 | 기본값 |
|-----|------|------|--------|
| namespace | string | K8s 네임스페이스 | `default` |
| deployment_name | string | Deployment 이름 | `celery-worker` |
| replicas | int | 초기 replica 수 | `2` |
| concurrency | int | 동시 처리 작업 수 | `4` |
| queues | list[string] | 구독 큐 목록 | `["celery", "critical", "batch"]` |
| max_tasks_per_child | int | Worker 재시작 주기 | `1000` |

**HPA (Horizontal Pod Autoscaler)**:
| 속성 | 값 |
|-----|-----|
| minReplicas | 2 |
| maxReplicas | 10 |
| targetCPUUtilizationPercentage | 70 |
| scaleUp.stabilizationWindowSeconds | 180 (3분) |
| scaleDown.stabilizationWindowSeconds | 300 (5분) |

**환경 변수**:
```bash
CELERY_BROKER_URL=redis://redis-queue-service:6379/0
CELERY_RESULT_BACKEND=redis://redis-queue-service:6379/1
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_MAX_TASKS_PER_CHILD=1000
```

**작업 라우팅**:
```python
CELERY_ROUTES = {
    'payments.confirm_pending': {'queue': 'critical'},
    'payments.issue_receipts': {'queue': 'critical'},
    'notifications.send_email': {'queue': 'celery'},
    'data_collection.crawl_news': {'queue': 'batch'},
    'ai_analyzer.analyze': {'queue': 'batch'},
}
```

---

### 2.2 Celery Beat

**목적**: 주기적 작업 스케줄링

**속성**:
| 속성 | 타입 | 설명 | 기본값 |
|-----|------|------|--------|
| namespace | string | K8s 네임스페이스 | `default` |
| deployment_name | string | Deployment 이름 | `celery-beat` |
| replicas | int | replica 수 (고정) | `1` |
| strategy | string | 배포 전략 | `Recreate` |

**스케줄** (코드 정의):
```python
CELERY_BEAT_SCHEDULE = {
    'crawl-news-every-30min': {
        'task': 'data_collection.crawl_news',
        'schedule': crontab(minute='*/30'),
    },
    'build-rankings-daily': {
        'task': 'ranking.build_daily',
        'schedule': crontab(hour=2, minute=0),
    },
    'send-weekly-report': {
        'task': 'notifications.send_weekly_report',
        'schedule': crontab(day_of_week=1, hour=9, minute=0),
    },
}
```

**ConfigMap 동적 스케줄** (선택적):
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: celery-beat-schedule
data:
  schedule.json: |
    {
      "custom-task": {
        "task": "custom.task_name",
        "schedule": {"crontab": {"minute": "*/15"}}
      }
    }
```

---

### 2.3 Flower

**목적**: Celery 모니터링 대시보드

**속성**:
| 속성 | 타입 | 설명 | 기본값 |
|-----|------|------|--------|
| namespace | string | K8s 네임스페이스 | `default` |
| deployment_name | string | Deployment 이름 | `flower` |
| replicas | int | replica 수 | `1` |
| port | int | 서비스 포트 | `5555` |
| url_prefix | string | URL 경로 | `/flower` |
| basic_auth_enabled | boolean | Basic Auth 활성화 | `true` |

**인증**:
- Basic Auth: `admin:{FLOWER_PASSWORD}` (Secret에서 주입)
- Ingress whitelist: 내부 IP만 허용 (`10.0.0.0/8`)

**접근 URL**:
```
https://bodam.example.com/flower
```

**K8s 리소스**:
- Deployment: `flower`
- Service: `flower-service`
- Ingress: `flower-ingress`
- Secret: `flower-auth` (password 저장)

---

## 3. 모니터링 리소스

### 3.1 Redis Exporter

**Cache Redis Exporter**:
| 속성 | 값 |
|-----|-----|
| deployment_name | `redis-cache-exporter` |
| target | `redis-cache-service:6379` |
| metrics_port | `9121` |

**Queue Redis Exporter**:
| 속성 | 값 |
|-----|-----|
| deployment_name | `redis-queue-exporter` |
| target | `redis-queue-service:6379` |
| metrics_port | `9121` |

**메트릭**:
- `redis_memory_used_bytes`
- `redis_connected_clients`
- `redis_keyspace_hits_total`
- `redis_keyspace_misses_total`
- `redis_commands_duration_seconds_total`

---

### 3.2 Celery Exporter (Custom)

**목적**: Celery 작업 메트릭을 Prometheus로 노출

**메트릭**:
```python
celery_active_tasks{queue="celery"} 5          # 활성 작업 수
celery_pending_tasks{queue="critical"} 120     # 대기 작업 수
celery_failed_tasks_total{task="send_email"} 3 # 실패 작업 수 (Counter)
celery_task_duration_seconds{task="crawl_news"} 12.5  # 작업 실행 시간
celery_worker_status{worker="worker1@hostname"} 1    # Worker 상태 (1=up, 0=down)
```

---

## 4. 백업 리소스

### 4.1 Redis Backup CronJob

**목적**: Queue Redis RDB 파일 일일 백업

**속성**:
| 속성 | 타입 | 설명 | 기본값 |
|-----|------|------|--------|
| cronjob_name | string | CronJob 이름 | `redis-queue-backup` |
| schedule | string | cron 표현식 | `0 2 * * *` (매일 새벽 2시) |
| backup_retention | int | 백업 보관 일수 | `7` |
| backup_storage | string | 백업 저장소 | `s3://bodam-backups/redis/` |

**동작**:
1. Redis `BGSAVE` 명령 실행 (RDB 스냅샷 생성)
2. `/data/dump.rdb` 파일을 S3에 업로드
3. 7일 이상 된 백업 파일 삭제

**K8s 리소스**:
- CronJob: `redis-queue-backup`
- ServiceAccount: `redis-backup-sa` (S3 접근 권한)
- Secret: `aws-credentials` (S3 인증)

---

## 5. 데이터 흐름도

```
[사용자] → [Backend API] → [Redis Cache] (세션, 캐시)
                ↓
           [Celery Task 생성]
                ↓
           [Redis Queue (Broker)]
                ↓
           [Celery Worker] → [작업 실행]
                ↓
           [Redis Queue (Result Backend)]
                ↓
           [Flower] ← [개발자/운영자]
```

---

## 6. 상태 전이 다이어그램

### Celery 작업 상태
```
PENDING → STARTED → SUCCESS
                 ↓
               RETRY → SUCCESS
                 ↓
               FAILURE
```

**상태 설명**:
- `PENDING`: 큐에 추가됨
- `STARTED`: Worker가 작업 시작
- `RETRY`: 재시도 중
- `SUCCESS`: 성공
- `FAILURE`: 최종 실패 (Dead Letter Queue로 이동)

---

## 7. 검증 규칙

### Redis 설정 검증
- Cache Redis `maxmemory_policy`는 `allkeys-lru` 또는 `allkeys-lfu`여야 함
- Queue Redis `maxmemory_policy`는 `noeviction`이어야 함
- Queue Redis AOF가 활성화되어 있어야 함

### Celery 설정 검증
- Worker `concurrency`는 1 이상이어야 함
- Beat `replicas`는 항상 1이어야 함 (중복 스케줄링 방지)
- HPA `minReplicas`는 1 이상이어야 함

### 모니터링 검증
- 모든 Redis 인스턴스는 redis-exporter가 배포되어야 함
- Prometheus ServiceMonitor가 정의되어야 함
- AlertManager 규칙이 설정되어야 함

---

## 8. 마이그레이션 계획

### 현재 → 목표 아키텍처

**현재 상태**:
```
docker-compose:
  - redis:6379 (단일 인스턴스, DB 0=Broker, DB 1=Result)
  - celery-worker (profile로 분리)
```

**목표 상태**:
```
K8s:
  - redis-cache (Deployment)
  - redis-queue (StatefulSet + PVC)
  - celery-worker (Deployment + HPA)
  - celery-beat (Deployment, replicas=1)
  - flower (Deployment + Ingress)
```

### 마이그레이션 단계
1. K8s에 redis-cache, redis-queue 배포
2. Backend 환경 변수 업데이트 (`REDIS_URL` → `REDIS_CACHE_URL`, `CELERY_BROKER_URL`)
3. Celery Worker/Beat/Flower K8s 배포
4. docker-compose redis 중단
5. 모니터링 확인 (Prometheus, Flower)

---

## 9. 참고 사항

- 이 문서는 인프라 리소스를 정의하므로 애플리케이션 코드 변경은 최소화됩니다.
- 환경 변수만 업데이트하면 기존 Celery 작업 코드는 그대로 동작합니다.
- K8s YAML 파일은 `infra/k8s/redis/`, `infra/k8s/celery/` 디렉토리에 작성됩니다.
