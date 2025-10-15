# Kubernetes 배포 가이드

보담 플랫폼의 Kubernetes 배포 설정입니다.

## 디렉토리 구조

```
k8s/
├── kong/              # Kong Gateway 관련 매니페스트
│   ├── kong-deployment.yaml
│   ├── kong-service.yaml
│   └── kong-config.yaml
├── nginx/             # NGINX 관련 매니페스트
│   ├── nginx-deployment.yaml
│   ├── nginx-service.yaml
│   └── nginx-configmap.yaml
├── backend/           # 백엔드 서비스
│   ├── backend-deployment.yaml
│   └── backend-service.yaml
└── database/          # 데이터베이스 (PostgreSQL, Redis)
    ├── postgres-statefulset.yaml
    └── redis-deployment.yaml
```

## 배포 순서

### 1. Namespace 생성
```bash
kubectl create namespace bodam-staging
kubectl create namespace bodam-production
```

### 2. 데이터베이스 배포
```bash
kubectl apply -f database/ -n bodam-staging
```

### 3. 백엔드 서비스 배포
```bash
kubectl apply -f backend/ -n bodam-staging
```

### 4. Kong Gateway 배포
```bash
kubectl apply -f kong/ -n bodam-staging
```

### 5. NGINX 배포
```bash
kubectl apply -f nginx/ -n bodam-staging
```

### 6. 배포 확인
```bash
kubectl get pods -n bodam-staging
kubectl get svc -n bodam-staging
```

## 트래픽 마이그레이션 전략

### Phase 1: Shadow Mode (0% 트래픽)
- Kong Gateway 배포하지만 트래픽은 라우팅하지 않음
- 로깅 및 모니터링만 활성화
- 기간: 1주일

### Phase 2: Canary 10%
- 전체 트래픽의 10%를 Kong으로 라우팅
- 에러율 및 레이턴시 모니터링
- 기간: 48시간

### Phase 3: Canary 50%
- 전체 트래픽의 50%를 Kong으로 라우팅
- 성능 메트릭 검증
- 기간: 48시간

### Phase 4: Full Migration 100%
- 모든 트래픽을 Kong으로 라우팅
- 1주일 동안 모니터링

### Phase 5: 구 인프라 폐기
- 기존 NGINX Ingress 제거
- 리소스 정리

## 롤백 계획

문제 발생 시 즉시 이전 단계로 롤백:
```bash
kubectl rollout undo deployment/kong -n bodam-staging
kubectl rollout undo deployment/nginx -n bodam-staging
```

## 모니터링

### 주요 메트릭
- Kong Gateway 응답 시간 (목표: p95 < 100ms)
- 에러율 (목표: < 0.1%)
- 처리량 (목표: > 1000 req/s)
- CPU/메모리 사용률

### 로그 확인
```bash
kubectl logs -f deployment/kong -n bodam-staging
kubectl logs -f deployment/nginx -n bodam-staging
```

## Health Check

```bash
# Kong Admin API
kubectl port-forward svc/kong-admin 8001:8001 -n bodam-staging
curl http://localhost:8001/status

# NGINX Health
kubectl port-forward svc/nginx 80:80 -n bodam-staging
curl http://localhost/health
```
