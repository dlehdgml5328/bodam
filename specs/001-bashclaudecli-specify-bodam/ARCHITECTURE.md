# 보담(BoDam) 시스템 아키텍처

## 📋 목차
- [개요](#개요)
- [전체 아키텍처](#전체-아키텍처)
- [백엔드 아키텍처](#백엔드-아키텍처)
- [프론트엔드 아키텍처](#프론트엔드-아키텍처)
- [데이터 아키텍처](#데이터-아키텍처)
- [AI 시스템 아키텍처](#ai-시스템-아키텍처)
- [보안 아키텍처](#보안-아키텍처)
- [인프라 아키텍처](#인프라-아키텍처)
- [성능 및 확장성](#성능-및-확장성)

## 개요

보담(BoDam)은 마이크로서비스 아키텍처를 기반으로 한 현대적인 웹 애플리케이션입니다. 실시간 데이터 처리, AI 분석, 안전한 결제 시스템을 통합하여 소방대원 지원 기부 플랫폼을 제공합니다.

### 아키텍처 원칙
- **확장성**: 수평적 확장 가능한 마이크로서비스
- **안정성**: 99.9% 가용성을 위한 고가용성 설계
- **성능**: p95 < 300ms 응답시간 목표
- **보안**: 다층 보안 및 개인정보 보호
- **유지보수성**: 모듈화된 설계와 테스트 우선 개발

## 전체 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   사용자 (Web)   │    │   관리자 (Web)   │    │  모바일 앱 (미래) │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
┌──────────────────────────────────────────────────────────────────┐
│                         CDN / Load Balancer                      │
│                      (Cloudflare / NGINX)                       │
└─────────────────────────┬────────────────────────────────────────┘
                          │
┌─────────────────────────┼────────────────────────────────────────┐
│                    Kubernetes Cluster                           │
│  ┌─────────────────┐    │    ┌─────────────────┐                 │
│  │   Frontend      │    │    │    Backend      │                 │
│  │   (Next.js)     │    │    │   (FastAPI)     │                 │
│  │                 │    │    │                 │                 │
│  │ ┌─────────────┐ │    │    │ ┌─────────────┐ │                 │
│  │ │   Pages     │ │────┼────┤ │     API     │ │                 │
│  │ │ Components  │ │    │    │ │  Endpoints  │ │                 │
│  │ │   Hooks     │ │    │    │ │ Middleware  │ │                 │
│  │ └─────────────┘ │    │    │ └─────────────┘ │                 │
│  └─────────────────┘    │    └─────────┬───────┘                 │
│                         │              │                         │
│  ┌─────────────────┐    │    ┌─────────┼───────┐                 │
│  │   Workers       │    │    │   Services      │                 │
│  │   (Celery)      │    │    │                 │                 │
│  │                 │    │    │ ┌─────────────┐ │                 │
│  │ ┌─────────────┐ │    │    │ │   Business  │ │                 │
│  │ │ Data Collect│ │    │    │ │    Logic    │ │                 │
│  │ │ AI Analysis │ │    │    │ │  Services   │ │                 │
│  │ │ Payments    │ │    │    │ │             │ │                 │
│  │ │ Notifications│ │   │    │ └─────────────┘ │                 │
│  │ └─────────────┘ │    │    └─────────┬───────┘                 │
│  └─────────────────┘    │              │                         │
│                         │              │                         │
│  ┌─────────────────┐    │    ┌─────────┼───────┐                 │
│  │   Database      │    │    │   External      │                 │
│  │  (PostgreSQL)   │    │    │   Services      │                 │
│  │                 │    │    │                 │                 │
│  │ ┌─────────────┐ │    │    │ ┌─────────────┐ │                 │
│  │ │ Core Tables │ │    │    │ │ Together AI │ │                 │
│  │ │ Vector Data │ │    │    │ │ Toss Pay    │ │                 │
│  │ │ Geo Data    │ │    │    │ │ Social Auth │ │                 │
│  │ │ Cache       │ │    │    │ │ 소방청 API   │ │                 │
│  │ └─────────────┘ │    │    │ └─────────────┘ │                 │
│  └─────────────────┘    │    └─────────────────┘                 │
└──────────────────────────────────────────────────────────────────┘
```

## 백엔드 아키텍처

### 레이어 구조
```
┌─────────────────────────────────────────────┐
│                API Layer                    │
│  ┌─────────────┐ ┌─────────────┐           │
│  │   REST API  │ │  WebSocket  │           │
│  │ Endpoints   │ │   Server    │           │
│  └─────────────┘ └─────────────┘           │
└─────────────┬───────────────────────────────┘
              │
┌─────────────┼───────────────────────────────┐
│          Middleware Layer                   │
│  ┌─────────────┐ ┌─────────────┐           │
│  │    Auth     │ │    CORS     │           │
│  │ Rate Limit  │ │   Logging   │           │
│  └─────────────┘ └─────────────┘           │
└─────────────┼───────────────────────────────┘
              │
┌─────────────┼───────────────────────────────┐
│           Service Layer                     │
│  ┌─────────────┐ ┌─────────────┐           │
│  │  Business   │ │ Integration │           │
│  │   Logic     │ │  Services   │           │
│  └─────────────┘ └─────────────┘           │
└─────────────┼───────────────────────────────┘
              │
┌─────────────┼───────────────────────────────┐
│           Data Layer                        │
│  ┌─────────────┐ ┌─────────────┐           │
│  │   Models    │ │ Repositories│           │
│  │    ORM      │ │    DAOs     │           │
│  └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────┘
```

### 핵심 서비스들

#### 1. 인증 서비스 (AuthService)
```python
# 역할: 사용자 인증 및 권한 관리
- JWT 토큰 생성/검증
- 소셜 로그인 (구글/카카오/네이버)
- 권한 기반 접근 제어 (RBAC)
- 세션 관리
```

#### 2. 기부 서비스 (DonationService)
```python
# 역할: 기부 프로세스 관리
- 일시/정기 기부 생성
- Toss Payments 연동
- 영수증 생성 (PDF)
- 환불 처리
```

#### 3. 소방서 서비스 (FireStationService)
```python
# 역할: 소방서 데이터 관리
- 지리 기반 검색 (PostGIS)
- 소방청 데이터 동기화
- 즐겨찾기 관리
- 랭킹 시스템
```

#### 4. AI 분석 서비스 (AIAnalysisService)
```python
# 역할: 콘텐츠 AI 분석
- 뉴스/유튜브 데이터 수집
- Together AI 연동
- 신뢰도 점수 계산
- 벡터 임베딩 (pgvector)
```

#### 5. 알림 서비스 (NotificationService)
```python
# 역할: 실시간 알림 관리
- WebSocket 연결 관리
- 푸시 알림 발송
- 이메일/SMS 발송
- 알림 기록 관리
```

### 워커 시스템 (Celery)

```
┌─────────────────┐    ┌─────────────────┐
│   Data Collector │    │  AI Analyzer    │
│                 │    │                 │
│ • 소방청 API     │    │ • 뉴스 분석     │
│ • 뉴스 수집     │    │ • 관련성 판별   │
│ • 유튜브 수집   │    │ • 요약 생성     │
│ • 30분 주기     │    │ • 임베딩 생성   │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
        ┌─────────────────────────┐
        │     Redis Queue         │
        └─────────────────────────┘
                     │
         ┌───────────┴───────────┐
┌─────────────────┐    ┌─────────────────┐
│ Payment Worker  │    │ Notification    │
│                 │    │    Worker       │
│ • 결제 처리     │    │ • WebSocket     │
│ • 영수증 생성   │    │ • 이메일 발송   │
│ • 환불 처리     │    │ • 푸시 알림     │
│ • 정기결제     │    │ • SMS 발송      │
└─────────────────┘    └─────────────────┘
```

## 프론트엔드 아키텍처

### Next.js App Router 구조
```
frontend/src/
├── app/                        # App Router (Next.js 14)
│   ├── (auth)/                # 인증 관련 페이지 그룹
│   │   ├── login/
│   │   └── signup/
│   ├── (public)/              # 공개 페이지 그룹
│   │   ├── page.tsx          # 홈페이지
│   │   └── stations/
│   │       ├── page.tsx      # 소방서 목록
│   │       └── [id]/
│   │           └── page.tsx  # 소방서 상세
│   ├── (dashboard)/          # 사용자 대시보드
│   │   ├── profile/
│   │   ├── donations/
│   │   └── favorites/
│   ├── admin/                # 관리자 페이지
│   │   ├── dashboard/
│   │   ├── review-queue/
│   │   └── analytics/
│   ├── api/                  # API Routes (서버사이드)
│   │   ├── auth/
│   │   └── webhooks/
│   ├── globals.css
│   ├── layout.tsx            # 루트 레이아웃
│   └── loading.tsx
├── components/               # 재사용 가능한 컴포넌트
│   ├── ui/                  # 기본 UI 컴포넌트
│   │   ├── Button.tsx
│   │   ├── Modal.tsx
│   │   └── Input.tsx
│   ├── features/            # 기능별 컴포넌트
│   │   ├── auth/
│   │   ├── donations/
│   │   ├── stations/
│   │   └── notifications/
│   └── layout/              # 레이아웃 컴포넌트
│       ├── Header.tsx
│       ├── Footer.tsx
│       └── Sidebar.tsx
├── lib/                     # 유틸리티 및 설정
│   ├── api-client.ts        # API 클라이언트
│   ├── auth.ts              # 인증 로직
│   ├── utils.ts             # 공통 유틸리티
│   └── constants.ts
├── hooks/                   # 커스텀 React Hooks
│   ├── useAuth.ts
│   ├── useWebSocket.ts
│   └── useLocalStorage.ts
├── store/                   # 상태 관리 (Zustand)
│   ├── authStore.ts
│   ├── donationStore.ts
│   └── notificationStore.ts
└── types/                   # TypeScript 타입 정의
    ├── api.ts
    ├── auth.ts
    └── donation.ts
```

### 상태 관리 전략
```typescript
// Zustand를 사용한 클라이언트 상태 관리
interface AuthStore {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
}

interface DonationStore {
  donations: Donation[];
  currentDonation: Donation | null;
  createDonation: (data: CreateDonationRequest) => Promise<void>;
  fetchDonations: () => Promise<void>;
}

// Server State는 TanStack Query (React Query) 사용
const { data: stations } = useQuery({
  queryKey: ['stations', filters],
  queryFn: () => api.stations.list(filters),
  staleTime: 5 * 60 * 1000, // 5분
});
```

## 데이터 아키텍처

### 데이터베이스 설계

#### 핵심 테이블 구조
```sql
-- 사용자 테이블
users (
  id UUID PRIMARY KEY,
  email VARCHAR UNIQUE,
  password_hash VARCHAR,
  name VARCHAR,
  role user_role,
  tier INTEGER,
  total_donated DECIMAL,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- 소방서 테이블 (지리 정보 포함)
fire_stations (
  id UUID PRIMARY KEY,
  name VARCHAR,
  address VARCHAR,
  location POINT, -- PostGIS
  station_code VARCHAR UNIQUE,
  region VARCHAR,
  district VARCHAR,
  status station_status,
  total_received DECIMAL,
  donor_count INTEGER
);

-- 기부 테이블
donations (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  fire_station_id UUID REFERENCES fire_stations(id),
  amount DECIMAL,
  type donation_type,
  status donation_status,
  toss_payment_key VARCHAR,
  created_at TIMESTAMP,
  completed_at TIMESTAMP
);

-- AI 분석 콘텐츠 (벡터 검색)
news_content (
  id UUID PRIMARY KEY,
  title VARCHAR,
  content TEXT,
  source VARCHAR,
  embedding VECTOR(1536), -- pgvector
  relevance_score INTEGER,
  status content_status,
  published_at TIMESTAMP
);
```

#### 인덱스 전략
```sql
-- 성능 최적화 인덱스
CREATE INDEX idx_stations_location ON fire_stations USING GIST (location);
CREATE INDEX idx_news_embedding ON news_content USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_donations_user_date ON donations (user_id, created_at DESC);
CREATE INDEX idx_donations_station_date ON donations (fire_station_id, created_at DESC);

-- 복합 인덱스
CREATE INDEX idx_users_role_active ON users (role, is_active) WHERE is_active = true;
CREATE INDEX idx_content_status_score ON news_content (status, relevance_score) WHERE status IN ('auto_approved', 'pending_review');
```

#### 파티셔닝 전략
```sql
-- 뉴스 데이터 월별 파티션 (데이터 증가 대비)
CREATE TABLE news_content_y2025m01 PARTITION OF news_content
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- 알림 데이터 분기별 파티션
CREATE TABLE notifications_q1_2025 PARTITION OF notifications
FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');
```

### 캐싱 전략

#### Redis 캐시 구조
```
Redis 키 구조:
├── session:user:{user_id}           # 사용자 세션 (TTL: 7일)
├── stations:nearby:{lat}:{lng}      # 근처 소방서 (TTL: 1시간)
├── rankings:{station_id}:{period}   # 랭킹 데이터 (TTL: 1일)
├── news:latest                      # 최신 뉴스 (TTL: 30분)
└── rate_limit:{ip}:{endpoint}       # Rate limiting (TTL: 1분)
```

## AI 시스템 아키텍처

### AI 파이프라인
```
1. 데이터 수집 (30분 주기)
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   뉴스 API      │    │   유튜브 API    │    │   재난문자 API   │
│   (네이버)      │    │   (구글)        │    │   (행안부)       │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
2. AI 분석 (Together AI - Llama 3.3 70B)
┌─────────────────────────────────┼─────────────────────────────────┐
│                           AI 분석 서버                            │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │   텍스트 정제   │ -> │   관련성 판별   │ -> │   요약 생성     │  │
│  │   (전처리)      │    │ (화재 관련성)   │    │   (핵심 내용)   │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘  │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │  임베딩 생성    │    │  신뢰도 점수    │    │  키워드 추출    │  │
│  │ (벡터 변환)     │    │  (1-100점)     │    │  (태그)         │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘  │
└─────────────────────────────────┼─────────────────────────────────┘
                                 │
3. 저장 및 분류
┌─────────────────────────────────┼─────────────────────────────────┐
│                           PostgreSQL                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │ 점수 ≥ 70       │    │ 점수 50-69      │    │ 점수 < 50       │  │
│  │ (자동 승인)     │    │ (수동 검토)     │    │ (자동 폐기)     │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘  │
└─────────────────────────────────┼─────────────────────────────────┘
                                 │
4. 사용자 알림
┌─────────────────────────────────┼─────────────────────────────────┐
│                         알림 시스템                               │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │   WebSocket     │    │     이메일      │    │     푸시 알림   │  │
│  │  (실시간)       │    │   (일괄 발송)   │    │   (모바일)      │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### AI 프롬프트 시스템
```python
# 관련성 판별 프롬프트
RELEVANCE_PROMPT = """
다음 뉴스 기사가 화재, 소방, 응급구조와 관련이 있는지 1-100점으로 평가하세요.

기사 내용: {content}

평가 기준:
- 90-100점: 화재 사건, 소방관 활동 직접 관련
- 70-89점: 응급구조, 안전사고 관련
- 50-69점: 간접적 관련성 (안전 교육, 예방 등)
- 30-49점: 약간의 관련성
- 0-29점: 관련성 없음

JSON 형식으로 응답:
{
  "relevance_score": 점수,
  "reasoning": "판단 근거",
  "summary": "핵심 내용 요약",
  "keywords": ["키워드1", "키워드2", ...]
}
"""
```

## 보안 아키텍처

### 다층 보안 모델
```
┌─────────────────────────────────────────────────────────────────┐
│                        Layer 1: 네트워크                        │
│  • Cloudflare WAF (웹 방화벽)                                   │
│  • DDoS Protection                                             │
│  • SSL/TLS 암호화                                              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────────┐
│                     Layer 2: 애플리케이션                       │
│  • CORS 정책                                                   │
│  • Rate Limiting (분당 100회)                                  │
│  • Input Validation                                           │
│  • SQL Injection 방지                                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────────┐
│                     Layer 3: 인증/인가                          │
│  • JWT + HttpOnly 쿠키                                         │
│  • RBAC (Role-Based Access Control)                           │
│  • OAuth2 (소셜 로그인)                                        │
│  • BOLA 방지 (Broken Object Level Authorization)               │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────────┐
│                     Layer 4: 데이터                             │
│  • 개인정보 암호화 (AES-256)                                    │
│  • PII 마스킹 (로그)                                           │
│  • 백업 암호화                                                 │
│  • 데이터베이스 접근 제어                                       │
└─────────────────────────────────────────────────────────────────┘
```

### 인증 흐름
```
1. 로그인 요청
User -> Frontend -> Backend API
                     |
                     v
2. 인증 처리
              [Auth Service]
                     |
                     v
3. JWT 토큰 생성
              [Token Service]
              - Access Token (15분)
              - Refresh Token (7일)
                     |
                     v
4. 응답 (HttpOnly Cookie)
Backend -> Frontend -> User
                     |
                     v
5. API 요청 (자동 포함)
User -> Frontend -> Backend API
      (Cookie)      |
                    v
6. 토큰 검증
              [Auth Middleware]
              - 토큰 유효성 검사
              - 권한 확인
              - Rate Limit 체크
```

## 인프라 아키텍처

### Kubernetes 클러스터 구조
```
┌─────────────────────────────────────────────────────────────────┐
│                        Kubernetes Cluster                      │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │   Namespace:    │    │   Namespace:    │                     │
│  │   Production    │    │    Staging      │                     │
│  │                 │    │                 │                     │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │                     │
│  │ │  Frontend   │ │    │ │  Frontend   │ │                     │
│  │ │   (3 pods)  │ │    │ │   (1 pod)   │ │                     │
│  │ └─────────────┘ │    │ └─────────────┘ │                     │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │                     │
│  │ │  Backend    │ │    │ │  Backend    │ │                     │
│  │ │   (5 pods)  │ │    │ │   (2 pods)  │ │                     │
│  │ └─────────────┘ │    │ └─────────────┘ │                     │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │                     │
│  │ │  Workers    │ │    │ │  Workers    │ │                     │
│  │ │   (4 pods)  │ │    │ │   (1 pod)   │ │                     │
│  │ └─────────────┘ │    │ └─────────────┘ │                     │
│  └─────────────────┘    └─────────────────┘                     │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │   Namespace:    │    │   Namespace:    │                     │
│  │   Database      │    │   Monitoring    │                     │
│  │                 │    │                 │                     │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │                     │
│  │ │ PostgreSQL  │ │    │ │ Prometheus  │ │                     │
│  │ │  (Primary)  │ │    │ │   Server    │ │                     │
│  │ └─────────────┘ │    │ └─────────────┘ │                     │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │                     │
│  │ │ PostgreSQL  │ │    │ │   Grafana   │ │                     │
│  │ │ (Replica)   │ │    │ │  Dashboard  │ │                     │
│  │ └─────────────┘ │    │ └─────────────┘ │                     │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │                     │
│  │ │    Redis    │ │    │ │ Alertmanager│ │                     │
│  │ │  (Cluster)  │ │    │ │             │ │                     │
│  │ └─────────────┘ │    │ └─────────────┘ │                     │
│  └─────────────────┘    └─────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

### Blue-Green 배포 전략
```
Current Traffic (Blue Environment)
┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │────│   Blue Pods     │
│   (NGINX)       │    │   (v1.0.0)      │
└─────────────────┘    └─────────────────┘
         │
         │ Deploy New Version
         v
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │────│   Blue Pods     │    │   Green Pods    │
│   (NGINX)       │    │   (v1.0.0)      │    │   (v1.1.0)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                                             │
         │ Health Check OK → Switch Traffic           │
         v                                             │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │────────────────────────────│   Green Pods    │
│   (NGINX)       │    │   Blue Pods     │    │   (v1.1.0)      │
└─────────────────┘    │   (Standby)     │    └─────────────────┘
                       └─────────────────┘
```

## 성능 및 확장성

### 성능 목표 및 최적화

#### 응답 시간 목표
```
┌─────────────────┬─────────────┬─────────────┬─────────────┐
│     엔드포인트   │    p50      │     p95     │     p99     │
├─────────────────┼─────────────┼─────────────┼─────────────┤
│ GET /stations   │   < 100ms   │   < 200ms   │   < 300ms   │
│ POST /donations │   < 200ms   │   < 400ms   │   < 600ms   │
│ WebSocket       │   < 50ms    │   < 100ms   │   < 150ms   │
│ AI Analysis     │   < 5s      │   < 10s     │   < 15s     │
└─────────────────┴─────────────┴─────────────┴─────────────┘
```

#### 확장성 전략
```
동시 사용자 수에 따른 Auto Scaling:

┌─────────────────┐
│   0-100 users   │ -> 최소 설정 (2 pods)
├─────────────────┤
│  100-500 users  │ -> 중간 설정 (5 pods)
├─────────────────┤
│ 500-1000 users  │ -> 확장 설정 (10 pods)
├─────────────────┤
│  1000+ users    │ -> 최대 설정 (20 pods) + DB 분산
└─────────────────┘

HPA (Horizontal Pod Autoscaler) 설정:
- CPU 사용률 70% 초과 시 Scale Up
- Memory 사용률 80% 초과 시 Scale Up
- 커스텀 메트릭: API 응답시간 300ms 초과 시 Scale Up
```

### 모니터링 및 관찰성

#### 메트릭 수집
```yaml
# Prometheus 메트릭
system_metrics:
  - cpu_usage_percent
  - memory_usage_percent
  - disk_usage_percent
  - network_io_bytes

application_metrics:
  - http_requests_total
  - http_request_duration_seconds
  - database_connections_active
  - cache_hit_ratio

business_metrics:
  - donations_created_total
  - users_registered_total
  - ai_analysis_success_rate
  - payment_success_rate
```

#### 로깅 전략
```json
{
  "timestamp": "2025-09-19T10:00:00Z",
  "level": "INFO",
  "service": "donation-service",
  "trace_id": "abc-123-def",
  "user_id": "user-456",
  "action": "create_donation",
  "amount": 10000,
  "station_id": "station-789",
  "duration_ms": 150,
  "success": true
}
```

이 아키텍처는 높은 가용성, 확장성, 보안성을 제공하며, 한국의 특수한 요구사항(소방청 데이터, Toss 결제, 소셜 로그인)을 효과적으로 지원합니다.