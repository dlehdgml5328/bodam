# 보담(BoDam) 플랫폼 빠른시작 가이드

## 개요
이 가이드는 보담 커피 기부 플랫폼의 핵심 기능을 검증하기 위한 E2E 테스트 시나리오를 제공합니다. 각 단계는 사용자 스토리를 기반으로 하며, 구현 완료 후 이 가이드를 실행하여 플랫폼이 올바르게 작동하는지 확인할 수 있습니다.

## 사전 준비

### 환경 설정
```bash
# 환경 변수 설정
export BODAM_API_URL="https://api.bodam.example"
export BODAM_FRONTEND_URL="https://app.bodam.example"
export TEST_USER_EMAIL="test@example.com"
export TEST_USER_PASSWORD="Test123!@#"
```

### 테스트 데이터
```bash
# 테스트용 소방서 데이터가 있는지 확인
curl $BODAM_API_URL/stations?limit=5
```

## 시나리오 1: 사용자 회원가입 및 로그인

### 1.1 회원가입
```bash
# 새 사용자 계정 생성
curl -X POST $BODAM_API_URL/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "'$TEST_USER_EMAIL'",
    "password": "'$TEST_USER_PASSWORD'",
    "name": "테스트 사용자",
    "phone": "01012345678"
  }'

# 예상 응답: 201 Created
# {
#   "user_id": "uuid",
#   "email": "test@example.com",
#   "message": "인증 이메일이 발송되었습니다"
# }
```

### 1.2 로그인
```bash
# 이메일/비밀번호로 로그인
LOGIN_RESPONSE=$(curl -X POST $BODAM_API_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "'$TEST_USER_EMAIL'",
    "password": "'$TEST_USER_PASSWORD'"
  }')

# JWT 토큰 추출
ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "로그인 성공: $ACCESS_TOKEN"
```

### 1.3 프로필 조회
```bash
# 내 정보 조회
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  $BODAM_API_URL/me

# 예상 응답: 사용자 정보와 기부 통계
```

## 시나리오 2: 소방서 검색 및 즐겨찾기

### 2.1 근처 소방서 검색
```bash
# 서울시청 좌표로 근처 소방서 검색
NEARBY_STATIONS=$(curl "$BODAM_API_URL/stations/nearby?lat=37.5665&lng=126.9780&radius=5000")

# 첫 번째 소방서 ID 추출
STATION_ID=$(echo $NEARBY_STATIONS | jq -r '.stations[0].id')
echo "선택된 소방서 ID: $STATION_ID"
```

### 2.2 소방서 상세 정보 조회
```bash
# 소방서 상세 정보
curl $BODAM_API_URL/stations/$STATION_ID

# 예상 응답: 소방서 정보, 기부 통계, 최근 기부 목록
```

### 2.3 즐겨찾기 추가
```bash
# 소방서를 즐겨찾기에 추가
curl -X POST $BODAM_API_URL/stations/$STATION_ID/favorites \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# 예상 응답: 201 Created
```

## 시나리오 3: 일시 기부 및 결제

### 3.1 기부 생성
```bash
# 10,000원 일시 기부 생성
DONATION_RESPONSE=$(curl -X POST $BODAM_API_URL/donations \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fire_station_id": "'$STATION_ID'",
    "amount": 10000,
    "type": "one_time",
    "message": "소방관들을 위한 따뜻한 커피 기부합니다!",
    "is_anonymous": false
  }')

# 기부 ID와 결제 URL 추출
DONATION_ID=$(echo $DONATION_RESPONSE | jq -r '.donation_id')
PAYMENT_URL=$(echo $DONATION_RESPONSE | jq -r '.payment_url')

echo "기부 ID: $DONATION_ID"
echo "결제 URL: $PAYMENT_URL"
```

### 3.2 결제 상태 확인 (수동)
```bash
# 브라우저에서 결제 URL 방문하여 테스트 결제 진행
echo "브라우저에서 결제를 진행하세요: $PAYMENT_URL"
echo "결제 완료 후 Enter를 눌러 계속..."
read

# 결제 완료 후 기부 상태 확인
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  $BODAM_API_URL/donations/$DONATION_ID

# 예상: status가 "completed"로 변경됨
```

### 3.3 영수증 다운로드
```bash
# PDF 영수증 다운로드
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  $BODAM_API_URL/donations/$DONATION_ID/receipt \
  --output receipt_$DONATION_ID.pdf

echo "영수증이 receipt_$DONATION_ID.pdf로 저장되었습니다"
```

## 시나리오 4: 정기 기부 설정

### 4.1 월간 정기 기부 생성
```bash
# 5,000원 월간 정기 기부
SUBSCRIPTION_RESPONSE=$(curl -X POST $BODAM_API_URL/donations \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fire_station_id": "'$STATION_ID'",
    "amount": 5000,
    "type": "recurring",
    "frequency": "monthly",
    "message": "매월 정기 기부로 지속적인 응원을 보냅니다"
  }')

SUBSCRIPTION_ID=$(echo $SUBSCRIPTION_RESPONSE | jq -r '.donation_id')
echo "정기 기부 ID: $SUBSCRIPTION_ID"
```

### 4.2 정기 기부 목록 조회
```bash
# 내 정기 기부 목록
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  $BODAM_API_URL/subscriptions

# 예상: 활성 정기 기부 목록
```

## 시나리오 5: 소방서 랭킹 및 사건 정보

### 5.1 기부자 랭킹 조회
```bash
# 소방서별 전체 기간 기부자 랭킹
curl $BODAM_API_URL/stations/$STATION_ID/rankings?period=all_time&limit=10

# 예상: 기부 금액순 상위 10명 랭킹
```

### 5.2 최근 화재 사건 조회
```bash
# 소방서 근처 최근 7일간 화재 사건
curl $BODAM_API_URL/stations/$STATION_ID/incidents?days=7

# 예상: AI가 분석한 화재 관련 뉴스 목록
```

## 시나리오 6: 알림 및 실시간 업데이트

### 6.1 WebSocket 연결 테스트
```javascript
// 브라우저 콘솔에서 실행
const ws = new WebSocket('wss://api.bodam.example/ws/notifications');

ws.onopen = function() {
    console.log('WebSocket 연결됨');
    // 인증 토큰 전송
    ws.send(JSON.stringify({
        type: 'auth',
        token: 'YOUR_ACCESS_TOKEN'
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('알림 수신:', data);
};

// 기부 완료, 화재 사건 알림 등이 실시간으로 수신되어야 함
```

### 6.2 내 알림 목록 조회
```bash
# 최근 알림 목록
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  $BODAM_API_URL/notifications?limit=20

# 예상: 기부 완료, 화재 사건 등의 알림 목록
```

## 시나리오 7: 관리자 기능 (관리자 계정 필요)

### 7.1 관리자 로그인
```bash
# 관리자 계정으로 로그인
ADMIN_LOGIN=$(curl -X POST $BODAM_API_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@bodam.example",
    "password": "AdminPassword123!"
  }')

ADMIN_TOKEN=$(echo $ADMIN_LOGIN | jq -r '.access_token')
```

### 7.2 AI 검토 대기 콘텐츠 확인
```bash
# 관리자 검토가 필요한 뉴스 콘텐츠
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  $BODAM_API_URL/admin/review-queue

# 예상: 신뢰도 점수 50-69인 콘텐츠 목록
```

### 7.3 환불 요청 관리
```bash
# 환불 요청 목록
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  $BODAM_API_URL/admin/refunds?status=pending

# 특정 환불 승인
curl -X POST $BODAM_API_URL/admin/refunds/REFUND_ID/approve \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## 성능 및 모니터링 검증

### API 응답 시간 테스트
```bash
# k6를 사용한 부하 테스트
cat > load-test.js << EOF
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 },
    { duration: '5m', target: 100 },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    'http_req_duration': ['p(95)<300'], // 95%ile < 300ms
    'http_req_failed': ['rate<0.01'],   // 실패율 < 1%
  },
};

export default function() {
  let response = http.get('$BODAM_API_URL/stations?limit=20');
  check(response, {
    'status is 200': (r) => r.status === 200,
  });
}
EOF

k6 run load-test.js
```

### 헬스체크 확인
```bash
# 서비스 상태 확인
curl $BODAM_API_URL/healthz
curl $BODAM_API_URL/readyz

# Prometheus 메트릭 확인
curl $BODAM_API_URL/metrics
```

## 검증 체크리스트

### 기능적 검증
- [ ] 사용자 회원가입/로그인 정상 작동
- [ ] 소방서 검색 및 즐겨찾기 기능
- [ ] 일시 기부 및 Toss 결제 연동
- [ ] 정기 기부 설정 및 관리
- [ ] 영수증 생성 및 다운로드
- [ ] 실시간 알림 (WebSocket)
- [ ] 기부자 랭킹 시스템
- [ ] AI 뉴스 분석 및 관리자 검토
- [ ] 환불 요청 및 처리

### 비기능적 검증
- [ ] API 응답시간 p95 < 300ms
- [ ] 에러율 < 1%
- [ ] 동시 사용자 1000명 처리
- [ ] 모든 API 엔드포인트 HTTPS
- [ ] JWT 토큰 보안 (HttpOnly 쿠키)
- [ ] CORS 정책 적용
- [ ] SQL 인젝션 방지
- [ ] 권한 분리 (BOLA 방지)

### 모니터링 검증
- [ ] Prometheus 메트릭 수집
- [ ] Grafana 대시보드 표시
- [ ] 알람 정책 작동
- [ ] 로그 구조화 및 집계
- [ ] 성능 모니터링 정상

이 빠른시작 가이드를 모두 실행하여 성공하면, 보담 플랫폼의 핵심 기능이 정상적으로 구현되었음을 확인할 수 있습니다.