# 🎉 보담 플랫폼 배포 자동화 완성!

**완성일**: 2025-11-11
**환경**: Production (donghee 브랜치)
**상태**: ✅ 완료 (Preview 환경은 나중에 추가)

---

## ✅ 완성된 것들

### 1. Claude Skills (배포 에이전트)
- ✅ `deploy` - 자동 배포
- ✅ `predeploy` - 배포 전 검증
- ✅ `rollback` - 롤백
- ✅ `deploy-status` - 상태 모니터링

위치: `.claude/skills/`

### 2. K8s 매니페스트 (로컬 개발 환경과 동일)
- ✅ Redis 3개 분리 (cache, queue, semantic)
- ✅ Backend (FastAPI, 3 replicas)
- ✅ Celery Workers 3개 (main, news, beat)
- ✅ Ingress (Production)
- ✅ HPA (Auto Scaling)

위치: `infra/k8s/`

### 3. GitHub Actions 워크플로우
- ✅ Backend CI/CD (donghee 브랜치)
- ✅ Frontend CI/CD (donghee 브랜치)
- ✅ Redis 3개 + Celery 3개 자동 배포
- ✅ Health Check + Smoke Test

위치: `.github/workflows/`

### 4. 배포 스크립트
- ✅ `deploy-all.sh` - 통합 배포 스크립트
- ✅ Skills용 헬퍼 스크립트들

위치: `infra/k8s/deploy-all.sh`

---

## 📋 현재 설정

### Production 환경
| 항목 | 값 |
|------|-----|
| **GitHub** | |
| Repo | https://github.com/dlehdgml5328/bodam |
| 브랜치 | donghee |
| **URLs** | |
| Backend | https://api.bodam.website/ |
| Frontend | https://frontend-sigma-pearl-65.vercel.app/ |
| **Kubernetes** | |
| Cluster ID | d3e14d15-3c77-4620-95d5-ff84a8eee455 |
| Namespace | bodam-prod |
| Region | Singapore (sgp1) |
| **Services** | |
| Backend Pods | 3 replicas |
| Celery Worker | 2 replicas |
| Celery News | 1 replica |
| Celery Beat | 1 replica |
| Redis Cache | 1 replica (LRU, 512MB) |
| Redis Queue | 1 replica (AOF+RDB, 1GB, PVC 10GB) |
| Redis Semantic | 1 replica (Vector, 2GB, PVC 20GB) |

---

## 🚀 사용 방법

### Claude에게 말하기만 하면 됩니다!

```bash
# 배포 전 검증
"배포해도 될까?"

# Production 배포
"production 배포해줘"

# 배포 상태 확인
"배포 상태 확인해줘"

# 문제 발생 시
"롤백해줘"
```

### 수동 배포 (필요시)
```bash
# 1. K8s 클러스터 인증
doctl kubernetes cluster kubeconfig save d3e14d15-3c77-4620-95d5-ff84a8eee455

# 2. 통합 배포 스크립트 실행
cd infra/k8s
./deploy-all.sh production

# 3. 상태 확인
kubectl get pods -n bodam-prod
```

---

## 🔄 GitHub Actions 자동 배포

donghee 브랜치에 push하면 자동으로:

1. ✅ 테스트 실행 (Backend + Frontend)
2. ✅ 린트/타입 검사
3. ✅ Docker 이미지 빌드 & 푸시
4. ✅ Redis 3개 배포
5. ✅ Backend 배포
6. ✅ Celery Workers 3개 배포
7. ✅ Health Check
8. ✅ Smoke Test
9. ✅ Slack 알림 (설정된 경우)

모니터링: https://github.com/dlehdgml5328/bodam/actions

---

## 📊 리소스 사용량

| 서비스 | Replicas | CPU Request | Memory Request | CPU Limit | Memory Limit |
|--------|----------|-------------|----------------|-----------|--------------|
| Backend | 3 | 250m | 512Mi | 500m | 1Gi |
| Celery Worker | 2 | 250m | 512Mi | 500m | 1Gi |
| Celery News | 1 | 500m | 1Gi | 1000m | 2Gi |
| Celery Beat | 1 | 100m | 128Mi | 200m | 256Mi |
| Redis Cache | 1 | 100m | 256Mi | 200m | 512Mi |
| Redis Queue | 1 | 200m | 512Mi | 500m | 1Gi |
| Redis Semantic | 1 | 200m | 1Gi | 500m | 2Gi |
| **합계** | **10** | **~2.1 vCPU** | **~4.5GB RAM** | **~4.0 vCPU** | **~9.2GB RAM** |

**현재 클러스터**: 충분한 리소스 보유 ✅

---

## 🔜 나중에 추가할 것 (Preview 환경)

### Phase 2: Preview 환경 구성

#### 1. DNS 설정
```
A Record 추가:
- preview-api.bodam.website → Load Balancer IP
```

#### 2. Vercel Preview 도메인
Vercel에서 자동 생성되는 develop 브랜치 URL 사용

#### 3. K8s Ingress 추가
```bash
# Preview Ingress 생성
kubectl apply -f infra/k8s/backend/ingress-preview.yaml -n bodam-preview
```

#### 4. GitHub Actions 업데이트
develop 브랜치 트리거 추가

#### 5. Skills 업데이트
Preview 환경 지원 추가

---

## 🛡️ 보안 체크리스트

- [x] GitHub Secrets 설정
- [x] Docker Registry 인증 (regcred)
- [x] Ingress TLS 설정 (Let's Encrypt)
- [x] CORS 설정
- [x] Rate Limiting
- [x] 환경 변수 민감 정보 보호

---

## 📚 참고 문서

- [K8s 배포 가이드](../../infra/k8s/README.md)
- [Skills 사용법](.claude/skills/README.md)
- [로컬 개발 환경](../../docker-compose.dev.yml)
- [프로젝트 구조](../../CLAUDE.md)

---

## 🐛 트러블슈팅

### Pod가 시작하지 않을 때
```bash
kubectl describe pod <pod-name> -n bodam-prod
kubectl logs <pod-name> -n bodam-prod
```

### Ingress가 작동하지 않을 때
```bash
kubectl get ingress -n bodam-prod
kubectl describe ingress bodam-prod-ingress -n bodam-prod
```

### PVC 마운트 실패
```bash
kubectl get pvc -n bodam-prod
kubectl describe pvc redis-queue-pvc -n bodam-prod
```

---

## 🎯 다음 단계

1. **테스트 배포** (donghee 브랜치에 push)
2. **모니터링 확인** (Grafana 대시보드)
3. **부하 테스트** (K6)
4. **Preview 환경 구성** (필요시)

---

**🎉 축하합니다! 배포 자동화가 완성되었습니다!**

이제 Claude에게 "배포해줘"라고만 말하면 모든 게 자동으로 진행됩니다! 😊
