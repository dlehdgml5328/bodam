# 데이터 모델: DB 커넥션 풀과 HTTP 커넥션 풀

**작성일**: 2025-10-16
**목적**: 연결 풀 설정 및 모니터링을 위한 데이터 구조 정의

---

## 1. 설정 엔티티 (Configuration Entities)

### 1.1 DatabasePoolConfig

DB 연결 풀 설정을 관리하는 설정 객체입니다.

**필드**:
- `pool_size`: int = 10
  - 설명: 기본 연결 수
  - 제약: 1 이상, 100 이하
  - 기본값: 10

- `max_overflow`: int = 20
  - 설명: 추가 확장 가능 연결 수 (pool_size + max_overflow = 총 최대)
  - 제약: 0 이상, 100 이하
  - 기본값: 20

- `pool_recycle`: int = 3600
  - 설명: 연결 재활용 시간 (초)
  - 제약: 60 이상
  - 기본값: 3600 (1시간)

- `pool_pre_ping`: bool = True
  - 설명: 연결 유효성 검증 활성화
  - 기본값: True

- `pool_timeout`: float = 0.4
  - 설명: 연결 대기 타임아웃 (초)
  - 제약: 0.1 이상, 10.0 이하
  - 기본값: 0.4

**환경 변수 매핑**:
```bash
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true
DB_POOL_TIMEOUT=0.4
```

**관계**:
- SQLAlchemy `create_async_engine()` 함수의 인자로 전달됨

---

### 1.2 HttpClientConfig

HTTP 클라이언트 연결 풀 설정을 관리하는 설정 객체입니다.

**필드**:
- `max_connections`: int = 100
  - 설명: 전체 최대 연결 수
  - 제약: 1 이상, 1000 이하
  - 기본값: 100

- `max_keepalive_connections`: int = 20
  - 설명: Keep-Alive 유지 연결 수
  - 제약: 1 이상, max_connections 이하
  - 기본값: 20

- `keepalive_expiry`: float = 60.0
  - 설명: Keep-Alive 연결 만료 시간 (초)
  - 제약: 5.0 이상
  - 기본값: 60.0

**환경 변수 매핑**:
```bash
HTTP_MAX_CONNECTIONS=100
HTTP_MAX_KEEPALIVE_CONNECTIONS=20
HTTP_KEEPALIVE_EXPIRY=60.0
```

**관계**:
- httpx `AsyncClient` 생성 시 `limits` 인자로 전달됨

---

### 1.3 HttpTimeoutConfig

HTTP 요청의 타임아웃 설정을 관리하는 설정 객체입니다.

**필드**:
- `connect_timeout`: float = 4.0
  - 설명: 연결 타임아웃 (초)
  - 제약: 0.1 이상
  - 기본값: 4.0 (일반 API), 180.0 (결제 API)

- `read_timeout`: float = 8.0
  - 설명: 읽기 타임아웃 (초)
  - 제약: 0.1 이상
  - 기본값: 8.0 (일반 API), 180.0 (결제 API)

- `write_timeout`: float = 10.0
  - 설명: 쓰기 타임아웃 (초)
  - 제약: 0.1 이상
  - 기본값: 10.0

- `pool_timeout`: float = 10.0
  - 설명: 연결 풀에서 연결 대기 타임아웃 (초)
  - 제약: 0.1 이상
  - 기본값: 10.0

**프리셋**:
- `GENERAL_API`: connect=4.0, read=8.0, write=10.0, pool=10.0
- `PAYMENT_API`: connect=180.0, read=180.0, write=180.0, pool=10.0

**환경 변수 매핑**:
```bash
HTTP_CONNECT_TIMEOUT=4.0
HTTP_READ_TIMEOUT=8.0
HTTP_WRITE_TIMEOUT=10.0
HTTP_POOL_TIMEOUT=10.0
HTTP_PAYMENT_CONNECT_TIMEOUT=180.0
HTTP_PAYMENT_READ_TIMEOUT=180.0
```

**관계**:
- httpx `AsyncClient` 생성 시 `timeout` 인자로 전달됨

---

### 1.4 RetryPolicyConfig

재시도 정책 설정을 관리하는 설정 객체입니다.

**필드**:
- `max_attempts`: int = 3
  - 설명: 최대 시도 횟수 (최초 1회 + 재시도 2회)
  - 제약: 1 이상, 10 이하
  - 기본값: 3

- `retry_interval`: float = 4.0
  - 설명: 재시도 간격 (초, fixed delay)
  - 제약: 0.1 이상, 60.0 이하
  - 기본값: 4.0

- `retryable_methods`: list[str] = ["GET", "PUT", "DELETE"]
  - 설명: 재시도 허용 HTTP 메서드
  - 기본값: ["GET", "PUT", "DELETE"]

- `retryable_exceptions`: list[str] = ["ConnectTimeout", "ReadTimeout", "NetworkError"]
  - 설명: 재시도 허용 예외 타입
  - 기본값: httpx의 ConnectTimeout, ReadTimeout, NetworkError

- `excluded_domains`: list[str] = ["api.tosspayments.com", "pay.naver.com"]
  - 설명: 재시도 제외 도메인 (결제 API)
  - 기본값: 결제 PG사 도메인

**환경 변수 매핑**:
```bash
RETRY_MAX_ATTEMPTS=3
RETRY_INTERVAL=4.0
RETRY_EXCLUDED_DOMAINS=api.tosspayments.com,pay.naver.com
```

**관계**:
- tenacity `@retry` 데코레이터의 인자로 사용됨

---

## 2. 모니터링 엔티티 (Monitoring Entities)

### 2.1 PoolMetrics

연결 풀 상태를 추적하는 메트릭 객체입니다 (추후 구현).

**필드**:
- `pool_name`: str
  - 설명: 풀 식별자 ("db" 또는 "http")

- `pool_size`: int
  - 설명: 현재 풀 크기

- `checked_out`: int
  - 설명: 체크아웃된 연결 수

- `overflow`: int
  - 설명: 오버플로우 연결 수

- `timeouts_total`: int
  - 설명: 타임아웃 발생 횟수 (누적)

- `timestamp`: datetime
  - 설명: 메트릭 수집 시각

**수집 주기**: 10초마다
**저장소**: Prometheus (시계열 DB)
**보존 기간**: 30일

**관계**:
- Prometheus Gauge/Counter 메트릭으로 export됨

---

### 2.2 HttpRequestMetrics

HTTP 요청 메트릭을 추적하는 객체입니다 (추후 구현).

**필드**:
- `method`: str
  - 설명: HTTP 메서드 (GET, POST, PUT, DELETE)

- `host`: str
  - 설명: 요청 대상 호스트

- `status_code`: int
  - 설명: HTTP 응답 상태 코드

- `duration_seconds`: float
  - 설명: 요청 소요 시간 (초)

- `retry_count`: int
  - 설명: 재시도 횟수

- `error_type`: str | None
  - 설명: 에러 타입 (ConnectTimeout, ReadTimeout, NetworkError 등)

- `timestamp`: datetime
  - 설명: 요청 시각

**수집 방법**: 각 HTTP 요청마다 기록
**저장소**: Prometheus (시계열 DB)
**보존 기간**: 30일

**관계**:
- Prometheus Counter/Histogram 메트릭으로 export됨

---

### 2.3 AlertRule

알람 규칙을 정의하는 객체입니다 (추후 구현).

**필드**:
- `rule_name`: str
  - 설명: 알람 규칙 이름

- `condition`: str
  - 설명: Prometheus 쿼리 (PromQL)
  - 예: `db_pool_checked_out / db_pool_size > 0.9`

- `threshold`: float
  - 설명: 임계값

- `duration`: str
  - 설명: 조건 지속 시간 (예: "5m")

- `severity`: str
  - 설명: 심각도 (critical, warning, info)

- `annotations`: dict
  - 설명: 알람 메시지 템플릿

**사전 정의된 알람 규칙**:

1. **HighDBPoolUsage**:
   - 조건: `db_pool_checked_out / db_pool_size > 0.9`
   - 지속: 5분
   - 심각도: warning
   - 메시지: "DB 연결 풀 사용률 90% 초과"

2. **HighMemoryUsage**:
   - 조건: `process_resident_memory_bytes / node_memory_MemTotal_bytes > 0.7`
   - 지속: 5분
   - 심각도: warning
   - 메시지: "메모리 사용률 70% 초과"

3. **HighHttpErrorRate**:
   - 조건: `rate(http_requests_total{status=~"5.."}[5m]) > 0.05`
   - 지속: 5분
   - 심각도: critical
   - 메시지: "HTTP 5xx 에러율 5% 초과"

**관계**:
- Prometheus AlertManager로 전송됨
- Grafana 대시보드에서 시각화됨

---

## 3. 상태 전이 (State Transitions)

### 3.1 DB 연결 상태

```
[풀 초기화] → [연결 생성] → [대기 중]
                  ↓
              [체크아웃] → [사용 중] → [체크인] → [대기 중]
                  ↓                        ↓
              [타임아웃]              [유효성 검증 실패]
                  ↓                        ↓
              [에러 반환]              [연결 폐기] → [연결 생성]
```

**상태 설명**:
- **대기 중**: 풀에 반환된 상태, 재사용 가능
- **사용 중**: 체크아웃되어 쿼리 실행 중
- **타임아웃**: pool_timeout 초과 시 에러 발생
- **유효성 검증 실패**: pool_pre_ping으로 끊어진 연결 감지

---

### 3.2 HTTP 연결 상태

```
[연결 풀 초기화] → [연결 생성] → [Keep-Alive 대기]
                      ↓
                  [요청 전송] → [응답 수신] → [Keep-Alive 대기]
                      ↓              ↓
                  [타임아웃]      [에러 응답]
                      ↓              ↓
                  [재시도 체크] ←←←←←←
                      ↓
              [재시도 가능?]
                 ↙        ↘
            [예]          [아니오]
             ↓              ↓
        [4초 대기]      [에러 반환]
             ↓
        [요청 전송]
```

**상태 설명**:
- **Keep-Alive 대기**: 연결 유지 상태, 재사용 가능
- **재시도 체크**: 멱등성, 도메인, 예외 타입 확인
- **4초 대기**: 고정 간격 재시도 (최대 2회)

---

## 4. 검증 규칙 (Validation Rules)

### 4.1 설정 검증

**DatabasePoolConfig**:
- `pool_size + max_overflow <= PostgreSQL max_connections`
- `pool_recycle < PostgreSQL tcp_keepalives_idle`
- `pool_timeout > 0.1` (너무 짧으면 항상 타임아웃)

**HttpClientConfig**:
- `max_keepalive_connections <= max_connections`
- `keepalive_expiry >= 5.0` (너무 짧으면 재연결 오버헤드)

**HttpTimeoutConfig**:
- `connect_timeout < read_timeout` (일반적으로)
- `read_timeout + write_timeout < 전체 응답 시간 목표 (5초)`
- 결제 API는 예외 (180초)

**RetryPolicyConfig**:
- `max_attempts >= 1`
- `retry_interval * max_attempts < 전체 응답 시간 목표`
  - 예: 4초 × 3회 = 12초 (5초 목표 초과, 하지만 일부 API에서 허용)

---

## 5. 데이터 흐름 (Data Flow)

### 5.1 DB 연결 풀 사용 흐름

```
[FastAPI 요청] → [get_session() 의존성]
                       ↓
                 [SessionLocal() 호출]
                       ↓
                 [engine.connect()]
                       ↓
              [풀에서 연결 체크아웃]
              (pool_timeout 대기)
                       ↓
              [pool_pre_ping 검증]
                       ↓
              [쿼리 실행]
                       ↓
              [session.commit()]
                       ↓
              [연결 반환 (체크인)]
                       ↓
              [응답 반환]
```

**에러 핸들링**:
- `TimeoutError`: pool_timeout 초과 → 503 Service Unavailable
- `OperationalError`: DB 연결 실패 → 500 Internal Server Error
- `IntegrityError`: DB 제약 위반 → 400 Bad Request

---

### 5.2 HTTP 연결 풀 사용 흐름

```
[외부 API 호출 필요] → [http_client.get_client(api_type)]
                              ↓
                       [AsyncClient 선택]
                       (general or payment)
                              ↓
                       [fetch_with_retry() 호출]
                              ↓
                    [재시도 정책 적용]
                    (tenacity 데코레이터)
                              ↓
                       [httpx.request()]
                              ↓
                    [연결 풀에서 연결 가져오기]
                    (Keep-Alive 재사용)
                              ↓
                       [요청 전송]
                              ↓
                       [응답 수신]
                              ↓
               [에러 발생?] ←←← [재시도 체크]
                 ↙        ↘
            [예]          [아니오]
             ↓              ↓
        [4초 대기]      [응답 반환]
             ↓
        [재시도]
```

**에러 핸들링**:
- `ConnectTimeout`: 재시도 (최대 2회)
- `ReadTimeout`: 재시도 (최대 2회)
- `NetworkError`: 재시도 (최대 2회)
- `HTTPStatusError` (4xx, 5xx): 재시도 안 함 (클라이언트/서버 에러)

---

## 6. 요약

**설정 엔티티**:
1. DatabasePoolConfig: DB 연결 풀 설정
2. HttpClientConfig: HTTP 연결 풀 설정
3. HttpTimeoutConfig: 타임아웃 설정
4. RetryPolicyConfig: 재시도 정책 설정

**모니터링 엔티티** (추후 구현):
1. PoolMetrics: 연결 풀 메트릭
2. HttpRequestMetrics: HTTP 요청 메트릭
3. AlertRule: 알람 규칙

**상태 전이**:
1. DB 연결: 대기 → 사용 → 반환 → 대기
2. HTTP 연결: Keep-Alive → 요청 → 응답 → Keep-Alive

**검증 규칙**:
- 설정값 범위 검증
- PostgreSQL 서버 설정과의 호환성 검증
- 성능 목표와의 일관성 검증
