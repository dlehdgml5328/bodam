# 연구 보고서: DB 커넥션 풀과 HTTP 커넥션 풀

**작성일**: 2025-10-16
**목적**: DB 및 HTTP 연결 풀 설정에 대한 기술 조사 및 설계 결정

---

## 1. SQLAlchemy Async Pool 연구

### 결정사항
```python
# backend/src/database/connection.py 설정
pool_size = 10                # 기본 연결 수
max_overflow = 20             # 추가 확장 연결 (총 최대 30개)
pool_recycle = 3600           # 1시간 후 연결 재활용
pool_pre_ping = True          # 연결 유효성 검증
pool_timeout = 0.4            # 대기 시간 (초)
```

### 근거

**pool_size = 10, max_overflow = 20**:
- 기본 10개 연결로 평상시 트래픽 처리
- 피크 시간에 최대 30개까지 확장 (10 + 20)
- PostgreSQL의 기본 max_connections (100)을 고려하면 충분한 여유
- 동시 요청 100개 처리 가능 (각 요청이 평균 50ms DB 작업 가정 시)
- 공식: 최소 연결 수 = (평균 동시 요청 수) × (평균 DB 작업 시간) / (응답 시간 목표)
  - 예: 100 × 0.05 / 5 = 1개 (최소)
  - 여유를 두고 10개로 시작, 피크 시 30개까지 확장

**pool_recycle = 3600초**:
- PostgreSQL의 기본 tcp_keepalives_idle (7200초)보다 짧게 설정
- 네트워크 방화벽의 idle timeout (보통 30분~1시간) 회피
- 연결이 끊긴 상태로 재사용되는 것을 방지

**pool_pre_ping = True**:
- 연결을 풀에서 꺼낼 때 `SELECT 1` 쿼리로 유효성 검증
- 오버헤드: 약 1~2ms (네트워크 latency)
- 장점: 끊어진 연결로 인한 에러 방지 (특히 재시작 후)
- 단점: 모든 요청마다 추가 쿼리 발생
- 결론: 안정성을 위해 활성화 (프로덕션 환경에서 필수)

**pool_timeout = 0.4초**:
- 연결 풀이 가득 찼을 때 새 연결을 기다리는 최대 시간
- 0.4초 이내에 연결을 얻지 못하면 TimeoutError 발생
- 빠른 실패(fail-fast)로 사용자 경험 개선
- 대기 큐가 쌓이는 것을 방지

### SQLAlchemy Pool Events (모니터링)

```python
from sqlalchemy import event
from prometheus_client import Gauge

# 메트릭 정의
db_pool_size = Gauge('db_pool_size', 'Current pool size')
db_pool_checked_out = Gauge('db_pool_checked_out', 'Checked out connections')
db_pool_overflow = Gauge('db_pool_overflow', 'Overflow connections')

@event.listens_for(engine.pool, "connect")
def receive_connect(dbapi_conn, connection_record):
    """새 연결 생성 시"""
    db_pool_size.inc()

@event.listens_for(engine.pool, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """연결 체크아웃 시"""
    db_pool_checked_out.inc()

@event.listens_for(engine.pool, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """연결 반환 시"""
    db_pool_checked_out.dec()

@event.listens_for(engine.pool, "close")
def receive_close(dbapi_conn, connection_record):
    """연결 종료 시"""
    db_pool_size.dec()
```

### 대안 검토

**대안 1: NullPool (연결 풀 미사용)**
- 장점: 메모리 사용량 최소화
- 단점: 매 요청마다 연결 생성/종료 (성능 저하)
- 결론: 기각 (성능이 중요한 웹 애플리케이션에 부적합)

**대안 2: StaticPool (단일 연결)**
- 장점: 가장 단순
- 단점: 동시 요청 처리 불가
- 결론: 기각 (동시성 필요)

**대안 3: pool_size = 5, max_overflow = 5 (더 작은 풀)**
- 장점: 메모리 절약
- 단점: 동시 요청 100개 처리 시 병목 가능성
- 결론: 기각 (성능 목표 달성 어려움)

### 참고 자료
- SQLAlchemy 2.0 공식 문서: Engine Configuration
- PostgreSQL 문서: Connection Management
- Best Practice: pool_size를 CPU 코어 수의 2~4배로 설정 (I/O bound 작업)

---

## 2. HTTP 클라이언트 연결 풀 연구

### 결정사항: **httpx 선택**

**httpx AsyncClient 설정**:
```python
# backend/src/integrations/http_client.py
import httpx

# 일반 API용 클라이언트
general_client = httpx.AsyncClient(
    limits=httpx.Limits(
        max_connections=100,      # 전체 최대 연결
        max_keepalive_connections=20,  # Keep-Alive 연결 유지
    ),
    timeout=httpx.Timeout(
        connect=4.0,              # 연결 타임아웃
        read=8.0,                 # 읽기 타임아웃
        write=10.0,               # 쓰기 타임아웃
        pool=10.0,                # 풀에서 연결 대기 타임아웃
    ),
)

# 결제 API용 클라이언트
payment_client = httpx.AsyncClient(
    limits=httpx.Limits(
        max_connections=20,
        max_keepalive_connections=10,
    ),
    timeout=httpx.Timeout(
        connect=180.0,            # 3분
        read=180.0,               # 3분
        write=180.0,
        pool=10.0,
    ),
)
```

### 근거

**httpx 선택 이유**:
1. **HTTP/2 지원**: aiohttp는 HTTP/1.1만 지원, httpx는 HTTP/2 지원
2. **requests-like API**: 친숙한 API (requests 라이브러리와 유사)
3. **타입 힌트 완벽 지원**: mypy와 호환성 우수
4. **동기/비동기 통합**: sync/async 모두 지원
5. **활발한 개발**: 최신 Python 버전 지원
6. **성능**: aiohttp와 비슷하거나 약간 우수 (벤치마크 결과)

**연결 풀 설정 근거**:
- **max_connections = 100**: 전체 최대 연결 수
  - 외부 API 호출이 많지 않은 경우 충분
  - 메모리: 연결당 약 5~10KB (총 500KB~1MB)
- **max_keepalive_connections = 20**: Keep-Alive 유지 연결
  - 자주 호출하는 API 호스트의 연결 재사용
  - HTTP Keep-Alive로 TCP 핸드셰이크 오버헤드 제거 (약 100ms 절약)
- **호스트당 제한**: httpx는 내부적으로 관리 (명시적 설정 불필요)

**타임아웃 설정 근거**:
- **일반 API (4초/8초)**:
  - connect=4초: 네트워크 연결 수립 시간
  - read=8초: 응답 읽기 시간
  - 총 최대 12초 (connect + read)
- **결제 API (180초)**:
  - PG사 응답이 느릴 수 있음 (승인/취소 처리)
  - 3분은 일반적인 PG 타임아웃 (토스페이먼츠, 네이버페이 등)
- **write=10초**: 요청 바디 전송 시간 (대용량 파일 업로드 가능)
- **pool=10초**: 연결 풀에서 대기 (소켓 타임아웃과 다름)

### 재시도 정책 구현

**tenacity 라이브러리 사용**:
```python
# backend/src/integrations/retry_policy.py
from tenacity import (
    retry,
    stop_after_attempt,
    wait_fixed,
    retry_if_exception_type,
)
import httpx

# 재시도 가능한 예외
RETRYABLE_EXCEPTIONS = (
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.NetworkError,
)

# 재시도 정책
@retry(
    stop=stop_after_attempt(3),  # 최초 1회 + 재시도 2회
    wait=wait_fixed(4),           # 4초 고정 간격
    retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
    reraise=True,
)
async def fetch_with_retry(client: httpx.AsyncClient, method: str, url: str, **kwargs):
    """재시도 가능한 HTTP 요청"""
    response = await client.request(method, url, **kwargs)
    response.raise_for_status()
    return response


# 멱등성 체크 데코레이터
def idempotent_only(func):
    """GET, PUT, DELETE만 재시도 허용 (POST는 멱등성 키 필요)"""
    async def wrapper(method: str, url: str, **kwargs):
        if method.upper() not in ["GET", "PUT", "DELETE"]:
            # POST는 idempotency_key 헤더 필요
            if "headers" not in kwargs or "idempotency-key" not in kwargs["headers"]:
                # 재시도 비활성화
                return await httpx.AsyncClient().request(method, url, **kwargs)
        return await func(method, url, **kwargs)
    return wrapper


# 결제 API 재시도 제외
def exclude_payment_api(url: str) -> bool:
    """결제 API는 재시도 안 함"""
    payment_domains = ["api.tosspayments.com", "pay.naver.com"]
    return any(domain in url for domain in payment_domains)
```

### 멱등성 보장 패턴

**Idempotency Key 헤더**:
```python
import uuid

# 멱등성 키 생성
idempotency_key = str(uuid.uuid4())

# POST 요청 시 헤더 추가
response = await client.post(
    "https://api.example.com/orders",
    json={"item_id": 123},
    headers={"idempotency-key": idempotency_key},
)
```

**서버 측 멱등성 체크** (백엔드 구현 필요):
```python
# 멱등성 키를 DB에 저장하고 중복 요청 감지
# TTL: 24시간 (Redis 또는 PostgreSQL)
```

### 연결 풀 모니터링

**httpx 연결 풀 메트릭**:
```python
from prometheus_client import Gauge

http_pool_connections = Gauge('http_pool_connections', 'Active HTTP connections')
http_pool_idle = Gauge('http_pool_idle', 'Idle HTTP connections')

# httpx는 내부 pool 상태를 직접 노출하지 않음
# 대안: 요청/응답 시 메트릭 수동 업데이트
```

### 대안 검토

**대안 1: aiohttp**
- 장점: 성능 우수 (약간), 오래된 검증된 라이브러리
- 단점: HTTP/2 미지원, API가 httpx보다 복잡, 타입 힌트 미흡
- 결론: 기각 (httpx가 최신 기술 스택에 적합)

**대안 2: urllib3 (동기)**
- 장점: 표준 라이브러리 기반
- 단점: async/await 미지원 (비동기 불가)
- 결론: 기각 (FastAPI는 async 필요)

**대안 3: requests (동기)**
- 장점: 가장 친숙한 API
- 단점: async 미지원
- 결론: 기각

**exponential backoff vs fixed delay**:
- exponential backoff: 1초 → 2초 → 4초 → 8초 (기하급수적 증가)
  - 장점: 서버 과부하 시 부담 감소
  - 단점: 재시도 간격이 너무 길어질 수 있음
- fixed delay: 4초 → 4초 (고정)
  - 장점: 예측 가능한 응답 시간
  - 단점: 서버 과부하 시 부담 유지
- **결정**: fixed delay 4초 (사용자 경험 우선, 재시도 2회로 제한)

### 참고 자료
- httpx 공식 문서: Advanced Usage - Timeouts, Connection Pooling
- tenacity 문서: Retrying Code
- RFC 7231: Idempotent Methods
- PG사 API 문서: 토스페이먼츠, 네이버페이 타임아웃 정책

---

## 3. 모니터링 & 메트릭 (추후 구현)

### Prometheus 메트릭 설계

**DB 연결 풀 메트릭**:
```python
db_pool_size = Gauge('db_pool_size', 'Current pool size')
db_pool_checked_out = Gauge('db_pool_checked_out', 'Checked out connections')
db_pool_overflow = Gauge('db_pool_overflow', 'Overflow connections')
db_pool_timeouts = Counter('db_pool_timeouts_total', 'Pool timeout errors')
```

**HTTP 연결 풀 메트릭**:
```python
http_requests_total = Counter('http_requests_total', 'Total HTTP requests', ['method', 'host', 'status'])
http_request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'host'])
http_retries_total = Counter('http_retries_total', 'Total HTTP retries', ['method', 'host', 'reason'])
```

**알람 규칙** (Prometheus AlertManager):
```yaml
# alertmanager.yml
groups:
  - name: connection_pool_alerts
    rules:
      - alert: HighDBPoolUsage
        expr: db_pool_checked_out / db_pool_size > 0.9
        for: 5m
        annotations:
          summary: "DB 연결 풀 사용률 90% 초과"

      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes / node_memory_MemTotal_bytes > 0.7
        for: 5m
        annotations:
          summary: "메모리 사용률 70% 초과"
```

---

## 4. 성능 테스트 계획 (추후 구현)

### K6 테스트 시나리오

**DB 연결 풀 부하 테스트**:
```javascript
// tests/performance/db_pool_load_test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '1m', target: 50 },   // 50 VUs
    { duration: '3m', target: 100 },  // 100 VUs
    { duration: '1m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<5000'],  // 95%가 5초 이내
    http_req_failed: ['rate<0.01'],     // 에러율 1% 미만
  },
};

export default function() {
  let res = http.get('http://localhost:8080/api/health');
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(1);
}
```

**HTTP 연결 풀 재시도 테스트**:
```javascript
// tests/performance/http_retry_test.js
export default function() {
  // 외부 API 호출 시뮬레이션
  let res = http.get('http://localhost:8080/api/external/test');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'retry count < 3': (r) => r.headers['X-Retry-Count'] <= 2,
  });
}
```

---

## 5. 결론 및 다음 단계

### 최종 결정사항 요약

1. **DB 커넥션 풀**: SQLAlchemy async engine
   - pool_size=10, max_overflow=20, pool_recycle=3600, pool_pre_ping=True, pool_timeout=0.4

2. **HTTP 커넥션 풀**: httpx AsyncClient
   - max_connections=100, max_keepalive_connections=20
   - 일반 API: connect=4s, read=8s
   - 결제 API: connect=180s, read=180s

3. **재시도 정책**: tenacity
   - 재시도 2회, 간격 4초 (fixed delay)
   - GET, PUT, DELETE (멱등성) 또는 idempotency key 있는 POST만 재시도
   - 결제 API 제외

4. **모니터링**: Prometheus + Grafana (추후 구현)
   - DB 연결 풀, HTTP 연결 풀 메트릭
   - 알람: 메모리 70% 초과, DB 풀 90% 사용

### Phase 1으로 진행 준비 완료
- 모든 NEEDS CLARIFICATION 해결됨
- 기술 스택 확정: SQLAlchemy 2.0 + httpx + tenacity
- 설정값 구체화 완료
