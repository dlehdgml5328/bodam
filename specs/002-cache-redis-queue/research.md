# Research: Redis 분리 배포 및 Celery K8s 운영

**Date**: 2025-10-07
**Feature**: 002-cache-redis-queue

## 1. K8s에서 Redis 분리 배포 (Cache/Queue)

### 1.1 StatefulSet vs Deployment

**Decision**:
- **Cache Redis**: Deployment 사용
- **Queue Redis**: StatefulSet 사용

**Rationale**:
- Cache는 데이터 손실이 허용되므로 stateless Deployment로 충분
- Queue는 작업 데이터 지속성이 중요하므로 StatefulSet + PersistentVolume 필요
- StatefulSet은 안정적인 네트워크 ID와 스토리지 보장

**Alternatives**:
- 둘 다 StatefulSet: 과도한 리소스 사용, Cache는 stateless로 충분
- 둘 다 Deployment: Queue 데이터 손실 위험

**Trade-offs**:
- StatefulSet은 스케일링이 느림 (순차적 Pod 생성)
- Deployment는 빠른 롤링 업데이트 가능

**References**:
- https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/
- https://redis.io/docs/management/persistence/

---

### 1.2 Redis 백업 정책

**Decision**:
- **Cache Redis**: 백업 없음 (메모리 전용)
- **Queue Redis**: AOF (Append-Only File) + 1시간마다 RDB 스냅샷

**Rationale**:
- AOF는 모든 쓰기 작업 기록 → 데이터 손실 최소화 (최대 1초)
- RDB 스냅샷은 복구 속도 빠름 (대용량 데이터 복구 시)
- 1시간 주기 스냅샷은 성능과 안정성 균형

**Alternatives**:
- RDB만 사용: 마지막 스냅샷 이후 데이터 손실 위험
- AOF만 사용: 복구 시간이 RDB보다 느림

**Configuration**:
```yaml
# Queue Redis AOF 설정
appendonly yes
appendfsync everysec  # 1초마다 fsync
save 3600 1           # 1시간마다 최소 1개 변경 시 스냅샷
```

**Backup Strategy**:
- K8s CronJob으로 매일 새벽 2시 RDB 파일을 S3/MinIO에 백업
- 백업 보관 기간: 7일 (일일 백업), 4주 (주간 백업)

**References**:
- https://redis.io/docs/management/persistence/
- https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/

---

### 1.3 Redis 고가용성

**Decision**: 현재 단계에서는 **단일 인스턴스** 사용 (Sentinel/Cluster 미적용)

**Rationale**:
- 프로젝트 초기 단계, 트래픽 규모가 작음
- Redis Sentinel/Cluster는 최소 3개 노드 필요 → 리소스 부담
- StatefulSet + PersistentVolume으로 Pod 재시작 시 데이터 보존 가능

**Future Upgrade Path**:
- 트래픽 증가 시 Redis Sentinel (고가용성)
- 대용량 데이터 시 Redis Cluster (샤딩)

**Alternatives**:
- Redis Sentinel: 자동 failover, 최소 3개 노드 (1 master + 2 replicas + 3 sentinels)
- Redis Cluster: 샤딩 지원, 최소 6개 노드 (3 master + 3 replicas)

**References**:
- https://redis.io/docs/management/sentinel/
- https://redis.io/docs/management/scaling/

---

### 1.4 Redis 메모리 제한 및 Eviction 정책

**Decision**:
- **Cache Redis**: `maxmemory 512MB`, `maxmemory-policy allkeys-lru`
- **Queue Redis**: `maxmemory 1GB`, `maxmemory-policy noeviction`

**Rationale**:
- Cache는 LRU (Least Recently Used) 정책으로 오래된 캐시 자동 삭제
- Queue는 작업 데이터 손실 방지를 위해 eviction 금지 (메모리 부족 시 알림)
- 메모리 임계치 90% 도달 시 AlertManager가 Slack 알림 발송

**Alternatives**:
- `allkeys-lfu`: 사용 빈도 기반 삭제 (캐시 패턴에 따라 유리할 수 있음)
- `volatile-ttl`: TTL이 짧은 키부터 삭제

**References**:
- https://redis.io/docs/reference/eviction/

---

## 2. Celery Worker/Beat/Flower K8s 배포

### 2.1 Celery Worker Deployment

**Decision**: Deployment + HorizontalPodAutoscaler (HPA)

**Configuration**:
```yaml
# Worker 기본 설정
replicas: 2
concurrency: 4  # 각 Worker당 4개 작업 동시 처리
autoscaling:
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

**Rationale**:
- 2개 인스턴스로 시작 → 장애 시 1개가 계속 작업 처리
- CPU 70% 도달 시 자동 스케일 아웃
- concurrency=4는 I/O 바운드 작업(이메일, API 호출)에 적합

**Task Routing**:
```python
# 작업 타입별 큐 분리
CELERY_ROUTES = {
    'payments.*': {'queue': 'critical'},      # 결제 처리 (높은 우선순위)
    'notifications.*': {'queue': 'default'},  # 알림 발송
    'data_collection.*': {'queue': 'batch'},  # 크롤링 (낮은 우선순위)
}
```

**References**:
- https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/
- https://docs.celeryq.dev/en/stable/userguide/routing.html

---

### 2.2 Celery Beat 단일 인스턴스 보장

**Decision**: Deployment with `replicas: 1` + Leader Election (선택적)

**Rationale**:
- K8s Deployment는 항상 1개 Pod만 실행 보장
- 중복 스케줄링 방지 (Beat가 2개 실행되면 작업이 2번 추가됨)
- Leader Election은 복잡도 증가 → 현재 단계에서는 불필요

**Configuration**:
```yaml
replicas: 1
strategy:
  type: Recreate  # 롤링 업데이트 대신 Recreate (중복 실행 방지)
```

**Future Upgrade**:
- 고가용성 필요 시 `celery-beat-redis` 라이브러리로 분산 락 구현

**References**:
- https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html
- https://github.com/liuliqiang/celery-beat-redis-scheduler

---

### 2.3 Celery Beat 스케줄 관리

**Decision**: Python 코드에 정적 스케줄 정의 + ConfigMap으로 동적 변경 지원

**Static Schedule (코드)**:
```python
# backend/src/worker.py
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'crawl-news-every-30min': {
        'task': 'data_collection.crawl_news',
        'schedule': crontab(minute='*/30'),
    },
    'build-rankings-daily': {
        'task': 'ranking.build_daily',
        'schedule': crontab(hour=2, minute=0),  # 매일 새벽 2시
    },
}
```

**Dynamic Schedule (ConfigMap)**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: celery-beat-schedule
data:
  schedule.json: |
    {
      "send-weekly-report": {
        "task": "notifications.send_weekly_report",
        "schedule": {"crontab": {"day_of_week": "1", "hour": "9", "minute": "0"}}
      }
    }
```

**Rationale**:
- 정적 스케줄은 코드 리뷰 가능, 버전 관리 용이
- ConfigMap 변경 시 Beat Pod 재시작으로 스케줄 업데이트
- DB 기반 동적 스케줄(django-celery-beat)은 복잡도 증가 → 필요 시 추가

**References**:
- https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html

---

### 2.4 Flower 모니터링 및 인증

**Decision**: Deployment + Basic Auth + Ingress 제한

**Configuration**:
```yaml
# Flower 실행 옵션
command:
  - celery
  - -A
  - src.worker.celery_app
  - flower
  - --port=5555
  - --basic_auth=admin:$(FLOWER_PASSWORD)  # Secret에서 주입
  - --url_prefix=/flower  # Ingress path prefix

# Ingress 접근 제한
annotations:
  nginx.ingress.kubernetes.io/whitelist-source-range: "10.0.0.0/8"  # 내부망만 접근
```

**Rationale**:
- Basic Auth로 간단한 인증 구현 (OAuth는 과도)
- Ingress whitelist로 내부 IP만 접근 허용
- Flower는 작업 제어 기능 제공 → 외부 노출 금지

**Alternatives**:
- OAuth2 Proxy: 복잡도 증가, 현재 단계에서 불필요
- VPN 접근만 허용: 운영 편의성 저하

**References**:
- https://flower.readthedocs.io/en/latest/auth.html

---

### 2.5 Celery 작업 재시도 및 Dead Letter Queue

**Decision**: Task-level 재시도 + Sentry 에러 추적

**Configuration**:
```python
@celery_app.task(
    bind=True,
    autoretry_for=(NetworkError, TimeoutError),
    retry_kwargs={'max_retries': 3, 'countdown': 60},  # 3회 재시도, 60초 대기
    retry_backoff=True,  # 지수 백오프 (60초 → 120초 → 240초)
)
def send_donation_receipt(self, donation_id):
    try:
        # 영수증 발송 로직
        pass
    except Exception as exc:
        # Sentry에 에러 전송
        sentry_sdk.capture_exception(exc)
        raise self.retry(exc=exc)
```

**Dead Letter Queue**:
- 3회 재시도 후 실패 → `failed_tasks` 큐로 이동
- Flower에서 수동 재시도 또는 디버깅

**Rationale**:
- 일시적 네트워크 오류는 자동 재시도로 해결
- 영구적 실패는 Sentry 알림 + 수동 처리
- 지수 백오프로 외부 API 과부하 방지

**References**:
- https://docs.celeryq.dev/en/stable/userguide/tasks.html#retrying
- https://docs.sentry.io/platforms/python/integrations/celery/

---

## 3. 모니터링 및 알림

### 3.1 Redis 메트릭 수집

**Decision**: redis-exporter + Prometheus + AlertManager

**현재 상태**:
- `infra/monitoring/redis-exporter.yaml` 이미 존재
- Prometheus ServiceMonitor 설정됨

**추가 작업**:
- Cache/Queue 각각의 redis-exporter 배포
- AlertManager 규칙 확장 (Queue Redis 작업 큐 길이 모니터링)

**Key Metrics**:
- `redis_memory_used_bytes`: 메모리 사용량
- `redis_connected_clients`: 연결 수
- `redis_keyspace_hits_total / redis_keyspace_misses_total`: 캐시 히트율
- `redis_commands_duration_seconds`: 명령 실행 시간

**References**:
- https://github.com/oliver006/redis_exporter

---

### 3.2 Celery 메트릭 수집

**Decision**: Flower API + Custom Exporter

**Implementation**:
```python
# backend/src/monitoring/celery_exporter.py
from prometheus_client import Gauge, Counter
from celery.app.control import Inspect

active_tasks = Gauge('celery_active_tasks', 'Active tasks', ['queue'])
failed_tasks = Counter('celery_failed_tasks', 'Failed tasks', ['task_name'])
task_duration = Histogram('celery_task_duration_seconds', 'Task duration', ['task_name'])

def collect_metrics():
    inspect = Inspect(app=celery_app)
    stats = inspect.stats()
    for worker, data in stats.items():
        active_tasks.labels(queue=worker).set(data['total'])
```

**Flower API**:
- `/api/workers`: Worker 상태
- `/api/tasks`: 작업 목록
- Prometheus가 15초마다 Flower API 스크래핑

**References**:
- https://flower.readthedocs.io/en/latest/api.html
- https://prometheus.io/docs/instrumenting/exporters/

---

### 3.3 알림 규칙

**Decision**: AlertManager Slack 알림 (이미 구현됨)

**추가 알림 규칙**:
```yaml
# Queue Redis 작업 대기 시간 초과
- alert: CeleryTaskQueueTooLong
  expr: redis_list_length{instance="redis-queue"} > 1000
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Celery 작업 큐가 1000개 이상 쌓임"
    description: "Worker 스케일링 필요"

# Worker 다운
- alert: CeleryWorkerDown
  expr: up{job="celery-worker"} == 0
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Celery Worker가 다운됨"
```

**References**:
- `infra/monitoring/slack-alerts.yaml` 참고

---

## 4. 구현 결정 요약

| 항목 | 결정 사항 | 상태 |
|-----|----------|-----|
| Cache Redis | Deployment, 메모리 전용, LRU eviction | 신규 구현 필요 |
| Queue Redis | StatefulSet, AOF+RDB, noeviction | 신규 구현 필요 |
| Redis 백업 | CronJob으로 일일 RDB 백업 (7일 보관) | 신규 구현 필요 |
| Celery Worker | Deployment, HPA (2-10 replicas) | 신규 구현 필요 |
| Celery Beat | Deployment (replicas=1), Recreate 전략 | 신규 구현 필요 |
| Celery 스케줄 | 정적 (코드) + ConfigMap (동적) | 신규 구현 필요 |
| Flower | Deployment, Basic Auth, Ingress 제한 | 신규 구현 필요 |
| Redis 모니터링 | redis-exporter (이미 있음) | 확장 필요 (2개 인스턴스) |
| Celery 모니터링 | Flower API + Custom Exporter | 신규 구현 필요 |
| 알림 | AlertManager + Slack (이미 있음) | 규칙 추가 필요 |

---

## 5. 명확화된 요구사항

### FR-005: Redis 백업 정책
- **RDB 스냅샷**: 1시간마다 (Queue Redis만)
- **AOF**: everysec (1초마다 fsync)
- **백업 보관**: 7일 (일일), 4주 (주간)
- **복구 절차**: PVC 마운트 → RDB/AOF 파일 복사 → Redis 재시작

### FR-014: Beat 동적 스케줄 관리
- **정적 스케줄**: Python 코드에 정의 (버전 관리)
- **동적 스케줄**: ConfigMap → Beat Pod 재시작으로 적용
- **제한사항**: DB 기반 동적 스케줄은 1차 범위 외 (필요 시 추가)

### FR-021: Worker 오토스케일링 정책
- **최소 replicas**: 2
- **최대 replicas**: 10
- **스케일 아웃 조건**: CPU 70% 이상, 5분 지속
- **스케일 인 조건**: CPU 50% 이하, 10분 지속
- **쿨다운**: 3분 (스케일 아웃), 5분 (스케일 인)

---

## 6. Out of Scope (향후 고려)

- Redis Sentinel/Cluster (고가용성)
- Celery Beat 분산 락 (Leader Election)
- DB 기반 동적 스케줄 (django-celery-beat)
- Celery Canvas (복잡한 워크플로우)
- Multi-tenancy (큐/Worker 분리)
