# 빠른 시작 가이드: DB 및 HTTP 연결 풀 설정

**목적**: 연결 풀 설정을 빠르게 테스트하고 검증하는 가이드
**소요 시간**: 약 10분
**전제 조건**:
- Python 3.11+ 설치
- PostgreSQL 실행 중
- Docker (선택사항, 테스트용)

---

## 1단계: 의존성 설치

```bash
cd backend

# 기존 의존성 확인
pip list | grep -E "sqlalchemy|httpx|tenacity"

# 새로운 의존성 설치 (아직 없는 경우)
pip install httpx==0.25.0 tenacity==8.2.3

# SQLAlchemy는 이미 설치되어 있음 (2.0.23)
# asyncpg도 이미 설치되어 있음
```

---

## 2단계: 환경 변수 설정

`.env` 파일에 다음 설정 추가:

```bash
# DB 연결 풀 설정
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true
DB_POOL_TIMEOUT=0.4

# HTTP 연결 풀 설정
HTTP_MAX_CONNECTIONS=100
HTTP_MAX_KEEPALIVE_CONNECTIONS=20
HTTP_KEEPALIVE_EXPIRY=60.0

# HTTP 타임아웃 설정
HTTP_CONNECT_TIMEOUT=4.0
HTTP_READ_TIMEOUT=8.0
HTTP_WRITE_TIMEOUT=10.0
HTTP_POOL_TIMEOUT=10.0

# 결제 API 타임아웃 설정
HTTP_PAYMENT_CONNECT_TIMEOUT=180.0
HTTP_PAYMENT_READ_TIMEOUT=180.0

# 재시도 설정
RETRY_MAX_ATTEMPTS=3
RETRY_INTERVAL=4.0
RETRY_EXCLUDED_DOMAINS=api.tosspayments.com,pay.naver.com
```

---

## 3단계: DB 연결 풀 테스트

### 3.1 연결 풀 동작 확인

```bash
# Python 인터프리터 실행
python3

# 테스트 코드 실행
```

```python
import asyncio
from backend.src.database.connection import engine, SessionLocal

async def test_db_pool():
    """DB 연결 풀 기본 동작 테스트"""
    print(f"Pool size: {engine.pool.size()}")
    print(f"Checked out connections: {engine.pool.checkedout()}")

    # 10개 연결 동시 체크아웃 (pool_size 내에서)
    sessions = []
    for i in range(10):
        session = SessionLocal()
        sessions.append(session)
        print(f"Session {i+1} created")

    # 연결 풀 상태 확인
    print(f"After checkout - Pool size: {engine.pool.size()}")
    print(f"After checkout - Checked out: {engine.pool.checkedout()}")

    # 연결 반환
    for session in sessions:
        await session.close()

    print("모든 연결 반환 완료")

# 실행
asyncio.run(test_db_pool())
```

**예상 출력**:
```
Pool size: 10
Checked out connections: 0
Session 1 created
Session 2 created
...
After checkout - Pool size: 10
After checkout - Checked out: 10
모든 연결 반환 완료
```

### 3.2 pool_timeout 테스트

```python
async def test_pool_timeout():
    """pool_timeout 동작 테스트 (0.4초 대기)"""
    from sqlalchemy.exc import TimeoutError

    # pool_size(10) + max_overflow(20) = 총 30개 연결 모두 사용
    sessions = [SessionLocal() for _ in range(30)]

    try:
        # 31번째 연결 시도 (0.4초 대기 후 실패)
        extra_session = SessionLocal()
        print("예상치 못한 성공 - 연결 풀 설정 확인 필요")
    except TimeoutError as e:
        print(f"예상된 타임아웃 발생: {e}")
        print("pool_timeout 설정 정상 동작")
    finally:
        for session in sessions:
            await session.close()

# 실행
asyncio.run(test_pool_timeout())
```

**예상 출력**:
```
예상된 타임아웃 발생: QueuePool limit of size 10 overflow 20 reached, connection timed out, timeout 0.4
pool_timeout 설정 정상 동작
```

### 3.3 pool_pre_ping 테스트

```python
async def test_pool_pre_ping():
    """pool_pre_ping 동작 테스트 (연결 유효성 검증)"""
    async with SessionLocal() as session:
        # 첫 번째 쿼리 (연결 생성)
        result = await session.execute("SELECT 1")
        print(f"첫 번째 쿼리 결과: {result.scalar()}")

    # 연결 반환 (풀에 저장)

    # PostgreSQL 서버 재시작 시뮬레이션 (실제 환경에서는 수동으로 재시작)
    # docker restart bodam-postgres

    async with SessionLocal() as session:
        # pool_pre_ping이 끊어진 연결 감지하고 재생성
        try:
            result = await session.execute("SELECT 2")
            print(f"재연결 후 쿼리 결과: {result.scalar()}")
            print("pool_pre_ping 정상 동작 (자동 재연결)")
        except Exception as e:
            print(f"재연결 실패: {e}")

# 실행
asyncio.run(test_pool_pre_ping())
```

---

## 4단계: HTTP 연결 풀 테스트

### 4.1 HTTP 클라이언트 생성 확인

```python
import httpx
from backend.src.integrations.http_client import get_client

async def test_http_client():
    """HTTP 클라이언트 연결 풀 설정 확인"""
    async with get_client("general") as client:
        # 클라이언트 설정 확인
        print(f"Max connections: {client._limits.max_connections}")
        print(f"Max keepalive: {client._limits.max_keepalive_connections}")
        print(f"Timeout: {client.timeout}")

    async with get_client("payment") as client:
        print(f"Payment API timeout: {client.timeout}")

# 실행
asyncio.run(test_http_client())
```

**예상 출력**:
```
Max connections: 100
Max keepalive: 20
Timeout: Timeout(timeout=4.0, connect=4.0, read=8.0, write=10.0, pool=10.0)
Payment API timeout: Timeout(timeout=180.0, connect=180.0, read=180.0, write=180.0, pool=10.0)
```

### 4.2 재시도 정책 테스트

```python
from backend.src.integrations.retry_policy import fetch_with_retry
import httpx

async def test_retry_policy():
    """재시도 정책 동작 테스트"""
    async with get_client("general") as client:
        # 존재하지 않는 도메인 호출 (ConnectTimeout 발생)
        try:
            response = await fetch_with_retry(
                client, "GET", "http://nonexistent-domain-12345.com"
            )
        except httpx.ConnectTimeout as e:
            print(f"재시도 후 최종 실패: {e}")
            print("재시도 정책 정상 동작 (3회 시도 후 실패)")

# 실행
asyncio.run(test_retry_policy())
```

**예상 출력**:
```
재시도 1/3...
재시도 2/3...
재시도 3/3...
재시도 후 최종 실패: ConnectTimeout
재시도 정책 정상 동작 (3회 시도 후 실패)
```

### 4.3 멱등성 키 테스트

```python
import uuid

async def test_idempotency_key():
    """멱등성 키를 사용한 POST 요청 재시도 테스트"""
    async with get_client("general") as client:
        idempotency_key = str(uuid.uuid4())

        # POST 요청에 멱등성 키 추가
        response = await fetch_with_retry(
            client,
            "POST",
            "https://httpbin.org/post",
            headers={"idempotency-key": idempotency_key},
            json={"test": "data"}
        )

        print(f"Response status: {response.status_code}")
        print(f"Idempotency key: {idempotency_key}")

# 실행
asyncio.run(test_idempotency_key())
```

---

## 5단계: 부하 테스트 (K6)

### 5.1 K6 설치

```bash
# macOS
brew install k6

# Ubuntu/Debian
sudo apt-get install k6

# Windows
choco install k6
```

### 5.2 부하 테스트 스크립트

`tests/performance/connection_pool_load_test.js` 생성:

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '30s', target: 50 },   // 50 VUs로 램프업
    { duration: '1m', target: 100 },   // 100 VUs 유지
    { duration: '30s', target: 0 },    // 램프다운
  ],
  thresholds: {
    http_req_duration: ['p(95)<5000'],  // 95%가 5초 이내
    http_req_failed: ['rate<0.01'],     // 에러율 1% 미만
  },
};

export default function() {
  // DB 조회 API 호출 (DB 연결 풀 테스트)
  let res1 = http.get('http://localhost:8080/api/health');
  check(res1, { 'health check status is 200': (r) => r.status === 200 });

  // 외부 API 호출 시뮬레이션 (HTTP 연결 풀 테스트)
  let res2 = http.get('http://localhost:8080/api/external/test');
  check(res2, { 'external API status is 200': (r) => r.status === 200 });

  sleep(1);
}
```

### 5.3 부하 테스트 실행

```bash
# 백엔드 서버 실행
cd backend
uvicorn src.main:app --host 0.0.0.0 --port 8080

# 새 터미널에서 K6 테스트 실행
k6 run tests/performance/connection_pool_load_test.js
```

**예상 출력**:
```
scenarios: (100.00%) 1 scenario, 100 max VUs, 2m30s max duration
default: 50 iterations/s for 2m0s (gracefulStop: 30s)

✓ health check status is 200
✓ external API status is 200

checks.........................: 100.00% ✓ 12000 ✗ 0
http_req_duration..............: avg=150ms min=50ms med=120ms max=500ms p(95)=300ms
http_req_failed................: 0.00%   ✓ 0     ✗ 12000
```

---

## 6단계: 모니터링 메트릭 확인 (추후 구현)

현재는 로그로 확인, 추후 Prometheus + Grafana 연동:

```bash
# 백엔드 로그 확인
tail -f backend/logs/app.log | grep -E "pool|connection|retry"
```

**예상 로그**:
```json
{"timestamp": "2025-10-16T10:30:00", "level": "INFO", "message": "DB pool checked out", "pool_size": 10, "checked_out": 5}
{"timestamp": "2025-10-16T10:30:01", "level": "INFO", "message": "HTTP request", "method": "GET", "host": "api.example.com", "duration": 0.25}
{"timestamp": "2025-10-16T10:30:02", "level": "WARNING", "message": "HTTP retry", "attempt": 1, "reason": "ConnectTimeout"}
```

---

## 7단계: 검증 체크리스트

연결 풀 설정이 올바르게 동작하는지 확인:

### DB 연결 풀
- [ ] `engine.pool.size()` 가 10을 반환
- [ ] 30개 연결 동시 체크아웃 가능 (pool_size + max_overflow)
- [ ] 31번째 연결 시도 시 0.4초 후 TimeoutError 발생
- [ ] pool_pre_ping으로 끊어진 연결 자동 재생성

### HTTP 연결 풀
- [ ] 일반 API 클라이언트: connect=4s, read=8s
- [ ] 결제 API 클라이언트: connect=180s, read=180s
- [ ] max_connections=100, max_keepalive_connections=20 설정 확인

### 재시도 정책
- [ ] GET 요청: 연결 실패 시 최대 3회 시도 (최초 1회 + 재시도 2회)
- [ ] POST 요청 (멱등성 키 없음): 재시도 안 함
- [ ] POST 요청 (멱등성 키 있음): 재시도 함
- [ ] 결제 API: 재시도 안 함 (excluded_domains)
- [ ] 재시도 간격: 4초 고정

### 부하 테스트
- [ ] 100 VUs 부하 시 95% 요청이 5초 이내 응답
- [ ] 에러율 1% 미만 유지
- [ ] DB 연결 풀 타임아웃 없음
- [ ] HTTP 연결 풀 타임아웃 없음

---

## 트러블슈팅

### 문제 1: DB 연결 풀 타임아웃 발생
```
sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 20 reached
```

**해결**:
- `DB_POOL_SIZE` 또는 `DB_MAX_OVERFLOW` 증가
- 또는 `DB_POOL_TIMEOUT` 증가 (0.4초 → 1.0초)

### 문제 2: HTTP 재시도가 동작하지 않음
```
httpx.ConnectTimeout (재시도 없이 바로 실패)
```

**해결**:
- `fetch_with_retry()` 함수 사용 확인
- `RETRY_EXCLUDED_DOMAINS`에 해당 도메인이 없는지 확인
- POST 요청인 경우 `idempotency-key` 헤더 추가

### 문제 3: 결제 API 타임아웃
```
httpx.ReadTimeout after 180 seconds
```

**해결**:
- PG사 응답이 느린 경우 정상 동작 (180초는 일반적인 PG 타임아웃)
- PG사 상태 확인 또는 타임아웃 증가 고려

---

## 다음 단계

1. **모니터링 구현**: Prometheus + Grafana 연동 (추후)
2. **알람 설정**: AlertManager 연동 (추후)
3. **성능 튜닝**: 부하 테스트 결과 기반으로 pool_size 조정
4. **Circuit Breaker**: 추후 필요 시 추가 (tenacity 또는 pybreaker)

---

**문서 작성**: 2025-10-16
**검증 완료**: ❌ (구현 후 검증 필요)
