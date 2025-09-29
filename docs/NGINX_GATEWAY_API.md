# NGINX Gateway API 검토 및 마이그레이션 가이드

## 개요

현재 BoDam 프로젝트는 NGINX Ingress Controller를 사용하고 있으나, Kubernetes Gateway API로의 전환을 고려할 수 있습니다.

## 현재 상태 vs Gateway API 비교

### NGINX Ingress (현재)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: bodam-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.bodam.example
    secretName: bodam-tls
  rules:
  - host: api.bodam.example
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: bodam-backend
            port:
              number: 8000
```

### Gateway API (제안)

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: bodam-gateway
spec:
  gatewayClassName: nginx
  listeners:
  - name: https
    port: 443
    protocol: HTTPS
    tls:
      certificateRefs:
      - name: bodam-tls
    allowedRoutes:
      namespaces:
        from: Same
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: bodam-api-route
spec:
  parentRefs:
  - name: bodam-gateway
  hostnames:
  - api.bodam.example
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /auth
    filters:
    - type: ExtensionRef
      extensionRef:
        group: gateway.nginx.org
        kind: RateLimitPolicy
        name: auth-rate-limit
    backendRefs:
    - name: bodam-backend
      port: 8000
  - matches:
    - path:
        type: PathPrefix
        value: /
    backendRefs:
    - name: bodam-backend
      port: 8000
```

## 장단점 분석

### NGINX Ingress (현재)

**장점:**
- ✅ 성숙하고 안정적인 솔루션
- ✅ 풍부한 커뮤니티 지원
- ✅ 다양한 annotation 기반 설정
- ✅ 즉시 사용 가능
- ✅ 기존 팀 노하우 활용

**단점:**
- ❌ Vendor-specific annotations
- ❌ 설정이 Ingress 리소스에 집중
- ❌ 복잡한 라우팅 규칙 관리 어려움
- ❌ 멀티 프로토콜 지원 제한

### Gateway API

**장점:**
- ✅ Kubernetes 표준 API
- ✅ 역할 기반 설정 분리 (인프라 vs 앱)
- ✅ 강력한 라우팅 기능
- ✅ 멀티 프로토콜 지원 (HTTP, gRPC, TCP, UDP)
- ✅ 미래 지향적 솔루션
- ✅ Vendor 중립적

**단점:**
- ❌ 상대적으로 새로운 기술
- ❌ 일부 기능이 아직 실험적
- ❌ 제한된 커뮤니티 지원
- ❌ 학습 곡선

## 전환 시나리오

### 즉시 전환이 필요한 경우

1. **복잡한 트래픽 라우팅**: A/B 테스트, Canary 배포가 자주 필요
2. **멀티 프로토콜**: gRPC, WebSocket 등 다양한 프로토콜 사용
3. **멀티 팀 환경**: 인프라팀과 개발팀의 역할 분리 필요
4. **표준화 요구**: 조직 차원의 Kubernetes 표준 API 사용 정책

### 현재 유지가 적절한 경우

1. **안정성 우선**: 현재 시스템이 잘 동작하고 있음
2. **단순한 라우팅**: 기본적인 HTTP 라우팅만 필요
3. **리소스 제약**: 마이그레이션에 투입할 인력/시간 부족
4. **기존 노하우**: NGINX Ingress에 대한 팀의 경험과 지식

## 단계별 마이그레이션 계획 (필요시)

### Phase 1: 준비 단계 (4주)

1. **Gateway API 학습 및 검증**
   ```bash
   # Gateway API CRD 설치
   kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.0.0/standard-install.yaml

   # NGINX Gateway Fabric 설치
   kubectl apply -f https://raw.githubusercontent.com/nginxinc/nginx-gateway-fabric/main/deploy/default/deploy.yaml
   ```

2. **개발 환경 테스트**
   - 기존 Ingress와 병행 운영
   - 기본 라우팅 기능 검증
   - 성능 테스트

### Phase 2: 스테이징 전환 (2주)

1. **스테이징 환경 Gateway API 적용**
   ```yaml
   # 기존 Ingress 백업
   kubectl get ingress -o yaml > ingress-backup.yaml

   # Gateway API 리소스 생성
   kubectl apply -f gateway-api-resources.yaml
   ```

2. **기능 검증**
   - 모든 엔드포인트 동작 확인
   - SSL/TLS 설정 검증
   - Rate limiting 동작 확인

### Phase 3: 프로덕션 전환 (2주)

1. **Blue-Green 배포**
   ```bash
   # 1. Gateway API 설정 배포
   kubectl apply -f production-gateway.yaml

   # 2. DNS 전환 (점진적)
   # 3. 모니터링 및 롤백 준비
   ```

2. **모니터링 강화**
   - 트래픽 패턴 모니터링
   - 에러율 추적
   - 응답 시간 측정

## 리소스 예제

### 현재 NGINX Ingress 설정

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: bodam-api-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    nginx.ingress.kubernetes.io/cors-allow-origin: "*"
    nginx.ingress.kubernetes.io/cors-allow-methods: "GET, POST, PUT, DELETE, OPTIONS"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.bodam.example
    secretName: bodam-api-tls
  rules:
  - host: api.bodam.example
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: bodam-backend
            port:
              number: 8000
```

### Gateway API 등가 설정

```yaml
# gateway.yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: bodam-gateway
spec:
  gatewayClassName: nginx
  listeners:
  - name: https
    port: 443
    protocol: HTTPS
    hostname: api.bodam.example
    tls:
      mode: Terminate
      certificateRefs:
      - name: bodam-api-tls
---
# httproute.yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: bodam-api-route
spec:
  parentRefs:
  - name: bodam-gateway
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /auth
    filters:
    - type: ExtensionRef
      extensionRef:
        group: gateway.nginx.org
        kind: RateLimitPolicy
        name: auth-rate-limit
    backendRefs:
    - name: bodam-backend
      port: 8000
  - matches:
    - path:
        type: PathPrefix
        value: /api
    filters:
    - type: ExtensionRef
      extensionRef:
        group: gateway.nginx.org
        kind: CORSPolicy
        name: api-cors
    backendRefs:
    - name: bodam-backend
      port: 8000
  - matches:
    - path:
        type: PathPrefix
        value: /
    backendRefs:
    - name: bodam-backend
      port: 8000
---
# policies.yaml
apiVersion: gateway.nginx.org/v1alpha1
kind: RateLimitPolicy
metadata:
  name: auth-rate-limit
spec:
  targetRef:
    group: gateway.networking.k8s.io
    kind: HTTPRoute
    name: bodam-api-route
  rateLimits:
  - rate: 5r/m
    key: ${remote_addr}
---
apiVersion: gateway.nginx.org/v1alpha1
kind: CORSPolicy
metadata:
  name: api-cors
spec:
  targetRef:
    group: gateway.networking.k8s.io
    kind: HTTPRoute
    name: bodam-api-route
  allowOrigins:
  - https://app.bodam.example
  allowMethods:
  - GET
  - POST
  - PUT
  - DELETE
  - OPTIONS
  allowHeaders:
  - "*"
```

## 성능 고려사항

### 벤치마크 테스트

```bash
# NGINX Ingress 성능 테스트
ab -n 10000 -c 100 https://api.bodam.example/health

# Gateway API 성능 테스트
ab -n 10000 -c 100 https://api-gateway.bodam.example/health

# 결과 비교
# - 처리량 (RPS)
# - 응답 시간 (평균, 95th percentile)
# - 에러율
# - 리소스 사용량
```

### 모니터링 메트릭

```yaml
# prometheus-rules.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: gateway-api-alerts
spec:
  groups:
  - name: gateway-api
    rules:
    - alert: GatewayHighErrorRate
      expr: rate(nginx_gateway_http_requests_total{status=~"5.."}[5m]) / rate(nginx_gateway_http_requests_total[5m]) > 0.1
      for: 5m
      annotations:
        summary: "Gateway API high error rate"
    - alert: GatewayHighLatency
      expr: histogram_quantile(0.95, rate(nginx_gateway_http_request_duration_seconds_bucket[5m])) > 1
      for: 10m
      annotations:
        summary: "Gateway API high latency"
```

## 권장사항

### 현재 상황 (BoDam 프로젝트)

**권장: NGINX Ingress 유지**

**이유:**
1. 현재 시스템이 안정적으로 동작
2. 단순한 HTTP 라우팅 요구사항
3. 팀의 NGINX Ingress 경험
4. 급하게 전환할 필요성 없음

### 향후 고려사항

다음 조건 중 하나라도 해당될 때 Gateway API 전환 검토:

1. **복잡한 라우팅 요구**:
   - A/B 테스트, Canary 배포 자동화
   - 트래픽 분할 정책

2. **멀티 프로토콜 지원**:
   - gRPC API 추가
   - WebSocket 실시간 기능

3. **조직 표준화**:
   - 회사 차원의 Gateway API 도입 정책

4. **팀 성숙도**:
   - Kubernetes 전문성 향상
   - 새로운 기술 도입 여력

### 준비 방안

Gateway API 전환에 대비한 준비 사항:

1. **학습 및 실험**
   ```bash
   # 로컬 테스트 환경 구축
   kind create cluster
   kubectl apply -f gateway-api-crd.yaml
   ```

2. **문서화**
   - 현재 Ingress 설정 문서화
   - Gateway API 등가 설정 연구

3. **모니터링 강화**
   - 현재 트래픽 패턴 분석
   - 성능 베이스라인 설정

## 결론

BoDam 프로젝트는 현재 NGINX Ingress를 유지하되, Gateway API에 대한 이해도를 높이고 향후 필요시 전환할 수 있도록 준비하는 것이 적절합니다.