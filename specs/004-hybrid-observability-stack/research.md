# Research 문서: 하이브리드 관측성 스택

**Feature**: 004-hybrid-observability-stack
**Date**: 2025-10-16
**Status**: Complete

## 실행 요약

이 문서는 Prometheus, Loki, Tempo를 로컬 Kubernetes에 배포하고 Grafana Cloud로 Remote Write하는 하이브리드 관측성 스택 구현을 위한 기술 연구 결과입니다. 모든 NEEDS CLARIFICATION이 해결되었으며, 구현 가능한 수준으로 상세화되었습니다.

---

## 1. Prometheus 메트릭 수집 전략

### Decision: Phase 1 (MVP) - 14개 핵심 메트릭

**선택된 메트릭**:

#### A. FastAPI Backend (6개)
```python
# 1. HTTP 요청 총 수 (RED: Rate, Errors)
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']  # status: 2xx, 4xx, 5xx
)

# 2. HTTP 요청 지연시간 (RED: Duration)
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0]  # 7 buckets (효율적)
)

# 3. 동시 HTTP 요청 수 (USE: Saturation)
http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently in progress',
    ['method', 'endpoint']
)

# 4. DB 커넥션 풀 활성 커넥션 (USE: Saturation)
db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections'
)

# 5. HTTP 클라이언트 커넥션 풀 활성 (USE: Saturation)
http_client_active_connections = Gauge(
    'http_client_active_connections',
    'Active HTTP client connections',
    ['host']  # Gemini API, 외부 서비스별
)

# 6. HTTP 클라이언트 대기 요청 수 (병목 최우선 지표!)
http_client_waiting_requests = Gauge(
    'http_client_waiting_requests',
    'Requests waiting for HTTP connection from pool',
    ['host']
)
```

**상태 코드 그룹화 전략**:
```python
# ✅ 추천: 3-tier 그룹화 (2xx, 4xx, 5xx)
def get_status_group(status_code: int) -> str:
    if 200 <= status_code < 300:
        return "2xx"  # 성공
    elif 400 <= status_code < 500:
        return "4xx"  # 클라이언트 에러 (패턴 관찰용)
    else:  # 500-599
        return "5xx"  # 서버 에러 (최우선 알람!)

# Series 수: 10 endpoints × 5 methods × 3 status = 150 series
```

**알람 우선순위**:
```promql
# 1. 5XX 즉시 알람 (최우선)
rate(http_requests_total{status="5xx"}[1m]) > 0

# 2. 4XX 패턴 관찰 (30% 이상 시 경고)
rate(http_requests_total{status="4xx"}[5m])
/
rate(http_requests_total[5m])
> 0.3

# 3. HTTP 커넥션 풀 고갈 (즉시 알람)
http_client_waiting_requests > 0
```

#### B. Celery Worker (1개)
```python
# 큐 길이 (작업 적체 감지)
celery_queue_length = Gauge(
    'celery_queue_length',
    'Tasks waiting in Celery queue',
    ['queue_name']
)
```

**Phase 2 추가 예정**:
- `celery_tasks_total`: 작업 성공률 (Selenium 크롤링 빈도 증가 후)
- `celery_task_duration_seconds`: 작업 소요 시간

#### C. Kong Gateway (2개)
```python
# Kong 기본 메트릭 (공식 Prometheus 플러그인)
kong_http_status  # HTTP 상태 코드별 요청 수
kong_latency_seconds  # Kong 처리 지연시간
```

#### D. Kubernetes (3개)
```yaml
# kube-state-metrics 자동 수집
kube_pod_container_resource_usage_cpu_cores       # HPA 트리거
kube_pod_container_resource_usage_memory_bytes    # OOM 예방
kube_deployment_status_replicas_available         # Pod 가용성
```

#### E. Bodam 커스텀 메트릭 (2개)
```python
# FR-004: 비즈니스 메트릭
bodam_donations_total = Counter(
    'bodam_donations_total',
    'Total donations',
    ['fire_station_id', 'status']  # status: pending, completed, failed
)

bodam_crawler_success_rate = Gauge(
    'bodam_crawler_success_rate',
    'Crawler job success rate',
    ['source']  # 연합뉴스, KBS 등
)
```

### Rationale

1. **Grafana Cloud Free Tier 효율**:
   - 예상 Series: ~2,500 (10K 중 25%)
   - 75% 여유 확보 → Phase 2 확장 가능

2. **Llama 쿼리 성능**:
   - 6개 데이터소스 (Prometheus 엔드포인트)
   - 쿼리 시간: < 0.5초 (NFR-001 만족)

3. **4 Golden Signals 커버**:
   - Latency: `http_request_duration_seconds`
   - Traffic: `http_requests_total`
   - Errors: `http_requests_total{status="5xx"}`
   - Saturation: `http_requests_in_progress`, `http_client_waiting_requests`

4. **HTTP 커넥션 풀 최우선**:
   - Gemini API 등 외부 서비스 호출 병목 조기 감지
   - `http_client_waiting_requests > 0` = 즉시 알람 필요

### Alternatives Considered

**대안 1: 모든 상태 코드 개별 측정** (❌ 거부)
- 200, 201, 400, 401, 404, 500, 503 등 개별 레이블
- Series 폭발: ~1,000 series
- Grafana Cloud 제한 압박

**대안 2: 2-tier 그룹화 (success, error)** (❌ 거부)
- `status="success"` (2XX)
- `status="error"` (4XX + 5XX 통합)
- 4XX와 5XX 구분 불가 → 알람 정확도 하락

**대안 3: 4-tier 그룹화 (2xx, 4xx, 5xx, 중요 코드)** (⚠️ Phase 2 고려)
- 기본: 2xx, 4xx, 5xx
- 추가: 401, 429, 500, 503 개별 측정
- Series: ~300 (수용 가능)
- 현재는 과잉, 트래픽 증가 후 재평가

---

## 2. Prometheus + Grafana Cloud Remote Write

### Decision: Local TSDB (3일) + Remote Write (14일)

**Prometheus 설정**:
```yaml
# infra/k8s/observability/prometheus/configmap.yaml
global:
  scrape_interval: 15s      # 기본 스크래핑 주기
  evaluation_interval: 15s  # 알람 룰 평가 주기

storage:
  tsdb:
    retention.time: 3d      # 로컬 보관 3일 (Llama 쿼리용)
    retention.size: 5GB     # 디스크 제한

remote_write:
  - url: https://prometheus-prod-01-eu-west-0.grafana.net/api/prom/push
    basic_auth:
      username: ${GRAFANA_CLOUD_INSTANCE_ID}
      password: ${GRAFANA_CLOUD_API_KEY}

    # 메트릭 필터링 (불필요한 것 제외)
    write_relabel_configs:
      # Go runtime 메트릭 제외 (Grafana Cloud 절약)
      - source_labels: [__name__]
        regex: 'go_.*|process_.*'
        action: drop

      # High-cardinality 레이블 제거
      - source_labels: [instance]
        action: labeldrop

    # 재전송 설정 (네트워크 장애 대비)
    queue_config:
      capacity: 10000
      max_shards: 10
      min_shards: 1
      max_samples_per_send: 1000
      batch_send_deadline: 5s
      min_backoff: 30ms
      max_backoff: 100ms

scrape_configs:
  # Backend (FastAPI)
  - job_name: 'backend'
    scrape_interval: 15s
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        regex: backend
        action: keep
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: pod
      - source_labels: [__address__]
        regex: '([^:]+):.*'
        target_label: __address__
        replacement: '${1}:8080'  # /metrics 엔드포인트

  # Kong Gateway
  - job_name: 'kong'
    scrape_interval: 15s
    static_configs:
      - targets: ['kong:8001']  # Kong Admin API

  # Kubernetes (kube-state-metrics)
  - job_name: 'kubernetes'
    scrape_interval: 30s  # 인프라 메트릭은 덜 빈번하게
    static_configs:
      - targets: ['kube-state-metrics:8080']

  # Celery (저빈도)
  - job_name: 'celery'
    scrape_interval: 60s  # Selenium Job은 드물게 실행
    static_configs:
      - targets: ['celery-exporter:9808']
```

**PersistentVolume 설정**:
```yaml
# infra/k8s/observability/prometheus/pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: prometheus-storage
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10GB  # 3일 retention + 여유
```

### Rationale

1. **로컬 3일 retention**:
   - Llama 쿼리 대상 (FR-014: < 1초 응답)
   - 최근 데이터는 로컬이 훨씬 빠름 (네트워크 레이턴시 없음)

2. **Grafana Cloud 14일**:
   - 장기 분석 (과거 인시던트 조사)
   - 비용 $0 (Free Tier)
   - 네트워크 장애 시 로컬 버퍼링 → 복구 후 재전송

3. **Scrape Interval 차별화**:
   - Backend 15s: 고빈도 메트릭 (HTTP 요청)
   - Celery 60s: 저빈도 작업 (리소스 절약)

### Alternatives Considered

**대안 1: Grafana Agent 사용** (⚠️ Phase 3 고려)
- Prometheus + Loki + Tempo를 하나의 Agent로 통합
- 장점: 메모리 절약 (~100MB)
- 단점: 로컬 쿼리 불가 (Llama가 Agent 쿼리 불가)
- 결론: 현재는 Prometheus 독립 배포 (Llama 요구사항 우선)

**대안 2: Prometheus Operator** (❌ 거부)
- Kubernetes CRD 기반 자동화
- 장점: 선언적 관리
- 단점: 복잡도 증가 (학습 곡선)
- 결론: Raw Manifests로 충분 (Pod 9개 정도)

---

## 3. Loki + Promtail 로그 수집

### Decision: Loki (로컬 3일) + Promtail DaemonSet + Remote Write

**Loki 설정**:
```yaml
# infra/k8s/observability/loki/configmap.yaml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
  chunk_idle_period: 5m
  chunk_retain_period: 30s

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h  # 7일 이전 로그 거부
  ingestion_rate_mb: 10             # 10MB/s (충분)
  ingestion_burst_size_mb: 20

schema_config:
  configs:
    - from: 2024-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/index
    cache_location: /loki/cache
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

chunk_store_config:
  max_look_back_period: 72h  # 로컬 3일

table_manager:
  retention_deletes_enabled: true
  retention_period: 72h  # 3일 자동 삭제

# Grafana Cloud Remote Write
ruler:
  storage:
    type: local
  rule_path: /loki/rules
  alertmanager_url: http://alertmanager:9093
  ring:
    kvstore:
      store: inmemory

# Remote Write 설정 (Loki는 별도 설정 필요)
# backend에서 Loki HTTP API로 직접 전송 or Promtail → Grafana Cloud
```

**Promtail DaemonSet 설정**:
```yaml
# infra/k8s/observability/promtail/configmap.yaml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  # 로컬 Loki
  - url: http://loki:3100/loki/api/v1/push
    batchwait: 1s
    batchsize: 102400

  # Grafana Cloud (Remote Write)
  - url: https://logs-prod-eu-west-0.grafana.net/loki/api/v1/push
    basic_auth:
      username: ${GRAFANA_CLOUD_INSTANCE_ID}
      password: ${GRAFANA_CLOUD_API_KEY}
    batchwait: 1s
    batchsize: 102400

scrape_configs:
  # Kubernetes Pods 로그 수집
  - job_name: kubernetes-pods
    kubernetes_sd_configs:
      - role: pod

    relabel_configs:
      # Pod 메타데이터 추출
      - source_labels: [__meta_kubernetes_pod_label_app]
        target_label: app
      - source_labels: [__meta_kubernetes_namespace]
        target_label: namespace
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: pod
      - source_labels: [__meta_kubernetes_pod_container_name]
        target_label: container

    pipeline_stages:
      # JSON 로그 파싱 (FastAPI structured logging)
      - json:
          expressions:
            timestamp: timestamp
            level: level
            message: message
            trace_id: trace_id  # OpenTelemetry 연동

      # 타임스탬프 추출
      - timestamp:
          source: timestamp
          format: RFC3339

      # 레이블 추가
      - labels:
          level:
          trace_id:

      # 불필요한 로그 필터링
      - match:
          selector: '{level="debug"}'
          action: drop  # DEBUG 로그는 로컬만 (Grafana Cloud 절약)
```

**Promtail DaemonSet**:
```yaml
# infra/k8s/observability/promtail/daemonset.yaml
apiVersion: apps/v1
kind: DaemonSet  # 각 노드마다 1개
metadata:
  name: promtail
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
        image: grafana/promtail:2.9.0
        args:
          - -config.file=/etc/promtail/promtail.yaml
        volumeMounts:
          - name: config
            mountPath: /etc/promtail
          - name: varlog
            mountPath: /var/log
            readOnly: true
          - name: varlibdockercontainers
            mountPath: /var/lib/docker/containers
            readOnly: true
        resources:
          limits:
            memory: 128Mi
            cpu: 100m
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

### Rationale

1. **DaemonSet 패턴**:
   - 각 Worker Node마다 Promtail 1개 실행
   - Node의 `/var/log` 마운트하여 모든 Pod 로그 수집
   - Resource: 50-100MB per node (경량)

2. **Pipeline Stages**:
   - JSON 파싱: FastAPI structured logging (structlog)
   - Trace ID 추출: OpenTelemetry context propagation
   - DEBUG 로그 필터링: Grafana Cloud 용량 절약

3. **Dual Write**:
   - 로컬 Loki: Llama 쿼리용 (< 1초)
   - Grafana Cloud: 장기 보관 (14일)

### Alternatives Considered

**대안 1: Fluentd** (❌ 거부)
- 범용 로그 수집기
- 장점: 플러그인 생태계
- 단점: 무겁고 (200MB+), Loki 특화 아님
- 결론: Promtail이 Loki 최적화

**대안 2: Vector** (⚠️ Phase 3 고려)
- Rust 기반 고성능 로그 라우터
- 장점: 매우 빠르고 메모리 효율적
- 단점: 설정 복잡
- 결론: 현재는 Promtail로 충분

---

## 4. Tempo 분산 트레이싱

### Decision: OpenTelemetry SDK + Tempo (로컬 2일) + Remote Write

**OpenTelemetry FastAPI Instrumentation**:
```python
# backend/src/main.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

# TracerProvider 설정
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# OTLP Exporter → Tempo
otlp_exporter = OTLPSpanExporter(
    endpoint="http://tempo:4317",  # gRPC
    insecure=True
)

# Batch Processor (비동기 전송, 성능 최적화)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(otlp_exporter)
)

# FastAPI Auto-Instrumentation
app = FastAPI()
FastAPIInstrumentor.instrument_app(app)

# SQLAlchemy Auto-Instrumentation (DB 쿼리 추적)
SQLAlchemyInstrumentor().instrument(engine=engine)

# HTTPX Auto-Instrumentation (외부 API 호출 추적)
HTTPXClientInstrumentor().instrument()

# Custom Span 예시
@app.get("/api/donations")
async def get_donations():
    with tracer.start_as_current_span("fetch_donations"):
        # 비즈니스 로직
        donations = await db.query(Donation).all()

        # Span에 속성 추가
        span = trace.get_current_span()
        span.set_attribute("donations.count", len(donations))

        return donations
```

**Tempo 설정**:
```yaml
# infra/k8s/observability/tempo/configmap.yaml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317  # OpenTelemetry gRPC
        http:
          endpoint: 0.0.0.0:4318  # OpenTelemetry HTTP

ingester:
  trace_idle_period: 10s
  max_block_bytes: 1048576
  max_block_duration: 5m

compactor:
  compaction:
    block_retention: 48h  # 로컬 2일

storage:
  trace:
    backend: local
    local:
      path: /var/tempo/traces
    wal:
      path: /var/tempo/wal

# Grafana Cloud Remote Write (별도 설정 필요)
# Tempo는 직접 remote write 미지원 → Grafana Agent 필요
# Phase 1에서는 로컬만 사용, Phase 2에서 Grafana Agent 추가 고려
```

**Tempo PVC**:
```yaml
# infra/k8s/observability/tempo/pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: tempo-storage
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5GB  # 2일 retention + 여유
```

**Kong Gateway Tracing Plugin** (선택):
```yaml
# Kong에서 trace context 전파
plugins:
  - name: opentelemetry
    config:
      endpoint: "http://tempo:4318/v1/traces"
      resource_attributes:
        service.name: "kong-gateway"
```

### Rationale

1. **OpenTelemetry 표준**:
   - Vendor-neutral (Tempo 외에도 Jaeger, Zipkin 지원)
   - Auto-Instrumentation (FastAPI, SQLAlchemy, HTTPX)
   - W3C Trace Context 표준 (Kong, NGINX 연동 가능)

2. **로컬 2일 retention**:
   - Trace는 메트릭/로그보다 용량 큼
   - 최근 이슈 디버깅에 2일이면 충분 (NFR-001)

3. **Sampling Strategy** (Phase 2):
   ```python
   # 평상시: 100% 수집 (트래픽 적음)
   # 트래픽 증가 시: 10-30% 샘플링
   from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

   tracer_provider = TracerProvider(
       sampler=TraceIdRatioBased(0.1)  # 10% 샘플링
   )
   ```

### Alternatives Considered

**대안 1: Jaeger** (❌ 거부)
- 검증된 tracing 솔루션
- 단점: UI 포함 (Grafana와 중복), 더 무거움
- 결론: Tempo가 Grafana 생태계에 최적화

**대안 2: Zipkin** (❌ 거부)
- 오래된 표준
- 단점: OpenTelemetry 네이티브 아님
- 결론: OpenTelemetry → Tempo가 최신 베스트 프랙티스

---

## 5. K6 부하 테스트 + Prometheus 통합

### Decision: K6 statsd output → Prometheus statsd-exporter

**K6 시나리오**:
```javascript
// tests/load/scenarios/moderate-200vu.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';

// 커스텀 메트릭 정의
let errorCounter = new Counter('k6_errors');
let requestDuration = new Trend('k6_request_duration');

export let options = {
  stages: [
    { duration: '1m', target: 50 },   // Warm-up
    { duration: '3m', target: 200 },  // Peak load
    { duration: '1m', target: 0 },    // Ramp-down
  ],

  thresholds: {
    'http_req_duration': ['p(95)<500'],  // p95 < 500ms (spec.md 성공 기준)
    'http_req_failed': ['rate<0.01'],    // 에러율 < 1%
  },

  // Prometheus로 실시간 전송
  ext: {
    loadimpact: {
      projectID: 0,  # 로컬 실행
      name: "Bodam Load Test - 200 VU"
    }
  }
};

export default function () {
  // 1. 기부 목록 조회
  let res1 = http.get('http://backend/api/donations');
  check(res1, {
    'donations status 200': (r) => r.status === 200,
    'donations response time < 500ms': (r) => r.timings.duration < 500,
  });
  requestDuration.add(res1.timings.duration);

  // 2. 소방서 검색
  let res2 = http.get('http://backend/api/fire-stations?lat=37.5665&lng=126.9780');
  check(res2, {
    'fire-stations status 200': (r) => r.status === 200,
  });

  // 3. 기부 생성 (POST)
  let payload = JSON.stringify({
    fire_station_id: 1,
    amount: 5000,
  });
  let res3 = http.post('http://backend/api/donations', payload, {
    headers: { 'Content-Type': 'application/json' },
  });
  check(res3, {
    'create donation status 201': (r) => r.status === 201,
  });

  if (res3.status !== 201) {
    errorCounter.add(1);
  }

  sleep(1);  # Think time
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'summary.json': JSON.stringify(data),  // 결과 저장
  };
}
```

**K6 → Prometheus 연동**:
```bash
# K6 실행 시 statsd output 활성화
k6 run \
  --out statsd=http://localhost:8125 \
  tests/load/scenarios/moderate-200vu.js
```

**Prometheus statsd-exporter**:
```yaml
# infra/k8s/observability/k6-exporter/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: statsd-exporter
spec:
  replicas: 1
  selector:
    matchLabels:
      app: statsd-exporter
  template:
    metadata:
      labels:
        app: statsd-exporter
    spec:
      containers:
      - name: statsd-exporter
        image: prom/statsd-exporter:v0.22.0
        args:
          - --statsd.listen-udp=:8125
          - --web.listen-address=:9102
        ports:
        - containerPort: 8125
          protocol: UDP
        - containerPort: 9102
          protocol: TCP
```

**Prometheus scrape config**:
```yaml
scrape_configs:
  - job_name: 'k6'
    scrape_interval: 5s  # 부하 테스트 중엔 고빈도
    static_configs:
      - targets: ['statsd-exporter:9102']
```

### Rationale

1. **실시간 모니터링**:
   - K6 실행 중 Grafana 대시보드에서 즉시 확인
   - Llama 쿼리: "K6 테스트 중 에러율은?"

2. **성능 기준 검증**:
   - spec.md 성공 기준: 200 VU, p95 < 500ms
   - K6 thresholds로 자동 PASS/FAIL 판정

3. **Prometheus 통합**:
   - statsd-exporter가 K6 메트릭을 Prometheus 포맷으로 변환
   - 기존 Grafana 대시보드에 K6 패널 추가 가능

### Alternatives Considered

**대안 1: K6 Cloud** (❌ 거부)
- 장점: SaaS, 관리 불필요
- 단점: 비용 ($49/월), 학습 목적 부적합
- 결론: 로컬 실행 + Prometheus 연동

**대안 2: Locust** (❌ 거부)
- Python 기반 부하 테스트
- 단점: K6보다 성능 낮음 (Python GIL)
- 결론: K6가 업계 표준

---

## 6. Llama Observability Query Interface

### Decision: httpx AsyncClient + PromQL/LogQL/TraceQL

**ObservabilityAgent 구현**:
```python
# backend/src/services/observability_agent.py
import httpx
from datetime import datetime, timedelta

class ObservabilityAgent:
    def __init__(self):
        # 로컬 Observability 스택 (빠른 쿼리)
        self.prometheus_url = "http://prometheus:9090"
        self.loki_url = "http://loki:3100"
        self.tempo_url = "http://tempo:3200"

        # HTTP 커넥션 풀 (재사용)
        self.client = httpx.AsyncClient(
            timeout=5.0,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )

    async def query_prometheus(self, query: str, time_range: str = "1h"):
        """Prometheus PromQL 쿼리"""
        end = datetime.now()
        start = end - timedelta(hours=int(time_range.rstrip('h')))

        params = {
            "query": query,
            "start": int(start.timestamp()),
            "end": int(end.timestamp()),
            "step": "15s"
        }

        response = await self.client.get(
            f"{self.prometheus_url}/api/v1/query_range",
            params=params
        )
        response.raise_for_status()
        return response.json()["data"]["result"]

    async def query_loki(self, logql: str, time_range: str = "1h", limit: int = 100):
        """Loki LogQL 쿼리"""
        end = datetime.now()
        start = end - timedelta(hours=int(time_range.rstrip('h')))

        params = {
            "query": logql,
            "start": int(start.timestamp() * 1e9),  # 나노초
            "end": int(end.timestamp() * 1e9),
            "limit": limit
        }

        response = await self.client.get(
            f"{self.loki_url}/loki/api/v1/query_range",
            params=params
        )
        response.raise_for_status()
        return response.json()["data"]["result"]

    async def query_tempo(self, trace_id: str):
        """Tempo 트레이스 조회"""
        response = await self.client.get(
            f"{self.tempo_url}/api/traces/{trace_id}"
        )
        response.raise_for_status()
        return response.json()

    async def analyze_with_llama(self, question: str):
        """Llama를 사용한 관측성 데이터 분석 (FR-013, FR-014)"""
        # 1. 질문 유형 판별
        if "에러" in question or "error" in question.lower():
            return await self._analyze_errors(question)
        elif "느린" in question or "slow" in question.lower():
            return await self._analyze_latency(question)
        elif "CPU" in question or "메모리" in question:
            return await self._analyze_resources(question)
        else:
            return await self._generic_analysis(question)

    async def _analyze_errors(self, question: str):
        """에러 분석 (5XX 중심)"""
        # 1. Prometheus: 5XX 에러율
        promql = 'rate(http_requests_total{status="5xx"}[1h])'
        error_rate = await self.query_prometheus(promql)

        # 2. Loki: 에러 로그
        logql = '{app="backend", level="error"}'
        error_logs = await self.query_loki(logql, limit=20)

        # 3. PostgreSQL: 유사 에러 검색 (pgvector)
        similar_errors = await self._find_similar_errors(error_logs)

        # 4. Llama 분석
        context = f"""
        최근 1시간 동안:
        - 5XX 에러율: {error_rate}
        - 에러 로그: {error_logs}
        - 유사 과거 에러: {similar_errors}
        """

        # TODO: Llama API 호출
        answer = f"분석 결과: {context}"
        return answer

    async def _analyze_latency(self, question: str):
        """지연시간 분석"""
        # 1. Prometheus: p95 지연시간
        promql = 'histogram_quantile(0.95, http_request_duration_seconds_bucket[5m])'
        p95_latency = await self.query_prometheus(promql)

        # 2. Tempo: 느린 트레이스 검색
        # TraceQL: duration > 1s
        # (Tempo HTTP API는 TraceQL 검색 제한적, Phase 2에서 개선)

        context = f"p95 지연시간: {p95_latency}"
        return context

    async def _analyze_resources(self, question: str):
        """리소스 사용량 분석"""
        promql_cpu = 'kube_pod_container_resource_usage_cpu_cores{pod=~"backend.*"}'
        promql_mem = 'kube_pod_container_resource_usage_memory_bytes{pod=~"backend.*"}'

        cpu = await self.query_prometheus(promql_cpu)
        memory = await self.query_prometheus(promql_mem)

        context = f"CPU: {cpu}, Memory: {memory}"
        return context
```

**Llama Query API Endpoint**:
```python
# backend/src/api/observability.py
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/observability")

class QueryRequest(BaseModel):
    question: str
    time_range: str = "1h"

@router.post("/query")
async def query_observability(req: QueryRequest):
    """FR-013: Llama가 관측성 데이터를 자연어로 쿼리"""
    agent = ObservabilityAgent()

    import time
    start = time.time()
    answer = await agent.analyze_with_llama(req.question)
    duration = time.time() - start

    # NFR-001: < 1초 검증
    assert duration < 1.0, f"Query took {duration:.2f}s > 1s"

    return {
        "question": req.question,
        "answer": answer,
        "query_time_seconds": duration
    }
```

### Rationale

1. **로컬 쿼리 성능**:
   - Prometheus/Loki/Tempo HTTP API 직접 호출
   - 네트워크 레이턴시 최소 (같은 클러스터)
   - NFR-001 만족: < 1초

2. **httpx AsyncClient 재사용**:
   - 커넥션 풀 (keep-alive)
   - 비동기 I/O (FastAPI와 궁합)

3. **Llama 통합 단순화**:
   - Observability 데이터를 텍스트로 변환
   - Llama는 텍스트 분석만 수행 (쿼리 문법 불필요)

### Alternatives Considered

**대안 1: Grafana Cloud API 직접 쿼리** (❌ 거부)
- 장점: 14일 데이터 접근
- 단점:
  - 네트워크 레이턴시 (외부 API)
  - API Key 관리 복잡도
  - NFR-001 위반 (> 1초)
- 결론: 로컬 3일 데이터면 충분 (최근 이슈 99%)

**대안 2: Llama가 PromQL 직접 생성** (❌ 거부)
- 장점: 더 정교한 쿼리
- 단점:
  - Llama가 PromQL 학습 필요 (복잡)
  - 쿼리 오류 가능성
- 결론: Agent가 쿼리 생성, Llama는 결과 분석만

---

## 7. HPA (Horizontal Pod Autoscaler)

### Decision: CPU 70% + Memory 80%, maxReplicas 3

**HPA Manifest**:
```yaml
# infra/k8s/backend/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 1
  maxReplicas: 3

  metrics:
    # CPU 기준
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70  # 70% 초과 시 스케일 업

    # Memory 기준
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80  # 80% 초과 시 스케일 업

  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60  # 1분 관찰 후 스케일 업
      policies:
        - type: Percent
          value: 100  # 한 번에 2배씩 증가 (1→2→3)
          periodSeconds: 60
        - type: Pods
          value: 1  # 또는 1개씩 증가
          periodSeconds: 60
      selectPolicy: Max  # 더 빠른 정책 선택

    scaleDown:
      stabilizationWindowSeconds: 300  # 5분 안정화 (급격한 축소 방지)
      policies:
        - type: Pods
          value: 1  # 한 번에 1개씩만 감소
          periodSeconds: 60
```

**Backend Deployment Resource Limits**:
```yaml
# infra/k8s/backend/deployment.yaml
spec:
  template:
    spec:
      containers:
      - name: backend
        resources:
          requests:
            cpu: 200m      # HPA 기준점
            memory: 512Mi  # HPA 기준점
          limits:
            cpu: 500m
            memory: 1Gi
```

### Rationale

1. **maxReplicas 3 (not 10)**:
   - spec.md FR-021 준수
   - 8GB Node 1개로 충분 (Backend 3개 × 512MB = 1.5GB)

2. **CPU 70% + Memory 80%**:
   - spec.md FR-020 준수
   - 두 조건 중 하나라도 만족 시 스케일 업

3. **Stabilization Window**:
   - Scale Up 60s: 빠른 반응 (K6 테스트 중 부하 급증)
   - Scale Down 300s: 느린 축소 (flapping 방지)

### Alternatives Considered

**대안 1: Custom Metrics (Prometheus Adapter)** (⚠️ Phase 2 고려)
- HTTP 요청률 기반 스케일링
- 예: `http_requests_total` > 100 req/s
- 단점: 복잡도 증가
- 결론: CPU/Memory면 충분 (K6 200 VU 커버)

**대안 2: KEDA (Kubernetes Event-Driven Autoscaling)** (❌ 거부)
- Celery 큐 길이 기반 스케일링
- 단점: Celery는 Job으로 실행 (상시 아님)
- 결론: HPA는 Backend만, Celery는 수동

---

## 8. PostgreSQL pgvector for ErrorEvent

### Decision: pgvector extension + sentence-transformers

**ErrorEvent 모델**:
```python
# backend/src/models/error_event.py
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

class ErrorEvent(Base):
    __tablename__ = "error_events"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    level = Column(String(10), nullable=False)  # error, critical
    message = Column(Text, nullable=False)
    traceback = Column(Text)
    service = Column(String(50), nullable=False)  # backend, celery
    trace_id = Column(String(32), index=True)  # OpenTelemetry
    span_id = Column(String(16))
    context = Column(JSONB)  # 추가 컨텍스트 (request, user 등)

    # Vector embedding (384차원, all-MiniLM-L6-v2)
    embedding = Column(Vector(384))

    resolution_status = Column(String(20), default="new")  # new, analyzing, resolved
```

**Embedding 생성**:
```python
# backend/src/services/error_analyzer.py
from sentence_transformers import SentenceTransformer

class ErrorAnalyzer:
    def __init__(self):
        # 경량 임베딩 모델 (all-MiniLM-L6-v2: 384 dim, 80MB)
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    def create_embedding(self, error_message: str, traceback: str) -> list[float]:
        """에러 메시지 + 스택 트레이스를 임베딩"""
        text = f"{error_message}\n{traceback}"
        embedding = self.model.encode(text)
        return embedding.tolist()

    async def find_similar_errors(self, error_message: str, limit: int = 5):
        """유사 에러 검색 (FR-016)"""
        # 1. 현재 에러 임베딩
        query_embedding = self.create_embedding(error_message, "")

        # 2. pgvector cosine similarity 검색
        query = select(ErrorEvent).order_by(
            ErrorEvent.embedding.cosine_distance(query_embedding)
        ).limit(limit)

        results = await db.execute(query)
        similar_errors = results.scalars().all()

        return similar_errors
```

**Celery Worker: 자동 에러 저장**:
```python
# backend/src/workers/error_logger.py
from celery import shared_task

@shared_task
def log_error_event(error_data: dict):
    """중요 에러를 ErrorEvent 테이블에 저장 (FR-015)"""
    analyzer = ErrorAnalyzer()

    # Embedding 생성
    embedding = analyzer.create_embedding(
        error_data["message"],
        error_data["traceback"]
    )

    # DB 저장
    error_event = ErrorEvent(
        timestamp=datetime.now(),
        level=error_data["level"],
        message=error_data["message"],
        traceback=error_data["traceback"],
        service=error_data["service"],
        trace_id=error_data.get("trace_id"),
        embedding=embedding
    )

    db.add(error_event)
    db.commit()
```

### Rationale

1. **pgvector 선택**:
   - PostgreSQL extension (별도 DB 불필요)
   - Cosine similarity 지원
   - 인덱스 (ivfflat, hnsw) 지원

2. **all-MiniLM-L6-v2 모델**:
   - 384차원 (메모리 효율적)
   - 80MB (경량)
   - 문장 유사도 측정에 최적화

3. **Celery 비동기 처리**:
   - 에러 발생 시 즉시 반환 (사용자 대기 없음)
   - 백그라운드에서 임베딩 생성 및 저장

### Alternatives Considered

**대안 1: Pinecone/Weaviate (Vector DB)** (❌ 거부)
- 전용 Vector Database
- 단점: 별도 인프라, 비용 증가
- 결론: pgvector로 충분 (ErrorEvent 수 적음)

**대안 2: OpenAI Embeddings** (❌ 거부)
- GPT-3.5 임베딩 (1536차원)
- 단점: API 비용, 외부 의존성
- 결론: Sentence Transformers (로컬)

---

## 9. Alertmanager + Slack 연동

### Decision: Grafana Cloud Alerting → Slack Webhook

**Slack 연동 설정**:

#### A. Slack Incoming Webhook 생성
1. Slack Workspace → Apps → Incoming Webhooks
2. Channel 선택: `#bodam-alerts` (또는 `#monitoring`)
3. Webhook URL 획득: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX`

#### B. Grafana Cloud Alert Contact Point 설정
```yaml
# Grafana Cloud UI에서 설정 (UI 기반, YAML 예시)
apiVersion: 1
contactPoints:
  - orgId: 1
    name: slack-bodam-alerts
    receivers:
      - uid: slack-1
        type: slack
        settings:
          url: ${SLACK_WEBHOOK_URL}
          title: '{{ template "slack.title" . }}'
          text: |
            {{ range .Alerts }}
            *Alert:* {{ .Labels.alertname }}
            *Status:* {{ .Status }}
            *Severity:* {{ .Labels.severity }}
            *Summary:* {{ .Annotations.summary }}
            *Description:* {{ .Annotations.description }}
            *Time:* {{ .StartsAt }}
            {{ end }}
          username: 'Bodam Monitoring'
          icon_emoji: ':fire:'
```

#### C. Alert Rules (Grafana Cloud)

**1. 5XX 서버 에러 즉시 알람 (최우선)**:
```yaml
groups:
  - name: bodam_critical_alerts
    interval: 1m
    rules:
      - alert: ServerError5XX
        expr: rate(http_requests_total{status="5xx"}[1m]) > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "🚨 5XX 서버 에러 발생!"
          description: "{{ $labels.endpoint }}에서 5XX 에러 {{ $value }}건/초 발생 중"
          runbook_url: "https://github.com/your-org/bodam/wiki/Runbook-5XX-Errors"
```

**2. HTTP 커넥션 풀 고갈 (최우선)**:
```yaml
      - alert: HTTPConnectionPoolExhausted
        expr: http_client_waiting_requests > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "⚠️ HTTP 커넥션 풀 고갈!"
          description: "{{ $labels.host }}로의 요청이 {{ $value }}개 대기 중. 커넥션 풀 확장 필요."
```

**3. 4XX 클라이언트 에러 패턴 감지**:
```yaml
      - alert: HighClientErrorRate
        expr: |
          rate(http_requests_total{status="4xx"}[5m])
          /
          rate(http_requests_total[5m])
          > 0.3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "⚠️ 4XX 클라이언트 에러율 높음"
          description: "전체 요청의 {{ $value | humanizePercentage }}%가 4XX 에러. 프론트엔드 버그 의심."
```

**4. HPA Pod 부족**:
```yaml
      - alert: BackendPodsMaxedOut
        expr: kube_deployment_status_replicas{deployment="backend"} >= 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "⚠️ Backend Pod 최대치 도달"
          description: "Backend가 max replicas (3개)에 도달. 추가 확장 불가."
```

**5. DB 커넥션 풀 고갈**:
```yaml
      - alert: DBConnectionPoolHigh
        expr: db_connections_active > 80
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "⚠️ DB 커넥션 풀 사용률 높음"
          description: "활성 DB 커넥션: {{ $value }}개 / 100개. 고갈 임박."
```

**6. Disk 공간 부족 (Phase 2)**:
```yaml
      - alert: NodeDiskSpaceLow
        expr: node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes < 0.2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "⚠️ Node 디스크 공간 부족"
          description: "사용 가능 디스크: {{ $value | humanizePercentage }}% 남음"
```

#### D. Slack 메시지 템플릿

**템플릿 정의**:
```go-template
{{ define "slack.title" }}
[{{ .Status | toUpper }}{{ if eq .Status "firing" }}:{{ .Alerts.Firing | len }}{{ end }}] {{ .GroupLabels.alertname }}
{{ end }}

{{ define "slack.text" }}
{{ range .Alerts }}
*Alert:* {{ .Labels.alertname }}
*Status:* {{ .Status }}
*Severity:* {{ .Labels.severity }}
*Summary:* {{ .Annotations.summary }}
*Description:* {{ .Annotations.description }}
*Started:* {{ .StartsAt | humanizeTimestamp }}
{{ if .EndsAt }}*Ended:* {{ .EndsAt | humanizeTimestamp }}{{ end }}
*Grafana:* <https://your-instance.grafana.net/alerting/list|View in Grafana>
─────────────────────────────
{{ end }}
{{ end }}
```

**Slack 메시지 예시**:
```
🚨 [FIRING:1] ServerError5XX
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*Alert:* ServerError5XX
*Status:* firing
*Severity:* critical
*Summary:* 🚨 5XX 서버 에러 발생!
*Description:* /api/donations에서 5XX 에러 0.5건/초 발생 중
*Started:* 2025-10-16 17:30:15 KST
*Grafana:* View in Grafana
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### E. Alert Routing (선택적)

**Severity별 채널 분리** (Phase 2):
```yaml
route:
  receiver: 'slack-default'
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

  routes:
    # Critical → #bodam-critical
    - match:
        severity: critical
      receiver: 'slack-critical'
      repeat_interval: 1h  # 더 자주 알림

    # Warning → #bodam-alerts
    - match:
        severity: warning
      receiver: 'slack-alerts'
      repeat_interval: 4h

receivers:
  - name: 'slack-critical'
    slack_configs:
      - api_url: ${SLACK_WEBHOOK_CRITICAL}
        channel: '#bodam-critical'
        title: '🚨 CRITICAL ALERT'

  - name: 'slack-alerts'
    slack_configs:
      - api_url: ${SLACK_WEBHOOK_ALERTS}
        channel: '#bodam-alerts'
        title: '⚠️ Warning Alert'
```

#### F. 침묵(Silence) 및 억제(Inhibition)

**점검 중 알람 침묵**:
```bash
# Grafana Cloud UI에서 설정
# 또는 amtool (Alertmanager CLI)
amtool silence add \
  alertname=ServerError5XX \
  --duration=1h \
  --comment="Planned maintenance"
```

**Inhibition Rules** (Phase 2):
```yaml
# Backend Pod 다운 시 5XX 알람 억제 (중복 방지)
inhibit_rules:
  - source_match:
      alertname: BackendPodDown
    target_match:
      alertname: ServerError5XX
    equal: ['pod']
```

### Rationale

1. **Grafana Cloud Alerting 사용**:
   - Free Tier에 포함 (비용 $0)
   - UI 기반 관리 (코드 불필요)
   - 고가용성 (SLA 99.9%)

2. **Slack 연동 장점**:
   - 실시간 알림 (모바일 푸시)
   - 팀 협업 (스레드로 토론)
   - 히스토리 보존 (검색 가능)

3. **Alert 우선순위**:
   - Critical (즉시 대응): 5XX, HTTP 풀 고갈
   - Warning (모니터링): 4XX 패턴, HPA 한계, DB 풀

4. **False Positive 방지**:
   - `for: 1m` - 1분간 지속 시에만 알람
   - `group_wait: 30s` - 30초간 유사 알람 그룹화
   - `repeat_interval: 4h` - 4시간마다 재알림 (스팸 방지)

### Alternatives Considered

**대안 1: Self-hosted Alertmanager** (❌ 거부)
- 장점: 완전한 제어
- 단점: 관리 부담, 인프라 비용 (+$24/월)
- 결론: Grafana Cloud Alerting 압도적 우위

**대안 2: PagerDuty** (❌ 거부)
- 장점: 온콜 로테이션, 에스컬레이션
- 단점: 비용 ($29/user/월), 학습 프로젝트에 과잉
- 결론: Slack으로 충분

**대안 3: Email 알림** (❌ 거부)
- 단점: 실시간성 낮음, 스팸 필터 위험
- 결론: Slack 모바일 푸시가 훨씬 효과적

---

## 10. 비용 최적화 전략

### Decision: Grafana Cloud Free Tier + 메트릭 필터링

**예상 비용** (월 기준):
```
Frontend (Vercel Hobby):              $0
Backend (DOKS 8GB Node):              $24
Load Balancer:                        $12
Grafana Cloud:                        $0 (Free Tier)
─────────────────────────────────────
Total:                                $36/월 ✅ (NFR-006: < $40)
```

**Grafana Cloud 사용량**:
```
Free Tier 제한:
- Metrics: 10K active series
- Logs: 50GB ingestion/month
- Traces: 50GB ingestion/month

예상 사용량:
- Metrics: ~2,500 series (25%)
- Logs: ~10GB/month (평상시 트래픽)
- Traces: ~5GB/month (100% collection)

여유: 75% (Phase 2 확장 가능)
```

**메트릭 필터링 (remote_write)**:
```yaml
remote_write:
  - url: https://prometheus-prod.grafana.net/api/prom/push
    write_relabel_configs:
      # Go runtime 메트릭 제외
      - source_labels: [__name__]
        regex: 'go_.*|process_.*'
        action: drop

      # DEBUG 로그 제외
      - source_labels: [level]
        regex: 'debug'
        action: drop

      # High-cardinality 레이블 제거
      - source_labels: [instance, pod]
        action: labeldrop
```

### Rationale

1. **Grafana Cloud Free Tier 최대 활용**:
   - 14일 retention (NFR-007 만족)
   - 비용 $0
   - 고가용성 (SLA 99.9%)

2. **Phase별 확장 여유**:
   - Phase 1: 25% 사용
   - Phase 2: 50% 사용 (Celery, AI 메트릭 추가)
   - Phase 3: 70% 사용 (비즈니스 메트릭 확장)

### Alternatives Considered

**대안 1: Self-hosted Grafana + Prometheus** (❌ 거부)
- 장점: 무제한 데이터
- 단점:
  - 관리 부담 (업데이트, 백업)
  - 인프라 비용 증가 (+$24/월)
- 결론: Grafana Cloud Free Tier 압도적 우위

**대안 2: Grafana Cloud Pro Plan ($8/월)** (⚠️ Phase 3 고려)
- 100K series, 100GB logs, 100GB traces
- OnCall (PagerDuty 기능)
- 결론: 현재는 Free Tier로 충분

---

## 10. 구현 우선순위 및 Phase

### Phase 1 (MVP): Core Observability

**목표**: 시스템 건강도 파악 + Llama 쿼리 지원

**구현 순서**:
1. Prometheus (메트릭 14개)
2. Loki + Promtail (로그 수집)
3. Tempo (트레이싱)
4. Grafana Cloud Remote Write
5. ObservabilityAgent (Llama 쿼리)
6. HPA (Backend max 3)

**예상 소요**: 5-7일 (TDD 포함)

---

### Phase 2 (성장기): 확장 및 최적화

**추가 구현**:
1. K6 부하 테스트 자동화
2. Celery 메트릭 (작업 빈도 증가 후)
3. Custom Metrics (Prometheus Adapter)
4. ErrorEvent 자동 분석 (pgvector)
5. Grafana 대시보드 고도화

**예상 소요**: 3-5일

---

### Phase 3 (확장기): 고급 기능

**추가 구현**:
1. Grafana Agent (Prometheus + Loki + Tempo 통합)
2. Trace Sampling (10-30%)
3. Alertmanager (고급 알람 라우팅)
4. SLO Dashboard (가용성, 지연시간)

**예상 소요**: 3-5일

---

## 결론

모든 기술적 의사결정이 완료되었으며, 다음 단계(Phase 1: Design & Contracts)로 진행 가능합니다.

**주요 결정사항 요약**:
- ✅ Prometheus 14개 메트릭 (상태 코드 3-tier: 2xx, 4xx, 5xx)
- ✅ Loki + Promtail DaemonSet (로컬 3일 + Grafana Cloud 14일)
- ✅ Tempo + OpenTelemetry (로컬 2일)
- ✅ K6 + Prometheus statsd-exporter
- ✅ Llama 로컬 쿼리 (httpx AsyncClient)
- ✅ HPA CPU 70%, Memory 80%, max 3 replicas
- ✅ pgvector ErrorEvent (all-MiniLM-L6-v2)
- ✅ 비용 $36/월 (Grafana Cloud Free Tier)

**NEEDS CLARIFICATION**: 없음 (모두 해결) ✅
