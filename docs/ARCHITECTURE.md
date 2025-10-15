# 보담 아키텍처 설계

## Pod 구성 (총 5개 Pod)

### 1. bodam-backend-pod (1개 Pod, 2개 컨테이너)
**역할:** 애플리케이션 로직 처리

**컨테이너:**
1. **fastapi-container**
   - FastAPI 백엔드 서버
   - 포트: 8080
   - Health check: `/health`, `/ready`
   
2. **celery-worker-container**
   - 모든 Celery 워커 역할 통합
   - Selenium 크롤링 작업 처리
   - 백그라운드 작업 처리

**리소스:**
- CPU: 1 core
- Memory: 2Gi
- Replicas: 1

### 2. postgres-pod (1개 Pod)
**역할:** 데이터베이스

**컨테이너:**
- PostgreSQL 16 with pgvector & PostGIS
- 포트: 5432
- 볼륨: 50Gi PersistentVolume

**리소스:**
- CPU: 2 cores
- Memory: 4Gi
- Replicas: 1

### 3. redis-pod (1개 Pod)
**역할:** 메시지 브로커 & 캐시

**컨테이너:**
- Redis 7
- 포트: 6379
- 용도: Celery 브로커, 캐시

**리소스:**
- CPU: 500m
- Memory: 2Gi
- Replicas: 1

### 4. nginx-ingress-pod (1개 Pod)
**역할:** 외부 트래픽 수신 및 TLS 종료

**컨테이너:**
- NGINX Ingress Controller
- 포트: 80 (HTTP), 443 (HTTPS)
- TLS 인증서 관리

**리소스:**
- CPU: 500m
- Memory: 512Mi
- Replicas: 최소 2 (HA)

### 5. kong-gateway-pod (1개 Pod)
**역할:** API Gateway (라우팅, 인증, Rate Limiting)

**컨테이너:**
- Kong Gateway 3.5
- 포트: 8000 (Proxy), 8001 (Admin)
- DB-less 모드 (Declarative Config)

**리소스:**
- CPU: 1 core
- Memory: 1Gi
- Replicas: 1

## 트래픽 흐름

```
클라이언트
    ↓
[HTTPS/TLS]
    ↓
nginx-ingress-pod (포트 443)
    ↓ TLS 종료
[HTTP]
    ↓
┌─────────────────────┐
│                     │
│  /api/* 요청        │ → kong-gateway-pod (포트 8000)
│                     │        ↓ 라우팅/인증/Rate Limiting
│                     │   [HTTP]
│                     │        ↓
│  /static/* 요청     │        bodam-backend-pod:8080
│                     │               │
└─────────────────────┘               ├→ fastapi-container
    ↓ (bypass Kong)                   │
정적 파일 직접 서빙                    └→ celery-worker-container
```

## 데이터 플로우

### 1. API 요청 처리
```
Client → NGINX → Kong → FastAPI → PostgreSQL
                          ↓
                        Celery Task 생성
                          ↓
                        Redis Queue
                          ↓
                   Celery Worker 실행
                          ↓
                   Selenium 크롤링
                          ↓
                    PostgreSQL 저장
```

### 2. 크롤링 작업 처리
```
FastAPI: 크롤링 작업 생성
    ↓
PostgreSQL: 작업 저장 (pending 상태)
    ↓
Redis: Celery 메시지 큐에 추가
    ↓
Celery Worker: 작업 가져오기
    ↓
Selenium: 웹 크롤링 실행
    ↓
PostgreSQL: 결과 저장 (completed 상태)
```

## 네트워크 구성

### Service 정의

1. **postgres-service**
   - Type: ClusterIP (Headless)
   - Port: 5432
   - Selector: app=postgres

2. **redis-service**
   - Type: ClusterIP
   - Port: 6379
   - Selector: app=redis

3. **bodam-backend-service**
   - Type: ClusterIP
   - Port: 80 → 8080
   - Selector: app=bodam-backend

4. **kong-proxy-service**
   - Type: ClusterIP
   - Port: 8000
   - Selector: app=kong

5. **kong-admin-service**
   - Type: ClusterIP
   - Port: 8001
   - Selector: app=kong

6. **nginx-ingress-service**
   - Type: LoadBalancer
   - Port: 80, 443
   - Selector: app=nginx-ingress

### DNS 이름

- `postgres-service:5432` - PostgreSQL
- `redis-service:6379` - Redis
- `bodam-backend-service:80` - Backend
- `kong-proxy-service:8000` - Kong Proxy
- `kong-admin-service:8001` - Kong Admin

## 스토리지 구성

### PersistentVolumes

1. **postgres-pv**
   - 크기: 50Gi
   - Access Mode: ReadWriteOnce
   - 용도: PostgreSQL 데이터

2. **redis-pv**
   - 크기: 10Gi
   - Access Mode: ReadWriteOnce
   - 용도: Redis AOF 파일

## 환경 변수 흐름

### bodam-backend-pod

**fastapi-container:**
```yaml
env:
  - DATABASE_URL: postgresql+asyncpg://bodam:***@postgres-service:5432/bodam
  - REDIS_URL: redis://redis-service:6379/0
  - CELERY_BROKER_URL: redis://redis-service:6379/0
```

**celery-worker-container:**
```yaml
env:
  - DATABASE_URL: postgresql+asyncpg://bodam:***@postgres-service:5432/bodam
  - CELERY_BROKER_URL: redis://redis-service:6379/0
  - CELERY_RESULT_BACKEND: redis://redis-service:6379/0
  - SELENIUM_HEADLESS: "true"
  - SELENIUM_DRIVER_POOL_SIZE: "10"
```

### kong-gateway-pod
```yaml
env:
  - KONG_DATABASE: "off"
  - KONG_DECLARATIVE_CONFIG: /kong.yaml
  - KONG_PROXY_LISTEN: 0.0.0.0:8000
  - KONG_ADMIN_LISTEN: 0.0.0.0:8001
```

## 확장성 고려사항

### 현재 설계 (Replicas = 1)
- 단순성 우선
- 리소스 효율적
- 개발/스테이징 환경 적합

### 향후 확장 (Production)

**bodam-backend-pod:**
- Replicas: 3-5
- HPA 설정: CPU > 70% 시 자동 스케일링

**postgres-pod:**
- Replicas: 1 (Master)
- 필요시 Read Replica 추가

**redis-pod:**
- Replicas: 1
- 필요시 Redis Cluster 구성

**kong-gateway-pod:**
- Replicas: 2-3
- HPA 설정: Request/s 기반

**nginx-ingress-pod:**
- Replicas: 2 (HA 유지)

## 보안 설계

### Network Policies

```yaml
# Backend Pod만 PostgreSQL 접근 허용
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: postgres-policy
spec:
  podSelector:
    matchLabels:
      app: postgres
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: bodam-backend
```

### Secrets 관리

- PostgreSQL 비밀번호
- Redis 비밀번호 (필요시)
- JWT Secret Key
- TLS 인증서

## 모니터링 전략

### 메트릭 수집

각 Pod에서 수집할 메트릭:

1. **bodam-backend-pod**
   - FastAPI: 요청 수, 레이턴시, 에러율
   - Celery: 작업 수, 성공/실패, 큐 길이

2. **postgres-pod**
   - Connection pool 사용률
   - 쿼리 성능
   - 디스크 사용률

3. **redis-pod**
   - 메모리 사용률
   - 명령 처리 속도
   - 연결 수

4. **kong-gateway-pod**
   - 요청 수, 레이턴시
   - Rate limit 적용 횟수
   - 플러그인 성능

5. **nginx-ingress-pod**
   - 트래픽 양
   - TLS 핸드셰이크 시간
   - 업스트림 연결 상태

## 재해 복구 계획

### 백업 전략

1. **PostgreSQL**
   - 일일 전체 백업 (pg_dump)
   - WAL 아카이빙
   - 보관 기간: 30일

2. **Redis**
   - AOF 활성화
   - 일일 RDB 스냅샷

### 복구 절차

1. Pod 장애 시
   - Kubernetes가 자동 재시작
   - Liveness/Readiness Probe 활용

2. 데이터 손실 시
   - 최신 백업에서 복구
   - WAL replay (PostgreSQL)

## 비용 최적화

### 리소스 할당

| Pod | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-----|-------------|-----------|----------------|--------------|
| backend | 250m | 1000m | 512Mi | 2Gi |
| postgres | 500m | 2000m | 1Gi | 4Gi |
| redis | 100m | 500m | 256Mi | 2Gi |
| kong | 250m | 1000m | 512Mi | 1Gi |
| nginx | 100m | 500m | 128Mi | 512Mi |

**총 리소스 (Replicas=1):**
- CPU Request: 1.2 cores
- CPU Limit: 5 cores
- Memory Request: 2.4Gi
- Memory Limit: 9.5Gi

**권장 노드 사이즈:** 
- CPU: 4 cores
- Memory: 16Gi
- 1개 노드로 충분 (여유 있음)
