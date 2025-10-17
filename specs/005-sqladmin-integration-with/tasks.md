# Tasks: SQLAdmin + Llama AI 채팅 통합

**Input**: 설계 문서 from `/home/eugene/bodam/specs/005-sqladmin-integration-with/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## 실행 흐름

```
1. plan.md 로드 → 기술 스택, 라이브러리, 구조 추출
2. 선택적 설계 문서 로드:
   → data-model.md: 엔티티 추출 → 모델 태스크
   → contracts/: 각 파일 → contract test 태스크
   → research.md: 결정 사항 추출 → 설정 태스크
3. 카테고리별 태스크 생성:
   → Setup: 프로젝트 초기화, 의존성, 린팅
   → Contract Tests: 계약 테스트 (TDD)
   → Authentication: 관리자 인증, 세션 관리
   → Admin Views: SQLAlchemy 모델별 관리자 뷰
   → Llama Chat: AI 채팅 서비스, UI, API
   → Bulk Actions: 환불 대량 처리
   → Integration Tests: 통합 테스트
   → Documentation: 문서화
4. 태스크 규칙 적용:
   → 다른 파일 = [P] 병렬 실행
   → 같은 파일 = 순차 실행 (no [P])
   → 테스트 먼저, 구현 나중 (TDD)
5. 태스크 번호 부여 (T001, T002...)
6. 의존성 그래프 생성
7. 병렬 실행 예시 생성
8. 완료성 검증 완료
```

---

## Phase 3.1: Setup & Dependencies

### T001: SQLAdmin 프로젝트 구조 생성

**설명**:
SQLAdmin 관리자 패널을 위한 디렉토리 구조를 생성합니다.

**작업**:
- `/home/eugene/bodam/backend/src/admin/` 디렉토리 생성
- `/home/eugene/bodam/backend/src/admin/__init__.py` 생성
- `/home/eugene/bodam/backend/src/admin/views/` 디렉토리 생성
- `/home/eugene/bodam/backend/src/admin/actions/` 디렉토리 생성
- `/home/eugene/bodam/backend/src/admin/llama_chat/` 디렉토리 생성
- `/home/eugene/bodam/backend/src/admin/llama_chat/templates/` 디렉토리 생성

**의존성**:
- 없음

**검증**:
- [ ] 모든 디렉토리가 생성되었는지 확인
- [ ] `__init__.py` 파일이 각 디렉토리에 존재하는지 확인

---

### T002: SQLAdmin 라이브러리 설치 및 환경 변수 설정

**설명**:
SQLAdmin 및 관련 의존성을 설치하고 환경 변수를 설정합니다.

**작업**:
- `backend/requirements.txt`에 다음 추가:
  ```
  sqladmin>=0.16.0
  together>=1.0.0
  numpy>=1.24.0
  ```
- `.env` 파일에 환경 변수 추가:
  ```bash
  ADMIN_SECRET_KEY=your_secret_key_for_session_encryption
  TOGETHER_AI_API_KEY=your_together_ai_api_key_here
  SEMANTIC_CACHE_TTL=3600
  LLAMA_CACHE_SIMILARITY_THRESHOLD=0.85
  ```

**의존성**:
- 없음

**검증**:
- [ ] `pip install -r backend/requirements.txt` 성공
- [ ] `.env` 파일에 모든 환경 변수 존재 확인

---

### T003: SQLAdmin 설정 파일 생성 (backend/src/admin/config.py)

**설명**:
SQLAdmin 인스턴스를 생성하고 설정하는 모듈을 작성합니다.

**파일**:
- `/home/eugene/bodam/backend/src/admin/config.py` (생성)

**작업**:
```python
from sqladmin import Admin
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

async def setup_admin(app: FastAPI, engine: AsyncEngine) -> Admin:
    """SQLAdmin 인스턴스 생성 및 설정"""
    admin = Admin(
        app=app,
        engine=engine,
        title="보담 관리자 패널",
        base_url="/admin",
    )
    return admin
```

**의존성**:
- T002 완료 후

**검증**:
- [ ] `backend/src/admin/config.py` 파일 생성 확인
- [ ] `setup_admin` 함수 정의 확인

---

## Phase 3.2: Contract Tests (TDD) ⚠️ 구현 전 필수

**CRITICAL**: 이 테스트들은 **구현 전에 작성**되어야 하며, **실패해야** 합니다.

### T004 [P]: Admin UI Routes 계약 테스트

**설명**:
`admin-ui-routes.yaml` 계약서에 정의된 SQLAdmin UI 라우트를 테스트합니다.

**파일**:
- `/home/eugene/bodam/backend/tests/contract/test_admin_ui_routes.py` (생성)

**작업**:
- 관리자 대시보드 (`GET /admin`) 테스트
- 로그인 페이지 (`GET /admin/login`, `POST /admin/login`) 테스트
- 사용자 목록 (`GET /admin/user`) 테스트
- 기부 목록 (`GET /admin/donation`) 테스트
- 환불 목록 (`GET /admin/refund`) 테스트
- 소방서 목록 (`GET /admin/fire-station`) 테스트
- 뉴스 콘텐츠 목록 (`GET /admin/news-content`) 테스트
- 401/403 응답 테스트

**의존성**:
- 없음 (TDD - 구현 전)

**검증**:
- [ ] 테스트가 실패하는지 확인 (아직 구현 안 됨)
- [ ] `pytest backend/tests/contract/test_admin_ui_routes.py -v` 실행 시 모든 테스트 FAILED

---

### T005 [P]: Admin Chat API 계약 테스트

**설명**:
`admin-chat-api.yaml` 계약서에 정의된 Llama AI 채팅 API를 테스트합니다.

**파일**:
- `/home/eugene/bodam/backend/tests/contract/test_admin_chat_api.py` (생성)

**작업**:
- `POST /admin/api/chat/query` 요청/응답 스키마 테스트
- `GET /admin/api/chat/history` 요청/응답 스키마 테스트
- `POST /admin/api/chat/clear` 요청/응답 스키마 테스트
- `POST /admin/api/chat/session` 요청/응답 스키마 테스트
- `DELETE /admin/api/chat/session` 요청/응답 스키마 테스트
- 400/401/403/429/500 에러 응답 테스트

**의존성**:
- 없음 (TDD - 구현 전)

**검증**:
- [ ] 테스트가 실패하는지 확인 (아직 구현 안 됨)
- [ ] `pytest backend/tests/contract/test_admin_chat_api.py -v` 실행 시 모든 테스트 FAILED

---

### T006 [P]: Admin Refund Actions 계약 테스트

**설명**:
`admin-refund-actions.yaml` 계약서에 정의된 환불 액션 API를 테스트합니다.

**파일**:
- `/home/eugene/bodam/backend/tests/contract/test_admin_refund_actions.py` (생성)

**작업**:
- `POST /admin/api/refunds/bulk-approve` 요청/응답 스키마 테스트
- `POST /admin/api/refunds/bulk-reject` 요청/응답 스키마 테스트
- `POST /admin/api/refunds/{refund_id}/approve` 요청/응답 스키마 테스트
- `POST /admin/api/refunds/{refund_id}/reject` 요청/응답 스키마 테스트
- `GET /admin/api/refunds/{refund_id}` 요청/응답 스키마 테스트
- `GET /admin/api/audit-logs/refunds` 요청/응답 스키마 테스트
- 부분 성공 케이스 테스트 (일부 성공, 일부 실패)

**의존성**:
- 없음 (TDD - 구현 전)

**검증**:
- [ ] 테스트가 실패하는지 확인 (아직 구현 안 됨)
- [ ] `pytest backend/tests/contract/test_admin_refund_actions.py -v` 실행 시 모든 테스트 FAILED

---

## Phase 3.3: Admin Authentication

### T007: 관리자 인증 미들웨어 구현 (backend/src/admin/auth.py)

**설명**:
SQLAdmin 페이지 접근을 제한하는 인증 미들웨어를 구현합니다.

**파일**:
- `/home/eugene/bodam/backend/src/admin/auth.py` (생성)

**작업**:
- `require_admin` 의존성 함수 구현 (UserRole.ADMIN 검증)
- 세션 쿠키 검증 (Starlette SessionMiddleware)
- 401/403 에러 처리
- 감사 로그 기록 (관리자 액션)

**의존성**:
- T003 완료 후

**검증**:
- [ ] `require_admin` 함수가 UserRole.ADMIN만 허용하는지 테스트
- [ ] 비관리자 접근 시 403 에러 반환 확인
- [ ] 로그인 안 한 사용자 접근 시 401 에러 반환 확인

---

### T008: 로그인/로그아웃 엔드포인트 구현 (backend/src/api/admin/auth.py)

**설명**:
관리자 로그인 및 로그아웃 엔드포인트를 구현합니다.

**파일**:
- `/home/eugene/bodam/backend/src/api/admin/auth.py` (생성)

**작업**:
- `POST /admin/login` 엔드포인트 구현 (이메일, 비밀번호 검증)
- 세션 쿠키 생성 (HttpOnly, Secure, SameSite=Strict, Max-Age=1800)
- `POST /admin/logout` 엔드포인트 구현 (세션 삭제)
- `GET /admin/login` 로그인 페이지 렌더링 (Jinja2 템플릿)

**의존성**:
- T007 완료 후

**검증**:
- [ ] 올바른 자격 증명으로 로그인 시 세션 쿠키 생성 확인
- [ ] 잘못된 자격 증명으로 로그인 시 401 에러 확인
- [ ] 로그아웃 시 세션 쿠키 삭제 확인

---

## Phase 3.4: Admin Views (병렬 가능)

각 Admin View는 독립적인 파일이므로 병렬 실행 가능합니다.

### T009 [P]: UserAdmin View 구현 (backend/src/admin/views/user.py)

**설명**:
User 모델에 대한 SQLAdmin ModelView를 구현합니다.

**파일**:
- `/home/eugene/bodam/backend/src/admin/views/user.py` (생성)

**작업**:
- `UserAdmin(ModelView, model=User)` 클래스 정의
- 목록 필드: `id, email, name, role, tier, total_donated, is_active, created_at`
- 상세 필드: 모든 필드 (`password_hash` 제외)
- 필터: `role, tier, is_active`
- 검색: `email, name`
- 권한: `can_create=True, can_edit=True, can_delete=False`

**의존성**:
- T007 완료 후

**검증**:
- [ ] `GET /admin/user` 페이지 로드 확인
- [ ] 사용자 목록 표시 확인
- [ ] 필터 및 검색 동작 확인

---

### T010 [P]: DonationAdmin View 구현 (backend/src/admin/views/donation.py)

**설명**:
Donation 모델에 대한 SQLAdmin ModelView를 구현합니다.

**파일**:
- `/home/eugene/bodam/backend/src/admin/views/donation.py` (생성)

**작업**:
- `DonationAdmin(ModelView, model=Donation)` 클래스 정의
- 목록 필드: `id, user_id(email), fire_station_id(name), amount, status, type, created_at`
- 필터: `status, type, mode`
- 검색: `toss_order_id, donor_display_name`
- 통계: 총 기부 금액, 완료 건수, 환불 건수 (대시보드에 표시)
- 권한: `can_create=False, can_edit=True, can_delete=False`

**의존성**:
- T007 완료 후

**검증**:
- [ ] `GET /admin/donation` 페이지 로드 확인
- [ ] 기부 목록 표시 확인
- [ ] 필터 및 검색 동작 확인

---

### T011 [P]: RefundAdmin View 구현 (backend/src/admin/views/refund.py)

**설명**:
Refund 모델에 대한 SQLAdmin ModelView를 구현합니다.

**파일**:
- `/home/eugene/bodam/backend/src/admin/views/refund.py` (생성)

**작업**:
- `RefundAdmin(ModelView, model=Refund)` 클래스 정의
- 목록 필드: `id, donation_id, amount, status, created_at`
- 필터: `status`
- 권한: `can_create=False, can_edit=True, can_delete=False`
- **주의**: Bulk 액션은 T022에서 추가

**의존성**:
- T007 완료 후

**검증**:
- [ ] `GET /admin/refund` 페이지 로드 확인
- [ ] 환불 목록 표시 확인
- [ ] 필터 동작 확인

---

### T012 [P]: FireStationAdmin View 구현 (backend/src/admin/views/fire_station.py)

**설명**:
FireStation 모델에 대한 SQLAdmin ModelView를 구현합니다.

**파일**:
- `/home/eugene/bodam/backend/src/admin/views/fire_station.py` (생성)

**작업**:
- `FireStationAdmin(ModelView, model=FireStation)` 클래스 정의
- 목록 필드: `id, name, region, district, total_received, donor_count, status`
- 상세 필드: 모든 필드 + 지도 표시 (location)
- 필터: `status, region`
- 검색: `name, station_code`

**의존성**:
- T007 완료 후

**검증**:
- [ ] `GET /admin/fire-station` 페이지 로드 확인
- [ ] 소방서 목록 표시 확인
- [ ] 필터 및 검색 동작 확인

---

### T013 [P]: NewsContentAdmin View 구현 (backend/src/admin/views/news_content.py)

**설명**:
NewsContent 모델에 대한 SQLAdmin ModelView를 구현합니다.

**파일**:
- `/home/eugene/bodam/backend/src/admin/views/news_content.py` (생성)

**작업**:
- `NewsContentAdmin(ModelView, model=NewsContent)` 클래스 정의
- 목록 필드: `id, title, source, relevance_score, status, published_at`
- 상세 필드: 모든 필드 (embedding 제외)
- 필터: `status, source`
- 검색: `title, keywords`

**의존성**:
- T007 완료 후

**검증**:
- [ ] `GET /admin/news-content` 페이지 로드 확인
- [ ] 뉴스 콘텐츠 목록 표시 확인
- [ ] 필터 및 검색 동작 확인

---

### T014 [P]: SeleniumCrawlJobAdmin View 구현 (backend/src/admin/views/selenium_job.py)

**설명**:
SeleniumCrawlJob 모델에 대한 SQLAdmin ModelView를 구현합니다. (읽기 전용)

**파일**:
- `/home/eugene/bodam/backend/src/admin/views/selenium_job.py` (생성)

**작업**:
- `SeleniumCrawlJobAdmin(ModelView, model=SeleniumCrawlJob)` 클래스 정의
- 목록 필드: `id, url(truncated), status, retry_count, created_at`
- 필터: `status, browser_type`
- 권한: `can_create=False, can_edit=False, can_delete=False, can_view_details=True`

**의존성**:
- T007 완료 후

**검증**:
- [ ] `GET /admin/selenium-crawl-job` 페이지 로드 확인
- [ ] 크롤 작업 목록 표시 확인 (읽기 전용)
- [ ] 필터 동작 확인

---

### T015 [P]: GroupAdmin View 구현 (backend/src/admin/views/group.py)

**설명**:
Group 모델에 대한 SQLAdmin ModelView를 구현합니다.

**파일**:
- `/home/eugene/bodam/backend/src/admin/views/group.py` (생성)

**작업**:
- `GroupAdmin(ModelView, model=Group)` 클래스 정의
- 목록 필드: `id, name, target_amount, current_amount, member_count, status`
- 상세 필드: 모든 필드 + 멤버 목록
- 필터: `status`
- 검색: `name`

**의존성**:
- T007 완료 후

**검증**:
- [ ] `GET /admin/group` 페이지 로드 확인
- [ ] 그룹 목록 표시 확인
- [ ] 필터 및 검색 동작 확인

---

### T016: SQLAdmin 뷰 등록 (backend/src/admin/config.py 수정)

**설명**:
모든 Admin View를 SQLAdmin 인스턴스에 등록합니다.

**파일**:
- `/home/eugene/bodam/backend/src/admin/config.py` (수정)

**작업**:
```python
from .views.user import UserAdmin
from .views.donation import DonationAdmin
from .views.refund import RefundAdmin
from .views.fire_station import FireStationAdmin
from .views.news_content import NewsContentAdmin
from .views.selenium_job import SeleniumCrawlJobAdmin
from .views.group import GroupAdmin

async def setup_admin(app: FastAPI, engine: AsyncEngine) -> Admin:
    admin = Admin(...)

    # ModelView 등록
    admin.add_view(UserAdmin)
    admin.add_view(DonationAdmin)
    admin.add_view(RefundAdmin)
    admin.add_view(FireStationAdmin)
    admin.add_view(NewsContentAdmin)
    admin.add_view(SeleniumCrawlJobAdmin)
    admin.add_view(GroupAdmin)

    return admin
```

**의존성**:
- T009-T015 완료 후

**검증**:
- [ ] `GET /admin` 접속 시 모든 뷰가 메뉴에 표시되는지 확인
- [ ] 각 뷰 페이지 접근 가능 확인

---

## Phase 3.5: Llama Chat Service

### T017: LlamaChatService 서비스 레이어 구현 (backend/src/admin/llama_chat/service.py)

**설명**:
Llama AI 채팅 핵심 로직을 구현합니다.

**파일**:
- `/home/eugene/bodam/backend/src/admin/llama_chat/service.py` (생성)

**작업**:
- `LlamaChatService` 클래스 정의
- `process_query(query: str, session_id: str) -> dict` 메서드 구현
- 쿼리 분류 (knowledge_graph, database, general)
- Llama AI를 통한 SQL 쿼리 생성
- SQL Injection 방지 검증 (SELECT만 허용)
- 쿼리 실행 (GraphClient 또는 일반 DB)
- 결과를 자연어로 변환
- 세션 기록 저장 (Redis)

**의존성**:
- T003 완료 후

**검증**:
- [ ] `process_query` 메서드가 자연어 쿼리를 처리하는지 확인
- [ ] SQL Injection 방지 검증 동작 확인 (INSERT/UPDATE/DELETE 차단)
- [ ] Together AI API 호출 성공 확인

---

### T018: Semantic Cache 통합 (backend/src/admin/llama_chat/service.py 수정)

**설명**:
LlamaChatService에 Semantic Cache를 통합하여 유사 쿼리 응답을 재사용합니다.

**파일**:
- `/home/eugene/bodam/backend/src/admin/llama_chat/service.py` (수정)

**작업**:
- `_generate_embedding(text: str) -> list[float]` 메서드 추가 (Together AI 임베딩)
- `_check_semantic_cache(query: str, embedding: list[float]) -> dict | None` 메서드 추가
- 코사인 유사도 계산 (`_cosine_similarity`)
- `_save_to_semantic_cache(query, embedding, response)` 메서드 추가
- Redis에 캐시 저장 (TTL: 3600초, 키: `admin:llama:{query_hash}`)

**의존성**:
- T017 완료 후

**검증**:
- [ ] 첫 번째 쿼리 실행 시 캐시 미스 확인
- [ ] 유사한 쿼리 실행 시 캐시 히트 확인 (유사도 > 0.85)
- [ ] 캐시 히트 시 응답 시간 < 500ms 확인

---

### T019: Knowledge Graph 쿼리 패턴 구현 (backend/src/admin/llama_chat/service.py 수정)

**설명**:
Knowledge Graph 쿼리 처리 로직을 구현합니다.

**파일**:
- `/home/eugene/bodam/backend/src/admin/llama_chat/service.py` (수정)

**작업**:
- `_handle_graph_query(query: str, session_id: str) -> dict` 메서드 추가
- Llama AI에게 PostgreSQL 쿼리 생성 요청 (스키마 정보 포함)
- 생성된 SQL 검증 (SELECT만 허용, JOIN 허용)
- GraphClient를 통해 쿼리 실행
- 결과를 자연어로 요약

**의존성**:
- T017 완료 후

**검증**:
- [ ] "사고 ID XXX와 연결된 소방서는?" 같은 질문 처리 확인
- [ ] 생성된 SQL이 안전한지 확인 (INSERT/UPDATE/DELETE 없음)
- [ ] GraphClient를 통해 쿼리 실행 확인

---

### T020: Llama Chat API 엔드포인트 구현 (backend/src/api/admin/chat.py)

**설명**:
Llama AI 채팅 REST API 엔드포인트를 구현합니다.

**파일**:
- `/home/eugene/bodam/backend/src/api/admin/chat.py` (생성)

**작업**:
- `POST /admin/api/chat/query` 엔드포인트 구현 (LlamaChatService 호출)
- `GET /admin/api/chat/history` 엔드포인트 구현 (Redis에서 세션 기록 조회)
- `POST /admin/api/chat/clear` 엔드포인트 구현 (세션 기록 삭제)
- `POST /admin/api/chat/session` 엔드포인트 구현 (새 세션 생성)
- `DELETE /admin/api/chat/session` 엔드포인트 구현 (세션 삭제)
- 모든 엔드포인트에 `require_admin` 의존성 적용

**의존성**:
- T017, T018, T019 완료 후

**검증**:
- [ ] `POST /admin/api/chat/query` 응답 스키마 검증 (T005 테스트 통과)
- [ ] `GET /admin/api/chat/history` 응답 스키마 검증
- [ ] 세션 기록이 Redis에 저장되는지 확인

---

### T021: Llama Chat UI 템플릿 구현 (backend/src/admin/llama_chat/templates/llama_chat.html)

**설명**:
Llama AI 채팅 인터페이스 Jinja2 템플릿을 구현합니다.

**파일**:
- `/home/eugene/bodam/backend/src/admin/llama_chat/templates/llama_chat.html` (생성)

**작업**:
- SQLAdmin 레이아웃 확장 (`{% extends "sqladmin/layout.html" %}`)
- 채팅 메시지 표시 영역 (스크롤 가능)
- 입력 텍스트 영역 + 전송 버튼
- 로딩 인디케이터
- JavaScript fetch API로 `/admin/api/chat/query` 호출
- 대화 기록 초기화 버튼
- CSS 스타일링 (사용자/AI 메시지 구분)

**의존성**:
- T020 완료 후

**검증**:
- [ ] 채팅 UI가 SQLAdmin 레이아웃 내에 표시되는지 확인
- [ ] 메시지 전송 시 API 호출 확인
- [ ] AI 응답이 화면에 표시되는지 확인

---

### T022: Llama Chat 커스텀 페이지 등록 (backend/src/admin/llama_chat/page.py)

**설명**:
SQLAdmin에 Llama Chat 커스텀 페이지를 등록합니다.

**파일**:
- `/home/eugene/bodam/backend/src/admin/llama_chat/page.py` (생성)

**작업**:
- `LlamaChatPage(BaseView)` 클래스 정의
- `@expose("/llama-chat", methods=["GET"])` 데코레이터로 라우트 등록
- `chat_page(request: Request) -> Response` 메서드 구현
- 세션 ID 생성 또는 조회 (Starlette session)
- Redis에서 대화 기록 조회
- `llama_chat.html` 템플릿 렌더링

**의존성**:
- T021 완료 후

**검증**:
- [ ] SQLAdmin 메뉴에 "AI 채팅" 항목 표시 확인
- [ ] `GET /admin/llama-chat` 페이지 로드 확인
- [ ] 세션 ID가 자동으로 생성되는지 확인

---

### T023: Llama Chat 페이지를 SQLAdmin에 등록 (backend/src/admin/config.py 수정)

**설명**:
LlamaChatPage를 SQLAdmin 인스턴스에 등록합니다.

**파일**:
- `/home/eugene/bodam/backend/src/admin/config.py` (수정)

**작업**:
```python
from .llama_chat.page import LlamaChatPage

async def setup_admin(app: FastAPI, engine: AsyncEngine) -> Admin:
    admin = Admin(...)

    # ... ModelView 등록 ...

    # 커스텀 페이지 등록
    admin.add_view(LlamaChatPage)

    return admin
```

**의존성**:
- T022 완료 후

**검증**:
- [ ] SQLAdmin 대시보드에 "AI 채팅" 메뉴 표시 확인
- [ ] 클릭 시 채팅 페이지 로드 확인

---

## Phase 3.6: Bulk Refund Actions

### T024: RefundService bulk 처리 로직 구현 (backend/src/services/refund_service.py)

**설명**:
환불 대량 승인/거부 비즈니스 로직을 구현합니다.

**파일**:
- `/home/eugene/bodam/backend/src/services/refund_service.py` (생성 또는 수정)

**작업**:
- `RefundService` 클래스 정의
- `bulk_approve(refund_ids: list[UUID], reviewer_id: UUID) -> dict` 메서드 구현
- `bulk_reject(refund_ids: list[UUID], reviewer_id: UUID, rejection_reason: str) -> dict` 메서드 구현
- 각 환불에 대해 Toss Payments API 호출 (승인 시)
- 트랜잭션 처리 (일부 실패 시에도 성공한 것은 커밋)
- Celery 비동기 태스크로 알림 발송
- Semantic Cache 무효화

**의존성**:
- T011 완료 후

**검증**:
- [ ] `bulk_approve` 메서드가 여러 환불을 처리하는지 확인
- [ ] 일부 실패 시 부분 성공 응답 반환 확인
- [ ] Toss API 호출 성공/실패 처리 확인

---

### T025: Refund Bulk Actions API 엔드포인트 구현 (backend/src/api/admin/refunds.py)

**설명**:
환불 대량 승인/거부 REST API 엔드포인트를 구현합니다.

**파일**:
- `/home/eugene/bodam/backend/src/api/admin/refunds.py` (생성)

**작업**:
- `POST /admin/api/refunds/bulk-approve` 엔드포인트 구현
- `POST /admin/api/refunds/bulk-reject` 엔드포인트 구현
- `POST /admin/api/refunds/{refund_id}/approve` 엔드포인트 구현
- `POST /admin/api/refunds/{refund_id}/reject` 엔드포인트 구현
- `GET /admin/api/refunds/{refund_id}` 엔드포인트 구현
- `GET /admin/api/audit-logs/refunds` 엔드포인트 구현
- 모든 엔드포인트에 `require_admin` 의존성 적용
- RefundService 호출 및 응답 반환

**의존성**:
- T024 완료 후

**검증**:
- [ ] `POST /admin/api/refunds/bulk-approve` 응답 스키마 검증 (T006 테스트 통과)
- [ ] 부분 성공 케이스 동작 확인
- [ ] 감사 로그가 기록되는지 확인

---

### T026: RefundAdmin에 Bulk Actions 등록 (backend/src/admin/views/refund.py 수정)

**설명**:
RefundAdmin에 SQLAdmin 네이티브 bulk 액션을 추가합니다.

**파일**:
- `/home/eugene/bodam/backend/src/admin/views/refund.py` (수정)

**작업**:
- `@action` 데코레이터로 `bulk_approve_action` 메서드 추가
- `@action` 데코레이터로 `bulk_reject_action` 메서드 추가
- 확인 대화상자 설정 (`confirmation` 파라미터)
- 리스트 페이지에만 액션 표시 (`add_in_list=True`)
- RefundService 호출 및 성공/실패 메시지 반환

**의존성**:
- T024, T025 완료 후

**검증**:
- [ ] `GET /admin/refund` 페이지에서 체크박스 선택 가능 확인
- [ ] "선택 항목 승인" 버튼 클릭 시 확인 대화상자 표시 확인
- [ ] Bulk 승인 시 여러 환불이 한 번에 처리되는지 확인

---

## Phase 3.7: Main App Integration

### T027: FastAPI 앱에 SQLAdmin 통합 (backend/src/main.py 수정)

**설명**:
FastAPI 메인 앱에 SQLAdmin을 마운트하고 세션 미들웨어를 추가합니다.

**파일**:
- `/home/eugene/bodam/backend/src/main.py` (수정)

**작업**:
```python
from starlette.middleware.sessions import SessionMiddleware
from src.admin.config import setup_admin
from src.database.connection import get_engine

app = FastAPI(...)

# 세션 미들웨어 추가
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("ADMIN_SECRET_KEY"),
    max_age=1800,  # 30분
    same_site="strict",
    https_only=True,
)

# SQLAdmin 설정
engine = get_engine()
admin = await setup_admin(app, engine)

# Admin API 라우터 등록
from src.api.admin import chat, refunds
app.include_router(chat.router)
app.include_router(refunds.router)
```

**의존성**:
- T016, T023, T026 완료 후

**검증**:
- [ ] FastAPI 서버 시작 성공 확인
- [ ] `GET /admin` 접속 시 SQLAdmin 대시보드 로드 확인
- [ ] `GET /admin/login` 로그인 페이지 로드 확인

---

## Phase 3.8: Integration Tests (병렬 가능)

### T028 [P]: 관리자 인증 통합 테스트

**설명**:
관리자 로그인, 세션 관리, 권한 검증 통합 테스트를 작성합니다.

**파일**:
- `/home/eugene/bodam/backend/tests/integration/test_admin_authentication.py` (생성)

**작업**:
- 관리자 로그인 성공 테스트
- 비관리자 로그인 실패 테스트 (403)
- 로그아웃 테스트
- 세션 만료 테스트 (30분 후)
- 비인증 사용자 접근 차단 테스트 (401)

**의존성**:
- T007, T008, T027 완료 후

**검증**:
- [ ] `pytest backend/tests/integration/test_admin_authentication.py -v` 모두 통과
- [ ] 관리자만 SQLAdmin 페이지 접근 가능 확인

---

### T029 [P]: 사용자 관리 CRUD 통합 테스트

**설명**:
SQLAdmin을 통한 사용자 CRUD 작업 통합 테스트를 작성합니다.

**파일**:
- `/home/eugene/bodam/backend/tests/integration/test_admin_crud_operations.py` (생성)

**작업**:
- 사용자 목록 조회 테스트
- 사용자 상세 조회 테스트
- 사용자 정보 수정 테스트 (tier 변경)
- 필터 및 검색 테스트
- 페이지네이션 테스트

**의존성**:
- T009, T027 완료 후

**검증**:
- [ ] `pytest backend/tests/integration/test_admin_crud_operations.py -v` 모두 통과
- [ ] quickstart.md의 "2. 사용자 관리 테스트" 시나리오 통과

---

### T030 [P]: Llama AI 채팅 통합 테스트

**설명**:
Llama AI 채팅 기능 전체 흐름 통합 테스트를 작성합니다.

**파일**:
- `/home/eugene/bodam/backend/tests/integration/test_llama_chat_integration.py` (생성)

**작업**:
- 채팅 세션 생성 테스트
- 자연어 쿼리 실행 테스트 ("최근 30일 기부 총액은?")
- SQL 생성 및 실행 테스트
- Semantic Cache 히트/미스 테스트
- Knowledge Graph 쿼리 테스트
- 대화 기록 조회 테스트
- 대화 기록 초기화 테스트

**의존성**:
- T017, T018, T019, T020, T027 완료 후

**검증**:
- [ ] `pytest backend/tests/integration/test_llama_chat_integration.py -v` 모두 통과
- [ ] quickstart.md의 "3. Llama AI 채팅 테스트" 시나리오 통과
- [ ] Semantic Cache 히트율 > 60% 확인

---

### T031 [P]: 환불 Bulk Actions 통합 테스트

**설명**:
환불 대량 승인/거부 통합 테스트를 작성합니다.

**파일**:
- `/home/eugene/bodam/backend/tests/integration/test_admin_refund_bulk_actions.py` (생성)

**작업**:
- Bulk 환불 승인 테스트 (모두 성공)
- Bulk 환불 승인 테스트 (부분 성공)
- Bulk 환불 거부 테스트
- 개별 환불 승인/거부 테스트
- 감사 로그 기록 확인 테스트
- Toss API 모킹 (성공/실패 시나리오)

**의존성**:
- T024, T025, T026, T027 완료 후

**검증**:
- [ ] `pytest backend/tests/integration/test_admin_refund_bulk_actions.py -v` 모두 통과
- [ ] quickstart.md의 "4. 환불 bulk 승인 테스트" 시나리오 통과
- [ ] 부분 성공 케이스 처리 확인

---

### T032 [P]: Semantic Cache 성능 테스트

**설명**:
Semantic Cache의 히트율 및 응답 시간을 검증하는 성능 테스트를 작성합니다.

**파일**:
- `/home/eugene/bodam/backend/tests/integration/test_semantic_cache.py` (생성)

**작업**:
- 캐시 미스 시 응답 시간 측정 (< 10초)
- 캐시 히트 시 응답 시간 측정 (< 500ms)
- 유사도 임계값 테스트 (0.85 이상 히트)
- 캐시 TTL 만료 테스트
- 캐시 무효화 테스트 (데이터 변경 후)

**의존성**:
- T018, T027 완료 후

**검증**:
- [ ] `pytest backend/tests/integration/test_semantic_cache.py -v` 모두 통과
- [ ] quickstart.md의 "5. Semantic Cache 확인" 시나리오 통과
- [ ] 캐시 히트율 > 60% 확인

---

## Phase 3.9: Unit Tests (병렬 가능)

### T033 [P]: LlamaChatService 단위 테스트

**설명**:
LlamaChatService의 핵심 메서드를 개별적으로 테스트합니다.

**파일**:
- `/home/eugene/bodam/backend/tests/unit/test_llama_chat_service.py` (생성)

**작업**:
- `_classify_query` 메서드 테스트 (쿼리 유형 분류)
- `_is_safe_query` 메서드 테스트 (SQL Injection 방지)
- `_generate_embedding` 메서드 테스트 (임베딩 생성)
- `_cosine_similarity` 메서드 테스트 (유사도 계산)
- Together AI API 모킹

**의존성**:
- T017, T018, T019 완료 후

**검증**:
- [ ] `pytest backend/tests/unit/test_llama_chat_service.py -v` 모두 통과
- [ ] SQL Injection 차단 확인 (INSERT/UPDATE/DELETE)

---

### T034 [P]: RefundService 단위 테스트

**설명**:
RefundService의 bulk 처리 로직을 개별적으로 테스트합니다.

**파일**:
- `/home/eugene/bodam/backend/tests/unit/test_refund_service.py` (생성)

**작업**:
- `bulk_approve` 메서드 테스트 (모두 성공)
- `bulk_approve` 메서드 테스트 (부분 성공)
- `bulk_reject` 메서드 테스트
- Toss API 모킹
- 트랜잭션 롤백 테스트

**의존성**:
- T024 완료 후

**검증**:
- [ ] `pytest backend/tests/unit/test_refund_service.py -v` 모두 통과
- [ ] 부분 성공 케이스 처리 확인

---

### T035 [P]: Admin 인증 단위 테스트

**설명**:
관리자 인증 미들웨어 및 의존성 함수를 테스트합니다.

**파일**:
- `/home/eugene/bodam/backend/tests/unit/test_admin_auth.py` (생성)

**작업**:
- `require_admin` 함수 테스트 (UserRole.ADMIN만 허용)
- 세션 검증 테스트
- 401/403 에러 응답 테스트

**의존성**:
- T007 완료 후

**검증**:
- [ ] `pytest backend/tests/unit/test_admin_auth.py -v` 모두 통과
- [ ] 비관리자 접근 차단 확인

---

## Phase 3.10: Documentation

### T036: CLAUDE.md 업데이트

**설명**:
CLAUDE.md에 SQLAdmin 관련 기술 스택 및 명령어를 추가합니다.

**파일**:
- `/home/eugene/bodam/CLAUDE.md` (수정)

**작업**:
- **Active Technologies**에 `sqladmin>=0.16.0` 추가
- **Project Structure**에 `backend/src/admin/` 디렉토리 추가
- **Commands**에 SQLAdmin 개발 명령어 추가:
  ```bash
  # SQLAdmin 로컬 테스트
  uvicorn src.main:app --reload --port 8000

  # Llama AI 채팅 테스트
  pytest backend/tests/integration/test_llama_chat_integration.py -v

  # 환불 Bulk Actions 테스트
  pytest backend/tests/integration/test_admin_refund_bulk_actions.py -v
  ```
- **Recent Changes**에 `005-sqladmin-integration-with` 추가

**의존성**:
- T027 완료 후

**검증**:
- [ ] CLAUDE.md에 SQLAdmin 관련 내용 추가 확인
- [ ] 명령어 실행 가능 확인

---

### T037: 배포 문서 작성 (specs/005-sqladmin-integration-with/deployment.md)

**설명**:
SQLAdmin + Llama AI 채팅 기능 배포 가이드를 작성합니다.

**파일**:
- `/home/eugene/bodam/specs/005-sqladmin-integration-with/deployment.md` (생성)

**작업**:
- 환경 변수 설정 가이드
- SQLAdmin 관리자 계정 생성 스크립트
- Kong Gateway 라우팅 설정 (`/admin` 경로)
- Nginx 설정 (HTTPS, 세션 쿠키)
- Kubernetes 배포 매니페스트 업데이트
- 성능 모니터링 설정 (Prometheus, Grafana)

**의존성**:
- T027 완료 후

**검증**:
- [ ] deployment.md 파일 생성 확인
- [ ] 배포 가이드 내용 완전성 확인

---

## 의존성 그래프

```
Setup (T001-T003)
    ↓
Contract Tests [P] (T004-T006) ← TDD, 실패해야 함
    ↓
Authentication (T007-T008)
    ↓
Admin Views [P] (T009-T015)
    ↓
View Registration (T016)
    ↓
Llama Chat Service (T017-T019)
    ↓
Chat API & UI (T020-T023)
    ↓
Refund Service (T024-T026)
    ↓
Main Integration (T027)
    ↓
Integration Tests [P] (T028-T032)
    ↓
Unit Tests [P] (T033-T035)
    ↓
Documentation (T036-T037)
```

---

## 병렬 실행 가능 태스크 그룹

### 그룹 1: Contract Tests (T004-T006)
```bash
# 병렬 실행 (다른 파일, 의존성 없음)
pytest backend/tests/contract/test_admin_ui_routes.py -v &
pytest backend/tests/contract/test_admin_chat_api.py -v &
pytest backend/tests/contract/test_admin_refund_actions.py -v &
wait
```

### 그룹 2: Admin Views (T009-T015)
```bash
# 병렬 실행 (독립적인 View 파일들)
# T009: backend/src/admin/views/user.py
# T010: backend/src/admin/views/donation.py
# T011: backend/src/admin/views/refund.py
# T012: backend/src/admin/views/fire_station.py
# T013: backend/src/admin/views/news_content.py
# T014: backend/src/admin/views/selenium_job.py
# T015: backend/src/admin/views/group.py
```

### 그룹 3: Integration Tests (T028-T032)
```bash
# 병렬 실행 (독립적인 테스트 파일들)
pytest backend/tests/integration/test_admin_authentication.py -v &
pytest backend/tests/integration/test_admin_crud_operations.py -v &
pytest backend/tests/integration/test_llama_chat_integration.py -v &
pytest backend/tests/integration/test_admin_refund_bulk_actions.py -v &
pytest backend/tests/integration/test_semantic_cache.py -v &
wait
```

### 그룹 4: Unit Tests (T033-T035)
```bash
# 병렬 실행 (독립적인 단위 테스트)
pytest backend/tests/unit/test_llama_chat_service.py -v &
pytest backend/tests/unit/test_refund_service.py -v &
pytest backend/tests/unit/test_admin_auth.py -v &
wait
```

---

## 검증 체크리스트

### 계약 검증
- [x] 모든 계약서 (`contracts/*.yaml`)에 대응하는 contract test가 있음 (T004-T006)
- [x] 모든 엔드포인트가 구현됨 (T008, T020, T025)

### 엔티티 검증
- [x] 모든 우선순위 높음/중간 엔티티에 대응하는 Admin View가 있음 (T009-T015)
- [x] data-model.md의 서비스 레이어 엔티티가 구현됨 (AdminSession, LlamaChatMessage 등)

### TDD 검증
- [x] 모든 contract tests가 구현 전에 작성됨 (T004-T006)
- [x] Integration tests가 구현 후에 작성됨 (T028-T032)

### 병렬성 검증
- [x] [P] 태스크들이 실제로 독립적임 (다른 파일)
- [x] 같은 파일을 수정하는 태스크에는 [P] 마킹 없음

### 파일 경로 검증
- [x] 모든 태스크가 절대 경로 또는 명확한 상대 경로 포함
- [x] `/home/eugene/bodam/backend/...` 형식 사용

---

## 태스크 요약

| Phase | 태스크 수 | 병렬 가능 | 설명 |
|-------|----------|----------|------|
| 3.1 Setup | 3 | 일부 | 프로젝트 구조, 의존성, 설정 |
| 3.2 Contract Tests | 3 | 전체 [P] | TDD, 실패해야 함 |
| 3.3 Authentication | 2 | 순차 | 인증 미들웨어, 로그인 |
| 3.4 Admin Views | 8 | 대부분 [P] | SQLAdmin ModelView 구현 |
| 3.5 Llama Chat | 7 | 순차 | AI 채팅 서비스, API, UI |
| 3.6 Bulk Actions | 3 | 순차 | 환불 대량 처리 |
| 3.7 Integration | 1 | - | FastAPI 앱 통합 |
| 3.8 Integration Tests | 5 | 전체 [P] | 통합 테스트 |
| 3.9 Unit Tests | 3 | 전체 [P] | 단위 테스트 |
| 3.10 Documentation | 2 | 일부 [P] | 문서화 |
| **총계** | **37** | **21개 [P]** | - |

---

## 실행 순서 권장사항

### 1단계: 기반 구축 (T001-T003)
- 프로젝트 구조 생성 및 의존성 설치

### 2단계: TDD - Contract Tests 작성 (T004-T006) [P]
- **병렬 실행 가능**
- **반드시 실패해야 함** (아직 구현 안 됨)

### 3단계: 인증 구현 (T007-T008)
- 관리자 인증은 모든 페이지의 선행 조건

### 4단계: Admin Views 구현 (T009-T016) [대부분 P]
- T009-T015는 병렬 실행 가능
- T016은 T009-T015 완료 후 순차 실행

### 5단계: Llama Chat 구현 (T017-T023)
- 순차 실행 (의존성 있음)

### 6단계: Bulk Actions 구현 (T024-T026)
- 순차 실행

### 7단계: Main Integration (T027)
- FastAPI 앱에 모든 기능 통합

### 8단계: Integration Tests (T028-T032) [P]
- **병렬 실행 가능**
- Contract tests 통과 확인

### 9단계: Unit Tests (T033-T035) [P]
- **병렬 실행 가능**

### 10단계: Documentation (T036-T037)
- 최종 문서화

---

## 주의 사항

1. **TDD 원칙 준수**: T004-T006은 **반드시 구현 전에 작성**되어야 하며, **실패해야** 합니다.
2. **병렬 실행**: [P] 마킹된 태스크는 병렬 실행 가능하지만, 동일 파일 수정 태스크는 순차 실행해야 합니다.
3. **의존성 확인**: 각 태스크 시작 전에 의존성 태스크가 완료되었는지 확인하세요.
4. **테스트 우선**: Contract tests → Implementation → Integration tests 순서를 지키세요.
5. **커밋 전략**: 각 태스크 완료 후 커밋하여 진행 상황을 추적하세요.
6. **환경 변수**: T002에서 `.env` 파일 설정을 완료하고 시작하세요.
7. **Semantic Cache**: T018에서 Redis 연결을 확인하고 진행하세요.
8. **Toss API**: T024에서 Toss Payments API 키를 확인하세요.

---

**총 37개 태스크 정의 완료**
**병렬 실행 가능 태스크: 21개**
**예상 완료 시간: 모든 태스크 순차 실행 시 ~2-3일, 병렬 실행 활용 시 ~1-2일**
