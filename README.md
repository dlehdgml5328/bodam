# 보담 (BoDam) - 커피 기부 플랫폼

소방관과 소방서를 위한 커피 기부 매칭 플랫폼

## 주요 기능

- 커피 기부 매칭 시스템
- 소방서 위치 기반 검색 (PostGIS)
- 실시간 뉴스 크롤링 (Selenium)
- API Gateway (Kong)
- 비동기 작업 처리 (Celery)

## 기술 스택

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy 2.0 (Async)
- PostgreSQL + pgvector + PostGIS
- Celery + Redis
- Selenium 4.15+

### Frontend
- TypeScript/Node.js 18+
- Next.js
- TailwindCSS

### Infrastructure
- Kong Gateway 3.5 (API Gateway)
- NGINX (TLS Termination & Static Files)
- Docker & Docker Compose
- Kubernetes

## 빠른 시작

### 사전 요구사항

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- K6 (부하 테스트용)

### 로컬 개발 환경 설정

1. **저장소 클론**
```bash
git clone <repository-url>
cd bodam
```

2. **환경 변수 설정**
```bash
cp .env.example .env
# .env 파일을 편집하여 필요한 설정 변경
```

3. **Docker 서비스 시작**
```bash
# PostgreSQL, Redis, Kong Gateway 시작
docker-compose up -d
```

4. **데이터베이스 마이그레이션**
```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
```

5. **백엔드 서버 시작**
```bash
cd backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
```

6. **Celery Worker 시작** (별도 터미널)
```bash
cd backend
celery -A src.workers.celery_app worker --loglevel=info
```

7. **프론트엔드 시작** (별도 터미널)
```bash
cd frontend
npm install
npm run dev
```

## 서비스 접속 주소

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8080
- **Kong Proxy**: http://localhost:8000
- **Kong Admin**: http://localhost:8001
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## API 문서

FastAPI 자동 생성 문서:
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## 주요 API 엔드포인트

### 기부 관련
- `POST /api/donations` - 기부 생성
- `GET /api/donations` - 기부 목록 조회
- `GET /api/donations/{id}` - 기부 상세 조회

### 소방서 관련
- `GET /api/fire-stations/search` - 소방서 검색 (위치 기반)
- `GET /api/fire-stations/{id}` - 소방서 상세 정보

### 크롤러 관련
- `POST /api/crawler/jobs` - 크롤링 작업 생성
- `GET /api/crawler/jobs` - 작업 목록 조회
- `GET /api/crawler/jobs/{job_id}` - 작업 상태 조회
- `POST /api/crawler/jobs/{job_id}/retry` - 실패한 작업 재시도
- `GET /api/crawler/content/{job_id}` - 크롤링 결과 조회

### 뉴스 관련
- `GET /api/news` - 뉴스 목록 조회

## 테스트

### 백엔드 테스트
```bash
cd backend
pytest --cov=src --cov-report=xml
```

### 프론트엔드 테스트
```bash
cd frontend
npm test
```

### 코드 품질 검사
```bash
# Backend
cd backend
ruff check .
mypy .

# Frontend
cd frontend
npm run lint
```

## Kong Gateway 라우팅

Kong Gateway를 통해 모든 API 요청이 라우팅됩니다:

- Rate Limiting (요청 제한)
- CORS (교차 출처 리소스 공유)
- JWT 인증
- 요청/응답 로깅

## Selenium 크롤러

JavaScript 렌더링이 필요한 동적 웹페이지를 크롤링합니다:

- WebDriver Pool (재사용)
- 대기 조건 지원 (element_present, element_visible, etc.)
- 자동 재시도 (최대 3회)
- Celery를 통한 비동기 처리

## 연결 풀 (Connection Pooling)

### DB 연결 풀
- **라이브러리**: SQLAlchemy 2.0 async engine
- **설정**:
  - pool_size: 10 (기본 연결)
  - max_overflow: 20 (최대 확장)
  - pool_recycle: 3600초 (1시간)
  - pool_pre_ping: True (연결 유효성 검증)
  - pool_timeout: 0.4초

### HTTP 연결 풀
- **라이브러리**: httpx AsyncClient
- **설정**:
  - max_connections: 100
  - max_keepalive_connections: 20
  - 일반 API: connect=4s, read=8s
  - 결제 API: connect=180s, read=180s
- **재시도 정책**: tenacity (최대 3회, 간격 4초)

### 환경 변수 설정
```bash
# DB 연결 풀
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true
DB_POOL_TIMEOUT=0.4

# HTTP 연결 풀
HTTP_MAX_CONNECTIONS=100
HTTP_MAX_KEEPALIVE_CONNECTIONS=20
HTTP_CONNECT_TIMEOUT=4.0
HTTP_READ_TIMEOUT=8.0
HTTP_PAYMENT_CONNECT_TIMEOUT=180.0

# 재시도 설정
RETRY_MAX_ATTEMPTS=3
RETRY_INTERVAL=4.0
RETRY_EXCLUDED_DOMAINS=api.tosspayments.com,pay.naver.com
```

자세한 내용은 [specs/003-db-http/](specs/003-db-http/) 참조

## 프로젝트 구조

```
bodam/
├── backend/                # Python FastAPI 백엔드
│   ├── alembic/           # 데이터베이스 마이그레이션
│   ├── src/
│   │   ├── api/           # API 엔드포인트
│   │   ├── models/        # SQLAlchemy 모델
│   │   ├── services/      # 비즈니스 로직
│   │   ├── workers/       # Celery 워커
│   │   └── collectors/    # 데이터 수집기
│   └── tests/             # 테스트 코드
├── frontend/              # Next.js 프론트엔드
├── infra/                 # 인프라 설정
│   └── k8s/              # Kubernetes 매니페스트
│       ├── kong/         # Kong Gateway 설정
│       └── nginx/        # NGINX 설정
├── specs/                 # 기능 명세서
└── docker-compose.yml    # 로컬 개발 환경

```

## 기여 가이드

1. Feature 브랜치 생성
2. 변경사항 커밋
3. 테스트 실행 및 통과 확인
4. Pull Request 생성

## 라이선스

[라이선스 정보]

## 문의

- 이슈 트래커: [GitHub Issues]
- 이메일: [연락처]
