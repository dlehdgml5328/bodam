# Quickstart: Hybrid Observability Stack

빠르게 시작하기 위한 가이드입니다. 전체 observability stack을 로컬 또는 Kubernetes 환경에서 실행할 수 있습니다.

## Prerequisites

- Docker & Docker Compose (로컬 개발)
- Kubernetes cluster (운영 환경 - DigitalOcean DOKS 권장)
- kubectl 1.28+
- Helm 3.0+
- Python 3.11+
- K6 (load testing)
- Grafana Cloud 계정 (Free Tier)

## Quick Start (로컬 개발)

### 1. Grafana Cloud 설정

```bash
# Grafana Cloud Free Tier 가입
# https://grafana.com/auth/sign-up/create-user

# 설정 정보 수집
# - Prometheus Remote Write URL
# - Prometheus Instance ID & API Key
# - Loki URL & User ID & API Key
# - Tempo URL & Credentials
```

### 2. 환경 변수 설정

```bash
# .env.observability 파일 생성
cat > .env.observability <<EOF
# Grafana Cloud Credentials
GRAFANA_CLOUD_PROMETHEUS_URL=https://prometheus-prod-us-central-0.grafana.net/api/prom/push
GRAFANA_CLOUD_PROMETHEUS_USER=YOUR_INSTANCE_ID
GRAFANA_CLOUD_PROMETHEUS_PASS=YOUR_API_KEY

GRAFANA_CLOUD_LOKI_URL=https://logs-prod-us-central-0.grafana.net/loki/api/v1/push
GRAFANA_CLOUD_LOKI_USER=YOUR_LOKI_USER_ID
GRAFANA_CLOUD_LOKI_PASS=YOUR_API_KEY

GRAFANA_CLOUD_TEMPO_URL=tempo-prod-us-central-0.grafana.net:443
GRAFANA_CLOUD_TEMPO_CREDS=YOUR_BASE64_CREDENTIALS

# Slack Webhook (Alertmanager)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_CHANNEL=#bodam-alerts

# Backend Configuration
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
OTEL_SERVICE_NAME=backend-api
EOF
```

### 3. Docker Compose 실행

```bash
# Observability stack 시작
docker-compose -f docker-compose.observability.yml up -d

# 서비스 확인
docker-compose -f docker-compose.observability.yml ps

# 예상 서비스:
# - prometheus (9090)
# - loki (3100)
# - tempo (3200)
# - otel-collector (4317, 4318)
# - alertmanager (9093)
# - promtail (DaemonSet)
# - statsd-exporter (9102, 8125)
# - grafana (3000) - optional for local visualization
```

### 4. Backend API 계측

```bash
# OpenTelemetry 의존성 설치
cd backend
pip install \
  opentelemetry-api \
  opentelemetry-sdk \
  opentelemetry-instrumentation-fastapi \
  opentelemetry-instrumentation-sqlalchemy \
  opentelemetry-instrumentation-httpx \
  opentelemetry-instrumentation-celery \
  opentelemetry-exporter-otlp

# Prometheus client 설치
pip install prometheus-client

# 환경 변수 로드
export $(cat ../.env.observability | xargs)

# Backend 실행 (auto-instrumentation)
opentelemetry-instrument \
  --traces_exporter otlp \
  --metrics_exporter otlp \
  --logs_exporter otlp \
  --service_name backend-api \
  uvicorn main:app --host 0.0.0.0 --port 8000
```

### 5. Metrics 확인

```bash
# Prometheus 확인
curl http://localhost:9090/-/healthy

# Metrics endpoint 확인
curl http://localhost:8000/metrics

# 예상 출력:
# http_requests_total{method="GET",endpoint="/health",status="2xx"} 1
# db_connection_pool_size{service="backend-api"} 10
# db_connection_pool_in_use{service="backend-api"} 2
```

### 6. K6 Load Test 실행

```bash
# K6 설치
brew install k6  # macOS
# or
sudo apt-get install k6  # Ubuntu

# Baseline 시나리오 (50 VU)
K6_SCENARIO=baseline k6 run --out statsd specs/004-hybrid-observability-stack/contracts/k6-scenarios.js

# Target 시나리오 (200 VU - Success Criteria)
K6_SCENARIO=target BASE_URL=http://localhost:8000 k6 run --out statsd specs/004-hybrid-observability-stack/contracts/k6-scenarios.js

# 결과 확인
cat /tmp/k6-summary.json
```

### 7. Logs 확인

```bash
# Loki 쿼리 (LogQL)
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={service="backend-api"}' \
  --data-urlencode 'limit=10' | jq

# 에러 로그만 필터링
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={service="backend-api",level="error"}' \
  --data-urlencode 'limit=10' | jq
```

### 8. Traces 확인

```bash
# Tempo trace 검색 (TraceQL)
curl -G -s "http://localhost:3200/api/search" \
  --data-urlencode 'q={ service.name = "backend-api" }' | jq

# 특정 trace 조회
TRACE_ID="your-trace-id-here"
curl -s "http://localhost:3200/api/traces/${TRACE_ID}" | jq
```

### 9. Llama Observability Query 테스트

```bash
# Natural language query
curl -X POST http://localhost:8000/api/v1/observability/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "지난 1시간 동안 5XX 에러가 얼마나 발생했어?",
    "time_range": "1h",
    "language": "ko"
  }' | jq

# Dashboard metrics
curl http://localhost:8000/api/v1/observability/metrics/dashboard?time_range=15m | jq
```

## Kubernetes 배포 (운영 환경)

### 1. DOKS 클러스터 생성

```bash
# DigitalOcean CLI 설치
brew install doctl  # macOS

# 인증
doctl auth init

# Kubernetes 클러스터 생성 (8GB RAM, $24/month)
doctl kubernetes cluster create bodam-prod \
  --region sgp1 \
  --version 1.28.2-do.0 \
  --node-pool "name=worker;size=s-2vcpu-4gb;count=1;auto-scale=true;min-nodes=1;max-nodes=3"

# kubeconfig 설정
doctl kubernetes cluster kubeconfig save bodam-prod
```

### 2. Namespace 생성

```bash
# Observability namespace
kubectl create namespace observability

# Application namespace
kubectl create namespace bodam
```

### 3. Secrets 생성

```bash
# Grafana Cloud credentials
kubectl create secret generic grafana-cloud-creds \
  --from-literal=prometheus-user=$GRAFANA_CLOUD_PROMETHEUS_USER \
  --from-literal=prometheus-pass=$GRAFANA_CLOUD_PROMETHEUS_PASS \
  --from-literal=loki-user=$GRAFANA_CLOUD_LOKI_USER \
  --from-literal=loki-pass=$GRAFANA_CLOUD_LOKI_PASS \
  --from-literal=tempo-creds=$GRAFANA_CLOUD_TEMPO_CREDS \
  -n observability

# Slack webhook
kubectl create secret generic alertmanager-slack \
  --from-literal=webhook-url=$SLACK_WEBHOOK_URL \
  -n observability
```

### 4. Helm Charts 배포

```bash
# Prometheus (with remote_write to Grafana Cloud)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/prometheus \
  --namespace observability \
  --values infra/k8s/observability/prometheus-values.yaml

# Loki
helm repo add grafana https://grafana.github.io/helm-charts

helm install loki grafana/loki \
  --namespace observability \
  --values infra/k8s/observability/loki-values.yaml

# Promtail (DaemonSet)
helm install promtail grafana/promtail \
  --namespace observability \
  --values infra/k8s/observability/promtail-values.yaml

# Tempo
helm install tempo grafana/tempo \
  --namespace observability \
  --values infra/k8s/observability/tempo-values.yaml

# OpenTelemetry Collector
helm install otel-collector open-telemetry/opentelemetry-collector \
  --namespace observability \
  --values infra/k8s/observability/otel-collector-values.yaml

# Alertmanager (with Slack integration)
helm install alertmanager prometheus-community/alertmanager \
  --namespace observability \
  --values infra/k8s/observability/alertmanager-values.yaml
```

### 5. Backend Deployment (with auto-instrumentation)

```bash
# Backend deployment with OTEL env vars
kubectl apply -f infra/k8s/backend-deployment.yaml -n bodam

# HPA 설정 (CPU 70%, Memory 80%, max 3 replicas)
kubectl apply -f infra/k8s/backend-hpa.yaml -n bodam

# 확인
kubectl get pods -n bodam
kubectl get hpa -n bodam
```

### 6. 서비스 확인

```bash
# Prometheus
kubectl port-forward -n observability svc/prometheus-server 9090:80

# Loki
kubectl port-forward -n observability svc/loki 3100:3100

# Tempo
kubectl port-forward -n observability svc/tempo 3200:3200

# Backend API
kubectl port-forward -n bodam svc/backend 8000:8000
```

## 검증

### Success Criteria 확인 (spec.md)

```bash
# 1. K6 Target Load Test (200 VU)
K6_SCENARIO=target BASE_URL=http://your-load-balancer-ip k6 run \
  --out statsd=http://statsd-exporter:8125 \
  specs/004-hybrid-observability-stack/contracts/k6-scenarios.js

# 예상 결과:
# - p95 latency < 500ms ✓
# - p99 latency < 1000ms ✓
# - Error rate < 1% ✓
# - Status: PASSED ✓

# 2. Llama Query Response Time
time curl -X POST http://localhost:8000/api/v1/observability/query \
  -H "Content-Type: application/json" \
  -d '{"query": "현재 DB 커넥션 풀 사용량?"}'

# 예상: real < 1s ✓

# 3. Alert 발생 테스트
# 5XX 에러 발생 시 Slack 알림 확인
curl http://localhost:8000/api/v1/force-error  # Test endpoint

# Slack channel #bodam-alerts 확인 ✓

# 4. HPA Auto-scaling 테스트
# 부하 증가 시 max 3 replicas까지 확장
K6_SCENARIO=stress k6 run --out statsd k6-scenarios.js
kubectl get hpa -n bodam -w

# 예상: 1 → 2 → 3 replicas ✓

# 5. Cost 확인
# - DOKS: $24/month
# - Load Balancer: $12/month
# - Grafana Cloud: $0 (Free Tier)
# Total: $36/month < $40 ✓
```

## Troubleshooting

### Prometheus metrics not appearing

```bash
# Check Prometheus targets
kubectl port-forward -n observability svc/prometheus-server 9090:80
# Open: http://localhost:9090/targets

# Check backend /metrics endpoint
kubectl port-forward -n bodam svc/backend 8000:8000
curl http://localhost:8000/metrics
```

### Loki logs not appearing

```bash
# Check Promtail status
kubectl logs -n observability -l app=promtail --tail=50

# Check Loki ingester
kubectl logs -n observability -l app=loki --tail=50

# Query Loki directly
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="backend-api"}' \
  --data-urlencode 'limit=10'
```

### Tempo traces not appearing

```bash
# Check OTEL collector
kubectl logs -n observability -l app=otel-collector --tail=50

# Check Tempo ingester
kubectl logs -n observability -l app=tempo --tail=50

# Verify OTEL env vars in backend
kubectl exec -n bodam deployment/backend -- env | grep OTEL
```

### Alertmanager not sending to Slack

```bash
# Check Alertmanager config
kubectl logs -n observability -l app=alertmanager --tail=50

# Test Slack webhook
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text": "Test alert from Alertmanager"}'

# Check Alertmanager UI
kubectl port-forward -n observability svc/alertmanager 9093:9093
# Open: http://localhost:9093
```

### K6 load test failing

```bash
# Check statsd-exporter
kubectl logs -n observability -l app=statsd-exporter --tail=50

# Run K6 with verbose output
K6_SCENARIO=baseline k6 run --verbose \
  --out statsd=http://statsd-exporter:8125 \
  k6-scenarios.js

# Check K6 metrics in Prometheus
curl -G -s "http://localhost:9090/api/v1/query" \
  --data-urlencode 'query=k6_http_reqs_total'
```

## Next Steps

1. **Grafana Dashboards**: Grafana Cloud에서 대시보드 구성
   - HTTP Traffic Dashboard
   - Database Connection Pool Dashboard
   - Celery Tasks Dashboard
   - K6 Load Test Results Dashboard

2. **Alert Rules 튜닝**: Alertmanager rules 조정
   - 4XX rate threshold (현재 30%)
   - 5XX immediate alert sensitivity
   - DB pool exhaustion threshold

3. **Llama 고도화**: AI assistant 쿼리 패턴 학습
   - 자주 사용하는 쿼리 템플릿화
   - 에러 패턴 자동 분류
   - 장애 원인 자동 분석

4. **비용 최적화**:
   - Metric relabeling 추가
   - Scrape interval 조정
   - Grafana Cloud retention 정책 검토

## 참고 문서

- [spec.md](./spec.md) - Feature specification
- [plan.md](./plan.md) - Implementation plan
- [research.md](./research.md) - Technical research
- [data-model.md](./data-model.md) - Database models
- [contracts/](./contracts/) - Configuration files
