# 보담(BoDam) 배포 전략 및 인프라 설계

> **작성일**: 2025-10-01
> **대상 환경**: Production
> **주요 기술**: Vercel, DigitalOcean, Kubernetes, NGINX

---

## 📋 목차

1. [전체 배포 아키텍처](#전체-배포-아키텍처)
2. [각 도구의 역할](#각-도구의-역할)
3. [단계별 배포 가이드](#단계별-배포-가이드)
4. [인프라 비용 예상](#인프라-비용-예상)
5. [모니터링 및 운영](#모니터링-및-운영)

---

## 전체 배포 아키텍처

```mermaid
graph TB
    subgraph "사용자"
        U[Web Browser]
        M[Mobile App]
    end

    subgraph "Vercel (Frontend CDN)"
        V1[Next.js App]
        V2[Static Assets]
        V3[Edge Functions]
    end

    subgraph "DigitalOcean Cloud"
        subgraph "Load Balancer"
            LB[DO Load Balancer<br/>SSL Termination]
        end

        subgraph "Kubernetes Cluster"
            subgraph "NGINX Ingress"
                N1[NGINX Ingress Controller]
                N2[Rate Limiting]
                N3[Path Routing]
            end

            subgraph "Backend Services"
                A1[FastAPI Pod 1]
                A2[FastAPI Pod 2]
                A3[FastAPI Pod 3]
                AS[Service: backend-api]
            end

            subgraph "Workers"
                W1[Celery Worker 1]
                W2[Celery Worker 2]
                W3[Celery Beat Scheduler]
            end

            subgraph "Data Layer"
                DB[(PostgreSQL<br/>StatefulSet)]
                RD[(Redis<br/>StatefulSet)]
            end
        end

        subgraph "Managed Services"
            DO_DB[(DO Managed<br/>PostgreSQL)]
            DO_RD[(DO Managed<br/>Redis)]
        end
    end

    subgraph "External APIs"
        E1[Toss Payments]
        E2[Together AI]
        E3[KakaoTalk Biz]
    end

    U --> V1
    M --> V1
    V1 --> LB
    LB --> N1
    N1 --> N2
    N2 --> N3
    N3 --> AS
    AS --> A1
    AS --> A2
    AS --> A3

    A1 --> DB
    A2 --> DB
    A3 --> DB
    A1 --> RD
    A2 --> RD
    A3 --> RD

    W1 --> RD
    W2 --> RD
    W3 --> RD
    W1 --> DB
    W2 --> DB

    A1 -.대안.-> DO_DB
    A2 -.대안.-> DO_DB
    A3 -.대안.-> DO_DB

    A1 --> E1
    A2 --> E2
    W1 --> E2
    W2 --> E3
```

---

## 각 도구의 역할

### 1. **Vercel** 🚀

**역할**: Frontend 전용 호스팅 플랫폼

#### 장점
- ✅ Next.js에 최적화 (Zero-config 배포)
- ✅ 글로벌 CDN (한국 포함 전 세계 엣지 로케이션)
- ✅ Git 연동 자동 배포 (GitHub/GitLab push → 자동 빌드)
- ✅ Preview 배포 (PR마다 테스트 URL 생성)
- ✅ SSL 인증서 자동 발급 및 갱신
- ✅ 무료 플랜으로 시작 가능

#### 담당 범위
- Next.js 애플리케이션 빌드 및 호스팅
- 정적 파일 (이미지, CSS, JS) CDN 제공
- 서버사이드 렌더링 (SSR) 실행

#### 설정 예시
```json
// vercel.json
{
  "version": 2,
  "framework": "nextjs",
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/.next",
  "regions": ["icn1"],  // 서울 리전
  "env": {
    "NEXT_PUBLIC_API_URL": "https://api.bodam.kr"
  }
}
```

#### 비용
- **Hobby**: 무료 (개인 프로젝트)
- **Pro**: $20/월 (상용 서비스)

---

### 2. **DigitalOcean** 🌊

**역할**: 클라우드 인프라 제공자 (AWS/GCP 대체)

#### 장점
- ✅ 저렴한 비용 (AWS 대비 30-50% 절감)
- ✅ Managed Kubernetes (DOKS) 제공
- ✅ Managed Database (PostgreSQL, Redis) 옵션
- ✅ 간단한 UI/UX
- ✅ 한국어 커뮤니티 활성화

#### 담당 범위
- Kubernetes 클러스터 호스팅
- Load Balancer 제공
- Block Storage (영구 볼륨)
- Container Registry (Docker 이미지 저장소)

#### 리소스 구성
```
Kubernetes Cluster:
├── Node Pool (Backend)
│   ├── VM: s-2vcpu-4gb x 3개 = $72/월
│   └── Auto-scaling: 3-5개
├── Load Balancer: $12/월
└── Block Storage (DB): 50GB = $5/월

Managed Services (선택사항):
├── Managed PostgreSQL: $15/월 (1GB RAM)
└── Managed Redis: $15/월 (1GB RAM)
```

---

### 3. **Kubernetes** ☸️

**역할**: 컨테이너 오케스트레이션 플랫폼

#### 왜 Kubernetes?
- ✅ 컨테이너 자동 관리 (재시작, 롤링 업데이트)
- ✅ 수평 확장 (트래픽 증가 시 자동 Pod 추가)
- ✅ 선언적 설정 (YAML로 인프라 정의)
- ✅ 서비스 디스커버리 (Pod 간 통신 자동화)
- ✅ Health Check 및 Self-healing

#### 담당 범위
- FastAPI, PostgreSQL, Redis, Celery를 Pod로 실행
- 서비스 간 네트워킹 관리
- 영구 볼륨 관리 (DB 데이터)
- Auto-scaling (HPA: Horizontal Pod Autoscaler)

#### 주요 리소스
```
Pods:
├── fastapi-backend (3 replicas)
├── celery-worker (2 replicas)
├── celery-beat (1 replica)
├── postgresql (1 replica, StatefulSet)
└── redis (1 replica, StatefulSet)

Services:
├── fastapi-service (ClusterIP)
├── postgresql-service (ClusterIP)
└── redis-service (ClusterIP)

Ingress:
└── bodam-ingress (NGINX)
```

---

### 4. **NGINX Ingress Controller** 🔀

**역할**: Kubernetes 내부 리버스 프록시 + 로드 밸런서

#### 왜 NGINX Ingress?
- ✅ 외부 요청을 Kubernetes Service로 라우팅
- ✅ SSL/TLS 종료 (Let's Encrypt 자동 인증서)
- ✅ Rate Limiting (DDoS 방지)
- ✅ Path 기반 라우팅 (/api → Backend, /admin → Admin)
- ✅ WebSocket 지원 (`/ws/notifications`)

#### 담당 범위
- HTTP/HTTPS 요청 라우팅
- SSL 인증서 관리
- Rate Limiting (IP당 100 req/min)
- CORS 헤더 추가
- Access Logging

#### 설정 예시
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: bodam-ingress
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/enable-cors: "true"
spec:
  tls:
  - hosts:
    - api.bodam.kr
    secretName: api-bodam-kr-tls
  rules:
  - host: api.bodam.kr
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: fastapi-service
            port:
              number: 8000
```

---

### 5. **API Gateway** 🚪

**결론**: **사용하지 않음 (불필요)**

#### 이유
- NGINX Ingress가 이미 API Gateway 역할 수행
- 추가 레이어는 레이턴시 증가 및 비용 증가
- 현재 프로젝트 규모에는 과도한 복잡성

#### 언제 필요한가?
- 마이크로서비스가 10개 이상일 때
- GraphQL Federation이 필요할 때
- API 버전 관리가 복잡할 때

**현재 아키텍처에서는 제외**

---

## 단계별 배포 가이드

### Phase 1: Frontend 배포 (Vercel)

#### 1-1. Vercel 프로젝트 생성
```bash
# Vercel CLI 설치
npm i -g vercel

# 프로젝트 연결
cd /home/donghee/bodam
vercel login
vercel link

# 환경 변수 설정
vercel env add NEXT_PUBLIC_API_URL production
# 입력: https://api.bodam.kr
```

#### 1-2. GitHub Actions 설정
```yaml
# .github/workflows/deploy-frontend.yml
name: Deploy Frontend
on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: ./frontend
```

#### 1-3. 배포 확인
- 배포 URL: `https://bodam.vercel.app`
- 커스텀 도메인: `https://bodam.kr`

---

### Phase 2: DigitalOcean Kubernetes 설정

#### 2-1. Kubernetes 클러스터 생성
```bash
# doctl CLI 설치 (Ubuntu/WSL)
snap install doctl
doctl auth init

# 클러스터 생성 (서울 리전)
doctl kubernetes cluster create bodam-prod \
  --region sgp1 \
  --version 1.28.2-do.0 \
  --node-pool "name=backend-pool;size=s-2vcpu-4gb;count=3;auto-scale=true;min-nodes=2;max-nodes=5"

# kubeconfig 다운로드
doctl kubernetes cluster kubeconfig save bodam-prod

# 클러스터 확인
kubectl cluster-info
kubectl get nodes
```

#### 2-2. Container Registry 설정
```bash
# Registry 생성
doctl registry create bodam-registry

# Docker 로그인
doctl registry login

# Backend 이미지 빌드 및 푸시
cd backend
docker build -t registry.digitalocean.com/bodam-registry/backend:v1.0.0 .
docker push registry.digitalocean.com/bodam-registry/backend:v1.0.0
```

---

### Phase 3: NGINX Ingress 설치

#### 3-1. Helm으로 NGINX Ingress 설치
```bash
# Helm 설치
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# NGINX Ingress Chart 추가
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

# NGINX Ingress 설치
helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer
```

#### 3-2. cert-manager 설치 (SSL)
```bash
# cert-manager 설치
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Let's Encrypt Issuer 생성
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@bodam.kr
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

---

### Phase 4: Backend 배포

#### 4-1. Namespace 생성
```bash
kubectl create namespace bodam
```

#### 4-2. Secrets 생성
```bash
# Database credentials
kubectl create secret generic db-credentials \
  --from-literal=username=bodam_user \
  --from-literal=password=SECURE_PASSWORD_HERE \
  --from-literal=url=postgresql://bodam_user:SECURE_PASSWORD_HERE@postgresql:5432/bodam \
  -n bodam

# API Keys
kubectl create secret generic api-keys \
  --from-literal=toss_secret_key=YOUR_TOSS_KEY \
  --from-literal=together_api_key=YOUR_TOGETHER_KEY \
  -n bodam
```

#### 4-3. 배포 YAML 적용
```bash
# 모든 리소스 배포
kubectl apply -f infra/k8s/deployment.yaml -n bodam
kubectl apply -f infra/k8s/ingress.yaml -n bodam

# 배포 상태 확인
kubectl get pods -n bodam
kubectl get svc -n bodam
kubectl get ingress -n bodam
```

#### 4-4. 도메인 연결
```bash
# Load Balancer IP 확인
kubectl get svc -n ingress-nginx

# DNS 설정 (DigitalOcean DNS 또는 외부 DNS)
# A Record: api.bodam.kr → EXTERNAL-IP
```

---

## 인프라 비용 예상

### 월간 예상 비용 (Production)

| 항목 | 서비스 | 스펙 | 비용 (USD) |
|------|--------|------|------------|
| **Frontend** | Vercel Pro | Unlimited bandwidth | $20 |
| **Kubernetes Nodes** | DO Droplets | s-2vcpu-4gb x 3 | $72 |
| **Load Balancer** | DO LB | 1개 | $12 |
| **Block Storage** | DO Volumes | 50GB | $5 |
| **Container Registry** | DO Registry | 5GB | $5 |
| **Managed PostgreSQL** | DO Database | db-s-1vcpu-1gb | $15 |
| **Managed Redis** | DO Database | db-s-1vcpu-1gb | $15 |
| **도메인** | Namecheap | .kr 도메인 | $3 |
| **모니터링** | Grafana Cloud | Free tier | $0 |
| **Total** | | | **$147/월** |

### 비용 최적화 옵션

#### Option 1: Self-hosted DB (비용 절감)
- Managed DB 대신 Kubernetes StatefulSet 사용
- **절감액**: -$30/월
- **최종 비용**: $117/월

#### Option 2: 개발 단계 (최소 비용)
- Vercel Hobby (무료)
- Kubernetes Nodes: 1개
- DB: StatefulSet (무료)
- **최종 비용**: $29/월

---

## 배포 플로우

```mermaid
sequenceDiagram
    participant Dev as 개발자
    participant Git as GitHub
    participant Vercel
    participant GHA as GitHub Actions
    participant DO as DigitalOcean Registry
    participant K8s as Kubernetes

    rect rgb(200, 220, 250)
        Note over Dev,Vercel: Frontend 배포
        Dev->>Git: git push origin main
        Git->>Vercel: Webhook trigger
        Vercel->>Vercel: Build Next.js
        Vercel->>Vercel: Deploy to CDN
        Vercel-->>Dev: Deploy success
    end

    rect rgb(220, 250, 220)
        Note over Dev,K8s: Backend 배포
        Dev->>Git: git push origin main
        Git->>GHA: Trigger workflow
        GHA->>GHA: Build Docker image
        GHA->>DO: Push to registry
        GHA->>K8s: kubectl apply
        K8s->>K8s: Rolling update
        K8s-->>Dev: Deployment success
    end
```

---

## 모니터링 및 운영

### 1. Health Check 엔드포인트

```python
# backend/src/api/health.py
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }
```

### 2. Kubernetes 모니터링

```bash
# Pod 상태 확인
kubectl get pods -n bodam

# 로그 확인
kubectl logs -f deployment/fastapi-backend -n bodam

# 리소스 사용량
kubectl top pods -n bodam
kubectl top nodes
```

### 3. Prometheus + Grafana

```bash
# Prometheus 설치
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace

# Grafana 접속
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# http://localhost:3000 (admin/prom-operator)
```

### 4. 로그 수집 (Loki)

```bash
# Loki 설치
helm repo add grafana https://grafana.github.io/helm-charts
helm install loki grafana/loki-stack -n monitoring

# Grafana에서 Loki 데이터소스 추가
# http://loki:3100
```

---

## 보안 체크리스트

### Kubernetes 보안

- [ ] RBAC 활성화 (Role-based Access Control)
- [ ] Network Policy 설정 (Pod 간 통신 제한)
- [ ] Secret 암호화 (etcd encryption)
- [ ] Private Container Registry 사용
- [ ] Image 취약점 스캔 (Trivy)
- [ ] Pod Security Standards 적용

### Application 보안

- [ ] HTTPS 강제 (HTTP → HTTPS 리다이렉트)
- [ ] Rate Limiting 활성화
- [ ] CORS 설정 (특정 도메인만 허용)
- [ ] SQL Injection 방지 (SQLAlchemy ORM)
- [ ] XSS 방지 (React 자동 이스케이핑)
- [ ] 환경 변수로 비밀 관리 (절대 코드에 하드코딩 금지)

---

## Disaster Recovery

### 백업 전략

```bash
# PostgreSQL 백업 (매일 자정)
kubectl create cronjob pg-backup \
  --image=postgres:15 \
  --schedule="0 0 * * *" \
  -- pg_dump -h postgresql -U bodam_user bodam > /backups/$(date +%Y%m%d).sql

# DigitalOcean Spaces로 업로드
s3cmd put /backups/*.sql s3://bodam-backups/
```

### 복구 절차

1. Database 복구
```bash
kubectl exec -it postgresql-0 -- psql -U bodam_user -d bodam < backup.sql
```

2. Application 롤백
```bash
kubectl rollout undo deployment/fastapi-backend -n bodam
```

---

## CI/CD 파이프라인

### GitHub Actions 예시

```yaml
# .github/workflows/deploy-backend.yml
name: Deploy Backend to Kubernetes

on:
  push:
    branches: [main]
    paths:
      - 'backend/**'

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: |
          cd backend
          docker build -t registry.digitalocean.com/bodam-registry/backend:${{ github.sha }} .

      - name: Push to Registry
        run: |
          echo ${{ secrets.DO_REGISTRY_TOKEN }} | docker login registry.digitalocean.com -u ${{ secrets.DO_REGISTRY_USER }} --password-stdin
          docker push registry.digitalocean.com/bodam-registry/backend:${{ github.sha }}

      - name: Deploy to Kubernetes
        run: |
          echo ${{ secrets.KUBECONFIG }} | base64 -d > kubeconfig
          export KUBECONFIG=kubeconfig
          kubectl set image deployment/fastapi-backend fastapi=registry.digitalocean.com/bodam-registry/backend:${{ github.sha }} -n bodam
          kubectl rollout status deployment/fastapi-backend -n bodam
```

---

## 트러블슈팅

### 자주 발생하는 문제

#### 1. Pod가 시작되지 않음
```bash
# 원인 확인
kubectl describe pod <pod-name> -n bodam

# 흔한 원인:
# - 이미지 Pull 실패 → Registry 인증 확인
# - Health Check 실패 → /health 엔드포인트 확인
# - 리소스 부족 → kubectl top nodes
```

#### 2. Ingress가 작동하지 않음
```bash
# Ingress 상태 확인
kubectl get ingress -n bodam
kubectl describe ingress bodam-ingress -n bodam

# NGINX Logs 확인
kubectl logs -n ingress-nginx deployment/nginx-ingress-controller
```

#### 3. Database 연결 실패
```bash
# PostgreSQL Pod 확인
kubectl exec -it postgresql-0 -n bodam -- psql -U bodam_user -d bodam

# 연결 테스트
kubectl run -it --rm debug --image=postgres:15 --restart=Never -- psql -h postgresql.bodam.svc.cluster.local -U bodam_user -d bodam
```

---

## 다음 단계

### Phase 5: 고급 기능 추가

1. **Horizontal Pod Autoscaler (HPA)**
```bash
kubectl autoscale deployment fastapi-backend --cpu-percent=70 --min=3 --max=10 -n bodam
```

2. **Redis Cluster** (고가용성)
```bash
helm install redis bitnami/redis-cluster -n bodam
```

3. **CDN for API** (CloudFlare)
- API 응답 캐싱
- DDoS 방어

4. **Blue-Green Deployment**
- 무중단 배포
- Canary 릴리즈

---

## 참고 자료

- [DigitalOcean Kubernetes Docs](https://docs.digitalocean.com/products/kubernetes/)
- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [Vercel Deployment Docs](https://vercel.com/docs)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)

---

**문서 버전**: 1.0.0
**최종 업데이트**: 2025-10-01
**작성자**: Claude Sonnet 4.5
