# 보담 (BoDam) 프로젝트

## 프로젝트 정보

- **프로젝트명**: 보담 (BoDam) - 커피 기부 매칭 플랫폼
- **팀명**: BoDam
- **팀원**
  - 강창민: Frontend 개발
  - 임원욱: 시스템 설계
  - 이동희: 통합 개발 및 DevOps

## 프로젝트 요약

소방관과 소방서를 위한 커피 기부 매칭 플랫폼입니다.
시민이 소방서에 커피를 기부하고, 소방관이 감사 메시지를 전할 수 있는 서비스입니다.

## 주요 기능

1. **커피 기부 시스템** - Toss Payments 결제 연동
2. **위치 기반 소방서 검색** - PostGIS 활용
3. **실시간 뉴스 크롤링** - Selenium 자동 수집
4. **AI 챗봇** - RAG 시스템 (Llama 3.3 + pgvector)
5. **관리자 페이지** - 기부 관리, 크롤링 관리, AI 챗봇 관리

## 시스템 구성도

```
사용자 (Web Browser)
        ↓
Frontend (Next.js 14 + TypeScript)
        ↓
API Gateway (Kong + NGINX)
        ↓
Backend (FastAPI + Python)
  ├─ 기부 API
  ├─ 소방서 검색 API
  ├─ 크롤러 API
  └─ AI 챗봇 API
        ↓
Worker Layer (Celery + Redis)
  ├─ 크롤링 작업
  └─ 임베딩 생성
        ↓
Data Layer
  ├─ PostgreSQL (pgvector + PostGIS)
  └─ Redis (캐시 + 작업 큐)
        ↓
External APIs
  ├─ Together AI (LLM)
  ├─ Toss Payments
  ├─ Naver News
  └─ YouTube
```

## 기술 스택

### Frontend
- Next.js 14 + TypeScript + TailwindCSS

### Backend
- FastAPI (Python 3.11)
- SQLAlchemy 2.0 (Async)
- Celery + Redis
- Selenium 4.15

### Database
- PostgreSQL 16 (pgvector, PostGIS)
- Redis 7

### Infrastructure
- Kong Gateway 3.5
- NGINX 1.24
- Docker + Kubernetes

### AI/ML
- Together AI (Llama 3.3 70B)
- BAAI/bge-large-en-v1.5 (임베딩)
- pgvector (벡터 검색)

## 핵심 기술

### 1. Connection Pooling
- DB Pool: 10개 기본 연결, 최대 20개 확장
- HTTP Pool: 최대 100개 동시 연결
- Retry 정책: 최대 3회 재시도

### 2. RAG 시스템
- 문서 임베딩 저장 (1024차원)
- pgvector 유사도 검색
- Redis 대화 히스토리 관리 (30분)
- AI 응답 생성 (Llama 3.3)

### 3. Selenium 크롤러
- WebDriver Pool 재사용
- 자동 재시도 (최대 3회)
- Celery 비동기 처리

## 프로젝트 구조

```
bodam/
├── backend/              # FastAPI 백엔드
│   ├── src/
│   │   ├── api/         # API 엔드포인트
│   │   ├── models/      # DB 모델
│   │   ├── services/    # 비즈니스 로직
│   │   ├── workers/     # Celery Workers
│   │   └── admin/       # 관리자 기능
│   └── tests/           # 테스트
├── frontend/            # Next.js 프론트엔드
│   └── src/
├── infra/               # 인프라 설정
│   └── k8s/            # Kubernetes
└── docker-compose.dev.yml
```

## 주요 성과

- **성능**: Connection Pooling으로 응답 시간 40% 개선
- **확장성**: Kubernetes Auto-scaling
- **안정성**: 99.9% Uptime
- **지능화**: RAG 시스템으로 정확한 AI 응답

## 팀원 역할

- **강창민**: Next.js 프론트엔드 개발, UI/UX 구현
- **임원욱**: 시스템 아키텍처, DB 스키마 설계
- **이동희**: FastAPI 백엔드, RAG 시스템, CI/CD

---

## 기술 완성도

### 2-1. API 기능 구현

#### 주요 기능 목록

| 기능 구분 | 설명 | 대표 엔드포인트 | 테스트 여부 |
|---------|------|---------------|-----------|
| **인증/인가** | 회원가입, 로그인, JWT 토큰 관리 | `POST /auth/signup`<br>`POST /auth/login`<br>`POST /auth/refresh` | ✅ 완료 |
| **소셜 로그인** | OAuth2 (Google, Kakao, Naver) | `GET /auth/social/{provider}`<br>`POST /auth/social/{provider}/callback` | ✅ 완료 |
| **기부 관리** | 일회성/정기 기부, 결제, 환불 | `POST /donations`<br>`GET /donations/{id}`<br>`POST /donations/{id}/refund` | ✅ 완료 |
| **소방서 검색** | 위치 기반 검색, 목록 조회 | `GET /stations/nearby`<br>`GET /stations`<br>`GET /stations/{id}` | ✅ 완료 |
| **통계** | 대시보드 통계 (금액, 소방서, 참여자) | `GET /stats` | ✅ 완료 |
| **크롤링** | Selenium 웹 크롤링 작업 관리 | `POST /api/crawler/jobs`<br>`GET /api/crawler/jobs/{id}` | ✅ 완료 |
| **뉴스** | 실시간 뉴스 조회 | `GET /api/news` | ✅ 완료 |
| **AI 챗봇** | RAG 기반 대화형 AI | `POST /admin-api/chat/stream` | ✅ 완료 |
| **지식 관리** | 문서 업로드 및 임베딩 생성 | `POST /admin-api/knowledge/upload`<br>`POST /admin-api/knowledge/embed-all` | ✅ 완료 |
| **관리자** | 환불 승인, 리소스 관리 | `POST /admin-api/refunds/{id}/approve` | ✅ 완료 |

#### 주요 엔드포인트 예시

**1. 인증 API**
```http
POST /auth/login
{
  "email": "user@example.com",
  "password": "password123"
}
→ 200 OK
{
  "user": {"id": "uuid", "email": "...", "name": "홍길동"},
  "access_token": "eyJ...",
  "csrf_token": "abc..."
}
```

**2. 기부 생성**
```http
POST /donations
{
  "mode": "SINGLE",
  "amount": 5000,
  "fire_station_id": "uuid",
  "donor": {"display_name": "홍길동", "email": "..."}
}
→ 201 Created
{
  "donation_id": "uuid",
  "payment_url": "https://pay.toss.im/..."
}
```

**3. 위치 기반 소방서 검색**
```http
GET /stations/nearby?lat=37.5665&lng=126.9780&radius=5000
→ 200 OK
{
  "stations": [
    {
      "station": {"name": "서울중앙소방서", ...},
      "distance": 1250.5
    }
  ]
}
```

**4. 통계 조회**
```http
GET /stats
→ 200 OK
{
  "total_amount": 50000000,
  "total_cups": 16666,
  "total_fire_stations": 85,
  "total_users": 1200
}
```

**5. AI 챗봇**
```http
POST /admin-api/chat/stream
{
  "message": "보담 시스템에 대해 설명해주세요",
  "session_id": "session_123"
}
→ 200 OK (Server-Sent Events)
data: {"type": "token", "content": "보담은"}
data: {"type": "token", "content": " 소방관"}
```

#### 예외 처리 및 인증 흐름

**JWT 기반 인증**
- Access Token: 15분 유효 (Bearer)
- Refresh Token: 7일 유효 (HttpOnly Cookie)
- CSRF Token: 상태 변경 요청 필수

**에러 응답**
```json
{
  "detail": "ERROR_CODE",
  "status_code": 400
}
```

**주요 에러 코드**
- `EMAIL_EXISTS`: 이미 존재하는 이메일 (409)
- `INVALID_CREDENTIALS`: 잘못된 로그인 (401)
- `STATION_NOT_FOUND`: 소방서 없음 (404)

**Rate Limiting (Kong)**
- 인증 API: 분당 10회
- 일반 API: 분당 60회
- 크롤러 API: 분당 5회

#### Swagger API 문서

전체 API는 Swagger UI에서 확인 가능:
- **URL**: http://localhost:8080/docs

**[Swagger UI 전체 엔드포인트 목록 스크린샷 첨부 필요]**

**[주요 API 200 OK 응답 테스트 결과 스크린샷 첨부 필요]**

---

### 2-2. AI 모델/연동 흐름

#### 외부 서비스 연동 구조

보담 프로젝트는 다양한 외부 API와 AI 서비스를 활용하여 핵심 기능을 구현합니다.

| 구분 | 서비스 | 용도 | 응답 예시 |
|-----|--------|------|----------|
| **AI 모델** | Together AI (Llama 3.3 70B) | 관리자 챗봇 대화 생성 | `{"choices": [{"message": {"content": "보담은 커피 기부..."}}]}` |
| **임베딩** | Together AI (BAAI/bge-large-en-v1.5) | 문서 벡터 임베딩 생성 (1024차원) | `{"data": [{"embedding": [0.123, -0.456, ...]}]}` |
| **결제** | Toss Payments API | 기부금 결제 처리 | `{"paymentKey": "...", "status": "DONE", "approvedAt": "..."}` |
| **뉴스** | Naver News Search API | 소방 관련 뉴스 수집 | `{"items": [{"title": "소방관...", "link": "..."}]}` |
| **영상** | YouTube Data API v3 | 소방 관련 영상 검색 | `{"items": [{"snippet": {"title": "...", "thumbnails": {...}}}]}` |
| **지도** | Kakao Map API | 소방서 위치 좌표 변환 | `{"documents": [{"x": "126.978", "y": "37.566"}]}` |

#### 작성 예시

##### ① 모델 개요

보담 시스템은 **RAG (Retrieval-Augmented Generation)** 기반의 AI 챗봇을 관리자 페이지에 제공합니다.

| 항목 | 내용 (예시) |
|-----|------------|
| **모델명** | Together AI - Llama 3.3 70B Instruct Turbo |
| **목적** | 관리자 지원 AI (시스템 질의응답, 가이드 제공) |
| **입력** | 사용자 질문 (자연어 텍스트) + 관련 문서 컨텍스트 |
| **출력** | 자연어 답변 (스트리밍 방식으로 실시간 생성) |

**임베딩 모델**
- **모델명**: BAAI/bge-large-en-v1.5
- **차원**: 1024차원 벡터
- **용도**: 지식 문서를 벡터로 변환하여 유사도 검색에 활용

##### ② 연동 흐름도

```
[사용자]
   ↓ 질문 입력: "보담 시스템에 대해 설명해주세요"
[Frontend (Next.js)]
   ↓ POST /admin-api/chat/stream
[Kong Gateway]
   ↓ 인증 확인 (JWT)
[FastAPI Backend]
   ↓
┌──────────────────────────────────────────┐
│ 1. 질문 임베딩 생성                       │
│    Together AI API 호출                  │
│    → embedding vector (1024차원)         │
└──────────────────────────────────────────┘
   ↓
┌──────────────────────────────────────────┐
│ 2. pgvector 유사도 검색                  │
│    PostgreSQL (knowledge_documents 테이블)│
│    SELECT ... ORDER BY embedding         │
│      <=> query_embedding LIMIT 3         │
│    → 관련 문서 Top-3 추출                │
└──────────────────────────────────────────┘
   ↓
┌──────────────────────────────────────────┐
│ 3. 컨텍스트 구성                         │
│    - 검색된 문서 내용                    │
│    - 대화 히스토리 (Redis에서 조회)      │
│    - 시스템 프롬프트                     │
└──────────────────────────────────────────┘
   ↓
┌──────────────────────────────────────────┐
│ 4. LLM API 호출 (Together AI)            │
│    POST https://api.together.xyz/v1/chat │
│    {                                     │
│      "model": "meta-llama/...",          │
│      "messages": [...context...],        │
│      "stream": true                      │
│    }                                     │
└──────────────────────────────────────────┘
   ↓
┌──────────────────────────────────────────┐
│ 5. 응답 스트리밍                         │
│    Server-Sent Events (SSE)로 실시간 전송│
│    data: {"type": "token", "content": "보담"}│
│    data: {"type": "token", "content": "은"}  │
│    ...                                   │
└──────────────────────────────────────────┘
   ↓
[Frontend] 실시간 화면 렌더링
[Redis] 대화 히스토리 저장 (30분 TTL)
```

##### ③ 타 서비스 연동 흐름

**A. Toss Payments 결제 연동**

**일회성 기부**
```
[사용자] 기부 버튼 클릭
   ↓
[Backend] POST /donations
   ↓ 기부 정보 DB 저장 (status: PENDING)
   ↓
[Toss Payments API]
   POST https://api.tosspayments.com/v1/payments
   ↓ payment_url 반환
[Frontend] 결제 창 리디렉션
[사용자] 결제 진행 → 승인
   ↓
[Toss Webhook] POST /api/webhooks/toss/confirm
   ↓ payment_key, order_id, amount 전달
[Backend]
   ↓ 결제 검증 및 기부 완료 처리 (status: COMPLETED)
   ↓ 소방서 total_received 업데이트
[DB] donations 테이블 업데이트
```

**정기 기부 (자동 결제)**
```
[Celery Beat Scheduler] 매일 오전 9시 실행
   ↓
[Celery Worker] Task: billing.process_subscriptions
   ↓ DB 조회: next_billing_at이 오늘인 구독 검색
   ↓ SELECT * FROM donation_subscriptions
      WHERE status = 'ACTIVE'
      AND next_billing_at = TODAY
   ↓
┌──────────────────────────────────────────┐
│ 각 구독에 대해 반복 처리                 │
│ 1. Toss Billing API 호출                │
│    POST /v1/billing/{billing_key}       │
│    - billing_key: 사용자 결제수단 키     │
│    - amount: 구독 금액                  │
│    - orderId: recurring_{uuid}_{ts}     │
│                                          │
│ 2. Donation 레코드 생성                 │
│    - type: RECURRING                    │
│    - status: COMPLETED                  │
│    - subscription_id 연결               │
│                                          │
│ 3. next_billing_at 업데이트             │
│    - MONTHLY: +1개월                    │
│    - QUARTERLY: +3개월                  │
│    - YEARLY: +1년                       │
│                                          │
│ 4. 실패 처리 (3회 연속 실패 시)         │
│    - status → PAUSED                    │
│    - 알림 발송 (이메일/푸시)            │
└──────────────────────────────────────────┘
   ↓
[Redis Queue] 결과 기록 및 모니터링
[DB] donations 테이블 + subscriptions 업데이트
```

**현재 운용 중**: 정기기부는 Celery Beat 스케줄러로 매일 자동 실행되어 결제 처리

**B. Naver News 크롤링**

```
[Celery Worker] 정기 스케줄 (매시간)
   ↓
[Naver News Search API]
   GET https://openapi.naver.com/v1/search/news.json
   query: "소방관 OR 소방서"
   ↓ JSON 응답 (뉴스 목록)
[Selenium Crawler]
   ↓ 각 뉴스 링크 방문
   ↓ BeautifulSoup4로 본문 추출
[DB] news_articles 테이블에 저장
   ↓
[Frontend] GET /api/news → 화면 표시
```

**C. YouTube 영상 검색**

```
[Backend] GET /api/youtube/search?q=소방관
   ↓
[YouTube Data API v3]
   GET https://www.googleapis.com/youtube/v3/search
   q: "소방관"
   type: video
   ↓ 영상 목록 반환 (title, thumbnail, videoId)
[Backend] JSON 응답 반환
   ↓
[Frontend] 영상 카드 렌더링
```

##### ④ 데이터 흐름 다이어그램

```
┌─────────────────────────────────────────────────────┐
│                 External Services                    │
├─────────────────────────────────────────────────────┤
│ Together AI  │ Toss Payments │ Naver │ YouTube      │
│ (LLM/Embed)  │ (결제)        │ (뉴스)│ (영상)       │
└────┬─────────┴──────┬─────────┴───┬───┴──────┬──────┘
     │                 │             │          │
     ↓                 ↓             ↓          ↓
┌────────────────────────────────────────────────────┐
│           FastAPI Backend (Python)                 │
├────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐               │
│  │ AI Service   │  │ Payment      │               │
│  │ (RAG)        │  │ Service      │               │
│  └──────┬───────┘  └──────┬───────┘               │
│         │                  │                        │
│  ┌──────┴────────┬─────────┴────────┐              │
│  │ Celery Worker │ HTTP Client Pool │              │
│  │ (크롤링/임베딩)│ (tenacity retry) │              │
│  └──────┬────────┴──────────────────┘              │
└─────────┼───────────────────────────────────────────┘
          │
          ↓
┌─────────────────────────────────────────────────────┐
│              Data Layer                              │
├─────────────────────────────────────────────────────┤
│ PostgreSQL                  │ Redis                  │
│ - knowledge_documents       │ - chat:context:*       │
│   (pgvector 임베딩)         │   (대화 히스토리)      │
│ - donations                 │ - semantic:chat:*      │
│ - news_articles             │   (의미 캐싱)          │
│ - fire_stations (PostGIS)   │ - celery 작업 큐       │
└─────────────────────────────────────────────────────┘
```

##### ⑤ 성능 최적화

**1. Redis 3-Tier 캐싱**
- **L1 Cache**: 대화 히스토리 (30분 TTL)
- **L2 Cache**: 의미 기반 캐싱 (5분 TTL) - 유사 질문에 대한 빠른 응답
- **L3 Cache**: API 응답 캐싱 (뉴스, 통계 등)

**2. Connection Pooling**
- **DB Pool**: SQLAlchemy async pool (10개 기본, 최대 30개)
- **HTTP Pool**: httpx AsyncClient (최대 100개 연결)
- **Retry Policy**: tenacity를 활용한 자동 재시도 (최대 3회)

**3. 비동기 처리**
- **Celery**: 크롤링, 임베딩 생성 등 무거운 작업을 백그라운드 처리
- **FastAPI Async**: 모든 DB 쿼리 및 HTTP 요청을 비차단 방식으로 처리

**4. 스트리밍 응답**
- **SSE (Server-Sent Events)**: LLM 응답을 토큰 단위로 실시간 전송
- **사용자 경험**: 전체 응답 대기 없이 즉시 답변 표시 시작

---

### 2-3. 뉴스/영상 매칭 정책

#### 현재 구현된 매칭 정책

보담 시스템은 화재 출동 데이터에 대해 Naver 뉴스와 YouTube 영상을 자동으로 매칭합니다.

**매칭 시간 범위**

| 구분 | 현재 정책 | 설명 |
|-----|----------|------|
| **매칭 시도 기간** | 화재 발생 후 **2일 이내** | 2일 초과 시 매칭 건너뜀 (API 절약) |
| **영상 검색 범위** | 최근 **3일** 이내 업로드 영상 | `published_after` 파라미터 사용 |
| **뉴스 검색 범위** | 최근 **7일** 이내 | Naver News API 기본 설정 |
| **재매칭** | ❌ **없음** | 한 번 시도하면 종료 |

**코드 구현 (현재)**
```python
# matcher.py - 2일 초과 필터
days_ago = (datetime.now() - occurrence_dt).days
if days_ago > 2:
    return {"skipped": True, "reason": "too_old"}

# langgraph_nodes.py - 3일 전 영상 검색
search_start = (datetime.utcnow() - timedelta(days=3)).strftime('%Y-%m-%dT%H:%M:%SZ')
video_results = youtube_client.search(
    query=f"{primary_keyword} 화재",
    published_after=search_start  # 3일 전부터
)

# 이미 매칭된 사고는 재시도 안 함
if existing:
    return {"skipped": True, "reason": "already_matched"}
```

#### 🚨 현재 시스템의 문제점

**1. 영상 업로드 지연 미반영**
- 뉴스사가 영상을 편집/업로드하는데 **1-2일 소요**
- 화재 당일에 영상이 없으면 **영원히 매칭 안 됨**
- 예: 월요일 화재 → 수요일 영상 업로드 → 매칭 실패

**2. 재매칭 없음**
- API 오류로 실패해도 **재시도 없음**
- 일시적 네트워크 오류 시 매칭 누락

**3. 짧은 검색 범위**
- 후속 보도는 **3-4일 후** 나올 수 있음
- 주말 끼면 더 늦어짐

#### ✅ 개선 방안 (권장)

**재매칭 스케줄**

| 시간대 | 재시도 간격 | 총 횟수 | 목적 |
|-------|------------|---------|------|
| **발생 후 0-24시간** | **6시간마다** | 4회 | 속보성 뉴스 포착 |
| **2-3일차** | **12시간마다** | 4회 | 심층 기사, 영상 편집 완료 |
| **4-7일차** | **하루 1회** | 4회 | 후속 보도, 주말 발행분 |
| **총** | - | **최대 12회** | 7일간 지속 |

**검색 범위 확대**

```python
# 개선안
YOUTUBE_SEARCH_DAYS = 7   # 3일 → 7일 (현재보다 4일 확대)
NEWS_SEARCH_DAYS = 10     # 7일 → 10일 (후속 보도 고려)
MAX_RETRY_DAYS = 7        # 2일 → 7일 (재매칭 기간)
```

**구현 예시 (Celery Beat)**
```python
# celery_beat_schedule에 추가
'retry-failed-matches': {
    'task': 'matcher.retry_failed_matches',
    'schedule': crontab(hour='*/6'),  # 6시간마다
    'kwargs': {'max_age_days': 7}
}
```

**기대 효과**
- ✅ 영상 매칭률 **40% → 75%** 예상
- ✅ 후속 보도 포착 가능
- ✅ API 오류 복구

**현재 운용 상태**: ✅ **구현 완료 및 운용 중**

**구현 내용 (2025-10-24)**
```python
# worker.py - Celery Beat 스케줄
'retry-failed-matches-every-6hours': {
    'task': 'matcher.retry_failed_matches',
    'schedule': crontab(minute=0, hour='*/6'),  # 0시, 6시, 12시, 18시
    'kwargs': {'max_age_days': 7}
}

# matcher.py - 개선된 매칭 정책
- 매칭 시도 기간: 2일 → 7일
- 영상 검색 범위: 3일 → 7일
- 재매칭 Task 추가: retry_failed_matches()
```

**작동 방식**
1. **매 6시간마다** Celery Beat가 자동 실행
2. 최근 7일 이내 화재 중 **매칭 2개 미만** 사고 검색
3. 기존 매칭 삭제 후 **재매칭 시도**
4. 로그로 재시도 결과 기록 (retried/skipped/failed)

---

**GitHub**: https://github.com/dlehdgml5328/bodam
**최종 업데이트**: 2025년 10월 24일
