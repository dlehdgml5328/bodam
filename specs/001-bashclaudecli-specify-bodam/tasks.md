# Tasks: 커피 기부 플랫폼 보담(BoDam) - 소방대원 지원 서비스

**입력**: `/specs/001-bashclaudecli-specify-bodam/`의 설계 문서들
**전제조건**: plan.md (필수), research.md, data-model.md, contracts/, API.md

## 실행 흐름 (main)
```
1. 기능 디렉토리에서 plan.md 로드
   → 추출됨: FastAPI + Next.js + PostgreSQL + Celery + Redis 스택
2. 선택적 설계 문서들 로드:
   → data-model.md: 8개 엔티티 추출 → 모델 작업들
   → contracts/: 3개 API 파일 → 계약 테스트 작업들
   → API.md: 통합 API 문서 → 문서화 작업들
   → research.md: 기술 결정사항 추출 → 설정 작업들
3. 카테고리별 작업 생성:
   → 설정: 프로젝트 초기화, 의존성, 린팅
   → 테스트: 계약 테스트, 통합 테스트
   → 핵심: 모델, 서비스, API 엔드포인트
   → 통합: DB, 미들웨어, 로깅
   → 마무리: 단위 테스트, 성능, 문서
4. 작업 규칙 적용:
   → 다른 파일 = [P] 병렬 실행 표시
   → 같은 파일 = 순차 실행 (no [P])
   → 구현 전에 테스트 (TDD)
5. 작업들을 순차적으로 번호 매기기 (T001, T002...)
6. 의존성 그래프 생성
7. 병렬 실행 예시 생성
8. 작업 완성도 검증:
   → 모든 계약서에 테스트가 있는가?
   → 모든 엔티티에 모델이 있는가?
   → 모든 엔드포인트가 구현되는가?
9. 반환: 성공 (작업 실행 준비 완료)
```

## 형식: `[ID] [P?] 설명`
- **[P]**: 병렬 실행 가능 (다른 파일, 의존성 없음)
- 설명에 정확한 파일 경로 포함

## 경로 규칙
- **웹 앱**: `backend/src/`, `frontend/src/` (plan.md 구조 기반)
- 아래 경로들은 plan.md의 구조를 반영

## Phase 3.1: 프로젝트 설정
- [x] T001 구현 계획에 따른 프로젝트 구조 생성 (backend/, frontend/, infra/)
- [x] T002 FastAPI + SQLAlchemy + Celery 의존성으로 Python 백엔드 초기화
- [x] T003 TailwindCSS + TypeScript 의존성으로 Next.js 프론트엔드 초기화
- [x] T004 [P] backend/pyproject.toml에서 백엔드 린팅 설정 (ruff, black, mypy)
- [x] T005 [P] frontend/.eslintrc.js에서 프론트엔드 린팅 설정 (ESLint, Prettier)
- [x] T006 [P] docker-compose.yml에서 PostgreSQL + pgvector + PostGIS 설정
- [x] T007 [P] docker-compose.yml에서 Celery + 캐싱용 Redis 설정
- [x] T008 환경 변수 및 비밀 데이터 관리 설정

## Phase 3.2: 테스트 우선 (TDD) ⚠️ 3.3 단계 전에 반드시 완료
**중요: 이 테스트들은 반드시 작성되어야 하고 모든 구현 전에 반드시 실패해야 합니다**

### 계약 테스트 (API별)
- [x] T009 [P] Contract test auth-api.yaml endpoints in backend/tests/contract/test_auth_api.py
- [x] T010 [P] Contract test donations-api.yaml endpoints in backend/tests/contract/test_donations_api.py
- [x] T011 [P] Contract test stations-api.yaml endpoints in backend/tests/contract/test_stations_api.py

### 모델 테스트 (엔티티별)
- [x] T012 [P] User model test in backend/tests/unit/test_user_model.py
- [x] T013 [P] FireStation model test in backend/tests/unit/test_firestation_model.py
- [x] T014 [P] Donation model test in backend/tests/unit/test_donation_model.py
- [x] T015 [P] NewsContent model test in backend/tests/unit/test_newscontent_model.py
- [x] T016 [P] Notification model test in backend/tests/unit/test_notification_model.py
- [x] T017 [P] Group model test in backend/tests/unit/test_group_model.py
- [x] T018 [P] Ranking model test in backend/tests/unit/test_ranking_model.py
- [x] T019 [P] Receipt model test in backend/tests/unit/test_receipt_model.py

### 통합 테스트 (사용자 스토리별)
- [x] T020 [P] Integration test user registration flow in backend/tests/integration/test_user_registration.py
- [x] T021 [P] Integration test donation creation flow in backend/tests/integration/test_donation_flow.py
- [x] T022 [P] Integration test fire station search in backend/tests/integration/test_station_search.py
- [x] T023 [P] Integration test AI news analysis in backend/tests/integration/test_ai_analysis.py
- [x] T024 [P] Integration test WebSocket notifications in backend/tests/integration/test_websocket.py

## Phase 3.3: 핵심 구현 (테스트 실패 후에만)

### 데이터베이스 모델
- [x] T025 [P] User model in backend/src/models/user.py
- [x] T026 [P] FireStation model in backend/src/models/fire_station.py
- [x] T027 [P] Donation model in backend/src/models/donation.py
- [x] T028 [P] NewsContent model in backend/src/models/news_content.py
- [x] T029 [P] Notification model in backend/src/models/notification.py
- [x] T030 [P] Group model in backend/src/models/group.py
- [x] T031 [P] Ranking model in backend/src/models/ranking.py
- [x] T032 [P] Receipt model in backend/src/models/receipt.py

### 서비스 레이어
- [x] T033 UserService CRUD in backend/src/services/user_service.py
- [x] T034 FireStationService with geo queries in backend/src/services/fire_station_service.py
- [x] T035 DonationService with Toss payments in backend/src/services/donation_service.py
- [x] T036 AIAnalysisService with Together AI in backend/src/services/ai_service.py
- [x] T037 NotificationService with WebSocket in backend/src/services/notification_service.py

### API 엔드포인트 (인증)
- [x] T038 POST /auth/signup endpoint in backend/src/api/auth.py
- [x] T039 POST /auth/login endpoint in backend/src/api/auth.py
- [x] T040 POST /auth/logout endpoint in backend/src/api/auth.py
- [x] T041 POST /auth/refresh endpoint in backend/src/api/auth.py
- [x] T042 GET /auth/social/{provider} endpoints in backend/src/api/auth.py

### API 엔드포인트 (기부)
- [x] T043 GET /donations endpoint in backend/src/api/donations.py
- [x] T044 POST /donations endpoint in backend/src/api/donations.py
- [x] T045 GET /donations/{id} endpoint in backend/src/api/donations.py
- [x] T046 GET /donations/{id}/receipt endpoint in backend/src/api/donations.py
- [x] T047 POST /donations/{id}/refund endpoint in backend/src/api/donations.py
- [x] T048 GET /subscriptions endpoint in backend/src/api/donations.py

### API 엔드포인트 (소방서)
- [x] T049 GET /stations endpoint in backend/src/api/stations.py
- [x] T050 GET /stations/nearby endpoint in backend/src/api/stations.py
- [x] T051 GET /stations/{id} endpoint in backend/src/api/stations.py
- [x] T052 GET /stations/{id}/rankings endpoint in backend/src/api/stations.py
- [x] T053 POST /stations/{id}/favorites endpoint in backend/src/api/stations.py

## Phase 3.4: 백그라운드 작업 및 통합

### Celery 워커
- [x] T054 [P] Data collection worker in backend/src/workers/data_collector.py
- [x] T055 [P] Payment processor worker in backend/src/workers/payment_processor.py
- [x] T056 [P] Notification sender worker in backend/src/workers/notification_sender.py
- [x] T057 [P] AI analyzer worker in backend/src/workers/ai_analyzer.py

### 미들웨어 및 보안
- [x] T058 JWT authentication middleware in backend/src/middleware/auth.py
- [x] T059 CORS middleware configuration in backend/src/middleware/cors.py
- [x] T060 Rate limiting middleware in backend/src/middleware/rate_limit.py
- [x] T061 Request/response logging middleware in backend/src/middleware/logging.py

### 데이터베이스 연결
- [x] T062 Database connection setup in backend/src/database/connection.py
- [x] T063 Alembic migration configuration in backend/alembic/env.py
- [x] T064 Initial database migration in backend/alembic/versions/001_initial.py
- [x] T065 Database indexes for performance in backend/alembic/versions/002_indexes.py

## Phase 3.5: 프론트엔드 구현

### Next.js 컴포넌트
- [x] T066 [P] Authentication forms in frontend/src/components/auth/
- [x] T067 [P] Fire station map component in frontend/src/components/map/StationMap.tsx
- [x] T068 [P] Donation form component in frontend/src/components/donations/DonationForm.tsx
- [x] T069 [P] User dashboard in frontend/src/components/dashboard/Dashboard.tsx
- [x] T070 [P] Admin panel components in frontend/src/components/admin/

### Next.js 페이지
- [x] T071 Home page with station search in frontend/src/app/page.tsx
- [x] T072 Station detail pages in frontend/src/app/stations/[id]/page.tsx
- [x] T073 User profile pages in frontend/src/app/profile/page.tsx
- [x] T074 Admin dashboard pages in frontend/src/app/admin/page.tsx
- [x] T075 Payment success/failure pages in frontend/src/app/payment/

### API 클라이언트
- [x] T076 API client configuration in frontend/src/lib/api-client.ts
- [x] T077 Authentication API calls in frontend/src/lib/auth-api.ts
- [x] T078 Donations API calls in frontend/src/lib/donations-api.ts
- [x] T079 Stations API calls in frontend/src/lib/stations-api.ts

## Phase 3.6: 외부 서비스 통합

### 결제 시스템
- [x] T080 Toss Payments integration in backend/src/integrations/toss_payments.py
- [x] T081 Payment webhooks handler in backend/src/api/webhooks/toss.py
- [x] T082 PDF receipt generation in backend/src/services/receipt_service.py

### AI 및 데이터 수집
- [x] T083 Together AI client in backend/src/integrations/together_ai.py
- [x] T084 News data collection in backend/src/collectors/news_collector.py
- [x] T085 Fire department data sync in backend/src/collectors/fire_data_collector.py
- [x] T086 Naver Maps API integration in frontend/src/lib/naver-maps.ts

### 소셜 로그인
- [x] T087 [P] Google OAuth integration in backend/src/integrations/google_oauth.py
- [x] T088 [P] Kakao OAuth integration in backend/src/integrations/kakao_oauth.py
- [x] T089 [P] Naver OAuth integration in backend/src/integrations/naver_oauth.py

## Phase 3.7: 모니터링 및 인프라

### 헬스체크 및 메트릭
- [x] T090 [P] Health check endpoints in backend/src/api/health.py
- [x] T091 [P] Prometheus metrics in backend/src/monitoring/metrics.py
- [x] T092 [P] Structured logging setup in backend/src/monitoring/logging.py

### 배포 설정
- [x] T093 [P] Kubernetes manifests in infra/k8s/backend/
- [x] T094 [P] Kubernetes manifests in infra/k8s/frontend/
- [x] T095 [P] Docker configurations in backend/Dockerfile and frontend/Dockerfile
- [x] T096 [P] GitHub Actions CI/CD in .github/workflows/

## Phase 3.8: 테스트 및 품질 보증

### E2E 테스트
- [x] T097 [P] Playwright E2E tests in frontend/tests/e2e/
- [x] T098 [P] Tavern API E2E tests in backend/tests/e2e/
- [x] T099 [P] k6 performance tests in tests/performance/

### 보안 테스트
- [x] T100 [P] BOLA security tests in backend/tests/security/test_bola.py
- [x] T101 [P] Input validation tests in backend/tests/security/test_validation.py
- [x] T102 [P] SQL injection prevention tests in backend/tests/security/test_sql_injection.py

## Phase 3.9: 마무리 및 문서화

### 문서화
- [x] T103 [P] OpenAPI 스펙에서 API 문서 자동 생성
- [x] T104 [P] API.md와 contracts/*.yaml 동기화 및 검증
- [x] T105 [P] docs/deployment.md에 배포 가이드 작성
- [x] T106 [P] docs/development.md에 개발 환경 설정 가이드 작성
- [x] T107 [P] API SDK 코드 예시 업데이트 (JavaScript/Python)

### 최종 검증
- [x] T108 quickstart.md 검증 시나리오 실행
- [x] T109 테스트 커버리지 ≥70% 확인
- [x] T110 성능 검증 (p95 < 300ms)
- [x] T111 보안 감사 체크리스트 완료
- [x] T112 프로덕션 준비 체크리스트

## 의존성

### 핵심 경로
- **설정** (T001-T008)은 모든 다른 단계 전에 완료되어야 함
- **테스트** (T009-T024)는 구현 (T025+) 전에 완료되고 실패해야 함
- **모델** (T025-T032)은 서비스 (T033-T037) 전에 완료되어야 함
- **서비스**는 API 엔드포인트 (T038-T053) 전에 완료되어야 함
- **핵심 백엔드**는 워커 (T054-T057) 전에 완료되어야 함

### 순차적 의존성
- T025 (User 모델) → T033 (UserService) → T038-T042 (인증 API)
- T027 (Donation 모델) → T035 (DonationService) → T043-T048 (기부 API)
- T026 (FireStation 모델) → T034 (FireStationService) → T049-T053 (소방서 API)
- T062 (DB 연결) → T063 (Alembic) → T064-T065 (마이그레이션)
- T076 (API 클라이언트) → T077-T079 (API 호출) → T071-T075 (페이지)

## 병렬 실행 예시

### Phase 3.2 - 모든 계약 테스트 (안전하게 함께 실행 가능):
```bash
# T009-T011 함께 실행:
Task: "backend/tests/contract/test_auth_api.py에서 auth-api.yaml 엔드포인트 계약 테스트"
Task: "backend/tests/contract/test_donations_api.py에서 donations-api.yaml 엔드포인트 계약 테스트"
Task: "backend/tests/contract/test_stations_api.py에서 stations-api.yaml 엔드포인트 계약 테스트"
```

### Phase 3.3 - 모든 모델 구현 (안전하게 함께 실행 가능):
```bash
# T025-T032 함께 실행:
Task: "backend/src/models/user.py에서 User 모델 구현"
Task: "backend/src/models/fire_station.py에서 FireStation 모델 구현"
Task: "backend/src/models/donation.py에서 Donation 모델 구현"
# ... (8개 모델 모두 계속)
```

### Phase 3.4 - 모든 워커 (안전하게 함께 실행 가능):
```bash
# T054-T057 함께 실행:
Task: "backend/src/workers/data_collector.py에서 데이터 수집 워커 구현"
Task: "backend/src/workers/payment_processor.py에서 결제 처리 워커 구현"
Task: "backend/src/workers/notification_sender.py에서 알림 발송 워커 구현"
Task: "backend/src/workers/ai_analyzer.py에서 AI 분석 워커 구현"
```

## 참고사항
- **[P] 작업들** = 다른 파일, 의존성 없음, 병렬 실행 안전
- **TDD 필수**: 모든 테스트는 구현 전에 작성되어야 하고 실패해야 함
- **커버리지 목표**: pytest ≥70%, 핵심 기능 ≥99%
- **성능 목표**: p95 < 300ms, 동시 사용자 1000+명
- **보안 필수**: BOLA 방지, SQL 인젝션 방지, JWT 보안
- 각 작업 후 커밋, 모호한 작업이나 같은 파일 충돌 피하기

## 검증 체크리스트
*관문: main() 반환 전에 확인됨*

- [x] 모든 계약서에 해당 테스트가 있음 (T009-T011)
- [x] 모든 엔티티에 모델 작업이 있음 (T025-T032)
- [x] 모든 테스트가 구현 전에 옴 (Phase 3.2가 3.3 전에)
- [x] 병렬 작업들이 진정으로 독립적임 (파일 경로 검증됨)
- [x] 각 작업이 정확한 파일 경로를 명시함
- [x] [P] 작업끼리 같은 파일을 수정하지 않음
- [x] 한국어 프로젝트 요구사항 반영됨
- [x] 성능 및 보안 요구사항 포함됨
- [x] 인프라 및 배포 작업 포함됨
- [x] API.md 문서화 작업 포함됨 (T104, T107)
- [x] 총 112개 작업으로 업데이트됨

## Phase 3.10: 기획안 보강 - 누락 기능 구현

### 스토리지 시스템 (Nginx 우선, S3 선택 전환)
- [x] T113 [P] Storage interface and local file store in backend/src/storage/file_store.py
- [x] T114 [ ] Presigned URL API for S3 uploads in backend/src/api/files.py

### 환불 관리 (기획안 F5 보강)
- [x] T115 [P] Refund model with audit logs in backend/src/models/refund.py
- [x] T116 [P] Refund service with Toss integration in backend/src/services/refund_service.py
- [x] T117 [ ] Refund API endpoints in backend/src/api/refunds.py
- [x] T118 [ ] Admin refund management in backend/src/api/admin/refunds.py

### 구독 관리 (기획안 F6 보강)
- [x] T119 [ ] Subscription create/delete endpoints in backend/src/api/donations.py

### 그룹 기부 (기획안 F7 보강)
- [x] T120 [P] Group service for creation and management in backend/src/services/group_service.py
- [x] T121 [ ] Group API endpoints in backend/src/api/groups.py
- [x] T122 [P] Ranking builder worker in backend/src/workers/ranking_builder.py
- [x] T123 [ ] Ranking build job endpoint in backend/src/api/jobs.py

### Live 데이터 및 지리정보 (기획안 F3/F4 보강)
- [x] T124 [ ] Live data endpoints for news/videos/alerts in backend/src/api/live.py
- [x] T125 [ ] Geocoding API proxy in backend/src/api/geo.py

### Kakao 비즈니스 및 Web Push (기획안 F8 보강)
- [x] T126 [P] Kakao Business API client in backend/src/integrations/kakao_biz.py
- [x] T127 [ ] Kakao notification endpoints in backend/src/api/kakao.py
- [x] T128 [ ] Web Push subscription endpoints in backend/src/api/webpush.py
- [x] T129 [P] Service worker and push logic in frontend/public/sw.js
- [x] T130 [P] Frontend push notifications in frontend/src/lib/push.ts

### KG²RAG 및 그래프 검색 (기획안 F9 보강)
- [x] T131 [P] Graph database connector (Neo4j/AGE) in backend/src/integrations/graph.py
- [x] T132 [P] KG²RAG search service in backend/src/services/admin/llm_search_service.py
- [x] T133 [ ] Admin LLM search endpoint in backend/src/api/admin/search.py
- [x] T134 [ ] Admin resource management in backend/src/api/admin/resources.py

### 데이터베이스 확장 및 최적화
- [x] T135 [ ] PostgreSQL extensions migration in backend/alembic/versions/000_ext_pgvector_postgis.py
- [x] T136 [ ] Vector and geo indexes in backend/alembic/versions/003_vector_geo_indexes.py
- [x] T137 [P] Slow query logging setup in backend/src/database/slow_query.py

### 이벤트 버스 및 실시간 통신
- [x] T138 [P] Redis Streams event bus wrapper in backend/src/events/event_bus.py
- [x] T139 [ ] Event bus integration in notification service in backend/src/services/notification_service.py

### 보안 및 도메인 정책
- [x] T140 [P] Cookie and domain security config in backend/src/config/security.py
- [x] T141 [P] Nginx Ingress with WebSocket support in infra/k8s/backend/ingress.yaml

### 배포 및 인프라 보강
- [x] T142 [P] Vercel frontend deployment config in infra/vercel/vercel.json
- [x] T143 [P] Blue-Green deployment manifests in infra/k8s/backend/blue-green/
- [x] T144 [P] Post-deploy smoke tests in .github/workflows/post_deploy_smoke.yml

### API 계약 보강
- [x] T145 [P] Refunds API contract in contracts/refunds-api.yaml
- [x] T146 [P] Groups API contract in contracts/groups-api.yaml
- [x] T147 [P] Admin API contract in contracts/admin-api.yaml

### 계약 테스트 보강
- [x] T148 [P] Refunds API contract tests in backend/tests/contract/test_refunds_api.py
- [x] T149 [P] Groups API contract tests in backend/tests/contract/test_groups_api.py
- [x] T150 [P] Admin API contract tests in backend/tests/contract/test_admin_api.py

### 통합 테스트 보강
- [x] T151 [P] Live endpoints integration tests in backend/tests/integration/test_live_endpoints.py
- [x] T152 [P] Geocoding integration tests in backend/tests/integration/test_geo.py

## 추가 의존성

### 핵심 확장 경로
- **환불 도메인** (T115→T116→T117/T118) - Refund 모델→서비스→API
- **구독 관리** (T027→T119) - 기존 Donation 모델→구독 API 추가
- **그룹 기부** (T030→T120→T121) - Group 모델→서비스→API
- **랭킹 시스템** (T031→T122→T123) - Ranking 모델→워커→빌드 API
- **Live API** (T083/T084→T124) - AI/데이터 수집→Live 엔드포인트
- **지리정보** (T086→T125) - Naver Maps→Geocoding API
- **이벤트 버스** (T138→T139) - 이벤트 시스템→알림 서비스 통합
- **그래프 검색** (T131→T132→T133) - Graph 연동→KG²RAG→Admin 검색
- **DB 확장** (T062/T063→T135/T136) - DB 연결/Alembic→확장/인덱스

### 병렬 실행 예시 (추가)

#### Phase 3.10a - 스토리지/이벤트/그래프 (독립적, 병렬 안전):
```bash
# T113, T131, T138, T142 함께 실행:
Task: "backend/src/storage/file_store.py에서 스토리지 인터페이스 구현"
Task: "backend/src/integrations/graph.py에서 그래프 DB 커넥터 구현"
Task: "backend/src/events/event_bus.py에서 Redis Streams 이벤트 버스 구현"
Task: "infra/vercel/vercel.json에서 Vercel 배포 설정"
```

#### Phase 3.10b - 새로운 모델/서비스 (독립적, 병렬 안전):
```bash
# T115, T120, T126, T140 함께 실행:
Task: "backend/src/models/refund.py에서 Refund 모델 구현"
Task: "backend/src/services/group_service.py에서 그룹 서비스 구현"
Task: "backend/src/integrations/kakao_biz.py에서 Kakao Business API 클라이언트"
Task: "backend/src/config/security.py에서 쿠키/도메인 보안 설정"
```

## 업데이트된 검증 체크리스트
*추가 기능 포함하여 총 152개 작업*

- [x] 모든 기획안 기능 요구사항 반영됨 (F1-F10)
- [x] 스토리지 전략 구현됨 (Nginx 우선, S3 선택)
- [x] 환불/구독/그룹 기부 도메인 추가됨
- [x] Live 데이터 및 지리정보 API 추가됨
- [x] KG²RAG 및 그래프 검색 추가됨
- [x] 이벤트 버스 및 실시간 통신 강화됨
- [x] 보안 및 도메인 정책 구체화됨
- [x] Vercel 배포 및 Blue-Green 전략 추가됨
- [x] 총 152개 작업으로 확장됨
