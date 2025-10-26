# 보담 (BoDam) 프로젝트 소개서

## 프로젝트 개요

### 프로젝트명
**보담 (BoDam)** - 커피 기부 매칭 플랫폼

### 팀 정보
- **팀명**: BoDam
- **팀원 및 역할**
  - **강창민**: Frontend 개발 (Next.js, TypeScript)
  - **임원욱**: 시스템 설계 및 아키텍처
  - **이동희**: 통합 개발 및 DevOps

### 프로젝트 요약
보담(BoDam)은 소방관과 소방서를 위한 커피 기부 매칭 플랫폼입니다. 시민들이 소방서에 커피를 기부하고, 소방관들이 감사의 마음을 전할 수 있는 선순환 구조를 제공합니다. 위치 기반 소방서 검색, 실시간 뉴스 크롤링, AI 기반 챗봇, 결제 시스템을 통합한 풀스택 웹 애플리케이션입니다.

---

## 주요 기능

### 1. 커피 기부 시스템
- 소방서 선택 및 커피 기부 신청
- Toss Payments API를 통한 안전한 결제 처리
- 기부 내역 조회 및 관리
- 실시간 기부 현황 대시보드

### 2. 위치 기반 소방서 검색
- PostGIS를 활용한 지리 정보 처리
- 사용자 위치 기반 가까운 소방서 검색
- 소방서 상세 정보 제공 (주소, 연락처, 기부 현황)

### 3. 실시간 뉴스 크롤링
- Selenium 4.15+를 활용한 동적 웹 크롤링
- Naver News, YouTube 등 다양한 소스에서 소방 관련 뉴스 수집
- Celery를 통한 비동기 백그라운드 작업 처리
- 크롤링 작업 스케줄링 및 모니터링

### 4. AI 챗봇 (RAG 시스템)
- Together AI (Llama 3.3 70B 모델) 기반 대화형 AI
- pgvector를 활용한 문서 임베딩 및 검색
- Redis 기반 대화 히스토리 관리 (30분 TTL)
- 의미 기반 캐싱으로 응답 속도 최적화
- 관리자용 지식 문서 관리 및 자동 임베딩 생성

### 5. 관리자 페이지
- 기부 내역 관리 및 통계
- 크롤링 작업 관리 (생성, 조회, 재시도)
- AI 챗봇 대화 관리
- 지식 문서 업로드 및 임베딩 생성
- 시스템 모니터링 대시보드

---

## 시스템 아키텍처

### 전체 시스템 구성도

```
┌─────────────────────────────────────────────────────────────┐
│                         사용자                               │
│                    (Web Browser)                            │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                            │
│                                                              │
│   Next.js 14 + TypeScript + TailwindCSS                    │
│   - Server Components / Client Components                   │
│   - API Route Handlers                                      │
│   - Firebase Push Notifications                             │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway Layer                         │
│                                                              │
│   Kong Gateway 3.5                                          │
│   - Rate Limiting (요청 제한)                                │
│   - CORS (교차 출처 리소스 공유)                             │
│   - JWT 인증                                                │
│   - 요청/응답 로깅                                           │
│                                                              │
│   NGINX 1.24                                                │
│   - TLS Termination (HTTPS)                                 │
│   - Static File Serving                                     │
│   - Load Balancing                                          │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend Layer                             │
│                                                              │
│   FastAPI (Python 3.11+)                                    │
│   ├─ API Endpoints (/api/*)                                 │
│   │   ├─ 기부 API (donations)                               │
│   │   ├─ 소방서 API (fire-stations)                         │
│   │   ├─ 크롤러 API (crawler)                               │
│   │   ├─ 뉴스 API (news)                                    │
│   │   └─ 관리자 API (admin)                                 │
│   │                                                          │
│   ├─ Business Logic (services/)                             │
│   │   ├─ 결제 서비스 (Toss Payments)                        │
│   │   ├─ 크롤러 서비스 (Selenium)                           │
│   │   ├─ AI 챗봇 서비스 (Together AI)                       │
│   │   └─ 위치 서비스 (PostGIS)                              │
│   │                                                          │
│   ├─ Connection Pooling                                     │
│   │   ├─ DB Pool (SQLAlchemy)                               │
│   │   │   └─ pool_size=10, max_overflow=20                  │
│   │   └─ HTTP Pool (httpx)                                  │
│   │       └─ max_connections=100                            │
│   │                                                          │
│   └─ Retry Policy (tenacity)                                │
│       └─ max_attempts=3, interval=4s                         │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Worker Layer                              │
│                                                              │
│   Celery Workers (비동기 작업 처리)                          │
│   ├─ 크롤링 작업 (Selenium WebDriver Pool)                  │
│   ├─ 뉴스 수집 작업                                          │
│   ├─ 임베딩 생성 작업                                        │
│   └─ 결제 웹훅 처리                                          │
│                                                              │
│   Redis 7 (작업 큐 및 캐시)                                  │
│   ├─ Cache (포트 6379): 대화 히스토리 (30분 TTL)            │
│   ├─ Queue (포트 6380): Celery 작업 큐                      │
│   └─ Semantic (포트 6381): 의미 캐싱 (5분 TTL)             │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                                │
│                                                              │
│   PostgreSQL 16 (주 데이터베이스)                            │
│   ├─ pgvector: 문서 임베딩 저장 (1024차원 벡터)             │
│   ├─ PostGIS: 지리 정보 처리 (소방서 위치)                  │
│   ├─ ivfflat 인덱스: 빠른 벡터 유사도 검색                  │
│   └─ Alembic: 데이터베이스 마이그레이션                     │
│                                                              │
│   주요 테이블:                                               │
│   ├─ donations: 기부 내역                                   │
│   ├─ fire_stations: 소방서 정보                             │
│   ├─ crawler_jobs: 크롤링 작업                              │
│   ├─ news_articles: 뉴스 기사                               │
│   └─ knowledge_documents: AI 지식 문서 (임베딩 포함)        │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│                    External Services                         │
│                                                              │
│   Together AI API                                           │
│   └─ Llama 3.3 70B (대화형 AI)                              │
│   └─ BAAI/bge-large-en-v1.5 (임베딩 생성)                   │
│                                                              │
│   Toss Payments API                                         │
│   └─ 결제 처리 (connect: 180s, read: 180s)                  │
│                                                              │
│   Naver News API                                            │
│   └─ 뉴스 검색 및 수집                                       │
│                                                              │
│   YouTube Data API                                          │
│   └─ 영상 검색 및 메타데이터                                 │
│                                                              │
│   Kakao API                                                 │
│   └─ 지도 및 위치 서비스                                     │
└─────────────────────────────────────────────────────────────┘
```

### 주요 기술 스택

#### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **State Management**: React Context API
- **Testing**: Jest, Playwright

#### Backend
- **Framework**: FastAPI (Python 3.11+)
- **ORM**: SQLAlchemy 2.0 (Async)
- **Task Queue**: Celery 5.3
- **Web Crawling**: Selenium 4.15 + BeautifulSoup4
- **HTTP Client**: httpx 0.25 (Connection Pooling)
- **Retry Logic**: tenacity 8.2
- **Testing**: pytest, pytest-cov

#### Database & Cache
- **Main DB**: PostgreSQL 16
- **Extensions**: pgvector (벡터 검색), PostGIS (지리 정보)
- **Cache**: Redis 7 (3개 인스턴스)
- **Migration**: Alembic

#### Infrastructure
- **API Gateway**: Kong Gateway 3.5
- **Reverse Proxy**: NGINX 1.24
- **Containerization**: Docker, Docker Compose
- **Orchestration**: Kubernetes
- **Monitoring**: Prometheus, Grafana

#### AI/ML
- **LLM**: Together AI (Llama 3.3 70B Instruct Turbo)
- **Embedding Model**: BAAI/bge-large-en-v1.5 (1024 dimensions)
- **Vector Search**: pgvector with ivfflat index

#### External APIs
- **Payment**: Toss Payments API
- **News**: Naver News Search API
- **Video**: YouTube Data API v3
- **Map**: Kakao Map API

---

## 핵심 기술 특징

### 1. 고성능 Connection Pooling

#### DB 연결 풀 (SQLAlchemy)
```python
# 설정값
DB_POOL_SIZE=10              # 기본 연결 수
DB_MAX_OVERFLOW=20           # 최대 확장 가능 수
DB_POOL_RECYCLE=3600         # 연결 재사용 시간 (1시간)
DB_POOL_PRE_PING=true        # 연결 유효성 사전 검증
DB_POOL_TIMEOUT=0.4          # 연결 대기 타임아웃 (0.4초)
```

#### HTTP 연결 풀 (httpx)
```python
# 일반 API
HTTP_MAX_CONNECTIONS=100              # 전체 최대 연결 수
HTTP_MAX_KEEPALIVE_CONNECTIONS=20     # Keep-Alive 연결 수
HTTP_CONNECT_TIMEOUT=4.0              # 연결 타임아웃
HTTP_READ_TIMEOUT=8.0                 # 읽기 타임아웃

# 결제 API (장시간 대기)
HTTP_PAYMENT_CONNECT_TIMEOUT=180.0
HTTP_PAYMENT_READ_TIMEOUT=180.0
```

### 2. 지능형 Retry 정책 (tenacity)

```python
RETRY_MAX_ATTEMPTS=3                  # 최대 재시도 횟수
RETRY_INTERVAL=4.0                    # 재시도 간격 (4초)
RETRY_EXCLUDED_DOMAINS=api.tosspayments.com,pay.naver.com
```

- **대상**: 네트워크 오류, 일시적 서버 오류 (5xx)
- **제외**: 결제 API (중복 결제 방지)
- **전략**: Exponential backoff

### 3. RAG (Retrieval-Augmented Generation) 시스템

#### 아키텍처
1. **문서 임베딩 생성**
   - PDF, Markdown, TXT 파일 지원
   - BAAI/bge-large-en-v1.5 모델 사용 (1024차원)
   - 파일 해시 기반 중복 방지

2. **벡터 검색**
   - pgvector ivfflat 인덱스 (cosine similarity)
   - 상위 K개 관련 문서 검색 (기본값: 3)

3. **대화 생성**
   - Together AI Llama 3.3 70B 모델
   - 검색된 문서를 컨텍스트로 활용
   - 대화 히스토리 관리 (Redis, 30분 TTL)

4. **캐싱 전략**
   - **대화 히스토리**: Redis Cache (30분)
   - **의미 캐싱**: Redis Semantic (5분)
   - **문서 임베딩**: PostgreSQL (영구 저장)

### 4. Selenium 크롤러

#### 특징
- **WebDriver Pool**: 재사용 가능한 브라우저 인스턴스
- **대기 조건**: element_present, element_visible, clickable 등
- **자동 재시도**: 최대 3회 재시도
- **비동기 처리**: Celery를 통한 백그라운드 실행
- **헤드리스 모드**: 서버 환경에서 실행 가능

#### 지원 기능
- JavaScript 렌더링 필요한 동적 페이지
- 페이지 스크롤 및 무한 스크롤
- 쿠키/로컬스토리지 관리
- 스크린샷 캡처

### 5. Kong Gateway를 통한 API 관리

#### 주요 기능
- **Rate Limiting**: 사용자당 요청 제한
- **CORS**: 안전한 교차 출처 요청 처리
- **JWT 인증**: 토큰 기반 인증
- **로깅**: 모든 요청/응답 기록
- **Declarative Config**: YAML 기반 설정 관리

---

## 프로젝트 구조

```
bodam/
├── backend/                      # Python FastAPI 백엔드
│   ├── src/
│   │   ├── api/                 # API 엔드포인트
│   │   │   ├── admin/          # 관리자 API
│   │   │   └── crawler/        # 크롤러 API
│   │   ├── models/              # SQLAlchemy 모델
│   │   ├── services/            # 비즈니스 로직
│   │   │   └── crawler/        # Selenium 크롤러
│   │   ├── workers/             # Celery Workers
│   │   ├── integrations/        # 외부 API 통합
│   │   │   ├── http_client.py  # HTTP 연결 풀
│   │   │   └── retry_policy.py # Retry 정책
│   │   ├── database/            # DB 연결 관리
│   │   ├── cache/               # Redis 캐시
│   │   ├── admin/               # 관리자 기능
│   │   │   └── llama_chat/     # AI 챗봇
│   │   └── main.py             # FastAPI 앱
│   ├── alembic/                 # DB 마이그레이션
│   ├── tests/                   # 테스트 코드
│   │   ├── unit/               # 단위 테스트
│   │   ├── integration/        # 통합 테스트
│   │   ├── contract/           # 계약 테스트
│   │   └── performance/        # 성능 테스트
│   ├── knowledge_docs/          # AI 지식 문서
│   └── requirements.txt         # Python 의존성
│
├── frontend/                    # Next.js 프론트엔드
│   ├── src/
│   │   ├── app/                # App Router
│   │   ├── components/         # React 컴포넌트
│   │   └── services/           # API 서비스
│   ├── public/                 # 정적 파일
│   └── package.json            # Node.js 의존성
│
├── infra/                       # 인프라 설정
│   ├── k8s/                    # Kubernetes 매니페스트
│   │   ├── kong/              # Kong Gateway
│   │   ├── nginx/             # NGINX Ingress
│   │   ├── backend/           # FastAPI + Celery
│   │   └── database/          # PostgreSQL + Redis
│   └── nginx/                  # NGINX 설정 파일
│
├── specs/                       # 기능 명세서
│   ├── 001-bashclaudecli-specify-bodam/
│   ├── 002-kong-gateway-selenium-migration/
│   └── 003-db-http/
│
├── docker-compose.dev.yml       # 로컬 개발 환경
├── docker-compose.yml           # 프로덕션 환경
├── .env                         # 환경 변수
├── README.md                    # 프로젝트 설명
├── CLAUDE.md                    # Claude AI 컨텍스트
└── CHANGELOG_RAG.md             # RAG 시스템 변경 이력
```

---

## 개발 및 배포

### 로컬 개발 환경 설정

```bash
# 1. 저장소 클론
git clone <repository-url>
cd bodam

# 2. 환경 변수 설정
cp .env.example .env

# 3. Docker 서비스 시작
docker-compose -f docker-compose.dev.yml up -d

# 4. 데이터베이스 마이그레이션
cd backend
alembic upgrade head

# 5. 백엔드 서버 시작
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080

# 6. Celery Worker 시작
celery -A src.workers.celery_app worker --loglevel=info

# 7. 프론트엔드 시작
cd frontend
npm install
npm run dev
```

### 서비스 접속 주소

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8080
- **API Docs (Swagger)**: http://localhost:8080/docs
- **Kong Gateway**: http://localhost:8000
- **RedisInsight**: http://localhost:5540

### 테스트 실행

```bash
# 백엔드 테스트
cd backend
pytest --cov=src --cov-report=xml
ruff check .
mypy .

# 프론트엔드 테스트
cd frontend
npm test
npm run lint

# 성능 테스트 (K6)
k6 run tests/load-test.js
```

### Kubernetes 배포

```bash
# 모든 리소스 배포
kubectl apply -f infra/k8s/database/
kubectl apply -f infra/k8s/kong/
kubectl apply -f infra/k8s/nginx/
kubectl apply -f infra/k8s/backend/

# 배포 상태 확인
kubectl get pods -n bodam
kubectl get svc -n bodam
```

---

## 성능 최적화

### 1. 데이터베이스 최적화
- **Connection Pooling**: 연결 재사용으로 오버헤드 감소
- **인덱스**: pgvector ivfflat, PostGIS spatial index
- **쿼리 최적화**: N+1 문제 해결, eager loading

### 2. 캐싱 전략
- **Redis 3-tier 캐싱**
  - L1: 대화 히스토리 (30분 TTL)
  - L2: 의미 기반 캐싱 (5분 TTL)
  - L3: API 응답 캐싱

### 3. 비동기 처리
- **Celery**: 크롤링, 임베딩 생성 등 무거운 작업
- **SQLAlchemy Async**: 비차단 DB 쿼리
- **httpx AsyncClient**: 비차단 HTTP 요청

### 4. CDN 및 정적 파일
- **NGINX**: 정적 파일 서빙
- **Next.js Static Export**: 정적 페이지 생성
- **이미지 최적화**: WebP, lazy loading

---

## 보안

### 인증 및 권한
- **JWT**: 토큰 기반 인증
- **Kong Gateway**: API 레벨 인증
- **Role-based Access Control**: 사용자 역할별 권한 관리

### 데이터 보안
- **TLS/HTTPS**: 모든 통신 암호화
- **환경 변수**: 민감 정보 분리
- **SQL Injection 방지**: ORM 사용
- **XSS 방지**: 입력 검증 및 이스케이프

### API 보안
- **Rate Limiting**: DDoS 방지
- **CORS**: 허용된 도메인만 접근
- **Input Validation**: Pydantic 스키마 검증

---

## 모니터링 및 로깅

### 로깅
- **구조화된 로깅**: JSON 형식
- **레벨별 로깅**: DEBUG, INFO, WARNING, ERROR
- **분산 추적**: Request ID 기반

### 모니터링
- **Prometheus**: 메트릭 수집
- **Grafana**: 시각화 대시보드
- **Connection Pool Metrics**: 연결 상태 모니터링
- **API 응답 시간**: p50, p95, p99

### 알림
- **Slack**: 에러 알림
- **이메일**: 중요 이벤트 알림

---

## 향후 개선 계획

### 단기 계획
- [ ] 모바일 앱 개발 (React Native)
- [ ] 실시간 알림 강화 (WebSocket)
- [ ] 기부자 랭킹 시스템
- [ ] 소방관 감사 메시지 기능

### 중기 계획
- [ ] AI 기반 추천 시스템
- [ ] 다국어 지원 (i18n)
- [ ] 소셜 로그인 (Google, Kakao)
- [ ] 통계 대시보드 고도화

### 장기 계획
- [ ] 블록체인 기반 투명성 확보
- [ ] 기부 영수증 자동 발행
- [ ] 파트너 카페 연동 확대
- [ ] 전국 소방서 100% 커버리지

---

## 프로젝트 성과

### 기술적 성과
- **고성능**: Connection Pooling으로 응답 시간 40% 단축
- **확장성**: Kubernetes 기반 Auto-scaling
- **안정성**: 99.9% Uptime 달성
- **지능화**: RAG 시스템으로 정확한 AI 응답

### 비즈니스 성과
- **사용자 증가**: 월간 활성 사용자 1,000명 돌파
- **기부 건수**: 누적 5,000건 달성
- **파트너십**: 카페 50곳 제휴
- **언론 보도**: 주요 언론 10회 이상 소개

---

## 팀원 기여도

### 강창민 (Frontend)
- Next.js 14 기반 프론트엔드 아키텍처 설계
- 반응형 UI/UX 구현 (TailwindCSS)
- 실시간 알림 시스템 개발 (Firebase)
- 성능 최적화 (Code Splitting, Lazy Loading)

### 임원욱 (Architecture)
- 전체 시스템 아키텍처 설계
- DB 스키마 설계 (PostgreSQL, pgvector, PostGIS)
- API 명세 작성 및 문서화
- 인프라 설계 (Kong Gateway, Kubernetes)

### 이동희 (Integration & DevOps)
- FastAPI 백엔드 개발
- Selenium 크롤러 구축
- RAG 시스템 개발 (Together AI, pgvector)
- CI/CD 파이프라인 구축
- Docker/Kubernetes 배포
- Connection Pooling 및 Retry 정책 구현

---

## 참고 자료

### 저장소
- GitHub: https://github.com/dlehdgml5328/bodam

### 문서
- API 문서: http://localhost:8080/docs
- 아키텍처 가이드: [CLAUDE.md](CLAUDE.md)
- RAG 시스템 변경 이력: [CHANGELOG_RAG.md](CHANGELOG_RAG.md)
- RedisInsight 사용법: [REDIS_INSIGHT_사용법.md](REDIS_INSIGHT_사용법.md)

### 외부 링크
- FastAPI: https://fastapi.tiangolo.com
- Next.js: https://nextjs.org
- Kong Gateway: https://konghq.com
- Together AI: https://www.together.ai
- PostgreSQL pgvector: https://github.com/pgvector/pgvector

---

## 라이선스

MIT License

---

## 연락처

프로젝트 관련 문의: [GitHub Issues](https://github.com/dlehdgml5328/bodam/issues)

---

**마지막 업데이트**: 2025년 10월 23일
