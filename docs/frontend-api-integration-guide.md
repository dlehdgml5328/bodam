# 프론트엔드 API 연동 가이드

작성일: 2025-10-02
작성자: Claude Code

## 문제 상황

### 1. 더미 데이터 문제
- **증상**: 마이페이지에 하드코딩된 더미 데이터가 표시됨
- **원인**: 컴포넌트 내부에 하드코딩된 배열(`donationHistory`, `regularDonations`, `userInfo`)
- **영향**: 실제 사용자 데이터가 아닌 가짜 데이터가 표시됨

### 2. API 400 에러
- **증상**: 네트워크 탭에서 `/donations`, `/subscriptions` 호출 시 400 에러
- **원인**:
  - 인증 토큰 누락 (쿠키 또는 헤더)
  - 잘못된 요청 형식
  - 필수 파라미터 누락

## 해결 방법

### Step 1: 더미 데이터 제거

**파일**: `frontend/src/app/(account)/mypage/page.tsx`

#### Before (더미 데이터)
```typescript
const donationHistory = [
  {
    id: 1,
    date: new Date(2024, 11, 15),
    amount: 30000,
    // ... 하드코딩된 데이터
  },
  // ...
];

const [userInfo, setUserInfo] = useState({
  totalDonations: 485000,  // ❌ 하드코딩
  totalCups: 162,           // ❌ 하드코딩
  totalCount: 23,           // ❌ 하드코딩
});
```

#### After (API 연동)
```typescript
// State로 선언
const [donationHistory, setDonationHistory] = useState<any[]>([]);
const [regularDonations, setRegularDonations] = useState<any[]>([]);

// 초기값 0으로
const [userInfo, setUserInfo] = useState({
  totalDonations: 0,   // ✅ 0으로 초기화
  totalCups: 0,
  totalCount: 0,
});

// useEffect에서 API 호출
useEffect(() => {
  const fetchData = async () => {
    const donations = await apiRequest('/donations');
    setDonationHistory(donations.items || []);

    // 통계 계산
    const totalAmount = donations.items.reduce((sum, d) => sum + d.amount, 0);
    setUserInfo(prev => ({
      ...prev,
      totalDonations: totalAmount,
      totalCups: Math.floor(totalAmount / 3000),
      totalCount: donations.items.length,
    }));
  };

  fetchData();
}, []);
```

### Step 2: API 인증 문제 해결

#### 문제: 400 Bad Request
```
GET /donations → 400 (EMAIL_REQUIRED)
```

#### 원인
백엔드가 인증된 사용자만 접근 가능하도록 설정됨. 인증 토큰이 없으면 400 에러 발생.

#### 해결 방법

**Option 1: 쿠키 기반 인증 확인**
```typescript
// api.ts에서 credentials: 'include' 확인
export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(url, {
    ...options,
    credentials: 'include',  // ✅ 쿠키 포함
  });
}
```

**Option 2: 로그인 후 토큰/쿠키 확인**
```typescript
const response = await apiRequest('/auth/login', {
  method: 'POST',
  body: JSON.stringify({ email, password }),
});

sessionStorage.setItem('bodam_access_token', response.access_token);
sessionStorage.setItem('bodam_csrf_token', response.csrf_token);
console.log(document.cookie); // bodam_session=..., bodam_csrf=... 확인
```

**Option 3: 결제 API 호출 시 헤더 확인**
```typescript
import { apiRequest, buildPaymentHeaders } from '@/lib/api';

await apiRequest('/donations', {
  method: 'POST',
  headers: {
    ...buildPaymentHeaders(),
  },
  body: JSON.stringify(payload),
});
```

### Step 3: localStorage 데이터 활용

```typescript
// 로그인 시 저장
localStorage.setItem('userNickname', response.user.name);
localStorage.setItem('loggedInEmail', response.user.email);

// 마이페이지에서 사용
useEffect(() => {
  const userNickname = localStorage.getItem('userNickname') || '소방이';
  const userEmail = localStorage.getItem('loggedInEmail') || '';

  setUserInfo(prev => ({
    ...prev,
    name: userNickname,
    email: userEmail,
  }));
}, []);
```

## 디버깅 체크리스트

### 1. 네트워크 탭 확인
```
✅ Request URL: http://localhost:8000/donations
✅ Status Code: 200 (성공) or 400 (실패)
✅ Request Headers: Cookie가 포함되어 있는지
✅ Response: 에러 메시지 확인
```

### 2. 쿠키 확인
```javascript
// 개발자도구 Console에서
console.log(document.cookie);
// 출력: "bodam_session=eyJhbGc..." 확인
```

### 3. API 응답 구조 확인
```typescript
// 백엔드 응답 형식 확인
{
  "items": [
    {
      "id": "uuid",
      "amount": 5000,
      "created_at": "2025-10-02T...",
      // ...
    }
  ],
  "total": 1,
  "page": 1
}
```

### 4. 데이터 매핑 확인
```typescript
// 백엔드 필드명과 프론트엔드 사용 필드명이 일치하는지 확인
const donationList = donations.items.map(d => ({
  id: d.id,
  amount: d.amount,
  date: d.created_at,  // ✅ created_at → date
  fireStation: d.fire_station?.name,  // ✅ 관계 데이터 접근
}));
```

## 일반적인 더미 데이터 제거 패턴

### 패턴 1: 하드코딩된 배열
```typescript
// ❌ Before
const data = [{ id: 1, name: 'test' }, { id: 2, name: 'test2' }];

// ✅ After
const [data, setData] = useState([]);
useEffect(() => {
  fetchDataFromAPI().then(setData);
}, []);
```

### 패턴 2: 하드코딩된 통계
```typescript
// ❌ Before
const totalAmount = 485000;

// ✅ After
const totalAmount = donationHistory.reduce((sum, d) => sum + d.amount, 0);
```

### 패턴 3: 하드코딩된 사용자 정보
```typescript
// ❌ Before
const userName = '홍길동';

// ✅ After
const userName = localStorage.getItem('userNickname') || '사용자';
```

## 앞으로 주의할 점

1. **새 컴포넌트 작성 시**
   - 처음부터 API 연동을 고려한 구조로 작성
   - 더미 데이터는 `const MOCK_DATA =` 형태로 명확히 표시
   - 개발 중에는 `const USE_MOCK = true` 플래그 사용

2. **API 설계 시**
   - 프론트엔드가 필요로 하는 데이터 구조 확인
   - 인증 필요 여부 명확히 문서화
   - 에러 응답 형식 통일 (`{ detail: string }`)

3. **상태 관리**
   - 로딩 상태(`isLoading`)와 에러 상태(`error`) 추가
   - 빈 데이터 처리 (0건일 때 UI)
   - 재시도 로직 고려

## 참고 자료

- [backend/src/api/donations.py](../../backend/src/api/donations.py) - 기부 API
- [frontend/src/lib/api.ts](../frontend/src/lib/api.ts) - API 클라이언트
- [backend/src/middleware/auth.py](../../backend/src/middleware/auth.py) - 인증 미들웨어
