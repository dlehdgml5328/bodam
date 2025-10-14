# 보담 파이프라인 완성 🎉

## ✅ 완료된 전체 파이프라인

### 📊 데이터 흐름
```
GitHub Pages (JSON)
    ↓
Crawler (Celery Task - 5분마다)
    ↓
fire_incidents 테이블 저장
    ↓
LangGraph 워크플로우
    ├─ 키워드 추출
    ├─ 네이버 뉴스 검색 (20건 → 날짜 필터링)
    ├─ YouTube 검색 (10건)
    ├─ Llama 3.3 AI 평가 (관련성 점수 >= 0.6)
    └─ news_matches 테이블 저장
    ↓
REST API (/api/incidents/)
    ↓
Frontend (실시간 출동 현황)
```

---

## 🎯 완료된 작업

### 1. 인프라 구성 ✅
**Docker Compose 서비스:**
- PostgreSQL (port 5432) - 메인 DB
- Redis Cache (port 6379) - API 캐싱, 512MB LRU
- Redis Queue (port 6380) - Celery Broker/Result, AOF+RDB 영속성
- Redis Semantic (port 6381) - Vector Store, 2GB
- FastAPI Backend (port 8000) - REST API
- Next.js Frontend (port 3000) - 웹 UI
- Celery Worker - 메인 워커 (celery, critical 큐)
- Celery Worker News - 뉴스 매칭 워커 (news_matching 큐)
- Celery Beat - 스케줄러 (크롤러 5분마다 실행)
- ~~Mock Site~~ (제거됨 - GitHub Pages 사용)

### 2. 데이터베이스 모델 ✅
**생성된 테이블:**
- `fire_incidents` - 화재 사고 정보
- `dispatch_events` - 출동 이벤트 (미사용)
- `news_matches` - 뉴스/영상 매칭 결과

### 3. 크롤링 시스템 ✅
**파일:** `backend/src/workers/crawler.py`
- GitHub Pages JSON 직접 수집
- URL: `https://dlehdgml5328.github.io/mock-fire-station-site/data/incidents.json`
- 5분마다 자동 실행 (Celery Beat)
- DB 중복 체크 및 업데이트

### 4. 뉴스/영상 매칭 (LangGraph) ✅
**파일:**
- `backend/src/workers/matcher.py` - LangGraph 워크플로우
- `backend/src/workers/langgraph_nodes.py` - 각 노드 구현
- `backend/src/integrations/naver_news.py` - 네이버 뉴스 API
- `backend/src/integrations/youtube.py` - YouTube API
- `backend/src/integrations/together_ai.py` - Llama 3.3 AI

**워크플로우:**
1. `extract_keywords` - 검색 키워드 생성
2. `search_news` - 네이버 뉴스 검색
3. `search_videos` - YouTube 검색
4. `evaluate_relevance` - Llama 3.3 평가
5. `save_matches` - DB 저장 (중복 체크)

### 5. REST API ✅
**파일:** `backend/src/api/incidents.py`
- `GET /api/incidents/` - 화재 사고 목록 (필터, 페이징)
- `GET /api/incidents/{id}` - 사고 상세 정보

### 6. 프론트엔드 연동 ✅
**파일:**
- `frontend/src/lib/data/incidents.ts` - API 호출 함수
- `frontend/src/app/(public)/page.tsx` - 실시간 출동 현황 표시

---

## 🔧 API 키 설정

### 환경변수 (docker-compose.dev.yml)
```yaml
# Naver Search API
NAVER_CLIENT_ID=Le3v_zRXPEpKCD8hE_ei
NAVER_CLIENT_SECRET=g3Gcw_ACuH

# Naver Login API (별도)
NAVER_LOGIN_CLIENT_ID=Hb55laljP5_sxfrXzqEy
NAVER_LOGIN_CLIENT_SECRET=QwDd8nQjOw

# YouTube API
YOUTUBE_API_KEY=AIzaSyBjTLfPvieVfr2YZIHRQTfqf4eEs4joUmQ

# Together AI (Llama 3.3)
TOGETHER_AI_API_KEY=bfa8dc15b9a53289883f17fb87ad2e2bb114609b35d76f45bc49643364e12056
TOGETHER_AI_MODEL=meta-llama/Llama-3.3-70B-Instruct-Turbo-Free

# Crawler
CRAWLER_MOCK_SITE_URL=https://dlehdgml5328.github.io/mock-fire-station-site/
```

---

## 🚀 사용 방법

### 전체 시스템 시작
```bash
cd /home/donghee/bodam
docker-compose -f docker-compose.dev.yml up -d
```

### 서비스 접속
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis Cache: localhost:6379
- Redis Queue: localhost:6380
- Redis Semantic: localhost:6381

### 수동 크롤링 실행
```bash
docker exec bodam-celery-worker-1 celery -A src.worker.celery_app call src.workers.crawler.crawl_mock_site
```

### DB 확인
```bash
docker exec bodam-db-1 psql -U bodam -d bodam -c "SELECT * FROM fire_incidents;"
docker exec bodam-db-1 psql -U bodam -d bodam -c "SELECT * FROM news_matches;"
```

### 로그 확인
```bash
# Crawler & Matcher 로그
docker logs bodam-celery-worker-1 -f

# Backend 로그
docker logs bodam-backend-1 -f

# Frontend 로그
docker logs bodam-frontend-1 -f
```

---

## 📈 실제 작동 결과

### 크롤링 결과 (DB)
```sql
incident_id: 20251009007
title: 경기 안산소방서
location: 경기 안산시 단원구 선부동 아파트
status: resolved
severity: medium
casualties: 2명 부상
damage: 15,000,000원
```

### 뉴스 매칭 결과 (DB)
```sql
뉴스 1건:
- 제목: "경기 안산시 빌라서 불… 주민 5명 연기 흡입"
- 연관성: 0.8
- 발행일: 2025-10-02

비디오 1건:
- 제목: "새벽 안산 빌라 화재로 나이지리아 출신 4남매 숨져 / YTN"
- 연관성: 0.9
- 발행일: 2023-03-27
```

---

## 🏗️ 아키텍처

### 현재 (개발 환경)
```
Frontend (3000) ──→ Backend (8000) ──→ PostgreSQL (5432)
                         │
                         ├──→ Redis Cache (6379)
                         ├──→ Redis Queue (6380) ←── Celery Workers
                         └──→ Redis Semantic (6381)
```

### 향후 프로덕션 (Kong Gateway 적용 시)
```
Vercel (Frontend)
    ↓
Kong API Gateway
    ↓
Kubernetes (DigitalOcean)
    ├── Kong Ingress Controller
    ├── NGINX Ingress Controller
    ├── FastAPI Pods (Auto-scaling)
    ├── Static NGINX Pods
    ├── Celery Workers
    └── PostgreSQL + Redis
```

**참고 문서:** [docs/DEPLOYMENT-WITH-API-GATEWAY.md](docs/DEPLOYMENT-WITH-API-GATEWAY.md)

---

## 🎓 기술 스택

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy 2.0 (Async)
- Celery + Redis
- BeautifulSoup4 (크롤링)
- LangGraph (워크플로우)
- Together AI (Llama 3.3 70B)
- Naver Search API
- YouTube Data API v3

### Frontend
- Next.js 13 (App Router)
- TypeScript
- TailwindCSS
- Server Components

### Infrastructure
- Docker + Docker Compose
- PostgreSQL 15
- Redis 7.2 × 3 (Cache/Queue/Semantic)
- Celery Beat (스케줄러)

---

## 📝 주요 파일

### Backend
```
backend/src/
├── models/
│   ├── fire_incident.py          # 화재 사고 모델
│   ├── dispatch_event.py         # 출동 이벤트 모델
│   └── news_match.py             # 뉴스 매칭 모델
├── api/
│   └── incidents.py              # REST API 엔드포인트
├── workers/
│   ├── crawler.py                # GitHub Pages 크롤러
│   ├── matcher.py                # LangGraph 매칭 워크플로우
│   ├── langgraph_nodes.py        # 워크플로우 노드들
│   └── incident_pipeline.py      # 사고 처리 파이프라인
├── integrations/
│   ├── naver_news.py             # 네이버 뉴스 API
│   ├── youtube.py                # YouTube API
│   └── together_ai.py            # Llama 3.3 AI
└── worker.py                     # Celery 앱 설정
```

### Frontend
```
frontend/src/
├── lib/data/
│   └── incidents.ts              # API 호출 함수
└── app/(public)/
    └── page.tsx                  # 홈페이지 (실시간 출동 현황)
```

### Infrastructure
```
infra/
├── docker/
│   └── db/initdb/                # DB 초기화 스크립트
├── k8s/                          # Kubernetes 설정 (프로덕션용)
└── monitoring/                   # Prometheus/Grafana (프로덕션용)
```

---

## 🐛 트러블슈팅

### 1. 컨테이너 재시작 시 환경변수 적용 안 됨
**문제:** `docker restart`로는 환경변수가 변경되지 않음
**해결:** `docker-compose up -d`로 재생성

### 2. Frontend에서 Backend 접속 불가
**문제:** Docker 내부에서 `localhost` 사용 시 자기 자신을 가리킴
**해결:** 서비스명 사용 (`http://backend:8000`)

### 3. Redis Event Loop Closed 에러
**문제:** `asyncio.run()` 중첩 사용 시 발생
**해결:** LangGraph 노드에서 직접 async 작업 수행

### 4. 날짜 파싱 에러
**문제:** Naver/YouTube 날짜 형식이 다름
**해결:** 각각 `strptime`, `fromisoformat` 사용

---

## 🎉 완성!

모든 파이프라인이 정상 작동합니다:
- ✅ GitHub Pages에서 자동 크롤링 (5분마다)
- ✅ DB 저장 및 업데이트
- ✅ 네이버 뉴스 + YouTube 검색
- ✅ Llama 3.3 AI 평가
- ✅ DB 저장 (중복 체크)
- ✅ REST API 제공
- ✅ 프론트엔드 실시간 표시

---

**완성일:** 2025-10-14
**최종 업데이트:** Mock Site 컨테이너 제거 (GitHub Pages 사용)
