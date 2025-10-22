# CI/CD 파이프라인 및 Kubernetes 설정 완료 보고서

## 생성된 파일 목록

### 1. GitHub Actions 워크플로우

#### 백엔드 CI/CD
**파일**: `/home/eugene/bodam/.github/workflows/backend-ci-cd.yml`

**기능**:
- wonuk/donghee 브랜치 push 시 자동 트리거
- 전체 테스트 스위트 실행 (단위/통합/성능)
- Docker 이미지 빌드 및 DigitalOcean Registry 푸시
- Kubernetes 자동 배포 (namespace 환경 분리)
- 스모크 테스트 및 Slack 알림

**테스트 단계**:
1. Ruff 코드 검사
2. MyPy 타입 검사
3. pytest 단위 테스트 (커버리지 포함)
4. pytest 통합 테스트
5. pytest 성능 테스트
6. Codecov 업로드

**배포 환경**:
- `wonuk` → Preview 환경 (`bodam-preview` namespace)
- `donghee` → Production 환경 (`bodam-prod` namespace)

---

#### 프론트엔드 CI/CD
**파일**: `/home/eugene/bodam/.github/workflows/frontend-ci-cd.yml`

**기능**:
- wonuk/donghee 브랜치 push 시 자동 트리거
- Jest 단위 테스트 실행
- Playwright E2E 테스트 실행
- Vercel 자동 배포
- Lighthouse CI (Production만)

**테스트 단계**:
1. ESLint 검사
2. TypeScript 타입 검사
3. Jest 단위 테스트 (커버리지)
4. Playwright E2E 테스트
5. 프로덕션 빌드 검증

**배포 환경**:
- `wonuk` → Vercel Preview
- `donghee` → Vercel Production

---

### 2. Kubernetes HPA 설정

#### Backend HPA
**파일**: `/home/eugene/bodam/infra/k8s/backend/backend-hpa.yaml`

**설정**:
```yaml
minReplicas: 1
maxReplicas: 3
CPU target: 60% (기존 70%에서 낮춤)
Memory target: 70% (기존 80%에서 낮춤)
```

**스케일링 정책**:
- **Scale Up**: 30초 안정화 (빠른 확장)
  - 100% 증가율 (1→2→3)
  - 또는 최대 2개 Pod 동시 추가
  - 더 적극적인 정책 선택 (selectPolicy: Max)

- **Scale Down**: 3분 안정화 (보수적 축소)
  - 50% 감소율 (3→2→1)
  - 또는 최대 1개 Pod씩 제거
  - 더 보수적인 정책 선택 (selectPolicy: Min)

---

#### Celery Worker HPA
**파일**: `/home/eugene/bodam/infra/k8s/backend/celery-worker-hpa.yaml`

**설정**:
```yaml
minReplicas: 1
maxReplicas: 2
CPU target: 70%
Memory target: 75%
```

**참고**: 현재는 backend-deployment.yaml에 통합되어 있으나, 향후 Celery Worker 분리 시 바로 사용 가능하도록 준비

---

### 3. Backend Deployment 리소스 최적화

**파일**: `/home/eugene/bodam/infra/k8s/backend/backend-deployment.yaml`

**변경 사항**:
```yaml
# FastAPI 컨테이너
resources:
  requests:
    cpu: 200m      # 0.2 CPU (기존 250m에서 감소)
    memory: 256Mi  # 256MB (기존 512Mi에서 감소)
  limits:
    cpu: 500m      # 0.5 CPU (기존 1000m에서 감소)
    memory: 512Mi  # 512MB (기존 2Gi에서 대폭 감소)

# Celery Worker 컨테이너 (동일)
resources:
  requests:
    cpu: 200m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

**리소스 계산** (2vCPU/4GB 노드 기준):
- Pod당 CPU 요청: 0.2 + 0.2 = 0.4 CPU
- Pod당 메모리 요청: 256 + 256 = 512MB
- **노드당 최대 Pod 수**: 약 4개 (HPA 최대 3개로 여유 확보)

---

### 4. Cluster Autoscaler 설정

#### 설정 파일
**파일**: `/home/eugene/bodam/infra/k8s/cluster-autoscaler/autoscaler-config.yaml`

**주요 설정**:
```yaml
노드 범위: 1-2 노드
스케일 다운 지연: 5분
미사용 시간: 10분
사용률 임계값: 50%
Expander: least-waste
```

**포함된 리소스**:
- ServiceAccount
- ClusterRole & ClusterRoleBinding
- Role & RoleBinding
- Deployment (cluster-autoscaler)
- ConfigMap (상태 저장)
- PodDisruptionBudget (가용성 보장)

**필요한 Secrets** (수동 생성):
```bash
kubectl create secret generic digitalocean-token \
  --from-literal=token=YOUR_DO_TOKEN \
  --namespace=kube-system

kubectl create secret generic digitalocean-cluster \
  --from-literal=cluster-id=YOUR_CLUSTER_ID \
  --namespace=kube-system
```

#### 가이드 문서
**파일**: `/home/eugene/bodam/infra/k8s/cluster-autoscaler/README.md`

**내용**:
- 설치 단계별 가이드
- 설정 파라미터 설명
- 모니터링 방법
- 트러블슈팅 가이드
- 비용 최적화 전략

---

### 5. 종합 배포 가이드

**파일**: `/home/eugene/bodam/DEPLOYMENT.md`

**포함 내용**:
- GitHub Secrets 설정 방법
- CI/CD 워크플로우 상세 설명
- Kubernetes 수동 배포 가이드
- HPA 및 Cluster Autoscaler 설정 설명
- 모니터링 및 트러블슈팅 가이드
- 배포 체크리스트

---

## 핵심 개선 사항

### 1. HPA 최적화
✅ **CPU 목표 60%** (기존 70%에서 낮춤)
- 더 빠른 스케일 업으로 트래픽 급증 대응

✅ **메모리 목표 70%** (기존 80%에서 낮춤)
- OOM 발생 가능성 감소

✅ **빠른 스케일 업** (30초 안정화)
- 트래픽 증가 시 신속한 대응

✅ **보수적 스케일 다운** (3분 안정화)
- 트래픽 변동 시 안정성 유지

### 2. 리소스 최적화
✅ **CPU 요청 200m** (기존 250m)
- 노드당 더 많은 Pod 실행 가능

✅ **메모리 512Mi 제한** (기존 2Gi)
- 리소스 낭비 방지 및 비용 절감

✅ **2vCPU/4GB 노드에서 4개 Pod** 실행 가능
- HPA 최대 3개로 여유 리소스 확보

### 3. Cluster Autoscaler
✅ **1-2 노드 자동 스케일링**
- 평상시 1 노드 ($24/month)
- 피크 시 2 노드 ($48/month)

✅ **10분 미사용 시 스케일 다운**
- 비용 최적화

✅ **50% 사용률 임계값**
- 적절한 리소스 활용

### 4. CI/CD 자동화
✅ **전체 테스트 자동 실행**
- 단위/통합/성능 테스트 포함

✅ **테스트 실패 시 배포 중단**
- 품질 보장

✅ **환경 분리** (Preview/Production)
- wonuk → Preview
- donghee → Production

✅ **자동 스모크 테스트**
- Health check 및 API 응답 검증

---

## 필수 GitHub Secrets

### DigitalOcean
- `DIGITALOCEAN_TOKEN`
- `DIGITALOCEAN_CLUSTER_ID_PROD`
- `DIGITALOCEAN_CLUSTER_ID_PREVIEW`

### Database & Backend
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `TOGETHER_AI_API_KEY`
- `ADMIN_SECRET_KEY`

### API URLs
- `PRODUCTION_API_URL`
- `PREVIEW_API_URL`

### Vercel
- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`
- `NEXT_PUBLIC_API_URL`

### 선택사항
- `SLACK_WEBHOOK_URL` (배포 알림)
- `CODECOV_TOKEN` (커버리지 업로드)

---

## 배포 순서

### 1. 초기 설정 (1회만)

```bash
# 1. GitHub Secrets 설정 (웹 인터페이스 또는 gh CLI)
gh secret set DIGITALOCEAN_TOKEN -b"dop_v1_..."
gh secret set DATABASE_URL -b"postgresql+asyncpg://..."
# ... (나머지 Secrets)

# 2. Cluster Autoscaler 배포
kubectl create secret generic digitalocean-token \
  --from-literal=token=YOUR_DO_TOKEN \
  --namespace=kube-system

kubectl create secret generic digitalocean-cluster \
  --from-literal=cluster-id=YOUR_CLUSTER_ID \
  --namespace=kube-system

kubectl apply -f infra/k8s/cluster-autoscaler/autoscaler-config.yaml

# 3. 상태 확인
kubectl get pods -n kube-system -l app=cluster-autoscaler
kubectl logs -f deployment/cluster-autoscaler -n kube-system
```

### 2. 코드 배포 (자동)

```bash
# wonuk 브랜치 (Preview 환경)
git checkout wonuk
git add .
git commit -m "feat: new feature"
git push origin wonuk
# → GitHub Actions 자동 실행 → Preview 배포

# donghee 브랜치 (Production 환경)
git checkout donghee
git merge wonuk
git push origin donghee
# → GitHub Actions 자동 실행 → Production 배포
```

---

## 예상 비용

### DigitalOcean Kubernetes (DOKS)
- **평상시**: 1 노드 × $24 = **$24/month**
- **피크 시**: 2 노드 × $24 = **$48/month**
- **평균**: **$30-36/month**

### 기타
- Load Balancer: $12/month
- Container Registry: 무료 (5GB)
- **총 예상 비용**: **$42-48/month** (목표 $40 이하 초과 가능)

### 비용 절감 방안
1. Cluster Autoscaler로 불필요한 노드 제거
2. HPA로 최소 Pod 수 유지
3. 리소스 requests/limits 최적화로 노드당 Pod 밀도 증가

---

## 다음 단계

### 1. GitHub Secrets 설정
- [ ] 모든 필수 Secrets 등록
- [ ] Vercel 프로젝트 연동

### 2. Cluster Autoscaler 배포
- [ ] DigitalOcean Secrets 생성
- [ ] Autoscaler 배포 및 확인

### 3. 첫 배포 테스트
- [ ] wonuk 브랜치에 push
- [ ] GitHub Actions 성공 확인
- [ ] Preview 환경 테스트

### 4. Production 배포
- [ ] donghee 브랜치로 merge
- [ ] Production 배포 확인
- [ ] Grafana 모니터링

### 5. 모니터링 설정
- [ ] Slack 알림 확인
- [ ] HPA 메트릭 모니터링
- [ ] Cluster Autoscaler 로그 확인

---

## 참고 문서

- **배포 가이드**: `/home/eugene/bodam/DEPLOYMENT.md`
- **Autoscaler 가이드**: `/home/eugene/bodam/infra/k8s/cluster-autoscaler/README.md`
- **프로젝트 README**: `/home/eugene/bodam/CLAUDE.md`

---

**작성일**: 2025-10-18
**작성자**: Claude Code
**상태**: ✅ 완료
