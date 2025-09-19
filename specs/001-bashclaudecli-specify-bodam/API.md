# 보담(BoDam) API 문서

## 개요
보담 커피 기부 플랫폼의 REST API 문서입니다. 모든 API는 JSON 형식으로 통신하며, HTTPS를 통해 제공됩니다.

**Base URL**: `https://api.bodam.example`

## 인증
JWT Bearer 토큰을 사용합니다.
```
Authorization: Bearer {access_token}
```

## 응답 형식
모든 API는 다음 형식으로 응답합니다:
```json
{
  "success": true,
  "data": {...},
  "message": "성공 메시지",
  "timestamp": "2025-09-19T12:00:00Z"
}
```

오류 시:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "오류 메시지",
    "details": {...}
  },
  "timestamp": "2025-09-19T12:00:00Z"
}
```

## 1. 인증 API (`/auth`)

### 회원가입
```http
POST /auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "name": "사용자명",
  "phone": "01012345678"
}
```

**응답 (201 Created):**
```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "email": "user@example.com",
    "message": "인증 이메일이 발송되었습니다"
  }
}
```

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
  "success": true,
  "data": {
    "access_token": "jwt_token_here",
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "name": "사용자명",
      "role": "donor",
      "tier": 1,
      "total_donated": 0
    }
  }
}
```

### 로그아웃
```http
POST /auth/logout
Authorization: Bearer {token}
```

### 소셜 로그인
```http
GET /auth/social/{provider}
```
지원 제공자: `google`, `kakao`, `naver`

## 2. 소방서 API (`/stations`)

### 소방서 목록 조회
```http
GET /stations?page=1&limit=20&region=서울&search=강남
```

**응답:**
```json
{
  "success": true,
  "data": {
    "stations": [
      {
        "id": "uuid",
        "name": "강남소방서",
        "address": "서울 강남구 테헤란로 123",
        "location": {
          "lat": 37.5665,
          "lng": 126.9780
        },
        "region": "서울",
        "district": "강남구",
        "total_received": 1500000,
        "donor_count": 45
      }
    ],
    "total": 100,
    "page": 1,
    "limit": 20
  }
}
```

### 근처 소방서 검색
```http
GET /stations/nearby?lat=37.5665&lng=126.9780&radius=5000
```

**응답:**
```json
{
  "success": true,
  "data": {
    "stations": [
      {
        "id": "uuid",
        "name": "강남소방서",
        "distance": 1200.5,
        "location": {
          "lat": 37.5665,
          "lng": 126.9780
        }
      }
    ]
  }
}
```

### 소방서 상세 조회
```http
GET /stations/{station_id}
```

**응답:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "강남소방서",
    "address": "서울 강남구 테헤란로 123",
    "phone": "02-1234-5678",
    "station_code": "SEO001",
    "total_received": 1500000,
    "donor_count": 45,
    "recent_donations": [
      {
        "amount": 10000,
        "donor_name": "익명",
        "message": "응원합니다!",
        "created_at": "2025-09-19T10:00:00Z"
      }
    ],
    "is_favorite": false
  }
}
```

### 즐겨찾기 추가/제거
```http
POST /stations/{station_id}/favorites
DELETE /stations/{station_id}/favorites
Authorization: Bearer {token}
```

## 3. 기부 API (`/donations`)

### 기부 내역 조회
```http
GET /donations?page=1&limit=20&status=completed
Authorization: Bearer {token}
```

**응답:**
```json
{
  "success": true,
  "data": {
    "donations": [
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
        "created_at": "2025-09-19T10:00:00Z"
      }
    ],
    "total": 5
  }
}
```

### 기부 생성
```http
POST /donations
Authorization: Bearer {token}
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
  "success": true,
  "data": {
    "donation_id": "uuid",
    "payment_url": "https://toss.im/payment/...",
    "order_id": "ORDER_123"
  }
}
```

### 정기 기부 생성
```http
POST /donations
Authorization: Bearer {token}
Content-Type: application/json

{
  "fire_station_id": "uuid",
  "amount": 5000,
  "type": "recurring",
  "frequency": "monthly",
  "message": "매월 정기 응원!"
}
```

### 기부 상세 조회
```http
GET /donations/{donation_id}
Authorization: Bearer {token}
```

### 영수증 다운로드
```http
GET /donations/{donation_id}/receipt
Authorization: Bearer {token}
```

**응답:** PDF 파일

### 환불 요청
```http
POST /donations/{donation_id}/refund
Authorization: Bearer {token}
Content-Type: application/json

{
  "reason": "실수로 중복 결제했습니다"
}
```

### 정기결제 목록
```http
GET /subscriptions
Authorization: Bearer {token}
```

### 정기결제 취소
```http
POST /subscriptions/{subscription_id}/cancel
Authorization: Bearer {token}
```

## 4. 랭킹 API

### 소방서별 기부자 랭킹
```http
GET /stations/{station_id}/rankings?period=all_time&limit=10
```

**응답:**
```json
{
  "success": true,
  "data": {
    "rankings": [
      {
        "rank": 1,
        "user": {
          "name": "김기부",
          "tier": 5
        },
        "total_amount": 500000,
        "donation_count": 25
      }
    ],
    "period": "all_time"
  }
}
```

## 5. 알림 API

### 내 알림 목록
```http
GET /notifications?limit=20
Authorization: Bearer {token}
```

### 알림 읽음 처리
```http
PATCH /notifications/{notification_id}/read
Authorization: Bearer {token}
```

## 6. WebSocket 실시간 알림

### 연결
```javascript
const ws = new WebSocket('wss://api.bodam.example/ws/notifications');

// 인증
ws.send(JSON.stringify({
  type: 'auth',
  token: 'your_jwt_token'
}));

// 메시지 수신
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('알림:', data);
};
```

### 알림 타입
- `donation_success`: 기부 완료
- `incident_alert`: 화재 사건 알림
- `payment_failed`: 결제 실패
- `refund_approved`: 환불 승인

## 7. 관리자 API (`/admin`)

### AI 검토 대기 콘텐츠
```http
GET /admin/review-queue
Authorization: Bearer {admin_token}
```

### 콘텐츠 승인/거부
```http
POST /admin/content/{content_id}/approve
POST /admin/content/{content_id}/reject
Authorization: Bearer {admin_token}
```

### 환불 요청 관리
```http
GET /admin/refunds?status=pending
POST /admin/refunds/{refund_id}/approve
POST /admin/refunds/{refund_id}/reject
Authorization: Bearer {admin_token}
```

## 8. 헬스체크 & 모니터링

### 서비스 상태
```http
GET /healthz
GET /readyz
GET /metrics
```

## 오류 코드

| 코드 | 메시지 | 설명 |
|------|--------|------|
| `AUTH_REQUIRED` | 인증이 필요합니다 | 토큰 누락 또는 만료 |
| `INVALID_CREDENTIALS` | 잘못된 인증 정보 | 이메일/비밀번호 오류 |
| `USER_NOT_FOUND` | 사용자를 찾을 수 없음 | 존재하지 않는 사용자 |
| `STATION_NOT_FOUND` | 소방서를 찾을 수 없음 | 존재하지 않는 소방서 |
| `DONATION_NOT_FOUND` | 기부를 찾을 수 없음 | 존재하지 않는 기부 |
| `INSUFFICIENT_AMOUNT` | 최소 기부 금액 미달 | 1,000원 미만 기부 |
| `PAYMENT_FAILED` | 결제 처리 실패 | Toss 결제 오류 |
| `VALIDATION_ERROR` | 입력값 검증 실패 | 필수 필드 누락 등 |
| `RATE_LIMIT_EXCEEDED` | 요청 한도 초과 | 분당 100회 제한 |
| `SERVER_ERROR` | 서버 내부 오류 | 500 오류 |

## 요청 제한
- **Rate Limit**: 분당 100회
- **파일 업로드**: 최대 10MB
- **페이지네이션**: 최대 100개 항목

## SDK 및 라이브러리

### JavaScript/TypeScript
```bash
npm install @bodam/api-client
```

```javascript
import { BodamAPI } from '@bodam/api-client';

const api = new BodamAPI({
  baseURL: 'https://api.bodam.example',
  token: 'your_jwt_token'
});

// 소방서 검색
const stations = await api.stations.nearby(37.5665, 126.9780);

// 기부하기
const donation = await api.donations.create({
  fire_station_id: 'uuid',
  amount: 10000,
  type: 'one_time'
});
```

### Python
```bash
pip install bodam-python
```

```python
from bodam import BodamClient

client = BodamClient(
    base_url="https://api.bodam.example",
    token="your_jwt_token"
)

# 소방서 검색
stations = client.stations.nearby(lat=37.5665, lng=126.9780)

# 기부하기
donation = client.donations.create(
    fire_station_id="uuid",
    amount=10000,
    type="one_time"
)
```

이 API 문서는 contracts/ 폴더의 OpenAPI 스펙을 기반으로 작성되었으며, 실제 구현과 함께 업데이트됩니다.