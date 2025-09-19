# 데이터 모델 설계

## 핵심 엔티티 정의

### 1. User (사용자)
사용자 계정 정보와 권한 관리

```python
class User:
    id: UUID
    email: str                    # 로그인 이메일
    password_hash: str            # 해시된 비밀번호
    name: str                     # 표시 이름
    phone: Optional[str]          # 연락처
    role: UserRole               # 권한 (donor, admin, moderator)
    social_provider: Optional[str] # 소셜 로그인 제공자 (google, kakao, naver)
    social_id: Optional[str]      # 소셜 계정 ID
    tier: DonorTier              # 기부자 등급 (1-8단계)
    total_donated: Decimal        # 총 기부 금액
    created_at: datetime
    updated_at: datetime
    is_active: bool              # 계정 활성화 상태
```

**검증 규칙:**
- 이메일 중복 불가
- 비밀번호 최소 8자, 특수문자 포함
- 등급은 총 기부금액에 따라 자동 계산

**상태 전이:**
- 회원가입 → 이메일 인증 → 활성화
- 소셜 로그인 → 즉시 활성화

### 2. FireStation (소방서)
소방서 정보와 위치 데이터

```python
class FireStation:
    id: UUID
    name: str                     # 소방서명
    address: str                  # 주소
    location: Point              # PostGIS 좌표 (위도, 경도)
    phone: str                   # 연락처
    station_code: str            # 소방청 코드
    region: str                  # 지역 (시/도)
    district: str                # 구/군
    status: StationStatus        # 운영 상태 (active, closed, merged)
    total_received: Decimal      # 총 수혜 금액
    donor_count: int            # 기부자 수
    last_incident_at: Optional[datetime] # 마지막 출동 시간
    created_at: datetime
    updated_at: datetime
```

**검증 규칙:**
- station_code 유니크
- location 필수 (지도 표시용)
- 주소 → 좌표 변환 자동화

**관계:**
- 1:N → Donation (한 소방서가 여러 기부 받음)
- 1:N → Incident (한 소방서가 여러 사건 처리)

### 3. Donation (기부)
기부 내역과 결제 정보

```python
class Donation:
    id: UUID
    user_id: UUID               # 기부자 FK
    fire_station_id: UUID       # 수혜 소방서 FK
    amount: Decimal             # 기부 금액
    type: DonationType          # 일시/정기 (one_time, recurring)
    frequency: Optional[str]    # 정기결제 주기 (monthly, yearly)
    status: DonationStatus      # 상태 (pending, completed, failed, refunded)
    payment_method: str         # 결제 수단 (card, bank_transfer)
    toss_payment_key: str       # Toss 결제 키
    toss_order_id: str         # 주문 번호
    message: Optional[str]      # 기부 메시지
    is_anonymous: bool         # 익명 기부 여부
    receipt_url: Optional[str] # 영수증 URL
    created_at: datetime
    completed_at: Optional[datetime]
    refunded_at: Optional[datetime]
```

**검증 규칙:**
- amount > 0 (최소 1,000원)
- 정기결제는 frequency 필수
- toss_order_id 유니크

**상태 전이:**
- pending → completed (결제 성공)
- pending → failed (결제 실패)
- completed → refunded (환불 처리)

### 4. NewsContent (뉴스 콘텐츠)
AI 분석된 화재 관련 콘텐츠

```python
class NewsContent:
    id: UUID
    title: str                  # 뉴스 제목
    content: str               # 본문 내용
    source: str                # 출처 (naver_news, youtube, disaster_msg)
    source_url: str            # 원본 URL
    published_at: datetime     # 발행 시간
    location: Optional[Point]  # 사건 발생 위치
    embedding: List[float]     # AI 벡터 임베딩 (pgvector)
    relevance_score: int       # 관련성 점수 (1-100)
    summary: str               # AI 생성 요약
    keywords: List[str]        # 추출된 키워드
    status: ContentStatus      # 상태 (auto_approved, pending_review, rejected)
    reviewed_by: Optional[UUID] # 검토자 ID
    reviewed_at: Optional[datetime]
    created_at: datetime
```

**검증 규칙:**
- relevance_score ≥70: 자동 승인
- 50-69: 관리자 검토 필요
- <50: 자동 폐기

**AI 처리 플로우:**
1. 원본 수집 → 임베딩 생성
2. 관련성 점수 계산 → 상태 결정
3. 요약/키워드 추출 → 저장

### 5. Notification (알림)
사용자별 알림 메시지

```python
class Notification:
    id: UUID
    user_id: UUID              # 수신자 FK
    type: NotificationType     # 알림 유형 (donation_success, incident_alert, system)
    title: str                 # 알림 제목
    message: str               # 알림 내용
    related_id: Optional[UUID] # 연관 객체 ID (기부, 사건 등)
    channels: List[str]        # 발송 채널 (websocket, email, kakao, push)
    status: NotificationStatus # 상태 (pending, sent, failed)
    is_read: bool             # 읽음 상태
    sent_at: Optional[datetime]
    read_at: Optional[datetime]
    created_at: datetime
```

**발송 전략:**
- 즉시 발송: WebSocket (실시간)
- 지연 발송: 이메일, 카카오 (배치)
- 재시도: 실패 시 3회 재발송

### 6. Group (그룹 기부)
공동 목표 기부 캠페인

```python
class Group:
    id: UUID
    name: str                  # 그룹명
    description: str           # 설명
    target_amount: Decimal     # 목표 금액
    current_amount: Decimal    # 현재 달성 금액
    fire_station_id: UUID      # 대상 소방서 FK
    creator_id: UUID           # 생성자 FK
    is_public: bool           # 공개 여부
    invite_code: str          # 초대 코드
    deadline: Optional[datetime] # 마감일
    status: GroupStatus       # 상태 (active, completed, expired)
    member_count: int         # 멤버 수
    created_at: datetime
    completed_at: Optional[datetime]
```

**그룹 멤버십:**
```python
class GroupMembership:
    id: UUID
    group_id: UUID            # 그룹 FK
    user_id: UUID             # 사용자 FK
    role: MemberRole          # 역할 (creator, member)
    contributed_amount: Decimal # 기여 금액
    joined_at: datetime
```

### 7. Ranking (랭킹)
소방서별 기부자 순위

```python
class Ranking:
    id: UUID
    fire_station_id: UUID     # 소방서 FK
    user_id: UUID             # 사용자 FK
    total_amount: Decimal     # 총 기부 금액
    donation_count: int       # 기부 횟수
    rank: int                 # 순위
    period: RankingPeriod     # 기간 (monthly, yearly, all_time)
    calculated_at: datetime   # 계산 시점
```

**순위 계산:**
- 월간/연간/전체 기간별 분리
- 매일 자정 배치 작업으로 갱신
- 동일 금액 시 최초 기부 우선

### 8. Receipt (영수증)
기부 영수증 관리

```python
class Receipt:
    id: UUID
    donation_id: UUID         # 기부 FK
    receipt_number: str       # 영수증 번호
    recipient_name: str       # 수령자명
    recipient_phone: str      # 연락처
    amount: Decimal          # 금액
    issue_date: date         # 발행일
    pdf_url: str            # PDF 파일 URL
    email_sent: bool        # 이메일 발송 여부
    created_at: datetime
```

## 데이터베이스 인덱스 전략

### 성능 최적화 인덱스
```sql
-- 지리 검색 (소방서 근처 찾기)
CREATE INDEX idx_fire_stations_location ON fire_stations USING GIST (location);

-- 벡터 유사도 검색 (뉴스 관련성)
CREATE INDEX idx_news_embedding ON news_content USING ivfflat (embedding vector_cosine_ops);

-- 기부 내역 조회
CREATE INDEX idx_donations_user_created ON donations (user_id, created_at DESC);
CREATE INDEX idx_donations_station_created ON donations (fire_station_id, created_at DESC);

-- 알림 조회
CREATE INDEX idx_notifications_user_created ON notifications (user_id, created_at DESC);
CREATE INDEX idx_notifications_unread ON notifications (user_id, is_read, created_at DESC);

-- 랭킹 조회
CREATE INDEX idx_rankings_station_period_rank ON rankings (fire_station_id, period, rank);
```

### 파티셔닝 전략
```sql
-- 뉴스 데이터 월별 파티션
CREATE TABLE news_content_y2025m01 PARTITION OF news_content
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- 알림 데이터 분기별 파티션
CREATE TABLE notifications_q1_2025 PARTITION OF notifications
FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');
```

## 관계 다이어그램

```
User (1) ←→ (N) Donation (N) → (1) FireStation
 ↓                                      ↑
 (1)                                    (1)
 ↓                                      ↓
GroupMembership (N) → (1) Group ────────┘

User (1) ←→ (N) Notification

NewsContent (location) → FireStation (spatial query)

Donation (1) ←→ (1) Receipt

User ←→ Ranking ←→ FireStation (소방서별 순위)
```

## 데이터 마이그레이션 계획

### Phase 1: 기본 테이블
1. User, FireStation, Donation 생성
2. 기본 인덱스 설정
3. 초기 데이터 삽입 (소방서 목록)

### Phase 2: AI/알림 기능
1. NewsContent, Notification 생성
2. 벡터 검색 인덱스 추가
3. 파티셔닝 설정

### Phase 3: 고급 기능
1. Group, Ranking, Receipt 생성
2. 성능 최적화 인덱스
3. 아카이빙 정책 설정

이 데이터 모델은 확장성과 성능을 고려하여 설계되었으며, PostgreSQL의 고급 기능들을 활용하여 복잡한 쿼리와 실시간 처리를 효율적으로 지원합니다.