# 데이터 모델: SQLAdmin 통합

## 개요
보담 프로젝트의 모든 데이터 모델과 SQLAdmin 관리자 화면에서 표시할 필드를 정의합니다.
기존 모델은 변경하지 않으며, 관리자 기능을 위한 서비스 레이어 엔티티만 추가합니다.

---

## 기존 모델 (DB 테이블, 변경 없음)

### User (사용자)
**테이블명**: `users`

#### 필드
- `id`: UUID (Primary Key)
- `email`: String(255) - 이메일 주소 (고유)
- `password_hash`: String(255) - 암호화된 비밀번호
- `name`: String(120) - 사용자 이름
- `phone`: String(20), nullable - 전화번호
- `role`: Enum(UserRole) - 사용자 역할 (donor, admin, moderator)
- `social_provider`: String(50), nullable - 소셜 로그인 제공자
- `social_id`: String(120), nullable - 소셜 로그인 ID
- `tier`: Integer - 사용자 등급 (기본값: 1)
- `total_donated`: Numeric(12,2) - 총 기부 금액
- `created_at`: DateTime(TZ) - 생성 시각
- `updated_at`: DateTime(TZ) - 수정 시각
- `is_active`: Boolean - 활성화 여부

#### 관계 (Relationships)
- `donations`: User가 한 기부 목록
- `donation_subscriptions`: 정기 기부 구독 목록

#### 관리자 화면 표시 필드
- 목록: id, email, name, role, tier, total_donated, is_active, created_at
- 상세: 모든 필드 + 관련 기부 내역
- 필터: role, tier, is_active
- 검색: email, name

---

### Donation (기부)
**테이블명**: `donations`

#### 필드
- `id`: UUID (Primary Key)
- `user_id`: UUID (FK → users.id)
- `fire_station_id`: UUID (FK → fire_stations.id)
- `group_id`: UUID (FK → groups.id), nullable
- `mode`: Enum(DonationMode) - single, multiple
- `amount`: Numeric(12,2) - 기부 금액
- `currency`: String(3) - 통화 (기본값: KRW)
- `type`: Enum(DonationType) - one_time, recurring
- `frequency`: String(20), nullable - 정기 기부 주기
- `status`: Enum(DonationStatus) - pending, completed, failed, refunded
- `payment_method`: String(50), nullable - 결제 수단
- `toss_payment_key`: String(120), nullable - Toss 결제 키
- `toss_order_id`: String(120) - Toss 주문 ID (고유)
- `billing_customer_key`: String(120), nullable
- `billing_key`: String(120), nullable
- `subscription_id`: UUID (FK → donation_subscriptions.id), nullable
- `message`: String(500), nullable - 응원 메시지
- `donor_display_name`: String(120), nullable - 기부자 표시 이름
- `is_anonymous`: Boolean - 익명 여부
- `needs_receipt`: Boolean - 영수증 필요 여부
- `is_group_anonymous`: Boolean - 그룹 내 익명 여부
- `metadata_json`: JSON, nullable - 메타데이터
- `receipt_url`: String(255), nullable - 영수증 URL
- `created_at`: DateTime(TZ)
- `completed_at`: DateTime(TZ), nullable
- `refunded_at`: DateTime(TZ), nullable

#### 관계
- `user`: 기부한 사용자
- `fire_station`: 수혜 소방서
- `group`: 그룹 기부 캠페인
- `allocations`: 기부금 분배 내역
- `subscription`: 정기 기부 구독

#### 관리자 화면 표시 필드
- 목록: id, user_id(email), fire_station_id(name), amount, status, type, created_at
- 상세: 모든 필드 + 사용자 정보 + 소방서 정보
- 필터: status, type, mode
- 검색: toss_order_id, donor_display_name
- 통계: 총 기부 금액, 완료 건수, 환불 건수

---

### DonationAllocation (기부금 배분)
**테이블명**: `donation_allocations`

#### 필드
- `id`: UUID (Primary Key)
- `donation_id`: UUID (FK → donations.id)
- `fire_station_id`: UUID (FK → fire_stations.id)
- `amount`: Numeric(12,2) - 배분 금액
- `allocation_type`: Enum(AllocationType) - primary, split, each, custom

#### 관계
- `donation`: 원본 기부
- `fire_station`: 배분 대상 소방서

#### 관리자 화면 표시 필드
- 목록: id, donation_id, fire_station_id(name), amount, allocation_type
- 상세: 모든 필드

---

### DonationSubscription (정기 기부 구독)
**테이블명**: `donation_subscriptions`

#### 필드
- `id`: UUID (Primary Key)
- `user_id`: UUID (FK → users.id)
- `origin_donation_id`: UUID (FK → donations.id), nullable
- `status`: Enum(SubscriptionStatus) - active, paused, cancelled
- `cycle`: Enum(SubscriptionCycle) - monthly, quarterly, yearly
- `amount`: Numeric(12,2) - 구독 금액
- `currency`: String(3)
- `next_billing_at`: DateTime(TZ), nullable
- `started_at`: DateTime(TZ)
- `paused_at`: DateTime(TZ), nullable
- `ended_at`: DateTime(TZ), nullable
- `toss_customer_key`: String(120), nullable
- `toss_billing_key`: String(120), nullable

#### 관계
- `user`: 구독자
- `origin_donation`: 최초 기부

#### 관리자 화면 표시 필드
- 목록: id, user_id(email), status, cycle, amount, next_billing_at
- 상세: 모든 필드 + 사용자 정보
- 필터: status, cycle

---

### FireStation (소방서)
**테이블명**: `fire_stations`

#### 필드
- `id`: UUID (Primary Key)
- `name`: String(200) - 소방서 이름
- `address`: String(255) - 주소
- `location`: Geometry(POINT, SRID=4326) - 위치 좌표
- `phone`: String(30) - 전화번호
- `station_code`: String(50) - 소방서 코드 (고유)
- `region`: String(100) - 지역
- `district`: String(100) - 구역
- `status`: Enum(StationStatus) - active, closed, merged
- `total_received`: Numeric(14,2) - 총 수령 금액
- `donor_count`: Integer - 기부자 수
- `last_incident_at`: DateTime(TZ), nullable - 최근 사고 시각
- `created_at`: DateTime(TZ)
- `updated_at`: DateTime(TZ)

#### 관계
- `status_snapshot`: 실시간 상태 정보
- `donations`: 받은 기부 목록

#### 관리자 화면 표시 필드
- 목록: id, name, region, district, total_received, donor_count, status
- 상세: 모든 필드 + 지도 표시(location)
- 필터: status, region
- 검색: name, station_code

---

### FireStationStatus (소방서 실시간 상태)
**테이블명**: `fire_station_statuses`

#### 필드
- `id`: UUID (Primary Key)
- `station_id`: UUID (FK → fire_stations.id, unique)
- `status`: Enum(LiveStatus) - dispatching, suppressing, standby, maintenance
- `priority`: Enum(EmergencyPriority) - high, medium, low
- `status_label`: String(50), nullable
- `summary`: Text, nullable
- `updated_at`: DateTime(TZ)

#### 관계
- `station`: 소방서
- `active_incidents`: 현재 진행 중인 사고 목록

#### 관리자 화면 표시 필드
- 목록: id, station_id(name), status, priority, updated_at
- 상세: 모든 필드 + 소방서 정보
- 필터: status, priority

---

### FireStationActiveIncident (진행 중 사고)
**테이블명**: `fire_station_active_incidents`

#### 필드
- `status_id`: UUID (FK → fire_station_statuses.id, PK)
- `incident_id`: UUID (FK → news_content.id, PK)
- `started_at`: DateTime(TZ), nullable

#### 관계
- `status`: 소방서 상태
- `incident`: 뉴스 콘텐츠

#### 관리자 화면 표시 필드
- 목록: status_id, incident_id, started_at
- 상세: 모든 필드 + 관련 정보

---

### NewsContent (뉴스 콘텐츠)
**테이블명**: `news_content`

#### 필드
- `id`: UUID (Primary Key)
- `analysis_job_id`: UUID, nullable - 분석 작업 ID
- `title`: String(255) - 제목
- `content`: Text - 본문
- `source`: String(50) - 출처
- `source_url`: String(255) - 원본 URL
- `published_at`: DateTime(TZ) - 발행 시각
- `location`: Geometry(POINT, SRID=4326), nullable - 사고 위치
- `embedding`: Vector(1536) - 임베딩 벡터
- `relevance_score`: Integer - 관련성 점수
- `summary`: Text - 요약
- `keywords`: ARRAY(String(50)) - 키워드 목록
- `status`: Enum(ContentStatus) - auto_approved, pending_review, rejected
- `reviewed_by`: UUID (FK → users.id), nullable
- `reviewed_at`: DateTime(TZ), nullable
- `created_at`: DateTime(TZ)

#### 관리자 화면 표시 필드
- 목록: id, title, source, relevance_score, status, published_at
- 상세: 모든 필드 (embedding 제외)
- 필터: status, source
- 검색: title, keywords

---

### NewsMatch (뉴스-사고 매칭)
**테이블명**: `news_matches`

#### 필드
- `id`: Integer (Primary Key, autoincrement)
- `incident_id`: String(50) (FK → fire_incidents.id)
- `news_type`: String(20) - naver, youtube
- `news_id`: String(200) - 뉴스 ID
- `title`: String(500) - 제목
- `url`: Text - URL
- `published_at`: DateTime(TZ), nullable
- `thumbnail_url`: Text, nullable
- `similarity_score`: Float, nullable - 유사도 점수 (0.0 ~ 1.0)
- `matched_at`: DateTime(TZ)
- `created_at`: DateTime(TZ)

#### 관계
- `incident`: 화재 사고

#### 관리자 화면 표시 필드
- 목록: id, incident_id, news_type, title, similarity_score, matched_at
- 상세: 모든 필드
- 필터: news_type
- 검색: title

---

### FireIncident (화재 사고)
**테이블명**: `fire_incidents`

#### 필드
- `id`: String(50) (Primary Key) - 예: F2025001
- `title`: String(500) - 제목
- `location_address`: Text - 주소
- `latitude`: Float, nullable
- `longitude`: Float, nullable
- `occurred_at`: DateTime(TZ) - 발생 시각
- `status`: String(50) - dispatching, suppressing, contained, resolved
- `severity`: String(20), nullable - critical, high, medium, low
- `casualties_injured`: Integer - 부상자 수
- `casualties_dead`: Integer - 사망자 수
- `estimated_damage`: BigInteger, nullable - 예상 피해액 (원)
- `source_url`: Text, nullable
- `created_at`: DateTime(TZ)
- `updated_at`: DateTime(TZ)

#### 관계
- `dispatch_events`: 출동 이벤트 목록
- `news_matches`: 관련 뉴스 목록

#### 관리자 화면 표시 필드
- 목록: id, title, status, severity, occurred_at, casualties_injured, casualties_dead
- 상세: 모든 필드 + 지도 표시(lat/lng)
- 필터: status, severity
- 검색: title, location_address

---

### SeleniumCrawlJob (Selenium 크롤 작업)
**테이블명**: `selenium_crawl_jobs`

#### 필드
- `id`: UUID (Primary Key)
- `url`: String(2048) - 크롤링 대상 URL
- `browser_type`: Enum(BrowserType) - chrome, firefox
- `wait_conditions`: JSONB, nullable - 대기 조건
- `retry_count`: Integer - 재시도 횟수
- `max_retries`: Integer - 최대 재시도 횟수
- `status`: Enum(JobStatus) - pending, running, completed, failed, timeout
- `created_at`: Timestamp(TZ)
- `started_at`: Timestamp(TZ), nullable
- `completed_at`: Timestamp(TZ), nullable
- `error_message`: Text, nullable
- `job_metadata`: JSONB, nullable

#### 관계
- `crawled_contents`: 크롤링된 콘텐츠 목록

#### 관리자 화면 표시 필드
- 목록: id, url(truncated), status, retry_count, created_at
- 상세: 모든 필드
- 필터: status, browser_type
- 액션: 재시도, 취소

---

### CrawledContent (크롤링된 콘텐츠)
**테이블명**: `crawled_contents`

#### 필드
- `id`: UUID (Primary Key)
- `crawl_job_id`: UUID (FK → selenium_crawl_jobs.id)
- `source_url`: String(2048) - 출처 URL
- `rendered_html`: Text, nullable - 렌더링된 HTML
- `extracted_data`: JSONB - 추출된 데이터
- `screenshot_url`: String(2048), nullable
- `content_metadata`: JSONB, nullable
- `created_at`: Timestamp(TZ)

#### 관계
- `crawl_job`: 크롤 작업

#### 관리자 화면 표시 필드
- 목록: id, source_url(truncated), created_at
- 상세: 모든 필드 (rendered_html 축약 표시)

---

### Refund (환불)
**테이블명**: `refunds`

#### 필드
- `id`: UUID (Primary Key)
- `donation_id`: UUID (FK → donations.id)
- `reason`: Text - 환불 사유
- `amount`: Numeric(12,2) - 환불 금액
- `status`: Enum(RefundStatus) - pending, approved, rejected
- `reviewer_id`: UUID, nullable - 검토자 ID
- `reviewed_at`: DateTime(TZ), nullable
- `created_at`: DateTime(TZ)

#### 관리자 화면 표시 필드
- 목록: id, donation_id, amount, status, created_at
- 상세: 모든 필드 + 기부 정보
- 필터: status
- 액션: 승인, 거부 (bulk 지원)

---

### Group (그룹 기부 캠페인)
**테이블명**: `groups`

#### 필드
- `id`: UUID (Primary Key)
- `name`: String(120) - 그룹 이름
- `description`: String(500) - 설명
- `target_amount`: Numeric(12,2) - 목표 금액
- `current_amount`: Numeric(12,2) - 현재 모금액
- `fire_station_id`: UUID (FK → fire_stations.id)
- `creator_id`: UUID (FK → users.id)
- `is_public`: Boolean - 공개 여부
- `invite_code`: String(24) - 초대 코드 (고유)
- `deadline`: DateTime(TZ), nullable
- `status`: Enum(GroupStatus) - active, completed, expired
- `member_count`: Integer - 멤버 수
- `created_at`: DateTime(TZ)
- `completed_at`: DateTime(TZ), nullable

#### 관계
- `members`: 그룹 멤버 목록

#### 관리자 화면 표시 필드
- 목록: id, name, target_amount, current_amount, member_count, status
- 상세: 모든 필드 + 멤버 목록
- 필터: status
- 검색: name

---

### GroupMembership (그룹 멤버십)
**테이블명**: `group_memberships`

#### 필드
- `id`: UUID (Primary Key)
- `group_id`: UUID (FK → groups.id)
- `user_id`: UUID (FK → users.id)
- `role`: String(20) - member, admin
- `contributed_amount`: Numeric(12,2) - 기여 금액
- `joined_at`: DateTime(TZ)

#### 관계
- `group`: 그룹

#### 관리자 화면 표시 필드
- 목록: id, group_id(name), user_id(email), role, contributed_amount
- 상세: 모든 필드

---

### Notification (알림)
**테이블명**: `notifications`

#### 필드
- `id`: UUID (Primary Key)
- `user_id`: UUID (FK → users.id)
- `type`: Enum(NotificationType) - donation_success, incident_alert, system
- `title`: String(200) - 제목
- `message`: Text - 메시지
- `related_id`: UUID, nullable - 관련 엔티티 ID
- `channels`: ARRAY(String(20)) - 알림 채널 목록
- `status`: Enum(NotificationStatus) - pending, sent, failed
- `is_read`: Boolean - 읽음 여부
- `sent_at`: DateTime(TZ), nullable
- `read_at`: DateTime(TZ), nullable
- `created_at`: DateTime(TZ)

#### 관리자 화면 표시 필드
- 목록: id, user_id(email), type, title, status, created_at
- 상세: 모든 필드
- 필터: type, status

---

### Receipt (영수증)
**테이블명**: `receipts`

#### 필드
- `id`: UUID (Primary Key)
- `donation_id`: UUID (FK → donations.id)
- `receipt_number`: String(50) - 영수증 번호 (고유)
- `recipient_name`: String(120) - 수령인 이름
- `recipient_phone`: String(20) - 수령인 전화번호
- `amount`: Numeric(12,2) - 금액
- `issue_date`: Date - 발행일
- `pdf_url`: String(255) - PDF URL
- `email_sent`: Boolean - 이메일 발송 여부
- `created_at`: DateTime(TZ)

#### 관계
- `donation`: 기부

#### 관리자 화면 표시 필드
- 목록: id, receipt_number, recipient_name, amount, issue_date, email_sent
- 상세: 모든 필드 + 기부 정보
- 필터: email_sent
- 검색: receipt_number, recipient_name

---

## 서비스 레이어 엔티티 (새로 추가, DB 테이블 아님)

이 엔티티들은 SQLAdmin 관리자 기능을 위한 인메모리 객체로, 데이터베이스 테이블로 생성되지 않습니다.

### AdminSession (관리자 세션)
**설명**: Llama AI 채팅 세션을 관리하는 인메모리 객체

#### 필드
- `session_id`: UUID - 세션 고유 ID
- `admin_user_id`: UUID - 관리자 사용자 ID
- `conversation_history`: List[LlamaChatMessage] - 대화 기록 (최대 20개)
- `created_at`: datetime - 세션 생성 시각
- `last_activity_at`: datetime - 마지막 활동 시각
- `expires_at`: datetime - 만료 시각 (생성 후 30분)
- `semantic_cache`: Dict[str, Any] - 시맨틱 캐시 (유사 쿼리 응답 저장)

#### 메서드
- `is_expired() -> bool`: 세션 만료 여부 확인
- `add_message(message: LlamaChatMessage)`: 메시지 추가
- `clear_history()`: 대화 기록 초기화
- `get_cached_response(query: str) -> Optional[str]`: 유사 쿼리 캐시 조회

---

### LlamaChatMessage (채팅 메시지)
**설명**: Llama AI 대화 메시지

#### 필드
- `role`: Literal["user", "assistant"] - 역할
- `content`: str - 메시지 내용
- `timestamp`: datetime - 전송 시각
- `token_count`: int - 토큰 수 (대략적)
- `metadata`: Dict[str, Any], optional - 메타데이터 (SQL 쿼리, 실행 시간 등)

#### 메서드
- `to_dict() -> dict`: 딕셔너리로 변환
- `estimate_tokens() -> int`: 토큰 수 추정

---

### RefundBulkAction (환불 bulk 액션 DTO)
**설명**: 환불 대량 처리를 위한 데이터 전송 객체

#### 필드
- `refund_ids`: List[UUID] - 처리할 환불 ID 목록
- `action`: Literal["approve", "reject"] - 액션 타입
- `reason`: str - 처리 사유
- `admin_id`: UUID - 처리하는 관리자 ID
- `processed_at`: datetime - 처리 시각

#### 메서드
- `validate() -> bool`: 입력 검증
- `to_dict() -> dict`: 딕셔너리로 변환

---

### QueryResult (쿼리 결과)
**설명**: Llama AI 쿼리 실행 결과

#### 필드
- `query`: str - 원본 쿼리
- `sql_query`: str, optional - 생성된 SQL 쿼리
- `result`: Any - 실행 결과 (DataFrame, JSON 등)
- `execution_time_ms`: float - 실행 시간 (밀리초)
- `error`: str, optional - 에러 메시지
- `cached`: bool - 캐시에서 반환 여부

#### 메서드
- `is_success() -> bool`: 성공 여부
- `to_dict() -> dict`: 딕셔너리로 변환

---

### AdminDashboardMetrics (관리자 대시보드 메트릭)
**설명**: 관리자 대시보드에 표시할 집계 메트릭

#### 필드
- `total_users`: int - 총 사용자 수
- `active_users_30d`: int - 30일 활성 사용자 수
- `total_donations`: Decimal - 총 기부 금액
- `donations_count`: int - 기부 건수
- `pending_refunds`: int - 대기 중 환불 건수
- `active_subscriptions`: int - 활성 구독 수
- `fire_stations_count`: int - 소방서 수
- `pending_reviews`: int - 검토 대기 중 콘텐츠 수
- `calculated_at`: datetime - 계산 시각

#### 메서드
- `to_dict() -> dict`: 딕셔너리로 변환
- `refresh()`: 메트릭 새로고침

---

## SQLAdmin 뷰 설정 요약

### 우선순위 높음 (필수)
1. **User**: 사용자 관리
2. **Donation**: 기부 내역 관리
3. **Refund**: 환불 관리 (bulk 액션 포함)
4. **FireStation**: 소방서 관리
5. **NewsContent**: 뉴스 콘텐츠 검토

### 우선순위 중간
6. **DonationSubscription**: 정기 기부 구독 관리
7. **FireIncident**: 화재 사고 관리
8. **Group**: 그룹 캠페인 관리
9. **Notification**: 알림 관리

### 우선순위 낮음 (읽기 전용)
10. **SeleniumCrawlJob**: 크롤 작업 모니터링
11. **CrawledContent**: 크롤 결과 확인
12. **Receipt**: 영수증 조회
13. **NewsMatch**: 뉴스-사고 매칭 조회

---

## 보안 고려사항

### 필드 보안
- `password_hash`: 관리자 화면에서 완전히 숨김
- `billing_key`, `toss_billing_key`: 마스킹 처리 (마지막 4자리만 표시)
- `social_id`: 마스킹 처리

### 액세스 제어
- `admin` 역할만 모든 뷰 접근 가능
- `moderator` 역할은 NewsContent 검토만 가능
- 민감한 필드는 읽기 전용 또는 완전히 숨김

### 감사 로그
- 모든 수정/삭제 액션은 로그 기록
- bulk 액션은 별도 감사 로그 생성

---

## Llama AI 채팅 통합

### 지원 쿼리 유형
1. **통계 쿼리**: "최근 30일 기부 총액은?"
2. **검색 쿼리**: "서울에 있는 소방서 목록 보여줘"
3. **분석 쿼리**: "상위 10명의 기부자는?"
4. **관계 쿼리**: "특정 사용자의 모든 기부 내역 보여줘"

### Semantic Cache 전략
- 임베딩 유사도 > 0.95인 쿼리는 캐시에서 반환
- 캐시 TTL: 5분
- 캐시 저장소: Redis (pgvector 대신 경량 솔루션)

---

## 데이터 마이그레이션

기존 모델은 변경하지 않으므로 마이그레이션 불필요.
새로운 서비스 레이어 엔티티는 인메모리 객체이므로 DB 스키마 변경 없음.
