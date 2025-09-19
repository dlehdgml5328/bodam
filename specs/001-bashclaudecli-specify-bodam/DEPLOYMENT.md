# 배포 가이드 🚀

## 개요
보담(BoDam) 플랫폼의 프로덕션 배포, Blue-Green 배포 전략, 인프라 관리, 모니터링 설정을 정의합니다.

## 🏗️ 인프라 아키텍처

### 1. 클라우드 환경
```yaml
# 프로덕션 환경 구성
Production Environment:
  Cloud Provider: AWS / Google Cloud / Azure
  Region: Korea (Seoul)
  Availability Zones: 3개 AZ 사용

  Compute:
    - Kubernetes Cluster (EKS/GKE/AKS)
    - Node Instance Type: c5.xlarge (4 vCPU, 8GB RAM)
    - Auto Scaling: 3-10 nodes

  Storage:
    - Database: PostgreSQL (RDS/Cloud SQL)
    - Cache: Redis (ElastiCache/MemoryStore)
    - File Storage: S3/Cloud Storage
    - Backup: Cross-region replication

  Network:
    - Load Balancer: Application Load Balancer
    - CDN: CloudFront/Cloud CDN
    - Domain: bodam.example (SSL/TLS)
    - VPC: Private subnets for security
```

### 2. Kubernetes 클러스터 설정
```yaml
# k8s-cluster-config.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: bodam-production
---
apiVersion: v1
kind: Namespace
metadata:
  name: bodam-staging
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: production-quota
  namespace: bodam-production
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    persistentvolumeclaims: "10"
```

## 🐳 컨테이너 이미지 빌드

### 1. 백엔드 프로덕션 Dockerfile
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim as builder

# 의존성 설치를 위한 빌드 도구
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 최종 이미지
FROM python:3.11-slim

# 런타임 의존성만 설치
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 보안을 위한 비루트 사용자 생성
RUN groupadd -r bodam && useradd -r -g bodam bodam

WORKDIR /app

# 빌더 스테이지에서 설치된 패키지 복사
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 소스 코드 복사
COPY . .

# 소유권 변경
RUN chown -R bodam:bodam /app

USER bodam

EXPOSE 8000

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/healthz')"

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. 프론트엔드 프로덕션 Dockerfile
```dockerfile
# frontend/Dockerfile
FROM node:18-alpine as builder

WORKDIR /app

# 의존성 파일 복사 및 설치
COPY package*.json ./
RUN npm ci --only=production

# 소스 코드 복사 및 빌드
COPY . .
RUN npm run build

# 최종 이미지 (nginx)
FROM nginx:alpine

# 보안 설정
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# 빌드된 파일 복사
COPY --from=builder /app/out /usr/share/nginx/html

# nginx 설정
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

### 3. CI/CD 파이프라인
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Run backend tests
        run: |
          cd backend
          pip install -r requirements-dev.txt
          pytest --cov=src --cov-report=xml

      - name: Run frontend tests
        run: |
          cd frontend
          npm ci
          npm run test:ci
          npm run lint
          npm run type-check

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    outputs:
      backend-image: ${{ steps.backend-meta.outputs.tags }}
      frontend-image: ${{ steps.frontend-meta.outputs.tags }}
    steps:
      - uses: actions/checkout@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract backend metadata
        id: backend-meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/backend
          tags: |
            type=ref,event=branch
            type=sha,prefix={{branch}}-

      - name: Extract frontend metadata
        id: frontend-meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/frontend
          tags: |
            type=ref,event=branch
            type=sha,prefix={{branch}}-

      - name: Build and push backend image
        uses: docker/build-push-action@v4
        with:
          context: ./backend
          push: true
          tags: ${{ steps.backend-meta.outputs.tags }}
          labels: ${{ steps.backend-meta.outputs.labels }}

      - name: Build and push frontend image
        uses: docker/build-push-action@v4
        with:
          context: ./frontend
          push: true
          tags: ${{ steps.frontend-meta.outputs.tags }}
          labels: ${{ steps.frontend-meta.outputs.labels }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-2

      - name: Deploy to EKS
        run: |
          aws eks update-kubeconfig --region ap-northeast-2 --name bodam-cluster

          # Blue-Green 배포 실행
          ./scripts/blue-green-deploy.sh \
            --backend-image="${{ needs.build.outputs.backend-image }}" \
            --frontend-image="${{ needs.build.outputs.frontend-image }}"
```

## 🔄 Blue-Green 배포 전략

### 1. Blue-Green 배포 스크립트
```bash
#!/bin/bash
# scripts/blue-green-deploy.sh

set -e

NAMESPACE="bodam-production"
BACKEND_IMAGE=""
FRONTEND_IMAGE=""

# 인자 파싱
while [[ $# -gt 0 ]]; do
  case $1 in
    --backend-image)
      BACKEND_IMAGE="$2"
      shift 2
      ;;
    --frontend-image)
      FRONTEND_IMAGE="$2"
      shift 2
      ;;
    *)
      echo "Unknown parameter: $1"
      exit 1
      ;;
  esac
done

# 현재 활성 환경 확인
CURRENT_ENV=$(kubectl get service bodam-backend-service -n $NAMESPACE -o jsonpath='{.spec.selector.environment}')
echo "Current environment: $CURRENT_ENV"

# 새 환경 결정
if [ "$CURRENT_ENV" = "blue" ]; then
    NEW_ENV="green"
else
    NEW_ENV="blue"
fi

echo "Deploying to environment: $NEW_ENV"

# 새 환경에 배포
envsubst < infra/k8s/backend-deployment.yaml | \
  sed "s/ENVIRONMENT_PLACEHOLDER/$NEW_ENV/g" | \
  sed "s|IMAGE_PLACEHOLDER|$BACKEND_IMAGE|g" | \
  kubectl apply -f -

envsubst < infra/k8s/frontend-deployment.yaml | \
  sed "s/ENVIRONMENT_PLACEHOLDER/$NEW_ENV/g" | \
  sed "s|IMAGE_PLACEHOLDER|$FRONTEND_IMAGE|g" | \
  kubectl apply -f -

# 배포 완료 대기
echo "Waiting for deployment to be ready..."
kubectl rollout status deployment/bodam-backend-$NEW_ENV -n $NAMESPACE --timeout=600s
kubectl rollout status deployment/bodam-frontend-$NEW_ENV -n $NAMESPACE --timeout=600s

# 헬스체크
echo "Running health checks..."
./scripts/health-check.sh --environment=$NEW_ENV

if [ $? -eq 0 ]; then
    echo "Health checks passed. Switching traffic to $NEW_ENV"

    # 서비스 selector 업데이트
    kubectl patch service bodam-backend-service -n $NAMESPACE -p '{"spec":{"selector":{"environment":"'$NEW_ENV'"}}}'
    kubectl patch service bodam-frontend-service -n $NAMESPACE -p '{"spec":{"selector":{"environment":"'$NEW_ENV'"}}}'

    echo "Traffic switched successfully"

    # 이전 환경 정리 (5분 후)
    echo "Scheduling cleanup of previous environment..."
    (sleep 300 && kubectl delete deployment bodam-backend-$CURRENT_ENV bodam-frontend-$CURRENT_ENV -n $NAMESPACE) &

else
    echo "Health checks failed. Rolling back..."
    kubectl delete deployment bodam-backend-$NEW_ENV bodam-frontend-$NEW_ENV -n $NAMESPACE
    exit 1
fi
```

### 2. Kubernetes 배포 매니페스트
```yaml
# infra/k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bodam-backend-ENVIRONMENT_PLACEHOLDER
  namespace: bodam-production
  labels:
    app: bodam-backend
    environment: ENVIRONMENT_PLACEHOLDER
spec:
  replicas: 3
  selector:
    matchLabels:
      app: bodam-backend
      environment: ENVIRONMENT_PLACEHOLDER
  template:
    metadata:
      labels:
        app: bodam-backend
        environment: ENVIRONMENT_PLACEHOLDER
    spec:
      containers:
      - name: backend
        image: IMAGE_PLACEHOLDER
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: bodam-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: bodam-secrets
              key: redis-url
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: bodam-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        readinessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
      imagePullSecrets:
      - name: ghcr-secret
---
apiVersion: v1
kind: Service
metadata:
  name: bodam-backend-service
  namespace: bodam-production
spec:
  selector:
    app: bodam-backend
    environment: blue  # 초기값
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

### 3. 인그레스 설정
```yaml
# infra/k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: bodam-ingress
  namespace: bodam-production
  annotations:
    kubernetes.io/ingress.class: "alb"
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/ssl-redirect: '443'
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:ap-northeast-2:ACCOUNT:certificate/CERTIFICATE-ID
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
spec:
  rules:
  - host: api.bodam.example
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: bodam-backend-service
            port:
              number: 80
  - host: app.bodam.example
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: bodam-frontend-service
            port:
              number: 80
```

## 🗄️ 데이터베이스 관리

### 1. 프로덕션 데이터베이스 설정
```yaml
# infra/terraform/rds.tf
resource "aws_db_instance" "bodam_postgres" {
  identifier = "bodam-production"

  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.r6g.xlarge"

  allocated_storage     = 100
  max_allocated_storage = 1000
  storage_type         = "gp3"
  storage_encrypted    = true

  db_name  = "bodam_production"
  username = "bodam_admin"
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  deletion_protection = true
  skip_final_snapshot = false

  performance_insights_enabled = true
  monitoring_interval         = 60

  tags = {
    Name        = "Bodam Production DB"
    Environment = "production"
  }
}
```

### 2. 데이터베이스 마이그레이션
```bash
#!/bin/bash
# scripts/migrate-production.sh

set -e

echo "Starting production database migration..."

# 백업 생성
kubectl create job --from=cronjob/db-backup db-backup-$(date +%Y%m%d-%H%M%S) -n bodam-production

# 마이그레이션 실행
kubectl run migration-job \
  --image=ghcr.io/your-org/bodam/backend:latest \
  --restart=Never \
  --env="DATABASE_URL=$(kubectl get secret bodam-secrets -n bodam-production -o jsonpath='{.data.database-url}' | base64 -d)" \
  --command -- alembic upgrade head

# 마이그레이션 상태 확인
kubectl wait --for=condition=complete job/migration-job --timeout=300s -n bodam-production

if [ $? -eq 0 ]; then
    echo "Migration completed successfully"
    kubectl delete job migration-job -n bodam-production
else
    echo "Migration failed"
    kubectl logs job/migration-job -n bodam-production
    exit 1
fi
```

## 📊 모니터링 및 로깅

### 1. Prometheus 모니터링
```yaml
# infra/k8s/monitoring/prometheus.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s

    scrape_configs:
    - job_name: 'bodam-backend'
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: bodam-backend

    - job_name: 'bodam-frontend'
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: bodam-frontend

    - job_name: 'postgres'
      static_configs:
      - targets: ['postgres-exporter:9187']

    - job_name: 'redis'
      static_configs:
      - targets: ['redis-exporter:9121']
```

### 2. Grafana 대시보드
```json
{
  "dashboard": {
    "title": "Bodam Production Metrics",
    "panels": [
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m]))",
            "legendFormat": "Error rate"
          }
        ]
      },
      {
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "pg_stat_database_numbackends",
            "legendFormat": "Active connections"
          }
        ]
      }
    ]
  }
}
```

### 3. 로그 수집 (Fluentd)
```yaml
# infra/k8s/logging/fluentd.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
  namespace: logging
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/*bodam*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      format json
      time_format %Y-%m-%dT%H:%M:%S.%NZ
    </source>

    <filter kubernetes.**>
      @type kubernetes_metadata
    </filter>

    <match kubernetes.**>
      @type elasticsearch
      host elasticsearch.logging.svc.cluster.local
      port 9200
      logstash_format true
      logstash_prefix bodam
    </match>
```

## 🔒 보안 설정

### 1. Secret 관리
```bash
# Kubernetes Secrets 생성
kubectl create secret generic bodam-secrets \
  --from-literal=database-url="postgresql://user:pass@host:5432/db" \
  --from-literal=redis-url="redis://host:6379/0" \
  --from-literal=jwt-secret="your-super-secret-key" \
  --from-literal=toss-secret-key="your-toss-secret" \
  -n bodam-production

# TLS 인증서 Secret
kubectl create secret tls bodam-tls \
  --cert=path/to/cert.pem \
  --key=path/to/key.pem \
  -n bodam-production
```

### 2. 네트워크 정책
```yaml
# infra/k8s/security/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: bodam-network-policy
  namespace: bodam-production
spec:
  podSelector:
    matchLabels:
      app: bodam-backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: bodam-frontend
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 5432  # PostgreSQL
    - protocol: TCP
      port: 6379  # Redis
    - protocol: TCP
      port: 443   # HTTPS
```

## 🚨 장애 대응

### 1. 자동 복구 스크립트
```bash
#!/bin/bash
# scripts/auto-recovery.sh

# 헬스체크 실패 시 자동 복구
check_health() {
    local service=$1
    local health_url=$2

    response=$(curl -s -o /dev/null -w "%{http_code}" $health_url)

    if [ $response -eq 200 ]; then
        echo "$service is healthy"
        return 0
    else
        echo "$service is unhealthy (HTTP $response)"
        return 1
    fi
}

# 백엔드 헬스체크
if ! check_health "backend" "https://api.bodam.example/healthz"; then
    echo "Restarting backend pods..."
    kubectl rollout restart deployment/bodam-backend-blue -n bodam-production
    kubectl rollout restart deployment/bodam-backend-green -n bodam-production
fi

# 프론트엔드 헬스체크
if ! check_health "frontend" "https://app.bodam.example/health"; then
    echo "Restarting frontend pods..."
    kubectl rollout restart deployment/bodam-frontend-blue -n bodam-production
    kubectl rollout restart deployment/bodam-frontend-green -n bodam-production
fi
```

### 2. 롤백 절차
```bash
#!/bin/bash
# scripts/rollback.sh

NAMESPACE="bodam-production"
PREVIOUS_VERSION=$1

if [ -z "$PREVIOUS_VERSION" ]; then
    echo "Usage: $0 <previous-version>"
    exit 1
fi

echo "Rolling back to version: $PREVIOUS_VERSION"

# 백엔드 롤백
kubectl set image deployment/bodam-backend-blue \
  backend=ghcr.io/your-org/bodam/backend:$PREVIOUS_VERSION \
  -n $NAMESPACE

kubectl set image deployment/bodam-backend-green \
  backend=ghcr.io/your-org/bodam/backend:$PREVIOUS_VERSION \
  -n $NAMESPACE

# 프론트엔드 롤백
kubectl set image deployment/bodam-frontend-blue \
  frontend=ghcr.io/your-org/bodam/frontend:$PREVIOUS_VERSION \
  -n $NAMESPACE

kubectl set image deployment/bodam-frontend-green \
  frontend=ghcr.io/your-org/bodam/frontend:$PREVIOUS_VERSION \
  -n $NAMESPACE

echo "Rollback initiated. Checking deployment status..."
kubectl rollout status deployment/bodam-backend-blue -n $NAMESPACE
kubectl rollout status deployment/bodam-frontend-blue -n $NAMESPACE
```

## 📈 성능 최적화

### 1. 수평적 확장 (HPA)
```yaml
# infra/k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: bodam-backend-hpa
  namespace: bodam-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: bodam-backend-blue
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 2. 캐싱 전략
```yaml
# Redis 클러스터 설정
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-config
  namespace: bodam-production
data:
  redis.conf: |
    maxmemory 2gb
    maxmemory-policy allkeys-lru
    save 900 1
    save 300 10
    save 60 10000
```

---

이 배포 가이드를 통해 보담 플랫폼의 안정적이고 확장 가능한 프로덕션 환경을 구축할 수 있습니다. 지속적인 모니터링과 개선을 통해 서비스 품질을 유지해 나가세요. 🚀