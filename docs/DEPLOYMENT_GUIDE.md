# 보담 배포 가이드

Kong Gateway 및 Selenium 크롤러를 포함한 전체 시스템 배포 절차

## 목차

1. [사전 요구사항](#사전-요구사항)
2. [로컬 개발 환경](#로컬-개발-환경)
3. [Staging 환경 배포](#staging-환경-배포)
4. [Production 마이그레이션](#production-마이그레이션)
5. [롤백 절차](#롤백-절차)
6. [모니터링](#모니터링)

## 사전 요구사항

### 필수 도구
- Docker & Docker Compose
- Kubernetes CLI (kubectl)
- Helm 3+
- Python 3.11+
- Node.js 18+

### 클라우드 리소스
- Kubernetes 클러스터 (1.25+)
- PostgreSQL (pgvector 지원)
- Redis 클러스터
- TLS 인증서 (Let's Encrypt)

## 로컬 개발 환경

### 1. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일 편집
```

필수 환경 변수:
- `DATABASE_URL`: PostgreSQL 연결 문자열
- `REDIS_URL`: Redis 연결 문자열
- `JWT_SECRET_KEY`: JWT 서명 키 (32+ 글자)

### 2. Docker Compose로 서비스 시작

```bash
# PostgreSQL, Redis, Kong Gateway 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f kong
```

### 3. 데이터베이스 마이그레이션

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
```

### 4. 백엔드 서버 시작

```bash
cd backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
```

### 5. Celery Worker 시작 (별도 터미널)

```bash
cd backend
celery -A src.workers.celery_app worker --loglevel=info
```

### 6. 프론트엔드 시작 (별도 터미널)

```bash
cd frontend
npm install
npm run dev
```

### 7. 로컬 테스트

```bash
# Kong을 통한 API 호출
curl http://localhost:8000/api/fire-stations/search

# Health check
curl http://localhost:8001/status
```

## Staging 환경 배포

### 1. Namespace 생성

```bash
kubectl create namespace bodam-staging
kubectl config set-context --current --namespace=bodam-staging
```

### 2. Secrets 생성

```bash
# PostgreSQL credentials
kubectl create secret generic postgres-secret \
  --from-literal=username=bodam \
  --from-literal=password=<SECURE_PASSWORD>

# Backend secrets
kubectl create secret generic bodam-secrets \
  --from-literal=database-url=postgresql+asyncpg://bodam:<PASSWORD>@postgres-service:5432/bodam \
  --from-literal=jwt-secret=<SECURE_JWT_SECRET>
```

### 3. ConfigMap 생성

```bash
kubectl apply -f infra/k8s/backend/configmap.yaml
```

### 4. 데이터베이스 배포

```bash
# PostgreSQL
kubectl apply -f infra/k8s/database/postgres-statefulset.yaml

# Redis
kubectl apply -f infra/k8s/database/redis-deployment.yaml

# 데이터베이스 준비 대기
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis --timeout=300s
```

### 5. 백엔드 배포

```bash
kubectl apply -f infra/k8s/backend/backend-deployment.yaml
kubectl set env deployment/bodam-backend \
  ALLOWED_ORIGINS="https://frontend-sigma-pearl-65.vercel.app,https://bodam.website,https://www.bodam.website" \
  -n <NAMESPACE>

# 배포 확인
kubectl rollout status deployment/bodam-backend
```

### 6. Kong Gateway 배포

```bash
kubectl apply -f infra/k8s/kong/

# Kong 준비 대기
kubectl wait --for=condition=ready pod -l app=kong --timeout=300s
```

### 7. NGINX 배포

```bash
kubectl apply -f infra/k8s/nginx/

# NGINX 준비 대기
kubectl wait --for=condition=ready pod -l app=nginx --timeout=300s
```

### 8. Ingress 설정

```bash
kubectl apply -f infra/k8s/ingress.yaml
```

### 9. 배포 검증

```bash
# Pod 상태 확인
kubectl get pods

# 서비스 확인
kubectl get svc

# 로그 확인
kubectl logs -f deployment/kong
kubectl logs -f deployment/bodam-backend
```

## Production 마이그레이션

Kong Gateway로의 점진적 마이그레이션 전략

### Phase 0: 준비 단계

**체크리스트:**
- [ ] Staging 환경에서 모든 테스트 통과
- [ ] 성능 테스트 완료 (p95 < 100ms)
- [ ] 백업 계획 수립
- [ ] 롤백 절차 문서화
- [ ] 모니터링 대시보드 설정
- [ ] 알림 설정 (Slack, PagerDuty 등)

### Phase 1: Shadow Mode (0% 트래픽)

**목표:** Kong Gateway 배포하되 실제 트래픽은 라우팅하지 않음

**기간:** 1주일

**작업:**
1. Production에 Kong Gateway 배포
2. 로깅만 활성화 (미러 트래픽)
3. 메트릭 수집 시작
4. 에러 로그 모니터링

**검증:**
```bash
# Kong 상태 확인
kubectl exec -it deployment/kong -- kong health

# 메트릭 확인
curl http://kong-admin:8001/status
```

**성공 기준:**
- Kong Gateway 안정적으로 실행
- 기존 서비스에 영향 없음
- 메트릭 정상 수집

### Phase 2: Canary 10% (10% 트래픽)

**목표:** 전체 트래픽의 10%를 Kong으로 라우팅

**기간:** 48시간

**작업:**
1. Ingress에서 트래픽 분배 설정 (90% old, 10% Kong)
2. 에러율 모니터링
3. 레이턴시 비교

**트래픽 분배 설정:**
```yaml
# ingress-canary.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: bodam-canary
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "10"
spec:
  rules:
  - host: api.bodam.example
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: kong-proxy
            port:
              number: 8000
```

**모니터링:**
```bash
# Kong 메트릭
watch -n 5 'kubectl exec deployment/kong -- curl -s localhost:8001/status'

# 에러 로그 모니터링
kubectl logs -f deployment/kong | grep ERROR
```

**성공 기준:**
- 에러율 < 0.1%
- p95 레이턴시 증가 < 10ms
- Kong을 통한 요청 정상 처리

**롤백 조건:**
- 에러율 > 1%
- p95 레이턴시 > 200ms
- 5xx 에러 급증

### Phase 3: Canary 50% (50% 트래픽)

**목표:** 트래픽의 절반을 Kong으로 라우팅

**기간:** 48시간

**작업:**
1. 트래픽 분배 비율 50%로 증가
2. 부하 테스트 실행
3. 성능 메트릭 분석

**트래픽 증가:**
```bash
kubectl patch ingress bodam-canary -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/canary-weight":"50"}}}'
```

**성능 테스트:**
```bash
cd backend/tests/performance
pytest test_kong_performance.py -v
```

**성공 기준:**
- 처리량 > 1000 req/s
- p95 레이턴시 < 100ms
- 에러율 < 0.1%
- CPU/메모리 사용률 안정적

### Phase 4: Full Migration (100% 트래픽)

**목표:** 모든 트래픽을 Kong으로 전환

**기간:** 1주일 (모니터링 기간)

**작업:**
1. 트래픽 100% Kong으로 전환
2. 기존 경로 비활성화 (유지)
3. 1주일 동안 집중 모니터링

**전환:**
```bash
# 기존 Ingress 비활성화
kubectl scale deployment/old-nginx-ingress --replicas=1

# Kong Ingress를 primary로 설정
kubectl annotate ingress bodam-canary nginx.ingress.kubernetes.io/canary- --overwrite
```

**모니터링 대시보드:**
- 요청 수 (total, 2xx, 4xx, 5xx)
- 레이턴시 (p50, p95, p99)
- 에러율
- Kong CPU/메모리 사용률
- 백엔드 응답 시간

**성공 기준:**
- 1주일 동안 안정적 운영
- 사용자 불만 없음
- 성능 저하 없음

### Phase 5: 구 인프라 폐기

**목표:** 기존 NGINX Ingress 제거

**작업:**
1. 최종 백업
2. 기존 리소스 삭제
3. 리소스 정리

**인프라 제거:**
```bash
# 기존 Ingress 삭제
kubectl delete deployment/old-nginx-ingress
kubectl delete svc/old-nginx-service

# 사용하지 않는 ConfigMap 정리
kubectl delete configmap old-nginx-config
```

**완료 확인:**
- [ ] 모든 트래픽이 Kong을 통해 처리됨
- [ ] 구 인프라 리소스 삭제 완료
- [ ] 문서 업데이트 완료
- [ ] 팀 교육 완료

## 롤백 절차

### 긴급 롤백 (Phase 2-4 중)

**상황:** 심각한 문제 발생 시 즉시 롤백

```bash
# 1. 트래픽을 즉시 구 인프라로 전환
kubectl patch ingress bodam-canary -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/canary-weight":"0"}}}'

# 2. Kong Gateway 스케일 다운
kubectl scale deployment/kong --replicas=0

# 3. 기존 Ingress 스케일 업
kubectl scale deployment/old-nginx-ingress --replicas=3

# 4. 확인
kubectl get pods
curl https://api.bodam.example/health
```

### 단계별 롤백 (Phase 2-3)

**상황:** 성능 문제로 이전 단계로 복귀

```bash
# Phase 3에서 Phase 2로 롤백 (50% → 10%)
kubectl patch ingress bodam-canary -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/canary-weight":"10"}}}'
```

## 모니터링

### 주요 메트릭

**Kong Gateway:**
- 요청 수 (total, success, error)
- 레이턴시 (p50, p95, p99)
- 처리량 (req/s)
- 에러율 (%)
- CPU/메모리 사용률

**Selenium 크롤러:**
- 처리된 작업 수
- 성공/실패 비율
- 평균 크롤링 시간
- WebDriver Pool 사용률

**데이터베이스:**
- Connection pool 사용률
- 쿼리 응답 시간
- Dead lock 발생 횟수

### 로그 수집

```bash
# Kong 로그
kubectl logs -f deployment/kong --tail=100

# 백엔드 로그
kubectl logs -f deployment/bodam-backend --tail=100

# 모든 에러 로그
kubectl logs deployment/kong | grep ERROR
```

### 알림 설정

**Prometheus + Alertmanager 규칙:**

```yaml
groups:
- name: kong_alerts
  rules:
  # 에러율 높음
  - alert: HighErrorRate
    expr: rate(kong_http_status{code=~"5.."}[5m]) > 0.01
    for: 5m
    annotations:
      summary: "Kong 에러율 높음: {{ $value }}"
  
  # 레이턴시 높음
  - alert: HighLatency
    expr: histogram_quantile(0.95, kong_latency_ms) > 100
    for: 5m
    annotations:
      summary: "Kong p95 레이턴시 높음: {{ $value }}ms"
  
  # Pod 다운
  - alert: KongPodDown
    expr: up{job="kong"} == 0
    for: 1m
    annotations:
      summary: "Kong pod 다운됨"
```

## 문제 해결

### Kong이 시작되지 않음

```bash
# 설정 파일 검증
kubectl exec -it deployment/kong -- kong config parse /kong.yaml

# 로그 확인
kubectl logs deployment/kong

# ConfigMap 확인
kubectl get configmap kong-config -o yaml
```

### 트래픽이 Kong으로 라우팅되지 않음

```bash
# Ingress 설정 확인
kubectl describe ingress bodam-canary

# Service 확인
kubectl get svc kong-proxy

# Endpoint 확인
kubectl get endpoints kong-proxy
```

### 크롤러 성능 저하

```bash
# WebDriver Pool 상태 확인
kubectl exec deployment/bodam-backend -- python3 -c "from src.services.crawler.webdriver_pool import driver_pool; print(driver_pool.pool.qsize())"

# Celery worker 상태
kubectl logs deployment/bodam-backend | grep "celery.worker"
```

## 참고 자료

- [Kong Gateway 공식 문서](https://docs.konghq.com/)
- [Kubernetes Canary Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#canary-deployments)
- [NGINX Ingress Canary](https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/annotations/#canary)
- [Selenium WebDriver](https://www.selenium.dev/documentation/)
