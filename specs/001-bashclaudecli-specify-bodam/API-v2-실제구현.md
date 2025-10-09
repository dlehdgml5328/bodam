# 보담(BoDam) API 문서 v2 - 실제 구현 기준

> **기준일**: 2025-10-02
> **상태**: 현재 구현된 실제 API 명세
> **원본 스펙**: [API.md](./API.md)

## 개요

보담 커피 기부 플랫폼의 REST API 실제 구현 문서입니다.

**Base URL**: `http://localhost:8000` (개발), `https://api.bodam.example` (운영)

---

## 인증

### 현재 구현: **쿠키 + CSRF + Bearer 혼합**
- 기본 조회·마이페이지 등 일반 API는 `bodam_session` 쿠키(JWT) 기반
- 상태 변경 요청(POST/PUT/DELETE)은 `bodam_csrf` 쿠키와 `X-CSRF-Token` 헤더 일치 여부 검사
- 결제 준비/확정 등 민감 API는 `Authorization: Bearer {access_token}` 헤더 필수
- 모든 요청에서 `credentials: 'include'` 필요 (쿠키 전송)

---

## 응답 형식

### 성공 응답
```json
{
  "items": [...],
  "total": 10,
  "page": 1
}
```

또는 단일 객체:
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "message": "Success"
}
```

### 에러 응답
```json
{
  "detail": "ERROR_MESSAGE"
}
```

---

## 1. 인증 API (`/auth`)

### 회원가입
```http
POST /auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "name": "사용자명",
  "phone": "01012345678"  // Optional
}
```

**응답 (201 Created):**
```json
{
  "user_id": "ef616d3b-3fd4-45ab-982f-533e71be26ab",
  "email": "user@example.com",
  "message": "인증 이메일이 발송되었습니다"
}
```

---

### 로그인
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**응답 (200 OK):**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "사용자명"
  },
  "access_token": "eyJhbGc...",
  "csrf_token": "xf93as..."
}
```

**Set-Cookie**
- `bodam_session=eyJhbGc...; HttpOnly; SameSite=Lax; Path=/`
- `bodam_csrf=xf93as...; SameSite=Lax; Path=/`

---

### 로그아웃
```http
POST /auth/logout
Cookie: bodam_session={token}; bodam_csrf={csrf}
X-CSRF-Token: {csrf}
```

**응답**: 200 OK

---

### 비밀번호 재설정 요청
```http
POST /auth/password-reset/request
Content-Type: application/json

{
  "email": "user@example.com"
}
```

---

### 비밀번호 재설정 확인
```http
POST /auth/password-reset/confirm
Content-Type: application/json

{
  "token": "reset_token_here",
  "new_password": "newpassword123"
}
```

---

## 2. 소방서 API (`/stations`)

### 소방서 목록 조회
```http
GET /stations?page=1&limit=20&region=서울&search=강남
```

**응답:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "강남소방서",
      "address": "서울 강남구 테헤란로 123",
      "location": {
        "lat": 37.5665,
        "lng": 126.9780
      },
      "total_received": 1500000,
      "donor_count": 45
    }
  ],
  "total": 100,
  "page": 1
}
```

---

### 근처 소방서 검색
```http
GET /stations/nearby?lat=37.5665&lng=126.9780&radius=5000
```

---

### 소방서 상세 조회
```http
GET /stations/{station_id}
```

---

### 즐겨찾기 추가
```http
POST /stations/{station_id}/favorites
Cookie: bodam_session={token}
```

---

## 3. 기부 API (`/donations`)

### ⚠️ 기부 내역 조회 (현재 구현)
```http
GET /donations?donor_email={email}&page=1&limit=20
Cookie: bodam_session={token}
```

**필수 파라미터**:
- `donor_email`: 조회할 사용자 이메일

**응답:**
```json
{
  "items": [
    {
      "id": "uuid",
      "fire_station": {
        "id": "uuid",
        "name": "강남소방서"
      },
      "amount": 10000,
      "type": "one_time",
      "status": "completed",
      "message": "응원합니다!",
      "created_at": "2025-10-02T10:00:00Z"
    }
  ],
  "total": 5
}
```

---

### 기부 생성
```http
POST /donations
Authorization: Bearer {access_token}
Cookie: bodam_session={token}
Content-Type: application/json

{
  "fire_station_id": "uuid",
  "amount": 10000,
  "type": "one_time",
  "message": "소방관들을 응원합니다!",
  "is_anonymous": false
}
```

**응답 (201 Created):**
```json
{
  "donation_id": "uuid",
  "payment_url": "https://toss.im/payment/...",
  "order_id": "ORDER_123"
}
```

---

### 기부 상세 조회
```http
GET /donations/{donation_id}
Cookie: bodam_session={token}
```

---

### 영수증 다운로드
```http
GET /donations/{donation_id}/receipt
Cookie: bodam_session={token}
```

**응답**: PDF 파일 또는 다운로드 URL

---

### 환불 요청
```http
POST /donations/{donation_id}/refund
Cookie: bodam_session={token}
Content-Type: application/json

{
  "reason": "실수로 중복 결제했습니다"
}
```

---

## 4. 정기 기부 API (`/subscriptions`)

### 정기결제 목록
```http
GET /subscriptions?donor_email={email}
Cookie: bodam_session={token}
```

**필수 파라미터**:
- `donor_email`: 조회할 사용자 이메일

---

### 정기결제 일시정지
```http
POST /subscriptions/{subscription_id}/pause
Cookie: bodam_session={token}
```

---

### 정기결제 재개
```http
POST /subscriptions/{subscription_id}/resume
Cookie: bodam_session={token}
```

---

### 정기결제 취소
```http
POST /subscriptions/{subscription_id}/cancel
Cookie: bodam_session={token}
```

---

## 5. 단체 API (`/groups`)

### 단체 목록 조회
```http
GET /groups?page=1&limit=20
```

---

### 단체 생성
```http
POST /groups
Cookie: bodam_session={token}
Content-Type: application/json

{
  "name": "보담 봉사단",
  "description": "따뜻한 마음을 전하는 단체"
}
```

---

## 6. 랭킹 API

### 소방서별 기부자 랭킹
```http
GET /stations/{station_id}/rankings?period=all_time&limit=10
```

---

## 7. 관리자 API (`/admin`)

### 환불 요청 목록
```http
GET /admin/refunds?status=pending
Cookie: bodam_session={admin_token}
```

---

### 환불 승인
```http
POST /admin/refunds/{refund_id}/decision
Cookie: bodam_session={admin_token}
Content-Type: application/json

{
  "decision": "approved",
  "note": "승인 사유"
}
```

---

## 8. Webhook

### Toss 결제 Webhook
```http
POST /webhooks/toss/payment
X-Toss-Signature: {signature}
Content-Type: application/json

{
  "orderId": "ORDER_123",
  "status": "DONE",
  "paymentKey": "payment_key",
  "amount": 10000
}
```

---

## 오류 코드

| HTTP Status | detail | 설명 |
|-------------|--------|------|
| 400 | `EMAIL_REQUIRED` | donor_email 파라미터 필요 |
| 401 | `UNAUTHORIZED` | 인증 토큰 없음 또는 만료 |
| 403 | `FORBIDDEN` | 권한 없음 (관리자 전용) |
| 404 | `NOT_FOUND` | 리소스 없음 |
| 409 | `CONFLICT` | 중복 (이메일 등) |
| 500 | `INTERNAL_SERVER_ERROR` | 서버 오류 |

---

## 스펙과의 차이점 정리

### 1. 인증 방식
| 항목 | 스펙 (API.md) | 실제 구현 |
|------|--------------|----------|
| 인증 | Bearer 토큰 단일 | 일반 API: `bodam_session` 쿠키 + CSRF<br>결제 API: Bearer 토큰 |
| 헤더 | `Authorization: Bearer {token}` | 일반 API: `X-CSRF-Token` + 쿠키<br>결제 API: `Authorization: Bearer {token}` |

### 2. 응답 구조
| 항목 | 스펙 (API.md) | 실제 구현 |
|------|--------------|----------|
| 성공 | `{ success: true, data: {...} }` | `{ items: [...], total: N }` |
| 에러 | `{ success: false, error: {...} }` | `{ detail: "..." }` |

### 3. API 엔드포인트 차이
| API | 스펙 | 실제 구현 |
|-----|------|----------|
| 기부 내역 | `GET /donations` | `GET /donations?donor_email={email}` ✅ |
| 정기 결제 | `GET /subscriptions` | `GET /subscriptions?donor_email={email}` ✅ |

---

## 프론트엔드 연동 가이드

### 1. API 클라이언트 설정
```typescript
// frontend/src/lib/api.ts
export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const csrfHeader = shouldSendCsrf(options.method)
    ? { 'X-CSRF-Token': readCsrfToken() }
    : {};

  const response = await fetch(`http://localhost:8000${path}`, {
    ...options,
    credentials: 'include',  // ✅ 쿠키 포함 필수
    headers: {
      'Content-Type': 'application/json',
      ...csrfHeader,
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new ApiError(error.detail, response.status);
  }

  return response.json();
}

function shouldSendCsrf(method: string | undefined): boolean {
  if (!method) return false;
  const upper = method.toUpperCase();
  return !['GET', 'HEAD', 'OPTIONS'].includes(upper);
}

function readCsrfToken(): string {
  const match = document.cookie.match(/bodam_csrf=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : '';
}

export function buildPaymentHeaders() {
  const accessToken = sessionStorage.getItem('bodam_access_token');
  if (!accessToken) throw new Error('Missing access token for payment API');
  return { Authorization: `Bearer ${accessToken}` };
}
```

### 2. 로그인 후 이메일 저장
```typescript
// 로그인 성공 시
const response = await apiRequest('/auth/login', {
  method: 'POST',
  body: JSON.stringify({ email, password }),
});

localStorage.setItem('loggedInEmail', response.user.email);
sessionStorage.setItem('bodam_access_token', response.access_token);
```

### 3. 기부 내역 조회
```typescript
const userEmail = localStorage.getItem('loggedInEmail');
const donations = await apiRequest(`/donations?donor_email=${userEmail}`);
```

---

## 향후 개선 계획

### Phase 1: 인증 개선
- [x] 결제 API Bearer 토큰 + 일반 API 쿠키 기반 혼합 적용
- [ ] Refresh Token 도입 (선택)
- [ ] 토큰에서 사용자 정보 자동 추출 (donor_email 파라미터 제거)

### Phase 2: 응답 표준화
- [ ] 모든 API를 `{ success, data, message }` 구조로 통일
- [ ] OpenAPI 스펙 자동 생성

### Phase 3: 실시간 기능
- [ ] WebSocket 알림 구현
- [ ] Server-Sent Events (SSE) 추가

---

**문서 버전**: 2.0.0
**최종 업데이트**: 2025-10-02
**작성자**: Claude Sonnet 4.5
**참고**: [ARCHITECTURE.md](../../docs/ARCHITECTURE.md)
