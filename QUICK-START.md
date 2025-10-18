# BoDam CI/CD 빠른 시작 가이드

## 5분 안에 배포 시작하기

### 1단계: GitHub Secrets 설정 (2분)

```bash
# GitHub CLI로 한 번에 설정
gh secret set DIGITALOCEAN_TOKEN -b"dop_v1_your_token"
gh secret set DATABASE_URL -b"postgresql+asyncpg://user:pass@host/db"
gh secret set JWT_SECRET_KEY -b"$(openssl rand -base64 32)"
gh secret set TOGETHER_AI_API_KEY -b"your_together_api_key"
gh secret set ADMIN_SECRET_KEY -b"$(openssl rand -base64 32)"

# Vercel (프론트엔드)
gh secret set VERCEL_TOKEN -b"your_vercel_token"
gh secret set VERCEL_ORG_ID -b"team_xxx"
gh secret set VERCEL_PROJECT_ID -b"prj_xxx"

# API URLs
gh secret set PRODUCTION_API_URL -b"https://api.bodam.com"
gh secret set PREVIEW_API_URL -b"https://api-preview.bodam.com"

# 선택사항
gh secret set SLACK_WEBHOOK_URL -b"https://hooks.slack.com/services/xxx"
```

**웹 인터페이스 사용 시**:
Repository → Settings → Secrets and variables → Actions → New repository secret

---

### 2단계: Cluster Autoscaler 배포 (1분)

```bash
# DigitalOcean Cluster ID 확인
doctl kubernetes cluster list

# Secrets 생성
kubectl create secret generic digitalocean-token \
  --from-literal=token=dop_v1_your_token \
  --namespace=kube-system

kubectl create secret generic digitalocean-cluster \
  --from-literal=cluster-id=your_cluster_id \
  --namespace=kube-system

# Autoscaler 배포
kubectl apply -f infra/k8s/cluster-autoscaler/autoscaler-config.yaml

# 확인
kubectl get pods -n kube-system -l app=cluster-autoscaler
```

---

### 3단계: 첫 배포 (2분)

```bash
# wonuk 브랜치에 push
git checkout wonuk
echo "# test" >> README.md
git add .
git commit -m "test: CI/CD 테스트"
git push origin wonuk

# GitHub Actions 확인
gh run list --branch wonuk
gh run watch  # 실시간 로그 보기
```

**성공 확인**:
- GitHub Actions: ✅ 모든 단계 통과
- Preview 환경: `curl https://api-preview.bodam.com/health`
- Slack: 배포 성공 알림

---

## 자주 사용하는 명령어

### GitHub Actions

```bash
# 워크플로우 실행 확인
gh run list --branch wonuk
gh run list --branch donghee

# 실시간 로그 보기
gh run watch

# 실패한 워크플로우 재실행
gh run rerun <run-id>
```

### Kubernetes

```bash
# Pod 상태 확인
kubectl get pods -n bodam-preview
kubectl get pods -n bodam-prod

# 로그 확인
kubectl logs -f deployment/bodam-backend -n bodam-prod
kubectl logs -f deployment/bodam-backend -c fastapi -n bodam-prod
kubectl logs -f deployment/bodam-backend -c celery-worker -n bodam-prod

# HPA 상태
kubectl get hpa -n bodam-prod
kubectl describe hpa bodam-backend -n bodam-prod

# 리소스 사용률
kubectl top pods -n bodam-prod
kubectl top nodes

# Autoscaler 로그
kubectl logs -f deployment/cluster-autoscaler -n kube-system
```

### 배포 롤백

```bash
# 이전 버전으로 롤백
kubectl rollout undo deployment/bodam-backend -n bodam-prod

# 특정 리비전으로 롤백
kubectl rollout history deployment/bodam-backend -n bodam-prod
kubectl rollout undo deployment/bodam-backend --to-revision=3 -n bodam-prod
```

---

## 트러블슈팅

### 배포 실패 시

1. **GitHub Actions 확인**
   ```bash
   gh run view --log-failed
   ```

2. **Pod 상태 확인**
   ```bash
   kubectl get pods -n bodam-prod
   kubectl describe pod <pod-name> -n bodam-prod
   ```

3. **로그 확인**
   ```bash
   kubectl logs <pod-name> -n bodam-prod --previous
   ```

### HPA가 작동하지 않을 때

```bash
# Metrics Server 확인
kubectl get deployment metrics-server -n kube-system

# HPA 이벤트 확인
kubectl describe hpa bodam-backend -n bodam-prod
```

### Cluster Autoscaler가 작동하지 않을 때

```bash
# Autoscaler 로그 확인
kubectl logs deployment/cluster-autoscaler -n kube-system | tail -100

# ConfigMap 상태
kubectl describe configmap cluster-autoscaler-status -n kube-system

# Pending Pod 확인
kubectl get pods --all-namespaces --field-selector=status.phase=Pending
```

---

## 환경별 배포 흐름

### Preview 환경 (wonuk 브랜치)

```bash
git checkout wonuk
# 작업...
git add .
git commit -m "feat: new feature"
git push origin wonuk
# → GitHub Actions → Preview 배포
# → Preview URL: https://api-preview.bodam.com
```

### Production 환경 (donghee 브랜치)

```bash
# wonuk에서 테스트 완료 후
git checkout donghee
git merge wonuk
git push origin donghee
# → GitHub Actions → Production 배포
# → Production URL: https://api.bodam.com
# → Lighthouse CI 실행 (프론트엔드)
```

---

## 모니터링

### Grafana 대시보드
- URL: https://grafana.bodam.com
- 14개 핵심 메트릭 모니터링
- Llama AI 쿼리: "지난 1시간 동안 5XX 에러가 얼마나 발생했어?"

### Slack 알림
- 배포 성공/실패
- 5XX 에러 발생 시 즉시 알림
- DB/HTTP Pool 고갈 시 알림

### DigitalOcean 대시보드
- Cluster 리소스 사용률
- 노드 스케일링 이벤트
- Load Balancer 상태

---

## 비용 모니터링

### 예상 비용 (월)
```
1 노드 (평상시):      $24
2 노드 (피크 시):     $48
Load Balancer:       $12
--------------------------
평균 예상:         $36-48
```

### 비용 절감 팁
1. Cluster Autoscaler가 10분 미사용 노드 자동 제거
2. HPA가 최소 1개 Pod 유지 (불필요한 스케일 업 방지)
3. 리소스 requests/limits 최적화로 노드당 Pod 밀도 증가

---

## 추가 참고 자료

- **상세 배포 가이드**: `/home/eugene/bodam/DEPLOYMENT.md`
- **설정 완료 보고서**: `/home/eugene/bodam/CI-CD-SETUP-SUMMARY.md`
- **Autoscaler 가이드**: `/home/eugene/bodam/infra/k8s/cluster-autoscaler/README.md`
- **프로젝트 README**: `/home/eugene/bodam/CLAUDE.md`

---

## 지원

문제가 발생하면:
1. DEPLOYMENT.md의 트러블슈팅 섹션 참조
2. GitHub Issues에 버그 리포트
3. Slack #bodam-dev 채널에 문의

**작성일**: 2025-10-18
