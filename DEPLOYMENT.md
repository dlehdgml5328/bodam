# BoDam CI/CD 및 배포 가이드

이 문서는 BoDam 프로젝트의 CI/CD 파이프라인 설정 및 Kubernetes 배포 방법을 설명합니다.

## 목차
1. [GitHub Actions 설정](#github-actions-설정)
2. [Kubernetes 배포](#kubernetes-배포)
3. [HPA 및 Cluster Autoscaler](#hpa-및-cluster-autoscaler)
4. [모니터링 및 트러블슈팅](#모니터링-및-트러블슈팅)

---

## GitHub Actions 설정

### 필수 GitHub Secrets

#### DigitalOcean
```bash
DIGITALOCEAN_TOKEN              # DigitalOcean API Token
DIGITALOCEAN_CLUSTER_ID_PROD    # Production Cluster ID
DIGITALOCEAN_CLUSTER_ID_PREVIEW # Preview Cluster ID
```

#### Database & Backend
```bash
DATABASE_URL                    # PostgreSQL 연결 URL
JWT_SECRET_KEY                  # JWT 서명 키
TOGETHER_AI_API_KEY             # Together AI API 키 (Llama)
ADMIN_SECRET_KEY                # SQLAdmin 세션 키
```

#### API URLs
```bash
PRODUCTION_API_URL              # Production 백엔드 URL
PREVIEW_API_URL                 # Preview 백엔드 URL
```

#### Vercel (프론트엔드)
```bash
VERCEL_TOKEN                    # Vercel API Token
VERCEL_ORG_ID                   # Vercel Organization ID
VERCEL_PROJECT_ID               # Vercel Project ID
NEXT_PUBLIC_API_URL             # 프론트엔드에서 사용할 API URL
```

#### Slack (선택사항)
```bash
SLACK_WEBHOOK_URL               # 배포 알림용 Slack Webhook
```

#### Codecov (선택사항)
```bash
CODECOV_TOKEN                   # 코드 커버리지 업로드
```

### Secrets 설정 방법

```bash
# GitHub CLI 사용
gh secret set DIGITALOCEAN_TOKEN -b"dop_v1_..."
gh secret set DATABASE_URL -b"postgresql+asyncpg://..."

# 또는 GitHub 웹 인터페이스
# Repository → Settings → Secrets and variables → Actions → New repository secret
```

---

## CI/CD 워크플로우

### Backend CI/CD Pipeline

**파일**: `.github/workflows/backend-ci-cd.yml`

**트리거**:
- `wonuk` 브랜치 push → Preview 환경 배포
- `donghee` 브랜치 push → Production 환경 배포

**단계**:
1. **테스트 실행**
   - Ruff 코드 검사
   - MyPy 타입 검사
   - 단위 테스트 (pytest)
   - 통합 테스트
   - 성능 테스트

2. **Docker 이미지 빌드 및 푸시**
   - DigitalOcean Container Registry에 푸시
   - 태그: `production-{SHA}` 또는 `preview-{SHA}`

3. **Kubernetes 배포**
   - 네임스페이스 생성 (`bodam-prod` 또는 `bodam-preview`)
   - Secrets 생성 (DB, JWT, API 키)
   - Deployment, HPA 배포

4. **스모크 테스트**
   - Health check 확인
   - API 응답 테스트
   - Slack 알림

### Frontend CI/CD Pipeline

**파일**: `.github/workflows/frontend-ci-cd.yml`

**트리거**:
- `wonuk` 브랜치 push → Vercel Preview 배포
- `donghee` 브랜치 push → Vercel Production 배포

**단계**:
1. **린트 및 테스트**
   - ESLint 검사
   - TypeScript 타입 검사
   - Jest 단위 테스트
   - Playwright E2E 테스트

2. **프로덕션 빌드**
   - Next.js 프로덕션 빌드
   - 빌드 아티팩트 검증

3. **Vercel 배포**
   - Preview: `wonuk` 브랜치
   - Production: `donghee` 브랜치
   - Lighthouse CI (Production만)

4. **스모크 테스트**
   - 홈페이지 접근 테스트
   - 렌더링 테스트

---

## Kubernetes 배포

### 리소스 구조

```
infra/k8s/
├── backend/
│   ├── backend-deployment.yaml     # FastAPI + Celery Worker
│   ├── backend-hpa.yaml            # HPA 설정
│   ├── celery-worker-hpa.yaml      # Celery Worker HPA (향후 분리용)
│   └── configmap.yaml              # 환경 변수
├── cluster-autoscaler/
│   ├── autoscaler-config.yaml      # Cluster Autoscaler
│   └── README.md                   # 설정 가이드
└── database/
    └── ...                         # PostgreSQL, Redis
```

### 수동 배포

#### 1. Cluster Autoscaler 설정

```bash
# DigitalOcean Secrets 생성
kubectl create secret generic digitalocean-token \
  --from-literal=token=YOUR_DIGITALOCEAN_TOKEN \
  --namespace=kube-system

kubectl create secret generic digitalocean-cluster \
  --from-literal=cluster-id=YOUR_CLUSTER_ID \
  --namespace=kube-system

# Autoscaler 배포
kubectl apply -f infra/k8s/cluster-autoscaler/autoscaler-config.yaml

# 상태 확인
kubectl get pods -n kube-system -l app=cluster-autoscaler
kubectl logs -f deployment/cluster-autoscaler -n kube-system
```

#### 2. 백엔드 배포

```bash
# 네임스페이스 생성
kubectl create namespace bodam-prod

# Secrets 생성
kubectl create secret generic bodam-secrets \
  --from-literal=database-url="postgresql+asyncpg://..." \
  --from-literal=jwt-secret="your-jwt-secret" \
  --from-literal=together-api-key="your-together-api-key" \
  --from-literal=admin-secret-key="your-admin-secret" \
  --namespace=bodam-prod

# Docker Registry Secret
kubectl create secret docker-registry regcred \
  --docker-server=registry.digitalocean.com \
  --docker-username=YOUR_DO_TOKEN \
  --docker-password=YOUR_DO_TOKEN \
  --namespace=bodam-prod

# 리소스 배포
kubectl apply -f infra/k8s/backend/configmap.yaml -n bodam-prod
kubectl apply -f infra/k8s/backend/backend-deployment.yaml -n bodam-prod
kubectl apply -f infra/k8s/backend/backend-hpa.yaml -n bodam-prod

# 배포 상태 확인
kubectl rollout status deployment/bodam-backend -n bodam-prod
kubectl get pods -n bodam-prod
```

---

## HPA 및 Cluster Autoscaler

### HPA (Horizontal Pod Autoscaler)

**Backend HPA 설정**:
- **최소 Replicas**: 1
- **최대 Replicas**: 3
- **CPU 목표**: 60% (기존 70%에서 낮춤)
- **메모리 목표**: 70% (기존 80%에서 낮춤)

**스케일링 정책**:
- **Scale Up**: 30초 안정화, 100% 증가 (1→2→3)
- **Scale Down**: 3분 안정화, 50% 감소 (3→2→1)

**리소스 제한** (Pod당):
```yaml
requests:
  cpu: 200m      # 0.2 CPU
  memory: 256Mi  # 256MB
limits:
  cpu: 500m      # 0.5 CPU
  memory: 512Mi  # 512MB
```

**계산**:
- 2vCPU/4GB 노드에서 최대 **4개 Pod** 실행 가능
- HPA 최대 3개 설정으로 **여유 리소스 확보**

### Cluster Autoscaler

**노드 스케일링**:
- **최소 노드**: 1
- **최대 노드**: 2
- **노드 타입**: 2vCPU / 4GB RAM

**스케일 다운 정책**:
- 노드 추가 후 5분 대기
- 10분간 미사용 시 제거
- 50% 미만 사용률일 때 제거 고려

**비용**:
- 1 노드: $24/month
- 2 노드 (피크): $48/month
- **평균**: $30-36/month

---

## 모니터링 및 트러블슈팅

### Pod 상태 확인

```bash
# Pod 목록
kubectl get pods -n bodam-prod

# Pod 상세 정보
kubectl describe pod <pod-name> -n bodam-prod

# Pod 로그
kubectl logs -f <pod-name> -n bodam-prod

# 특정 컨테이너 로그
kubectl logs -f <pod-name> -c fastapi -n bodam-prod
kubectl logs -f <pod-name> -c celery-worker -n bodam-prod
```

### HPA 모니터링

```bash
# HPA 상태
kubectl get hpa -n bodam-prod

# HPA 상세 정보
kubectl describe hpa bodam-backend -n bodam-prod

# 메트릭 확인
kubectl top pods -n bodam-prod
kubectl top nodes
```

### Cluster Autoscaler 모니터링

```bash
# Autoscaler 로그
kubectl logs -f deployment/cluster-autoscaler -n kube-system

# ConfigMap 상태
kubectl describe configmap cluster-autoscaler-status -n kube-system

# 노드 목록
kubectl get nodes

# 노드 리소스 사용률
kubectl top nodes
```

### 일반적인 문제 해결

#### 1. Pod가 Pending 상태인 경우

```bash
# Pod 상태 확인
kubectl describe pod <pod-name> -n bodam-prod

# 원인:
# - 리소스 부족: Cluster Autoscaler가 노드를 추가할 때까지 대기
# - 이미지 Pull 실패: Secret 확인
# - PVC 마운트 실패: PV/PVC 상태 확인
```

#### 2. Pod가 CrashLoopBackOff 상태인 경우

```bash
# 로그 확인
kubectl logs <pod-name> -n bodam-prod --previous

# 원인:
# - 환경 변수 누락: Secrets 확인
# - DB 연결 실패: DATABASE_URL 확인
# - 애플리케이션 오류: 로그에서 스택 트레이스 확인
```

#### 3. HPA가 스케일링하지 않는 경우

```bash
# Metrics Server 확인
kubectl get deployment metrics-server -n kube-system

# HPA 이벤트 확인
kubectl describe hpa bodam-backend -n bodam-prod

# 원인:
# - Metrics Server 미설치: DOKS는 기본 설치됨
# - 리소스 requests 미설정: Deployment 확인
```

#### 4. 배포가 실패하는 경우

```bash
# Rollout 상태 확인
kubectl rollout status deployment/bodam-backend -n bodam-prod

# Rollback
kubectl rollout undo deployment/bodam-backend -n bodam-prod

# 특정 리비전으로 Rollback
kubectl rollout history deployment/bodam-backend -n bodam-prod
kubectl rollout undo deployment/bodam-backend --to-revision=2 -n bodam-prod
```

---

## 배포 체크리스트

### 초기 설정 (1회만)

- [ ] GitHub Secrets 설정
- [ ] DigitalOcean Kubernetes Cluster 생성
- [ ] Cluster Autoscaler 배포
- [ ] Database (PostgreSQL, Redis) 배포
- [ ] Vercel 프로젝트 연동

### 매 배포 시

#### wonuk 브랜치 (Preview)
- [ ] 기능 개발 완료
- [ ] 로컬 테스트 통과
- [ ] wonuk 브랜치에 push
- [ ] GitHub Actions 성공 확인
- [ ] Preview 환경에서 수동 테스트
- [ ] donghee 브랜치로 PR 생성

#### donghee 브랜치 (Production)
- [ ] PR 리뷰 완료
- [ ] CI 테스트 통과
- [ ] donghee 브랜치로 merge
- [ ] GitHub Actions 성공 확인
- [ ] Production 환경에서 스모크 테스트
- [ ] Slack 알림 확인
- [ ] Grafana 대시보드 모니터링

---

## 참고 자료

- [GitHub Actions 문서](https://docs.github.com/en/actions)
- [DigitalOcean Kubernetes 가이드](https://docs.digitalocean.com/products/kubernetes/)
- [Kubernetes HPA](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [Cluster Autoscaler](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler)
- [Vercel CLI](https://vercel.com/docs/cli)
