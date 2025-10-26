# 보담 배포 체크리스트

전체 배포 프로세스를 단계별로 안내합니다.

## 📋 목차

1. [사전 준비](#사전-준비)
2. [로컬 테스트](#로컬-테스트)
3. [GitHub Secrets 설정](#github-secrets-설정)
4. [DigitalOcean 클러스터 생성](#digitalocean-클러스터-생성)
5. [첫 배포](#첫-배포)
6. [배포 후 확인](#배포-후-확인)

---

## 사전 준비

### 필수 도구 설치

```bash
# macOS
brew install doctl kubectl helm gh

# Linux
snap install doctl kubectl helm gh
```

### 계정 준비
- [ ] GitHub 계정 (레포지토리 권한)
- [ ] DigitalOcean 계정 (결제 수단 등록)
- [ ] Vercel 계정 (Frontend 배포용)
- [ ] Together AI 계정 (AI API)
- [ ] Slack 워크스페이스 (알림용, 선택사항)

---

## 로컬 테스트

### 1. 환경 변수 설정

```bash
# backend/.env 파일 생성
cp backend/.env.example backend/.env

# 필수 값 설정
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret
YOUTUBE_API_KEY=your_youtube_api_key
TOGETHER_AI_API_KEY=your_together_ai_key
```

### 2. Docker Compose로 전체 스택 시작

```bash
# 전체 서비스 시작
docker compose -f docker-compose.dev.yml up -d

# 로그 확인
docker compose -f docker-compose.dev.yml logs -f backend kong

# 헬스체크
curl http://localhost:8001/health  # Kong을 통한 백엔드 접근
curl http://localhost:8000/health  # 백엔드 직접 접근
curl http://localhost:8002/status  # Kong Admin API
```

### 3. API 테스트

```bash
# Kong Proxy를 통한 API 호출
curl http://localhost:8001/api/fire-stations/search

# Rate Limiting 테스트
for i in {1..10}; do curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8001/api/fire-stations/search; done

# CORS 테스트
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS \
     http://localhost:8001/api/fire-stations/search
```

### 4. Frontend 테스트

```bash
# 브라우저에서 접속
open http://localhost:3000

# Kong을 통해 API 호출 확인
# 브라우저 개발자 도구에서 Network 탭 확인
# X-Kong-Request-ID 헤더가 있는지 확인
```

### 로컬 테스트 체크리스트
- [ ] 모든 서비스가 healthy 상태
- [ ] Backend API 응답 정상
- [ ] Kong을 통한 프록시 동작
- [ ] Frontend에서 Backend API 호출 성공
- [ ] Rate Limiting 동작 확인
- [ ] CORS 헤더 정상 동작

---

## GitHub Secrets 설정

상세 가이드: [SETUP_SECRETS.md](./SETUP_SECRETS.md)

### 필수 Secrets (최소 구성)

```bash
# GitHub CLI로 빠른 설정
gh secret set DIGITALOCEAN_TOKEN
gh secret set DATABASE_URL
gh secret set JWT_SECRET_KEY
gh secret set TOGETHER_AI_API_KEY
gh secret set ADMIN_SECRET_KEY
gh secret set VERCEL_TOKEN
gh secret set VERCEL_ORG_ID
gh secret set VERCEL_PROJECT_ID
```

### Secrets 확인

```bash
gh secret list

# 출력 예시:
# DIGITALOCEAN_TOKEN              Updated 2024-01-15
# DATABASE_URL                    Updated 2024-01-15
# JWT_SECRET_KEY                  Updated 2024-01-15
# ...
```

### 체크리스트
- [ ] 모든 필수 Secrets 설정 완료
- [ ] `gh secret list`로 확인

---

## DigitalOcean 클러스터 생성

### 1. doctl 인증

```bash
doctl auth init
# DIGITALOCEAN_TOKEN 입력
```

### 2. Production 클러스터 생성

```bash
# 클러스터 생성 (약 5-10분 소요)
doctl kubernetes cluster create bodam-prod \
  --region sgp1 \
  --version 1.28.2-do.0 \
  --node-pool "name=app-pool;size=s-2vcpu-4gb;count=2;auto-scale=true;min-nodes=1;max-nodes=3" \
  --wait

# 클러스터 ID 확인 및 저장
CLUSTER_ID=$(doctl kubernetes cluster list --format ID --no-header)
echo $CLUSTER_ID

# GitHub Secret에 저장
gh secret set DIGITALOCEAN_CLUSTER_ID_PROD -b"$CLUSTER_ID"
```

### 3. Preview 클러스터 (선택사항)

**옵션 A: 별도 클러스터 생성** (추가 비용 발생)
```bash
doctl kubernetes cluster create bodam-preview \
  --region sgp1 \
  --version 1.28.2-do.0 \
  --node-pool "name=app-pool;size=s-2vcpu-4gb;count=1" \
  --wait

PREVIEW_CLUSTER_ID=$(doctl kubernetes cluster list --format ID,Name --no-header | grep preview | awk '{print $1}')
gh secret set DIGITALOCEAN_CLUSTER_ID_PREVIEW -b"$PREVIEW_CLUSTER_ID"
```

**옵션 B: Production 클러스터 공유** (비용 절약, 권장)
```bash
# Production 클러스터 ID를 Preview로도 사용
gh secret set DIGITALOCEAN_CLUSTER_ID_PREVIEW -b"$CLUSTER_ID"
```

### 4. kubeconfig 설정

```bash
# Production 클러스터
doctl kubernetes cluster kubeconfig save bodam-prod

# 연결 확인
kubectl get nodes
```

### 5. Container Registry 생성

```bash
# Registry 생성
doctl registry create bodam

# Docker 로그인
doctl registry login

# Registry URL 확인
doctl registry get bodam
# URL: registry.digitalocean.com/bodam
```

### 체크리스트
- [ ] 클러스터 생성 완료
- [ ] `kubectl get nodes` 정상 동작
- [ ] Container Registry 생성
- [ ] Cluster ID를 GitHub Secrets에 저장

---

## 첫 배포

### 1. Database 준비

**옵션 A: DigitalOcean Managed Database** (권장)
```bash
# Web Console에서 생성
# 1. Databases → Create Database
# 2. PostgreSQL 16
# 3. Region: Singapore (sgp1)
# 4. Plan: Basic ($15/month)

# Connection String 복사 후 GitHub Secret 업데이트
gh secret set DATABASE_URL
```

**옵션 B: Kubernetes에 PostgreSQL 배포**
```bash
kubectl create namespace bodam-prod

# PostgreSQL 배포
kubectl apply -f infra/k8s/database/postgres-statefulset.yaml -n bodam-prod

# Database URL 설정
# postgresql+asyncpg://bodam:password@postgresql.bodam-prod.svc.cluster.local:5432/bodam
```

### 2. 첫 배포 트리거

```bash
# wonuk 브랜치로 Preview 배포 테스트
git checkout wonuk
git pull origin wonuk

# 변경사항 push (또는 빈 커밋)
git commit --allow-empty -m "chore: trigger first deployment"
git push origin wonuk

# GitHub Actions 확인
gh run list
gh run view  # 최근 실행 상세 보기
gh run watch  # 실시간 로그
```

### 3. 배포 진행 상황 모니터링

```bash
# GitHub Actions에서 확인
# https://github.com/YOUR_ORG/bodam/actions

# 또는 CLI로 실시간 확인
gh run watch
```

### 4. API URL 확인 및 설정

```bash
# LoadBalancer IP 확인 (배포 완료 후)
kubectl get svc -n bodam-preview

# NGINX Ingress LoadBalancer IP
EXTERNAL_IP=$(kubectl get svc nginx-ingress-service -n bodam-preview -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "API URL: http://$EXTERNAL_IP"

# GitHub Secrets 업데이트
gh secret set PREVIEW_API_URL -b"http://$EXTERNAL_IP"
```

### 5. Production 배포

```bash
# Preview 테스트 완료 후
git checkout donghee
git merge wonuk
git push origin donghee

# 배포 확인
gh run watch

# Production API URL 설정
PROD_IP=$(kubectl get svc nginx-ingress-service -n bodam-prod -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
gh secret set PRODUCTION_API_URL -b"http://$PROD_IP"
gh secret set NEXT_PUBLIC_API_URL -b"http://$PROD_IP"
```

---

## 배포 후 확인

### 1. Backend 상태 확인

```bash
# Pod 상태
kubectl get pods -n bodam-prod

# 출력 예시:
# NAME                             READY   STATUS    RESTARTS   AGE
# bodam-backend-xxxxxxxxx-xxxxx    1/1     Running   0          5m
# kong-gateway-xxxxxxxxx-xxxxx     1/1     Running   0          5m

# 로그 확인
kubectl logs -f deployment/bodam-backend -n bodam-prod
kubectl logs -f deployment/kong-gateway -n bodam-prod
```

### 2. Health Check

```bash
# API URL 확인
echo $PROD_IP

# Health check
curl http://$PROD_IP/health

# Kong을 통한 API 호출
curl http://$PROD_IP/api/fire-stations/search
```

### 3. Frontend 확인

```bash
# Vercel 배포 URL 확인
# GitHub Actions 로그 또는 Vercel 대시보드에서 확인

# 브라우저에서 접속
# Frontend가 Backend API를 정상적으로 호출하는지 확인
```

### 4. Kong Gateway 상태 확인

```bash
# Kong Admin API 접근 (포트 포워딩)
kubectl port-forward -n bodam-prod svc/kong-admin-service 8001:8001 &

# Kong 상태 확인
curl http://localhost:8001/status

# 서비스 확인
curl http://localhost:8001/services

# 라우트 확인
curl http://localhost:8001/routes

# 포트 포워딩 종료
killall kubectl
```

### 5. 모니터링 대시보드

```bash
# Grafana 접근 (로컬에 이미 설정된 경우)
open http://localhost:3001

# 또는 Kubernetes에 Grafana 배포한 경우
kubectl port-forward -n observability svc/grafana 3000:3000
open http://localhost:3000
```

### 체크리스트
- [ ] 모든 Pod가 Running 상태
- [ ] Health check 성공 (200 OK)
- [ ] API 호출 정상 동작
- [ ] Frontend에서 Backend 연결 확인
- [ ] Kong Gateway 정상 동작
- [ ] Rate Limiting 동작 확인
- [ ] Grafana 대시보드 확인 (선택)

---

## 문제 해결

### Pod가 Pending 상태

```bash
# Pod 상세 정보
kubectl describe pod <pod-name> -n bodam-prod

# 원인:
# - 리소스 부족: 노드 추가 또는 리소스 요청량 조정
# - 이미지 Pull 실패: Secret 확인
```

### CrashLoopBackOff

```bash
# 로그 확인
kubectl logs <pod-name> -n bodam-prod --previous

# 원인:
# - 환경 변수 누락: Secrets 확인
# - DB 연결 실패: DATABASE_URL 확인
```

### LoadBalancer IP가 할당되지 않음

```bash
# Service 확인
kubectl describe svc nginx-ingress-service -n bodam-prod

# DigitalOcean에서 LoadBalancer 생성 확인
# Web Console → Networking → Load Balancers
```

### GitHub Actions 실패

```bash
# 로그 확인
gh run view --log-failed

# 일반적인 원인:
# - Secrets 누락
# - 클러스터 연결 실패
# - 이미지 빌드 실패
```

---

## 다음 단계

### 도메인 설정 (선택사항)

1. **DNS 설정**
   ```bash
   # LoadBalancer IP 확인
   echo $PROD_IP

   # DNS A 레코드 추가
   # api.bodam.kr → $PROD_IP
   ```

2. **TLS 인증서 (Let's Encrypt)**
   ```bash
   # cert-manager 설치
   kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

   # TLS 인증서 설정 적용
   kubectl apply -f infra/k8s/nginx/tls-certificate.yaml
   ```

3. **Secrets 업데이트**
   ```bash
   gh secret set PRODUCTION_API_URL -b"https://api.bodam.kr"
   gh secret set NEXT_PUBLIC_API_URL -b"https://api.bodam.kr"
   ```

### 모니터링 강화

```bash
# Prometheus + Grafana 배포
kubectl create namespace observability
kubectl apply -f infra/k8s/observability/
```

### Blue-Green 배포 설정

```bash
# Blue-Green 배포 매니페스트
kubectl apply -f infra/k8s/backend/blue-green/
```

---

## 참고 자료

- [SETUP_SECRETS.md](./SETUP_SECRETS.md) - GitHub Secrets 상세 가이드
- [DEPLOYMENT.md](./DEPLOYMENT.md) - CI/CD 파이프라인 상세
- [docs/DEPLOYMENT_GUIDE.md](./docs/DEPLOYMENT_GUIDE.md) - Kong Gateway 마이그레이션
- [docs/DEPLOYMENT-WITH-API-GATEWAY.md](./docs/DEPLOYMENT-WITH-API-GATEWAY.md) - 전체 아키텍처

---

## 배포 현황 추적

### 체크리스트

#### 사전 준비
- [ ] 필수 도구 설치 (doctl, kubectl, helm, gh)
- [ ] 계정 준비 (GitHub, DigitalOcean, Vercel)
- [ ] 로컬 테스트 성공

#### GitHub Secrets
- [ ] DIGITALOCEAN_TOKEN
- [ ] DATABASE_URL
- [ ] JWT_SECRET_KEY
- [ ] TOGETHER_AI_API_KEY
- [ ] ADMIN_SECRET_KEY
- [ ] VERCEL_TOKEN
- [ ] VERCEL_ORG_ID
- [ ] VERCEL_PROJECT_ID

#### 인프라
- [ ] DigitalOcean 클러스터 생성
- [ ] Container Registry 생성
- [ ] Database 준비 (Managed 또는 Self-hosted)

#### 배포
- [ ] Preview 환경 첫 배포 성공
- [ ] API URL 확인 및 Secrets 업데이트
- [ ] Production 배포 성공
- [ ] Frontend 배포 성공

#### 검증
- [ ] Health check 통과
- [ ] API 호출 정상
- [ ] Kong Gateway 동작 확인
- [ ] Frontend-Backend 연결 확인

#### 선택사항
- [ ] 도메인 설정
- [ ] TLS 인증서
- [ ] 모니터링 대시보드
- [ ] Slack 알림
