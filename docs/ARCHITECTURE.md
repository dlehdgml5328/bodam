# 보담(BoDam) 시스템 아키텍처 문서

> **프로젝트**: 소방관 커피 기부 플랫폼
> **작성일**: 2025-10-01
> **기술 스택**: FastAPI + Next.js + PostgreSQL + Celery + Redis

---

## 📋 목차

1. [전체 시스템 아키텍처](#전체-시스템-아키텍처)
2. [파이프라인별 상세 설계](#파이프라인별-상세-설계)
   - [1. 사용자 인증 파이프라인](#1-사용자-인증-파이프라인)
   - [2. 기부 처리 파이프라인](#2-기부-처리-파이프라인)
   - [3. 결제/환불 파이프라인](#3-결제환불-파이프라인)
   - [4. 소방서 데이터 수집 파이프라인](#4-소방서-데이터-수집-파이프라인)
   - [5. 실시간 알림 파이프라인](#5-실시간-알림-파이프라인)
   - [6. AI/뉴스 분석 파이프라인](#6-ai뉴스-분석-파이프라인)
   - [7. 관리자 파이프라인](#7-관리자-파이프라인)
3. [데이터 플로우](#데이터-플로우)
4. [기술 스택 상세](#기술-스택-상세)
5. [프런트엔드-백엔드 정합성 로드맵](#프런트엔드-백엔드-정합성-로드맵)

---

## 전체 시스템 아키텍처

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[Next.js App]
        A1[Public Pages]
        A2[Account Pages]
        A3[Admin Pages]
    end

    subgraph "API Gateway Layer"
        B[FastAPI Main]
        B1[Auth Middleware]
        B2[CORS Middleware]
        B3[Rate Limiter]
    end

    subgraph "Application Layer"
        C1[User Service]
        C2[Donation Service]
        C3[Fire Station Service]
        C4[AI Service]
        C5[Notification Service]
        C6[Payment Service]
    end

    subgraph "Background Workers (Celery)"
        D1[Payment Processor]
        D2[Data Collector]
        D3[AI Analyzer]
        D4[Notification Sender]
        D5[Ranking Builder]
    end

    subgraph "External Integrations"
        E1[Toss Payments]
        E2[Together AI]
        E3[KakaoTalk Biz]
        E4[OAuth Providers]
        E5[Fire Data API]
    end

    subgraph "Data Layer"
        F1[(PostgreSQL)]
        F2[(Redis)]
        F3[S3/File Store]
    end

    A --> B
    B --> B1
    B1 --> B2
    B2 --> B3
    B3 --> C1
    B3 --> C2
    B3 --> C3
    B3 --> C4
    B3 --> C5
    B3 --> C6

    C1 --> F1
    C2 --> F1
    C3 --> F1
    C4 --> F1
    C5 --> F1
    C6 --> F1

    C2 --> D1
    C3 --> D2
    C4 --> D3
    C5 --> D4

    D1 --> F2
    D2 --> F2
    D3 --> F2
    D4 --> F2
    D5 --> F2

    D1 --> E1
    D2 --> E5
    D3 --> E2
    D4 --> E3
    C1 --> E4
    C6 --> E1

    D1 --> F1
    D2 --> F1
    D3 --> F1
    D4 --> F1
    D5 --> F1

    C2 --> F3
```

---

## 파이프라인별 상세 설계

### 1. 사용자 인증 파이프라인

**목적**: 사용자 회원가입, 로그인, 소셜 인증, 비밀번호 재설정 처리

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Next.js
    participant API as FastAPI
    participant Auth as AuthMiddleware
    participant UserSvc as UserService
    participant DB as PostgreSQL
    participant OAuth as OAuth Providers

    rect rgb(200, 220, 250)
        Note over User,DB: 일반 회원가입/로그인
        User->>Frontend: 회원가입 요청
        Frontend->>API: POST /auth/signup
        API->>UserSvc: create_user()
        UserSvc->>UserSvc: hash_password()
        UserSvc->>DB: INSERT user
        DB-->>UserSvc: user_id
        UserSvc-->>API: user object
        API-->>Frontend: 201 Created + user_id
        Frontend-->>User: 가입 완료 메시지
    end

    rect rgb(220, 250, 220)
        Note over User,DB: 로그인
        User->>Frontend: 로그인 요청
        Frontend->>API: POST /auth/login
        API->>UserSvc: get_user_by_email()
        UserSvc->>DB: SELECT user
        DB-->>UserSvc: user data
        UserSvc-->>API: user object
        API->>API: verify_password()
        API->>API: create_access_token()
        API->>API: set_cookie(bodam_session)
        API-->>Frontend: 200 OK + access_token
        Frontend-->>User: 로그인 성공
    end

    rect rgb(250, 220, 220)
        Note over User,OAuth: 소셜 로그인
        User->>Frontend: 소셜 로그인 선택
        Frontend->>API: GET /auth/social/kakao
        API-->>Frontend: Redirect to OAuth
        Frontend-->>OAuth: OAuth 인증 요청
        OAuth-->>User: 인증 페이지
        User->>OAuth: 로그인 승인
        OAuth-->>API: GET /auth/social/kakao/callback?code=xxx
        API->>OAuth: Exchange code for token
        OAuth-->>API: access_token + user_info
        API->>UserSvc: get_or_create_user()
        UserSvc->>DB: SELECT/INSERT user
        API-->>Frontend: Redirect + set cookie
        Frontend-->>User: 로그인 완료
    end

    rect rgb(250, 240, 200)
        Note over User,DB: 비밀번호 재설정
        User->>Frontend: 비밀번호 찾기
        Frontend->>API: POST /auth/password-reset/request
        API->>UserSvc: get_user_by_email()
        UserSvc->>DB: SELECT user
        API->>DB: INSERT password_reset_token
        API-->>Frontend: 재설정 토큰 (이메일 전송)
        User->>Frontend: 토큰으로 접근
        Frontend->>API: POST /auth/password-reset/confirm
        API->>DB: SELECT + DELETE token
        API->>UserSvc: update_password()
        UserSvc->>DB: UPDATE user.password_hash
        API-->>Frontend: 200 OK
        Frontend-->>User: 비밀번호 변경 완료
    end
```

**주요 컴포넌트**:
- **API**: [src/api/auth.py](../backend/src/api/auth.py)
- **Service**: [src/services/user_service.py](../backend/src/services/user_service.py)
- **Middleware**: [src/middleware/auth.py](../backend/src/middleware/auth.py)
- **Security**: [src/security/tokens.py](../backend/src/security/tokens.py), [src/security/passwords.py](../backend/src/security/passwords.py)
- **Models**: [src/models/user.py](../backend/src/models/user.py), [src/models/password_reset.py](../backend/src/models/password_reset.py)

**데이터 흐름**:
1. 사용자 입력 → Frontend 유효성 검사
2. API 엔드포인트 → AuthMiddleware 검증 (로그인 필요 시)
3. UserService → 비즈니스 로직 처리
4. PostgreSQL → 사용자 데이터 저장/조회
5. JWT 토큰 생성 → HttpOnly Cookie 설정

**보안 요소**:
- bcrypt 비밀번호 해싱
- JWT 토큰 기반 인증
- HttpOnly, Secure Cookie
- Rate Limiting (로그인 시도 제한)
- CSRF 보호 (SameSite Cookie)

---

### 2. 기부 처리 파이프라인

**목적**: 일회성/정기 기부 생성, 조회, 영수증 발급

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Next.js
    participant API as FastAPI
    participant DonationSvc as DonationService
    participant PaymentSvc as PaymentService
    participant DB as PostgreSQL
    participant Toss as Toss Payments
    participant Worker as Celery Worker

    rect rgb(200, 220, 250)
        Note over User,DB: 기부 생성
        User->>Frontend: 소방서 선택 + 금액 입력
        Frontend->>API: POST /donations
        API->>DonationSvc: create_donation()
        DonationSvc->>DB: INSERT donation (status=pending)
        DB-->>DonationSvc: donation_id
        DonationSvc->>PaymentSvc: create_payment_order()
        PaymentSvc->>Toss: Create Payment
        Toss-->>PaymentSvc: payment_url + order_id
        PaymentSvc-->>API: payment_url
        API-->>Frontend: 201 Created + payment_url
        Frontend-->>User: Redirect to Toss
    end

    rect rgb(220, 250, 220)
        Note over User,Worker: 결제 완료 처리
        User->>Toss: 결제 진행
        Toss->>API: POST /webhooks/toss/payment
        API->>DonationSvc: confirm_donation()
        DonationSvc->>DB: UPDATE donation (status=completed)
        DonationSvc->>Worker: Queue receipt generation
        Worker->>Worker: Generate PDF receipt
        Worker->>DB: UPDATE donation (receipt_url)
        Worker->>User: Send email with receipt
    end

    rect rgb(250, 220, 220)
        Note over User,DB: 기부 내역 조회
        User->>Frontend: 마이페이지 접근
        Frontend->>API: GET /donations?page=1
        API->>DonationSvc: list_user_donations()
        DonationSvc->>DB: SELECT donations
        DB-->>DonationSvc: donation list
        DonationSvc-->>API: formatted list
        API-->>Frontend: 200 OK + donations
        Frontend-->>User: 기부 내역 표시
    end

    rect rgb(250, 240, 200)
        Note over User,DB: 정기 기부
        User->>Frontend: 정기 기부 설정
        Frontend->>API: POST /subscriptions
        API->>DonationSvc: create_subscription()
        DonationSvc->>DB: INSERT subscription
        DonationSvc->>Toss: Create billing key
        Toss-->>DonationSvc: billing_key
        DonationSvc->>DB: UPDATE subscription
        Note over Worker: 매월 자동 실행
        Worker->>DonationSvc: process_subscriptions()
        DonationSvc->>Toss: Charge with billing_key
        Toss-->>DonationSvc: Payment success
        DonationSvc->>DB: INSERT donation
    end
```

**주요 컴포넌트**:
- **API**: [src/api/donations.py](../backend/src/api/donations.py)
- **Service**: [src/services/donation_service.py](../backend/src/services/donation_service.py)
- **Worker**: [src/workers/payment_processor.py](../backend/src/workers/payment_processor.py)
- **Integration**: [src/integrations/toss_payments.py](../backend/src/integrations/toss_payments.py)
- **Models**: [src/models/donation.py](../backend/src/models/donation.py)

**상태 전이**:
```
pending → processing → completed
         ↓
       failed → refunded
```

---

### 3. 결제/환불 파이프라인

**목적**: Toss Payments 연동, 결제 확인, 환불 처리

```mermaid
flowchart TB
    Start([기부 시작]) --> CreateOrder[주문 생성]
    CreateOrder --> TossCheckout{Toss 결제창}

    TossCheckout -->|성공| WebhookReceive[Webhook 수신]
    TossCheckout -->|실패| PaymentFail[결제 실패]
    TossCheckout -->|취소| PaymentCancel[결제 취소]

    WebhookReceive --> VerifySignature{서명 검증}
    VerifySignature -->|실패| RejectWebhook[Webhook 거부]
    VerifySignature -->|성공| UpdateDB[DB 업데이트]

    UpdateDB --> IssueReceipt[영수증 발급]
    IssueReceipt --> SendEmail[이메일 발송]
    SendEmail --> Complete([완료])

    PaymentFail --> LogError[에러 로깅]
    PaymentCancel --> LogCancel[취소 로깅]
    RejectWebhook --> AlertAdmin[관리자 알림]

    subgraph "환불 프로세스"
        RefundRequest[환불 요청] --> AdminReview{관리자 승인}
        AdminReview -->|승인| CallTossRefund[Toss API 호출]
        AdminReview -->|거부| RejectRefund[환불 거부]
        CallTossRefund --> UpdateRefundDB[환불 상태 업데이트]
        UpdateRefundDB --> NotifyUser[사용자 알림]
    end
```

**주요 컴포넌트**:
- **Webhook**: [src/api/webhooks/toss.py](../backend/src/api/webhooks/toss.py)
- **Service**: [src/services/refund_service.py](../backend/src/services/refund_service.py)
- **API**: [src/api/refunds.py](../backend/src/api/refunds.py)
- **Models**: [src/models/refund.py](../backend/src/models/refund.py)

**Webhook 처리**:
1. Toss → `/webhooks/toss/payment` POST
2. `X-Toss-Signature` 검증
3. 결제 상태 업데이트 (pending → completed)
4. 영수증 생성 작업 큐잉
5. 200 OK 응답

---

### 4. 소방서 데이터 수집 파이프라인

**목적**: 외부 API에서 소방서 정보, 화재 사건 데이터 수집 및 동기화

```mermaid
graph TB
    subgraph "스케줄링"
        A[Celery Beat Scheduler]
        A -->|매 1시간| B[collect_fire_incidents]
        A -->|매일 자정| C[refresh_station_metrics]
    end

    subgraph "데이터 수집 Worker"
        B --> D[Fire Data Collector]
        D --> E[External Fire API]
        E --> F{응답 유효성 검증}
        F -->|성공| G[데이터 파싱]
        F -->|실패| H[에러 로깅 + 재시도]
        G --> I[DB 저장/업데이트]
    end

    subgraph "메트릭 집계 Worker"
        C --> J[Station Metrics Builder]
        J --> K[기부 데이터 조회]
        K --> L[소방서별 통계 계산]
        L --> M[ranking 테이블 업데이트]
    end

    subgraph "데이터베이스"
        I --> N[(fire_stations)]
        I --> O[(news_content)]
        M --> P[(rankings)]
    end

    subgraph "캐싱 Layer"
        N --> Q[Redis Cache]
        P --> Q
    end
```

**주요 컴포넌트**:
- **Worker**: [src/workers/data_collector.py](../backend/src/workers/data_collector.py)
- **Collector**: [src/collectors/fire_data_collector.py](../backend/src/collectors/fire_data_collector.py)
- **Service**: [src/services/fire_station_service.py](../backend/src/services/fire_station_service.py)
- **Models**: [src/models/fire_station.py](../backend/src/models/fire_station.py)

**수집 주기**:
- 화재 사건: 1시간마다
- 소방서 메트릭: 매일 자정
- 뉴스 수집: 6시간마다

---

### 5. 실시간 알림 파이프라인

**목적**: WebSocket, KakaoTalk, 이메일을 통한 실시간 알림 전송

```mermaid
sequenceDiagram
    participant Event as Event Source
    participant Bus as Event Bus
    participant NotifSvc as NotificationService
    participant DB as PostgreSQL
    participant Worker as Celery Worker
    participant WS as WebSocket
    participant Kakao as KakaoTalk Biz
    participant Email as SMTP

    Event->>Bus: Emit event (donation_completed)
    Bus->>NotifSvc: Handle event
    NotifSvc->>DB: INSERT notification
    NotifSvc->>Worker: Queue dispatch task

    par WebSocket 푸시
        Worker->>WS: Send to connected clients
        WS->>User: Real-time notification
    and KakaoTalk 알림
        Worker->>Kakao: Send template message
        Kakao->>User: KakaoTalk 메시지
    and 이메일 발송
        Worker->>Email: Send email
        Email->>User: Email 수신
    end

    Worker->>DB: UPDATE notification (sent=true)
```

**주요 컴포넌트**:
- **API**: [src/api/webpush.py](../backend/src/api/webpush.py), [src/api/kakao.py](../backend/src/api/kakao.py)
- **Service**: [src/services/notification_service.py](../backend/src/services/notification_service.py)
- **Worker**: [src/workers/notification_sender.py](../backend/src/workers/notification_sender.py)
- **Integration**: [src/integrations/kakao_biz.py](../backend/src/integrations/kakao_biz.py)
- **Models**: [src/models/notification.py](../backend/src/models/notification.py)
- **Event Bus**: [src/events/event_bus.py](../backend/src/events/event_bus.py)

**WebSocket 연결**:
```
ws://localhost:8000/ws/notifications
```

**알림 타입**:
- `donation_completed`: 기부 완료
- `refund_approved`: 환불 승인
- `fire_incident_nearby`: 인근 화재 발생
- `ranking_updated`: 랭킹 변동

---

### 6. AI/뉴스 분석 파이프라인

**목적**: Together AI를 활용한 뉴스 수집 및 자연어 분석

```mermaid
flowchart LR
    subgraph "수집"
        A[News Collector] --> B[RSS/API Fetch]
        B --> C[HTML 파싱]
        C --> D[(news_content)]
    end

    subgraph "AI 분석"
        D --> E[AI Analyzer Worker]
        E --> F[Together AI API]
        F --> G{분석 타입}
        G -->|감정 분석| H[Sentiment Score]
        G -->|키워드 추출| I[Keywords]
        G -->|요약| J[Summary]
    end

    subgraph "저장 및 활용"
        H --> K[Update DB]
        I --> K
        J --> K
        K --> L[Admin Dashboard]
        K --> M[User News Feed]
    end
```

**주요 컴포넌트**:
- **Worker**: [src/workers/ai_analyzer.py](../backend/src/workers/ai_analyzer.py)
- **Service**: [src/services/ai_service.py](../backend/src/services/ai_service.py)
- **Collector**: [src/collectors/news_collector.py](../backend/src/collectors/news_collector.py)
- **Integration**: [src/integrations/together_ai.py](../backend/src/integrations/together_ai.py)
- **Models**: [src/models/news_content.py](../backend/src/models/news_content.py)

**AI 처리 플로우**:
1. 뉴스 수집 (6시간 주기)
2. 텍스트 전처리
3. Together AI API 호출 (LLM 분석)
4. 결과 파싱 및 저장
5. 관리자 대시보드 업데이트

---

### 7. 관리자 파이프라인

**목적**: 관리자 전용 기능 (환불 승인, 리소스 관리, LLM 검색)

```mermaid
graph TB
    subgraph "관리자 인증"
        A[Admin Login] --> B{Role Check}
        B -->|Admin| C[Access Granted]
        B -->|User| D[Access Denied]
    end

    subgraph "환불 관리"
        C --> E[Refund Dashboard]
        E --> F[Pending Refunds List]
        F --> G{승인/거부}
        G -->|승인| H[Approve Refund]
        G -->|거부| I[Reject Refund]
        H --> J[Call Toss API]
        J --> K[Update DB]
        I --> K
    end

    subgraph "리소스 관리"
        C --> L[Resource Dashboard]
        L --> M[View System Stats]
        M --> N[CPU/Memory/DB]
        L --> O[Manage Fire Stations]
        L --> P[User Management]
    end

    subgraph "LLM 검색"
        C --> Q[Admin Search]
        Q --> R[Graph RAG Service]
        R --> S[Vector Search + LLM]
        S --> T[Search Results]
    end
```

**주요 컴포넌트**:
- **API**: [src/api/admin/refunds.py](../backend/src/api/admin/refunds.py), [src/api/admin/resources.py](../backend/src/api/admin/resources.py), [src/api/admin/search.py](../backend/src/api/admin/search.py)
- **Service**: [src/services/admin/llm_search_service.py](../backend/src/services/admin/llm_search_service.py)
- **Integration**: [src/integrations/graph.py](../backend/src/integrations/graph.py)

**관리자 권한 체크**:
```python
# src/middleware/auth.py
if user.role != "admin":
    raise HTTPException(403, "Admin required")
```

---

## 데이터 플로우

### 전체 데이터 흐름도

```mermaid
graph LR
    subgraph "입력"
        U[사용자]
        E[외부 API]
        W[Webhooks]
    end

    subgraph "Frontend"
        F[Next.js]
    end

    subgraph "Backend API"
        A[FastAPI]
        M[Middleware]
    end

    subgraph "Services"
        S1[User Service]
        S2[Donation Service]
        S3[Fire Station Service]
        S4[AI Service]
    end

    subgraph "Background Jobs"
        C1[Payment Processor]
        C2[Data Collector]
        C3[AI Analyzer]
        C4[Notification Sender]
    end

    subgraph "Storage"
        DB[(PostgreSQL)]
        R[(Redis)]
        FS[File Storage]
    end

    subgraph "External Services"
        T[Toss Payments]
        AI[Together AI]
        K[KakaoTalk]
    end

    U --> F
    F --> A
    A --> M
    M --> S1
    M --> S2
    M --> S3
    M --> S4

    S1 --> DB
    S2 --> DB
    S3 --> DB
    S4 --> DB

    S2 --> C1
    S3 --> C2
    S4 --> C3
    S1 --> C4

    C1 --> R
    C2 --> R
    C3 --> R
    C4 --> R

    C1 --> T
    C2 --> E
    C3 --> AI
    C4 --> K

    W --> A
    T --> W

    C1 --> DB
    C2 --> DB
    C3 --> DB
    C4 --> DB

    S2 --> FS
```

### 데이터베이스 주요 테이블

| 테이블 | 목적 | 주요 컬럼 |
|--------|------|-----------|
| `users` | 사용자 정보 | id, email, password_hash, role |
| `donations` | 기부 내역 | id, user_id, fire_station_id, amount, status |
| `fire_stations` | 소방서 정보 | id, name, region, location (PostGIS) |
| `refunds` | 환불 요청 | id, donation_id, status, admin_note |
| `notifications` | 알림 | id, user_id, type, content, sent |
| `news_content` | 뉴스 기사 | id, title, content, ai_summary |
| `rankings` | 랭킹 | id, fire_station_id, rank, total_donations |
| `password_reset` | 비밀번호 재설정 토큰 | id, user_id, token, expires_at |

---

## 기술 스택 상세

### Backend (FastAPI)

```
backend/
├── src/
│   ├── api/              # REST API endpoints
│   │   ├── auth.py       # 인증
│   │   ├── donations.py  # 기부
│   │   ├── stations.py   # 소방서
│   │   ├── webhooks/     # Webhook 수신
│   │   └── admin/        # 관리자 API
│   ├── services/         # 비즈니스 로직
│   ├── models/           # SQLAlchemy Models
│   ├── workers/          # Celery Tasks
│   ├── middleware/       # 미들웨어 (Auth, CORS, Rate Limit)
│   ├── integrations/     # 외부 API 연동
│   ├── security/         # 보안 (JWT, Password Hash)
│   └── database/         # DB 연결
└── tests/
```

**핵심 라이브러리**:
- `FastAPI`: 고성능 비동기 웹 프레임워크
- `SQLAlchemy 2.0`: ORM (async 지원)
- `Celery`: 백그라운드 작업 큐
- `Redis`: 캐싱 + Celery 브로커
- `pgvector`: 벡터 검색 (AI 임베딩)
- `PostGIS`: 지리 데이터 처리

### Frontend (Next.js)

```
frontend/
├── src/
│   ├── app/
│   │   ├── (public)/     # 공개 페이지
│   │   ├── (account)/    # 로그인 필요 페이지
│   │   └── layout.tsx    # 공통 레이아웃
│   ├── components/
│   │   ├── base/         # 기본 컴포넌트 (Button, Card)
│   │   ├── feature/      # 기능 컴포넌트 (Header, Footer)
│   │   └── home/         # 홈 섹션
│   └── lib/
│       ├── api.ts        # API 클라이언트
│       └── data/         # Static 데이터
└── public/
```

**핵심 라이브러리**:
- `Next.js 13`: React 프레임워크 (Pages Router)
- `TailwindCSS`: 유틸리티 CSS 프레임워크
- `@tosspayments/payment-sdk`: Toss 결제 SDK

### Infrastructure

```
infra/
├── docker/
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
└── ci-cd/
    └── github-actions.yaml
```

**배포 환경**:
- **컨테이너**: Docker
- **오케스트레이션**: Kubernetes
- **모니터링**: Prometheus + Grafana
- **로깅**: Structured logging (structlog)

---

## 파이프라인 통합 시나리오

### 시나리오 1: 사용자가 소방서에 기부하는 전체 플로우

```mermaid
sequenceDiagram
    autonumber
    Actor User
    participant Frontend
    participant API
    participant DonationSvc
    participant DB
    participant Toss
    participant Worker
    participant NotifSvc

    User->>Frontend: 소방서 선택 + 금액 입력
    Frontend->>API: POST /donations
    API->>DonationSvc: create_donation()
    DonationSvc->>DB: INSERT donation (pending)
    DonationSvc->>Toss: Create payment order
    Toss-->>DonationSvc: payment_url
    DonationSvc-->>API: payment_url
    API-->>Frontend: 201 Created
    Frontend-->>User: Redirect to Toss

    User->>Toss: 결제 진행
    Toss->>API: POST /webhooks/toss/payment
    API->>DonationSvc: confirm_donation()
    DonationSvc->>DB: UPDATE donation (completed)
    DonationSvc->>Worker: Queue receipt generation
    Worker->>Worker: Generate PDF
    Worker->>DB: UPDATE donation.receipt_url
    Worker->>NotifSvc: Send notification
    NotifSvc->>User: Email + KakaoTalk 알림
```

### 시나리오 2: 관리자가 환불 요청 처리

```mermaid
sequenceDiagram
    Actor Admin
    participant Frontend
    participant API
    participant RefundSvc
    participant Toss
    participant DB
    participant NotifSvc

    Admin->>Frontend: 환불 대시보드 접근
    Frontend->>API: GET /admin/refunds?status=pending
    API-->>Frontend: Refund list
    Admin->>Frontend: 환불 승인 클릭
    Frontend->>API: POST /admin/refunds/{id}/approve
    API->>RefundSvc: approve_refund()
    RefundSvc->>Toss: Cancel payment
    Toss-->>RefundSvc: Success
    RefundSvc->>DB: UPDATE refund (approved)
    RefundSvc->>NotifSvc: Notify user
    NotifSvc->>User: 환불 완료 알림
```

---

## 성능 최적화 전략

### 1. 캐싱 전략
- **Redis**: 소방서 목록, 랭킹 데이터 (TTL 1시간)
- **CDN**: 정적 파일 (이미지, CSS, JS)
- **DB 쿼리 캐싱**: SQLAlchemy 쿼리 결과 메모이제이션

### 2. 비동기 처리
- **Celery**: 무거운 작업 (PDF 생성, AI 분석, 이메일 발송)
- **FastAPI Async**: I/O 바운드 작업 (DB 쿼리, HTTP 요청)

### 3. 데이터베이스 최적화
- **인덱싱**: user.email, donation.user_id, fire_station.region
- **파티셔닝**: donations 테이블 (created_at 기준 월별)
- **Connection Pooling**: AsyncEngine (max 20 connections)

### 4. 모니터링
- **Slow Query Logging**: [src/database/slow_query.py](../backend/src/database/slow_query.py)
- **Prometheus Metrics**: [src/monitoring/metrics.py](../backend/src/monitoring/metrics.py)
- **Structured Logging**: [src/monitoring/logging.py](../backend/src/monitoring/logging.py)

---

## 프런트엔드-백엔드 정합성 로드맵

### 프런트엔드 기대 데이터 & 플로우
- `frontend/src/lib/data/emergency.ts:7` `EmergencyStation` 타입과 `/emergency-stations` 엔드포인트를 가정해 실시간 출동 현황을 표시
- `frontend/src/app/(public)/donations/page.tsx:600` 부근에서 단일/복수/정기 기부, Toss 결제, 그룹 기부 메타데이터를 모두 한 번에 처리하도록 UI 구성
- `frontend/src/app/(account)/mypage/page.tsx:100` 이후 마이페이지가 개인/단체 기부 내역, 정기 결제, 환불 사유, 영수증 여부 등을 관리하도록 더미 데이터를 사용
- `frontend/src/app/(public)/donation-ranking/page.tsx:9` 및 `frontend/src/components/home/DonationRanking.tsx:8` 에서 개인/단체/기업 랭킹 데이터를 100위 규모로 표시
- `frontend/src/components/feature/Header.tsx:40` 인앱 알림, 단체 로그인, 빠른 기부 조회 등 다양한 상태를 로컬 스토리지/가상 데이터에 의존

### 현재 Spec/Backend 상태
- 스펙 킷(`specs/001-bashclaudecli-specify-bodam/contracts`)에는 `/emergency-stations`, 알림, 랭킹, Toss 빌링 등 프런트가 기대하는 일부 엔티티가 정의되어 있지 않음
- FastAPI 라우트(`backend/src/api/stations.py`, `backend/src/api/donations.py`, `backend/src/api/groups.py` 등)는 목업 응답 또는 미구현 상태로 남아 있어 실제 데이터 제공 불가
- 도메인 모델(`backend/src/models`)은 기본 엔티티만 정의되어 있으며, 정기 결제 주기, 그룹 메타데이터, 알림 채널, 랭킹 지표 등 프런트 필드가 누락
- 결제 처리(Toss)와 관련된 백엔드 서비스/웹훅은 스켈레톤 수준이거나 미정리 상태로, 프런트 결제 흐름과 동기화가 불가

### 격차 요약

| 영역 | 프런트 요구 | 스펙/백엔드 현황 |
| --- | --- | --- |
| 실시간 출동 현황 | `/emergency-stations` API, 우선순위/시간 필드 | 관련 API/모델 부재 |
| 기부/결제 | 단일·복수·정기 기부, Toss 결제, 그룹 메타데이터 | `Donation` 기본 필드만 존재, 정기결제/그룹 확장 미정 |
| 마이페이지 | 정기 기부 관리, 환불 사유, 영수증 발급, 다운로드 | 환불/영수증 모델은 일부 있으나 API 미정, UX는 더미 데이터 |
| 랭킹 | 개인/단체/기업 랭킹 뷰, 100위 데이터 | `Ranking` 모델만 존재, 계산/조회 API 미구현 |
| 알림/실시간 | 알림 센터, 소셜/단체 로그인 상태, 로그인 모달 이벤트 | `Notification` 모델만 정의, 발송/조회 API 미구현 |

### 우선 작업 순서
- **Step 1 — 정합성 명세화**: 프런트 요구 필드·플로우를 스펙 문서와 공유 타입 정의로 추가해 단일 진실 공급원(Single Source of Truth) 확보
- **Step 2 — 핵심 API 구현**: `/emergency-stations`, 기부 생성/조회, 그룹 검색, 랭킹 조회 등 주요 엔드포인트부터 실제 비즈니스 로직과 DB 연동으로 구현
-   - 기부/정기 결제 확장 세부 계획은 `docs/roadmap/step-02-donations.md` 참고
- **Step 3 — 모델/서비스 확장**: `Donation`, `Group`, `Ranking`, `Notification` 등에 정기 결제, 단체 메타, 통계 필드를 추가하고 마이그레이션 설계
- **Step 4 — 결제/정기 과금 설계**: Toss 빌링 키 저장, 구독 스케줄링, 웹훅 처리 등 프런트 결제 흐름과 맞는 백엔드 파이프라인 추가
- **Step 5 — 프런트 리팩터링**: API 제공 순서에 맞춰 더미 데이터 → 실데이터 전환, 상태 관리 단순화, 인증 연동을 단계적으로 적용

### 더미 데이터 정리 전략
- API가 준비된 화면부터 `apiRequest` 또는 서버 액션으로 실제 데이터를 주입하고, 성공적으로 연동된 후 더미 배열/로컬 상태를 제거
- 아직 API가 없는 컴포넌트는 스펙 반영과 백엔드 구현이 완료될 때까지 더미 유지, 단 문서화로 “의존 API”를 명시해 추후 제거 시점을 관리
- 공통 DTO/타입을 `frontend/src/lib/types`(신규) 등에 배치해 프런트·백엔드 간 스키마 드리프트를 최소화하고, 필요 시 자동 생성(OpenAPI → TS) 파이프라인 도입 검토

### 백엔드 확장 제안 (재사용 우선)

#### 1) 실시간 출동 현황 (`/emergency-stations`)
- **재사용 대상**: `FireStation` 모델·`FireStationService`(기본 메타), `NewsContent`(연관 사건)
- **신규 제안**:
  - `FireStationStatus` 테이블: `fire_station_statuses(id, station_id FK, status, priority, summary, updated_at)`
    - 이력 보존이 필요하면 `version`/`expires_at` 추가, 단순 스냅샷이면 1:1 unique 인덱스 유지
  - `FireStationActiveIncident` 조인 테이블로 다중 사건 연결 (`incident_id`는 기존 `NewsContent.id` 재사용)
  - `FireStationService`에 `get_emergency_statuses(region?, priority?, limit)` 메서드 추가 → 기존 세션/쿼리 패턴 재사용
  - FastAPI 라우트(`backend/src/api/stations.py`)에서 서비스 호출 후 Pydantic 응답 스키마 매핑

  **모델 세부안**
  - Enum 재활용: `StationStatus` 확장 혹은 신규 `LiveStatus(str, Enum)` 정의 (`dispatching`, `suppressing`, `standby`, `maintenance`)
  - `fire_station_statuses`
    | 컬럼 | 타입 | 비고 |
    | --- | --- | --- |
    | `id` | UUID (PK) | 기본값 `uuid_generate_v4()` |
    | `station_id` | UUID (FK → `fire_stations.id`, unique) | 실시간 상태 1:1 매핑 |
    | `status` | Enum(LiveStatus) | NOT NULL |
    | `priority` | Enum(`high`, `medium`, `low`) | NOT NULL, 기본값 `medium` |
    | `status_label` | String(50) | 다국어/가독성용 |
    | `summary` | Text | 선택 |
    | `updated_at` | TIMESTAMPTZ | NOT NULL, `server_default=now()` |
  - `fire_station_active_incidents`
    | 컬럼 | 타입 | 비고 |
    | --- | --- | --- |
    | `status_id` | UUID (FK → `fire_station_statuses.id`, PK 구성) |
    | `incident_id` | UUID (FK → `news_content.id`, PK 구성) |
    | `started_at` | TIMESTAMPTZ | 선택, 기본값 없음 |
    | 복합 PK(`status_id`, `incident_id`), FK ON DELETE CASCADE

  **마이그레이션 플랜**
  1. Alembic revision 생성 → 두 테이블/Enum 추가
  2. 기존 데이터 없음: 초기 상태는 빈 테이블, 운영 스크립트/ETL이 주입
  3. `station_id`에 unique 인덱스 부여하여 최신 상태 1개 유지, 필요 시 ETL에서 UPSERT
  4. `news_content`와 FK 연동을 위해 관련 테이블이 비어 있어도 FK 생성 가능 (ON DELETE SET NULL 옵션 고려)

  **서비스/엔드포인트 구현 순서**
  1. `FireStationService` + 리포지토리에 상태/사건 조인 쿼리 추가 (`select(FireStation, FireStationStatus, NewsContent)`)
  2. `EmergencyStationStatusDTO` Pydantic 모델 정의 (spec과 동기화)
  3. `/emergency-stations` 라우트 신설 → 서비스 호출 후 DTO 리스트 반환
  4. 캐싱 전략: 단기적으로 30초 TTL Redis 캐시(선택), 추후 스트리밍 데이터 접속 고려

#### 2) 기부/정기 결제/그룹 연계
- **재사용 대상**: `Donation` 모델·`DonationService`, `Group`/`GroupMembership`, `ReceiptService`, `RefundService`
- **신규 제안**:
  - `Donation`에 정기 결제 속성 확장: `subscription_id`, `billing_customer_key`, `next_billing_at`, `frequency`, `is_primary` 등 (필요 시 `Subscription` 별도 테이블)
  - 다중 소방서 기부 지원을 위해 `DonationAllocation` 테이블 도입 (`donation_id`, `fire_station_id`, `amount`, `allocation_type`) → 기존 단일 FK는 대표 소방서로 유지
  - `GroupDonation` 뷰/테이블로 단체 기부 메타(`group_id`, `initiator_user_id`, `message`)를 추적하며 기존 `GroupService` 로직을 재사용
  - Toss 연동은 `donation_service.py`에 결제 준비/확정 함수를 추가하고, 기존 `webhooks/toss` 라우트를 확장해 중복 구현 방지

#### 3) 랭킹/알림/마이페이지 데이터
- **재사용 대상**: `Ranking` 모델, `Notification` 모델, `notification_service.py`
- **신규 제안**:
  - `Ranking`에 `category`(individual/group/organization) 및 `period_start/period_end` 컬럼 추가하여 프런트 탭 구조 대응
  - `Notification`에 `metadata` JSON 필드 추가해 다양한 UI 구성을 1개 테이블로 처리
  - `notification_service.py`에 목록/읽음 처리 메서드 추가 후 마이페이지·헤더에서 공통 API 활용
  - 마이페이지용 컴포지트 DTO는 서비스 계층에서 조합(기부 내역 + 정기 결제 + 환불 상태). 기존 `DonationService`/`RefundService` 결과를 묶어 전송

#### 4) 구현 순서 제안
1. `FireStationStatus` 관련 모델·마이그레이션 → 서비스 확장 → `/emergency-stations` 라우트 완성
2. Donation/Group 확장 스키마 설계 및 마이그레이션 → Toss 연동/웹훅 보강 → 관련 API 업데이트
3. Ranking/Notification 확장 → 마이페이지 API 통합 → 프런트 더미 제거 순서 확정

---

## 보안 고려사항

### 1. 인증/인가
- JWT 토큰 (Access Token TTL: 30분)
- HttpOnly Cookie (XSS 방지)
- Role-based Access Control (User/Admin)

### 2. 데이터 보호
- 비밀번호: bcrypt 해싱 (cost factor 12)
- 민감 정보: 환경 변수 관리 (.env)
- API 키: 서버 측 저장 (절대 프론트엔드 노출 금지)

### 3. API 보안
- Rate Limiting (IP당 100 req/min)
- CORS 설정 (특정 도메인만 허용)
- Webhook 서명 검증 (Toss X-Toss-Signature)

### 4. 취약점 대응
- SQL Injection: SQLAlchemy ORM 사용
- XSS: React 자동 이스케이핑
- CSRF: SameSite Cookie + CORS

---

## 확장성 계획

### 단기 (3개월)
- [ ] WebSocket 수평 확장 (Redis Pub/Sub)
- [ ] CDN 도입 (CloudFront)
- [ ] DB Read Replica 추가

### 중기 (6개월)
- [ ] 마이크로서비스 분리 (Payment Service)
- [ ] Kafka 이벤트 스트리밍 도입
- [ ] GraphQL API 추가

### 장기 (12개월)
- [ ] Multi-region 배포
- [ ] Kubernetes Auto-scaling
- [ ] AI 모델 자체 호스팅 (Together AI → Self-hosted LLM)

---

## 참고 문서

- [CLAUDE.md](../CLAUDE.md): 프로젝트 가이드라인
- [Backend README](../backend/README.md)
- [Frontend README](../frontend/README.md)
- [API Documentation](http://localhost:8000/docs): FastAPI Swagger UI

---

**문서 버전**: 1.0.0
**최종 업데이트**: 2025-10-01
**작성자**: Claude Sonnet 4.5
