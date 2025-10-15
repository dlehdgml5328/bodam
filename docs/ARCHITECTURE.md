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

---

# 보담 프로젝트 - 기능 상세 명세

## API 엔드포인트 목록

### 🔐 인증 (`/api/auth`)
- **POST** `/auth/register` - 회원가입
- **POST** `/auth/login` - 로그인 (JWT 토큰 발급)
- **POST** `/auth/logout` - 로그아웃
- **POST** `/auth/refresh` - 토큰 갱신
- **POST** `/auth/password-reset` - 비밀번호 재설정 요청
- **GET** `/auth/oauth/{provider}` - OAuth 로그인 (Naver, Kakao, Google)

### 💰 후원 시스템 (`/api/donations`)
**핵심 비즈니스 로직**

- **POST** `/donations/checkout` - 후원 결제 생성
  - 1회성 후원 / 정기 후원
  - 단일 소방서 / 다중 소방서 배분
  - Toss Payments 연동
- **POST** `/donations/{id}/confirm` - 결제 승인
- **GET** `/donations` - 후원 내역 조회
- **GET** `/donations/{id}` - 후원 상세 조회
- **GET** `/donations/{id}/receipt` - 기부금 영수증 PDF 다운로드
- **POST** `/donations/{id}/refund` - 환불 요청

**후원 모드:**
- `SINGLE`: 단일 소방서 후원
- `MULTIPLE`: 다중 소방서 배분
  - `split`: 금액 균등 분할
  - `each`: 각 소방서별 개별 금액
  - `custom`: 커스텀 배분 비율

**정기 후원:**
- 월간/연간 자동 결제
- Toss Payments 빌링키 연동
- 구독 관리 (중지/재개)

### 🚒 소방서 관리 (`/api/stations`)
- **GET** `/stations` - 소방서 목록 조회
  - 지역별 필터링
  - 거리 기반 검색 (PostGIS)
- **GET** `/stations/{id}` - 소방서 상세 정보
- **GET** `/stations/{id}/stats` - 소방서 통계
  - 후원 총액
  - 출동 건수
  - 실시간 상태

### 📰 뉴스 시스템 (`/api/news`)
**AI 기반 뉴스/영상 자동 매칭**

- **GET** `/news` - 뉴스 목록 조회
- **GET** `/news/{id}` - 뉴스 상세 조회
- **POST** `/news/analyze` - AI 분석 요청
  - Naver News API 크롤링
  - YouTube API 영상 매칭
  - Together AI (Llama 3.3) 분석
  - pgvector 임베딩 저장

**뉴스 매칭 프로세스:**
1. 소방서 출동 데이터 수집
2. 네이버 뉴스 API 검색 (지역+날짜 기반)
3. YouTube API 영상 검색
4. AI 연관성 분석 (relevance_score)
5. 임베딩 생성 및 유사도 계산
6. 자동 승인/검토 대기

### 🗺️ 지리 정보 (`/api/geo`)
**PostGIS 기반 공간 검색**

- **GET** `/geo/stations/nearby` - 내 주변 소방서 검색
- **GET** `/geo/incidents` - 화재 출동 위치 조회
- **POST** `/geo/calculate-distance` - 거리 계산

### 👥 그룹/단체 (`/api/groups`)
- **POST** `/groups` - 단체 등록
- **GET** `/groups` - 단체 목록
- **GET** `/groups/{id}` - 단체 상세
- **POST** `/groups/{id}/donations` - 단체 후원

### 📊 랭킹 시스템 (`/api/rankings`)
- **GET** `/rankings/donors` - 후원자 랭킹
- **GET** `/rankings/stations` - 소방서별 후원 랭킹
- **GET** `/rankings/groups` - 단체별 랭킹

### 🔔 실시간 데이터 (`/api/live`)
- **GET** `/live/stats` - 실시간 통계
  - 전체 후원액
  - 활성 소방서 수
  - 최근 후원 내역
- **GET** `/live/incidents` - 최근 화재 출동 정보

### 💸 환불 관리 (`/api/refunds`)
- **GET** `/refunds` - 환불 요청 목록
- **POST** `/refunds/{id}/approve` - 환불 승인 (관리자)
- **POST** `/refunds/{id}/reject` - 환불 거부 (관리자)

### 🔗 웹훅 (`/api/webhooks`)
- **POST** `/webhooks/toss` - Toss Payments 웹훅
  - 결제 승인 알림
  - 가상계좌 입금 알림
  - 정기 결제 알림

### 📱 푸시 알림 (`/api/webpush`)
- **POST** `/webpush/subscribe` - 푸시 구독
- **POST** `/webpush/send` - 알림 전송

### 🕷️ 크롤러 API (`/api/crawler`)
**Selenium 동적 크롤링**

- **POST** `/crawler/jobs` - 크롤링 작업 생성
- **GET** `/crawler/jobs` - 작업 목록
- **GET** `/crawler/jobs/{id}` - 작업 상태 조회
- **GET** `/crawler/content` - 크롤링된 콘텐츠 조회

### 🩺 헬스체크 (`/api/health`)
- **GET** `/health` - 서비스 상태
- **GET** `/ready` - Readiness Probe

### 👨‍💼 관리자 (`/api/admin`)
- **GET** `/admin/resources/search` - LLM 기반 통합 검색
- **GET** `/admin/refunds` - 환불 관리
- **GET** `/admin/stats` - 대시보드 통계

---

## 데이터 모델

### 핵심 도메인 모델

#### 1. **User (사용자)**
```python
- id: UUID
- email: str (unique)
- password_hash: str
- name: str
- phone: str
- role: UserRole (USER, ADMIN)
- oauth_provider: str (naver, kakao, google)
- created_at: datetime
```

#### 2. **Donation (후원)**
```python
- id: UUID
- user_id: UUID (FK → users)
- amount: Decimal
- type: DonationType (ONE_TIME, RECURRING)
- status: DonationStatus (PENDING, COMPLETED, FAILED, REFUNDED)
- mode: DonationMode (SINGLE, MULTIPLE)
- payment_method: str
- toss_payment_key: str
- toss_order_id: str
- message: str (최대 500자)
- is_anonymous: bool
- created_at: datetime
- completed_at: datetime
```

#### 3. **DonationAllocation (후원 배분)**
```python
- id: UUID
- donation_id: UUID (FK → donations)
- fire_station_id: UUID (FK → fire_stations)
- amount: Decimal
- allocation_type: AllocationType (PRIMARY, SPLIT, EACH, CUSTOM)
```

#### 4. **DonationSubscription (정기 후원)**
```python
- id: UUID
- user_id: UUID (FK → users)
- fire_station_id: UUID (FK → fire_stations)
- amount: Decimal
- cycle: SubscriptionCycle (MONTHLY, YEARLY)
- status: SubscriptionStatus (ACTIVE, PAUSED, CANCELLED)
- billing_key: str (Toss 빌링키)
- next_billing_date: date
- start_date: date
- end_date: date
```

#### 5. **FireStation (소방서)**
```python
- id: UUID
- name: str
- address: str
- location: Geometry(POINT, SRID=4326)  # PostGIS
- phone: str
- station_code: str (unique)
- region: str
- district: str
- status: StationStatus (ACTIVE, CLOSED, MERGED)
- total_donations: Decimal
- donation_count: int
- created_at: datetime
```

#### 6. **NewsContent (뉴스)**
```python
- id: UUID
- title: str
- content: text
- source: str (naver, youtube)
- source_url: str
- published_at: datetime
- location: Geometry(POINT)  # PostGIS
- embedding: Vector(1536)  # pgvector
- relevance_score: int (0-100)
- summary: text
- keywords: ARRAY[str]
- status: ContentStatus (AUTO_APPROVED, PENDING_REVIEW, REJECTED)
- fire_station_id: UUID (FK)
```

#### 7. **NewsMatch (뉴스-출동 매칭)**
```python
- id: UUID
- news_content_id: UUID (FK → news_content)
- dispatch_event_id: UUID (FK → dispatch_events)
- match_confidence: float (0.0-1.0)
- ai_reasoning: text
- created_at: datetime
```

#### 8. **Group (단체)**
```python
- id: UUID
- name: str
- code: str (unique, 초대 코드)
- contact_name: str
- contact_email: str
- contact_phone: str
- total_donations: Decimal
- member_count: int
- is_verified: bool
```

#### 9. **FireIncident (화재 출동)**
```python
- id: UUID
- fire_station_id: UUID (FK)
- location: Geometry(POINT)
- incident_type: str
- severity: int
- dispatch_time: datetime
- arrival_time: datetime
- description: text
```

#### 10. **Refund (환불)**
```python
- id: UUID
- donation_id: UUID (FK → donations)
- reason: str
- status: RefundStatus (PENDING, APPROVED, REJECTED, COMPLETED)
- requested_at: datetime
- processed_at: datetime
- admin_note: text
```

#### 11. **Receipt (영수증)**
```python
- id: UUID
- donation_id: UUID (FK → donations)
- user_id: UUID (FK → users)
- issue_date: date
- pdf_url: str
- receipt_number: str (unique)
- id_number: str (주민등록번호 뒤 7자리)
```

#### 12. **Ranking (랭킹)**
```python
- id: UUID
- entity_type: str (user, station, group)
- entity_id: UUID
- rank: int
- total_amount: Decimal
- period: str (daily, weekly, monthly, yearly)
- calculated_at: datetime
```

#### 13. **Notification (알림)**
```python
- id: UUID
- user_id: UUID (FK → users)
- type: NotificationType
- title: str
- message: text
- is_read: bool
- created_at: datetime
```

#### 14. **CrawledContent (크롤링 콘텐츠)** - Selenium
```python
- id: UUID
- url: str
- content_type: str
- html_content: text
- extracted_data: JSON
- crawled_at: datetime
- status: str
```

#### 15. **SeleniumCrawlJob (크롤링 작업)** - Selenium
```python
- id: UUID
- url: str
- status: JobStatus (PENDING, RUNNING, COMPLETED, FAILED)
- result_id: UUID (FK → crawled_content)
- error_message: text
- created_at: datetime
- completed_at: datetime
```

---

## 외부 API 연동

### 1. **Toss Payments API**
**파일:** `backend/src/integrations/toss_payments.py`

**기능:**
- 결제 생성 (`POST /v1/payments`)
- 결제 승인 (`POST /v1/payments/{paymentKey}/confirm`)
- 빌링키 발급 (정기 결제)
- 자동 결제 (`POST /v1/billing/{billingKey}/payments`)
- 결제 취소 (`POST /v1/payments/{paymentKey}/cancel`)
- 웹훅 수신 (결제 상태 변경 알림)

**인증:** Basic Auth (Secret Key)

### 2. **Naver News API**
**파일:** `backend/src/integrations/naver_news.py`

**기능:**
- 뉴스 검색 (`GET /v1/search/news.json`)
  - 쿼리: 지역 + 화재 키워드
  - 날짜 기반 필터링
  - 관련도/최신순 정렬

**인증:** Client ID + Client Secret (Header)

### 3. **YouTube Data API v3**
**파일:** `backend/src/integrations/youtube.py`

**기능:**
- 영상 검색 (`youtube.search().list()`)
  - 쿼리: 소방서명 + 화재 키워드
  - 날짜 기반 필터링
  - 영상 메타데이터 수집

**인증:** API Key

### 4. **Together AI (LLM)**
**파일:** `backend/src/integrations/together_ai.py`

**기능:**
- 뉴스-출동 연관성 분석
- 모델: `meta-llama/Llama-3.3-70B-Instruct-Turbo-Free`
- 임베딩 생성 (pgvector 저장)
- 요약 생성
- 키워드 추출

**인증:** Bearer Token

### 5. **Kakao OAuth & Biz API**
**파일:** `backend/src/integrations/kakao_oauth.py`, `kakao_biz.py`

**기능:**
- 소셜 로그인
- 카카오톡 알림 발송

### 6. **Naver/Google OAuth**
**파일:** `backend/src/integrations/naver_oauth.py`, `google_oauth.py`

**기능:**
- 소셜 로그인

---

## 크롤링 시스템

### 정적 크롤링 (BeautifulSoup4)
**사용처:**
- 네이버 뉴스 (HTML 파싱)
- 간단한 정적 페이지

**장점:**
- 빠른 속도
- 적은 리소스 사용

### 동적 크롤링 (Selenium)
**파일:** `backend/src/services/crawler/selenium_crawler.py`

**사용처:**
- JavaScript 렌더링 필요 페이지
- 무한 스크롤
- AJAX 동적 로딩

**구조:**
- `WebDriverPool`: 크롬 드라이버 풀 관리
- `SeleniumCrawler`: 크롤링 로직
- `ContentExtractor`: HTML 파싱 (BS4 사용)
- Celery Worker: 비동기 크롤링 작업

**흐름:**
```
1. API 요청 (/api/crawler/jobs)
2. Celery Worker에 작업 전달
3. WebDriverPool에서 드라이버 할당
4. Selenium으로 페이지 렌더링
5. BeautifulSoup4로 HTML 파싱
6. 결과 DB 저장 (crawled_content)
7. 드라이버 반환
```

---

## AI/ML 파이프라인

### 뉴스-출동 자동 매칭 시스템

**트리거:** Celery Beat 스케줄러 (매 5분)

**프로세스:**
```
1. 최근 화재 출동 데이터 조회 (dispatch_events)
2. 네이버 뉴스 API 검색
   - 쿼리: "{지역} {소방서} 화재"
   - 날짜: 출동 시각 ± 3시간
3. YouTube API 검색
   - 쿼리: "{지역} {소방서} 화재 영상"
4. Together AI 분석 요청
   - 프롬프트: "이 뉴스/영상이 출동 건과 관련있는가?"
   - 출력: relevance_score (0-100), reasoning
5. 임베딩 생성 (pgvector)
   - 뉴스 텍스트 → Vector(1536)
6. 유사도 계산 (cosine similarity)
7. 자동 승인/검토 대기 판단
   - relevance_score >= 80: AUTO_APPROVED
   - relevance_score >= 50: PENDING_REVIEW
   - relevance_score < 50: REJECTED
8. news_match 테이블에 매칭 정보 저장
```

**Celery 태스크:**
- `backend/src/workers/news_matcher_worker.py`

---

## 보안

### 인증/인가
- **JWT 토큰 기반 인증**
- **세션 쿠키** (HttpOnly, Secure, SameSite)
- **CSRF 토큰** (POST/PUT/DELETE 요청)
- **OAuth 2.0** (Naver, Kakao, Google)

### 데이터 보호
- **비밀번호 해싱**: bcrypt
- **개인정보 암호화**: 주민등록번호, 연락처
- **TLS 1.3** (HTTPS)

### API 보안
- **Kong Gateway Rate Limiting**
  - `/api/auth/*`: 10 req/min
  - `/api/donations/*`: 30 req/min
  - `/api/*`: 100 req/min
- **CORS 설정**
- **SQL Injection 방지** (SQLAlchemy ORM)

---

## 모니터링 & 로깅

### 로깅
- **구조화 로깅**: `structlog`
- **로그 레벨**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **파일:** `backend/src/monitoring/logging.py`

### 메트릭스
- **Prometheus 수집**
- **Grafana 대시보드**
- **주요 메트릭:**
  - API 응답 시간
  - 후원 건수/금액
  - 크롤링 작업 성공률
  - DB 쿼리 성능

### 알림
- **Slack 알림**
  - 결제 실패
  - 크롤링 오류
  - 시스템 장애

---

## 기술 스택 요약

### Backend
- **Python 3.12+**
- **FastAPI** (비동기 웹 프레임워크)
- **SQLAlchemy 2.0** (ORM, asyncpg)
- **Pydantic** (데이터 검증)
- **Celery** (비동기 작업 큐)
- **Redis** (캐시 + Celery 브로커)

### Database
- **PostgreSQL 16**
  - **pgvector** (임베딩 검색)
  - **PostGIS** (지리 정보)

### 크롤링
- **BeautifulSoup4** (HTML 파싱)
- **Selenium** (브라우저 자동화)
- **ChromeDriver** (Headless Chrome)

### AI/ML
- **Together AI** (Llama 3.3 70B)
- **pgvector** (임베딩 저장/검색)

### Infrastructure
- **Kubernetes** (컨테이너 오케스트레이션)
- **Kong Gateway** (API Gateway)
- **Nginx** (Ingress Controller, TLS 종료)

### 외부 서비스
- **Toss Payments** (PG)
- **Naver API** (뉴스, OAuth)
- **YouTube API** (영상 검색)
- **Kakao API** (OAuth, 알림)
- **Google OAuth**

### Frontend (참고)
- **Next.js** (React SSR)
- **TypeScript**
- **TailwindCSS**

---

## 디렉토리 구조

```
backend/
├── src/
│   ├── api/               # API 엔드포인트
│   │   ├── auth.py        # 인증
│   │   ├── donations.py   # 후원 (핵심)
│   │   ├── stations.py    # 소방서
│   │   ├── news.py        # 뉴스
│   │   ├── crawler/       # 크롤러 API
│   │   └── ...
│   ├── models/            # 데이터 모델
│   │   ├── donation.py
│   │   ├── fire_station.py
│   │   ├── news_content.py
│   │   └── ...
│   ├── services/          # 비즈니스 로직
│   │   ├── donation_service.py
│   │   ├── news_service.py
│   │   ├── ai_service.py
│   │   └── crawler/       # Selenium 크롤러
│   ├── integrations/      # 외부 API
│   │   ├── toss_payments.py
│   │   ├── naver_news.py
│   │   ├── youtube.py
│   │   ├── together_ai.py
│   │   └── ...
│   ├── workers/           # Celery Workers
│   │   ├── news_matcher_worker.py
│   │   └── selenium_crawler_worker.py
│   ├── database/          # DB 연결
│   ├── security/          # 인증/인가
│   ├── monitoring/        # 로깅/메트릭스
│   └── config.py          # 설정
├── tests/                 # 테스트
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   └── performance/
├── alembic/               # DB 마이그레이션
└── requirements.txt       # 의존성

infra/
├── k8s/                   # Kubernetes 매니페스트
│   ├── kong/              # Kong Gateway
│   ├── nginx/             # Nginx Ingress
│   ├── backend/           # FastAPI + Celery
│   ├── database/          # PostgreSQL + Redis
│   └── ...
└── nginx/                 # Nginx 설정

specs/                     # 기능 명세
├── 001-bashclaudecli-specify-bodam/
└── 002-kong-gateway-selenium-migration/

docs/                      # 문서
├── ARCHITECTURE.md        # 이 파일
└── DEPLOYMENT_GUIDE.md    # 배포 가이드
```

---

## 개발 워크플로우

### 로컬 개발 환경
```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload

# Celery Worker
celery -A src.worker.celery_app worker --loglevel=info

# Celery Beat (스케줄러)
celery -A src.worker.celery_app beat --loglevel=info
```

### 테스트
```bash
# 단위 테스트
pytest tests/unit/

# 통합 테스트
pytest tests/integration/

# 계약 테스트 (API)
pytest tests/contract/

# 커버리지
pytest --cov=src --cov-report=html
```

### 코드 품질
```bash
# 린팅
ruff check .

# 타입 체크
mypy .

# 포맷팅
ruff format .
```

---

**작성일:** 2025-10-15
**버전:** 1.1 (develop 브랜치 기준, Kong Gateway & Selenium 통합)
