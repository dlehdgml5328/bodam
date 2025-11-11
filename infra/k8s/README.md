# 보담 플랫폼 K8s 배포 가이드

로컬 개발 환경(`docker-compose.dev.yml`)과 동일한 구조로 Kubernetes에 배포합니다.

## 📐 아키텍처

### 로컬 개발 환경과 동일한 구조

```
┌─────────────────────────────────────────────────┐
│                  Load Balancer                  │
│               (Kong / Nginx Ingress)            │
└─────────────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌─────▼─────┐ ┌─────▼──────┐
│   Backend    │ │  Celery   │ │  Celery    │
│   (FastAPI)  │ │  Worker   │ │  Worker    │
│   x3 Pods    │ │  (Main)   │ │  (News)    │
└───────┬──────┘ └─────┬─────┘ └─────┬──────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌─────▼─────┐ ┌─────▼──────┐
│ Redis Cache  │ │Redis Queue│ │Redis Semant│
│   (LRU)      │ │ (AOF+RDB) │ │  (Vector)  │
│  512MB       │ │    1GB    │ │    2GB     │
└──────────────┘ └─────┬─────┘ └────────────┘
                       │
                 ┌─────▼─────┐
                 │ PostgreSQL│
                 │ (pgvector)│
                 └───────────┘
```

## 🗂️ 디렉토리 구조

```
infra/k8s/
├── redis/
│   ├── redis-cache-deployment.yaml      # 캐시용 Redis (LRU)
│   ├── redis-queue-deployment.yaml      # Celery 브로커 (영속성)
│   └── redis-semantic-deployment.yaml   # Vector Store (Redis Stack)
├── backend/
│   ├── backend-deployment-v2.yaml       # FastAPI (Redis 3개 분리)
│   ├── configmap.yaml                   # 환경 설정
│   ├── hpa.yaml                         # Auto Scaling
│   └── ingress.yaml                     # Ingress 설정
├── celery/
│   ├── celery-worker-deployment.yaml    # 메인 워커
│   ├── celery-worker-news-deployment.yaml  # 뉴스 매칭 워커
│   ├── celery-beat-deployment.yaml      # 스케줄러
│   └── celery-worker-hpa.yaml           # Worker Auto Scaling
├── observability/
│   ├── prometheus/                      # 메트릭 수집
│   ├── grafana/                         # 대시보드
│   └── alertmanager/                    # 알림
├── deploy-all.sh                        # 통합 배포 스크립트
└── README.md                            # 이 파일
```

## 🚀 배포 방법

### 1. 사전 준비

#### 필수 도구 설치
```bash
# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# doctl (DigitalOcean CLI)
cd ~
wget https://github.com/digitalocean/doctl/releases/download/v1.100.0/doctl-1.100.0-linux-amd64.tar.gz
tar xf ~/doctl-1.100.0-linux-amd64.tar.gz
sudo mv ~/doctl /usr/local/bin
```

#### Kubernetes 클러스터 인증
```bash
# DigitalOcean 인증
doctl auth init

# 클러스터 kubeconfig 다운로드
doctl kubernetes cluster kubeconfig save <cluster-id>

# 연결 확인
kubectl cluster-info
```

### 2. Secrets 생성

```bash
# 환경 변수 준비
export DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/bodam"
export JWT_SECRET_KEY="your-jwt-secret-key"
export TOGETHER_AI_API_KEY="your-together-ai-key"
export NAVER_CLIENT_ID="your-naver-client-id"
export NAVER_CLIENT_SECRET="your-naver-client-secret"
export YOUTUBE_API_KEY="your-youtube-api-key"
export TOSS_CLIENT_KEY="your-toss-client-key"
export TOSS_SECRET_KEY="your-toss-secret-key"

# Secrets 생성 (Preview 환경)
kubectl create secret generic bodam-secrets \
  --from-literal=database-url=$DATABASE_URL \
  --from-literal=jwt-secret=$JWT_SECRET_KEY \
  --from-literal=together-api-key=$TOGETHER_AI_API_KEY \
  --from-literal=naver-client-id=$NAVER_CLIENT_ID \
  --from-literal=naver-client-secret=$NAVER_CLIENT_SECRET \
  --from-literal=youtube-api-key=$YOUTUBE_API_KEY \
  --from-literal=toss-client-key=$TOSS_CLIENT_KEY \
  --from-literal=toss-secret-key=$TOSS_SECRET_KEY \
  -n bodam-preview

# Production 환경
kubectl create secret generic bodam-secrets \
  --from-literal=database-url=$DATABASE_URL \
  --from-literal=jwt-secret=$JWT_SECRET_KEY \
  --from-literal=together-api-key=$TOGETHER_AI_API_KEY \
  --from-literal=naver-client-id=$NAVER_CLIENT_ID \
  --from-literal=naver-client-secret=$NAVER_CLIENT_SECRET \
  --from-literal=youtube-api-key=$YOUTUBE_API_KEY \
  --from-literal=toss-client-key=$TOSS_CLIENT_KEY \
  --from-literal=toss-secret-key=$TOSS_SECRET_KEY \
  -n bodam-prod
```

### 3. 통합 배포 스크립트 실행

```bash
cd infra/k8s

# Preview 환경 배포
./deploy-all.sh preview

# Production 환경 배포
./deploy-all.sh production
```

### 4. 수동 배포 (단계별)

```bash
NAMESPACE=bodam-preview

# 1. 네임스페이스 생성
kubectl create namespace $NAMESPACE

# 2. Redis 3개 배포
kubectl apply -f redis/redis-cache-deployment.yaml -n $NAMESPACE
kubectl apply -f redis/redis-queue-deployment.yaml -n $NAMESPACE
kubectl apply -f redis/redis-semantic-deployment.yaml -n $NAMESPACE

# 3. Backend 배포
kubectl apply -f backend/backend-deployment-v2.yaml -n $NAMESPACE

# 4. Celery Workers 배포
kubectl apply -f celery/celery-worker-deployment.yaml -n $NAMESPACE
kubectl apply -f celery/celery-worker-news-deployment.yaml -n $NAMESPACE
kubectl apply -f celery/celery-beat-deployment.yaml -n $NAMESPACE

# 5. HPA 설정
kubectl apply -f backend/hpa.yaml -n $NAMESPACE
kubectl apply -f celery/celery-worker-hpa.yaml -n $NAMESPACE

# 6. Ingress 설정
kubectl apply -f backend/ingress.yaml -n $NAMESPACE
```

## 🔍 상태 확인

### Pod 상태
```bash
kubectl get pods -n bodam-preview
kubectl get pods -n bodam-preview -l app=bodam-backend
kubectl get pods -n bodam-preview -l component=worker
```

### Deployment 상태
```bash
kubectl get deployments -n bodam-preview
kubectl rollout status deployment/bodam-backend -n bodam-preview
```

### Service 및 Ingress
```bash
kubectl get services -n bodam-preview
kubectl get ingress -n bodam-preview
```

### 로그 확인
```bash
# Backend 로그
kubectl logs -f deployment/bodam-backend -n bodam-preview

# Celery Worker 로그
kubectl logs -f deployment/celery-worker -n bodam-preview

# 특정 Pod 로그
kubectl logs -f <pod-name> -n bodam-preview
```

### Health Check
```bash
# Port Forward
kubectl port-forward service/bodam-backend-service 8080:80 -n bodam-preview

# Health Check
curl http://localhost:8080/health
```

## 📊 리소스 요구사항

### 최소 클러스터 사양
- **노드**: 3개 (HA)
- **노드당 리소스**: 2 vCPU, 4GB RAM
- **총 리소스**: 6 vCPU, 12GB RAM

### 서비스별 리소스

| 서비스 | Replicas | CPU Request | Memory Request | CPU Limit | Memory Limit |
|--------|----------|-------------|----------------|-----------|--------------|
| Backend | 3 | 250m | 512Mi | 500m | 1Gi |
| Celery Worker | 2 | 250m | 512Mi | 500m | 1Gi |
| Celery News | 1 | 500m | 1Gi | 1000m | 2Gi |
| Celery Beat | 1 | 100m | 128Mi | 200m | 256Mi |
| Redis Cache | 1 | 100m | 256Mi | 200m | 512Mi |
| Redis Queue | 1 | 200m | 512Mi | 500m | 1Gi |
| Redis Semantic | 1 | 200m | 1Gi | 500m | 2Gi |

**총 요청**: ~2.6 vCPU, ~5GB RAM
**총 제한**: ~4.4 vCPU, ~9.7GB RAM

### 스토리지
- **Redis Queue PVC**: 10GB
- **Redis Semantic PVC**: 20GB
- **StorageClass**: `do-block-storage` (DigitalOcean)

## 🔄 롤백

### Deployment 롤백
```bash
# 이전 버전으로 롤백
kubectl rollout undo deployment/bodam-backend -n bodam-preview

# 특정 revision으로 롤백
kubectl rollout history deployment/bodam-backend -n bodam-preview
kubectl rollout undo deployment/bodam-backend --to-revision=2 -n bodam-preview
```

## 🧹 정리

### 전체 삭제
```bash
kubectl delete namespace bodam-preview
kubectl delete namespace bodam-prod
```

### 특정 서비스만 삭제
```bash
kubectl delete -f backend/backend-deployment-v2.yaml -n bodam-preview
kubectl delete -f celery/ -n bodam-preview
```

## 🛡️ 보안 체크리스트

- [ ] Secrets 생성 및 확인
- [ ] Docker Registry 인증 (regcred)
- [ ] Network Policy 설정 (필요시)
- [ ] RBAC 설정 확인
- [ ] Ingress TLS 인증서 설정
- [ ] 환경 변수 민감 정보 확인

## 📝 주요 차이점: 로컬 vs K8s

| 항목 | 로컬 (docker-compose.dev.yml) | K8s |
|------|-------------------------------|-----|
| Redis | 3개 분리 (동일) | 3개 분리 (동일) |
| Celery Workers | 3개 분리 (동일) | 3개 분리 (동일) |
| Backend Replicas | 1개 | 3개 (HA) |
| 스토리지 | Docker Volume | PersistentVolume |
| 네트워크 | Bridge | ClusterIP + Ingress |
| 모니터링 | 로컬 Grafana | K8s Prometheus/Grafana |
| Auto Scaling | 없음 | HPA 지원 |

## 🚨 트러블슈팅

### Pod가 Pending 상태
```bash
kubectl describe pod <pod-name> -n bodam-preview
```
**원인**: 리소스 부족, PVC 마운트 실패
**해결**: 노드 스케일링 또는 리소스 요청 조정

### CrashLoopBackOff
```bash
kubectl logs <pod-name> -n bodam-preview --previous
```
**원인**: 애플리케이션 시작 실패, 환경 변수 누락
**해결**: 로그 확인 후 Secrets/ConfigMap 수정

### ImagePullBackOff
```bash
kubectl describe pod <pod-name> -n bodam-preview
```
**원인**: Docker Registry 인증 실패
**해결**: regcred Secret 확인 및 재생성

## 📚 참고 문서

- [Kubernetes 공식 문서](https://kubernetes.io/docs/)
- [DigitalOcean Kubernetes](https://docs.digitalocean.com/products/kubernetes/)
- [보담 프로젝트 구조](../../CLAUDE.md)
- [로컬 개발 환경](../../docker-compose.dev.yml)

---

**작성일**: 2025-11-10
**버전**: 2.0.0 (Redis 3개 분리, Celery 분리)
**관리**: 보담 플랫폼 개발팀
