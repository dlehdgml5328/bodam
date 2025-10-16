# Tasks: DB 커넥션 풀과 HTTP 커넥션 풀 설정

**Input**: 설계 문서 from `/home/eugene/bodam/specs/003-db-http/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. plan.md 로드
   → 기술 스택 추출: Python 3.11+, SQLAlchemy 2.0, httpx 0.25+, tenacity
   → 프로젝트 구조: backend/ (web application)
2. 설계 문서 로드:
   → data-model.md: 4개 설정 엔티티 추출
   → contracts/: 2개 계약 파일 (db-pool-config, http-client-config)
   → quickstart.md: 7단계 테스트 시나리오
3. 태스크 생성:
   → 환경 준비 (3개)
   → Config 설정 (1개, 3개 엔티티)
   → Contract tests (3개) [P]
   → DB 연결 풀 구현 (4개)
   → HTTP 클라이언트 구현 (5개)
   → 통합 및 리팩토링 (4개)
   → 부하 테스트 (3개)
   → 문서화 (3개)
4. TDD 규칙 적용:
   → Tests before implementation
   → 다른 파일 = [P] 마크
   → 같은 파일 = 순차 실행
5. 총 28개 태스크 번호 부여 (T001-T028)
6. 의존성 그래프 생성
7. 병렬 실행 예시 생성
8. 검증: 모든 계약에 테스트 있는지 확인
9. 반환: SUCCESS (태스크 실행 준비 완료)
```

---

## Format: `[ID] [P?] 설명`
- **[P]**: 병렬 실행 가능 (다른 파일, 의존성 없음)
- 각 태스크에 정확한 파일 경로 포함

## Path Conventions
이 프로젝트는 **web application** 구조를 사용합니다:
- 백엔드: `backend/src/`, `backend/tests/`
- 프론트엔드: `frontend/src/` (이 기능에서는 수정 없음)

---

## Phase 3.1: 환경 준비

### T001: 의존성 추가 및 설치
**파일**: `backend/requirements.txt` 또는 `backend/pyproject.toml`
**설명**: httpx, tenacity 패키지를 의존성 파일에 추가하고 설치합니다.

**세부 작업**:
1. `backend/requirements.txt`에 추가:
   ```
   httpx==0.25.2
   tenacity==8.2.3
   ```
2. 설치 실행:
   ```bash
   cd backend
   pip install httpx==0.25.2 tenacity==8.2.3
   ```
3. 기존 패키지 확인:
   - SQLAlchemy 2.0+ (이미 설치됨)
   - asyncpg (이미 설치됨)
   - pytest, pytest-asyncio (이미 설치됨)

**검증**:
```bash
pip list | grep -E "httpx|tenacity"
```

**예상 출력**:
```
httpx                    0.25.2
tenacity                 8.2.3
```

---

### T002: 환경 변수 예시 파일 업데이트
**파일**: `backend/.env.example`
**설명**: 새로운 연결 풀 설정 환경 변수를 .env.example에 추가합니다.

**세부 작업**:
1. `backend/.env.example` 파일 열기
2. 다음 섹션 추가:
   ```bash
   # === DB 연결 풀 설정 ===
   DB_POOL_SIZE=10
   DB_MAX_OVERFLOW=20
   DB_POOL_RECYCLE=3600
   DB_POOL_PRE_PING=true
   DB_POOL_TIMEOUT=0.4

   # === HTTP 연결 풀 설정 ===
   HTTP_MAX_CONNECTIONS=100
   HTTP_MAX_KEEPALIVE_CONNECTIONS=20
   HTTP_KEEPALIVE_EXPIRY=60.0

   # === HTTP 타임아웃 설정 ===
   HTTP_CONNECT_TIMEOUT=4.0
   HTTP_READ_TIMEOUT=8.0
   HTTP_WRITE_TIMEOUT=10.0
   HTTP_POOL_TIMEOUT=10.0

   # === 결제 API 타임아웃 설정 ===
   HTTP_PAYMENT_CONNECT_TIMEOUT=180.0
   HTTP_PAYMENT_READ_TIMEOUT=180.0

   # === 재시도 설정 ===
   RETRY_MAX_ATTEMPTS=3
   RETRY_INTERVAL=4.0
   RETRY_EXCLUDED_DOMAINS=api.tosspayments.com,pay.naver.com
   ```

**검증**: `.env.example` 파일에 모든 환경 변수가 추가되었는지 확인

---

### T003: 로컬 환경 변수 파일 생성
**파일**: `backend/.env` (로컬 전용, Git에 커밋하지 않음)
**설명**: .env.example을 복사하여 .env 파일을 생성하고 로컬 환경에 맞게 수정합니다.

**세부 작업**:
```bash
cd backend
cp .env.example .env
```

**검증**: `backend/.env` 파일이 생성되고 `.gitignore`에 `.env`가 포함되어 있는지 확인

---

## Phase 3.2: Config 설정 추가

### T004: config.py에 연결 풀 설정 필드 추가
**파일**: `backend/src/config.py`
**설명**: DB 연결 풀, HTTP 연결 풀, 재시도 정책 설정을 config.py에 추가합니다.

**세부 작업**:
1. `backend/src/config.py`의 `Settings` 클래스에 다음 필드 추가:

```python
# DB 연결 풀 설정
db_pool_size: int = 10
db_max_overflow: int = 20
db_pool_recycle: int = 3600
db_pool_pre_ping: bool = True
db_pool_timeout: float = 0.4

# HTTP 연결 풀 설정
http_max_connections: int = 100
http_max_keepalive_connections: int = 20
http_keepalive_expiry: float = 60.0

# HTTP 타임아웃 설정 (일반 API)
http_connect_timeout: float = 4.0
http_read_timeout: float = 8.0
http_write_timeout: float = 10.0
http_pool_timeout: float = 10.0

# HTTP 타임아웃 설정 (결제 API)
http_payment_connect_timeout: float = 180.0
http_payment_read_timeout: float = 180.0

# 재시도 설정
retry_max_attempts: int = 3
retry_interval: float = 4.0
retry_excluded_domains: str = "api.tosspayments.com,pay.naver.com"
```

2. 타입 힌트 추가 확인 (`from typing import Optional` 등)

**검증**:
```python
from backend.src.config import settings
assert settings.db_pool_size == 10
assert settings.http_max_connections == 100
assert settings.retry_max_attempts == 3
```

---

## Phase 3.3: TDD - Contract Tests 작성 (병렬 실행 가능) ⚠️ 반드시 구현 전에 완료

**중요**: 이 테스트들은 **반드시 실패해야** 합니다. 구현 코드가 없으므로 당연히 실패합니다.

### T005 [P]: DB 연결 풀 Contract Test 작성
**파일**: `backend/tests/contract/test_db_pool_contract.py` (신규)
**설명**: DB 연결 풀 설정이 계약대로 동작하는지 검증하는 contract test를 작성합니다.

**세부 작업**:
1. `backend/tests/contract/` 디렉토리 생성 (없으면)
2. `test_db_pool_contract.py` 파일 생성
3. 다음 테스트 작성:

```python
"""DB 연결 풀 Contract Tests

계약서: specs/003-db-http/contracts/db-pool-config.yaml
"""
import pytest
from sqlalchemy.exc import TimeoutError
from backend.src.database.connection import engine, SessionLocal


class TestDBPoolContract:
    """DB 연결 풀 설정 계약 검증"""

    def test_pool_size_configuration(self):
        """pool_size와 max_overflow 설정이 올바른지 검증"""
        assert engine.pool.size() == 10, "pool_size는 10이어야 함"
        # max_overflow는 engine.pool에서 직접 확인 불가, 설정값 확인
        from backend.src.config import settings
        assert settings.db_max_overflow == 20

    @pytest.mark.asyncio
    async def test_pool_timeout_behavior(self):
        """pool_timeout 설정이 0.4초로 동작하는지 검증"""
        # 모든 연결 소진 (pool_size + max_overflow = 30개)
        sessions = [SessionLocal() for _ in range(30)]

        # 31번째 연결 시도 - 0.4초 후 타임아웃 발생해야 함
        import time
        start = time.time()
        try:
            extra_session = SessionLocal()
            pytest.fail("31번째 연결이 성공하면 안 됨")
        except TimeoutError:
            elapsed = time.time() - start
            assert 0.3 < elapsed < 0.6, f"타임아웃이 {elapsed}초에 발생 (예상: 0.4초)"
        finally:
            for session in sessions:
                await session.close()

    @pytest.mark.asyncio
    async def test_pool_pre_ping_enabled(self):
        """pool_pre_ping이 활성화되어 있는지 검증"""
        from backend.src.config import settings
        assert settings.db_pool_pre_ping is True

        # 연결 생성 후 유효성 검증 (pool_pre_ping이 SELECT 1 실행)
        async with SessionLocal() as session:
            result = await session.execute("SELECT 1")
            assert result.scalar() == 1

    def test_pool_recycle_configuration(self):
        """pool_recycle이 3600초로 설정되어 있는지 검증"""
        from backend.src.config import settings
        assert settings.db_pool_recycle == 3600
```

**실행 및 검증** (실패해야 정상):
```bash
cd backend
pytest tests/contract/test_db_pool_contract.py -v
```

**예상 결과**: 모든 테스트 **실패** (아직 구현 안 됨)

---

### T006 [P]: HTTP 연결 풀 Contract Test 작성
**파일**: `backend/tests/contract/test_http_pool_contract.py` (신규)
**설명**: HTTP 클라이언트 연결 풀 설정이 계약대로 동작하는지 검증하는 contract test를 작성합니다.

**세부 작업**:
1. `test_http_pool_contract.py` 파일 생성
2. 다음 테스트 작성:

```python
"""HTTP 연결 풀 Contract Tests

계약서: specs/003-db-http/contracts/http-client-config.yaml
"""
import pytest
from backend.src.integrations.http_client import get_client


class TestHttpPoolContract:
    """HTTP 클라이언트 연결 풀 설정 계약 검증"""

    @pytest.mark.asyncio
    async def test_general_client_configuration(self):
        """일반 API 클라이언트 설정 검증"""
        async with get_client("general") as client:
            # 연결 풀 설정 확인
            assert client._limits.max_connections == 100
            assert client._limits.max_keepalive_connections == 20

            # 타임아웃 설정 확인
            assert client.timeout.connect == 4.0
            assert client.timeout.read == 8.0
            assert client.timeout.write == 10.0
            assert client.timeout.pool == 10.0

    @pytest.mark.asyncio
    async def test_payment_client_configuration(self):
        """결제 API 클라이언트 설정 검증"""
        async with get_client("payment") as client:
            # 타임아웃이 180초로 설정되어 있는지 확인
            assert client.timeout.connect == 180.0
            assert client.timeout.read == 180.0
            assert client.timeout.write == 180.0

    @pytest.mark.asyncio
    async def test_keepalive_expiry_configuration(self):
        """Keep-Alive 만료 시간 설정 검증"""
        from backend.src.config import settings
        assert settings.http_keepalive_expiry == 60.0
```

**실행 및 검증** (실패해야 정상):
```bash
pytest tests/contract/test_http_pool_contract.py -v
```

**예상 결과**: 모든 테스트 **실패** (아직 구현 안 됨)

---

### T007 [P]: 재시도 정책 Contract Test 작성
**파일**: `backend/tests/contract/test_retry_policy_contract.py` (신규)
**설명**: 재시도 정책이 계약대로 동작하는지 검증하는 contract test를 작성합니다.

**세부 작업**:
1. `test_retry_policy_contract.py` 파일 생성
2. 다음 테스트 작성:

```python
"""재시도 정책 Contract Tests

계약서: specs/003-db-http/contracts/http-client-config.yaml (재시도_정책)
"""
import pytest
import httpx
from unittest.mock import AsyncMock, patch
from backend.src.integrations.retry_policy import fetch_with_retry
from backend.src.integrations.http_client import get_client


class TestRetryPolicyContract:
    """재시도 정책 설정 계약 검증"""

    @pytest.mark.asyncio
    async def test_retry_on_connect_timeout(self):
        """ConnectTimeout 발생 시 재시도하는지 검증 (최대 3회 시도)"""
        async with get_client("general") as client:
            # 항상 ConnectTimeout 발생하도록 mock
            with patch.object(client, 'request', side_effect=httpx.ConnectTimeout("Timeout")):
                with pytest.raises(httpx.ConnectTimeout):
                    await fetch_with_retry(client, "GET", "http://example.com")

                # 3회 시도 확인 (최초 1회 + 재시도 2회)
                assert client.request.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_interval_is_4_seconds(self):
        """재시도 간격이 4초인지 검증"""
        from backend.src.config import settings
        assert settings.retry_interval == 4.0

    @pytest.mark.asyncio
    async def test_no_retry_for_payment_api(self):
        """결제 API 도메인은 재시도하지 않는지 검증"""
        async with get_client("general") as client:
            payment_url = "https://api.tosspayments.com/v1/payments"

            with patch.object(client, 'request', side_effect=httpx.ConnectTimeout("Timeout")):
                with pytest.raises(httpx.ConnectTimeout):
                    await fetch_with_retry(client, "GET", payment_url)

                # 1회만 시도해야 함 (재시도 없음)
                assert client.request.call_count == 1

    @pytest.mark.asyncio
    async def test_no_retry_for_http_status_errors(self):
        """HTTP 4xx/5xx 에러는 재시도하지 않는지 검증"""
        async with get_client("general") as client:
            # 500 에러 응답 mock
            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Server Error", request=None, response=mock_response
            )

            with patch.object(client, 'request', return_value=mock_response):
                with pytest.raises(httpx.HTTPStatusError):
                    await fetch_with_retry(client, "GET", "http://example.com")

                # 1회만 시도해야 함 (재시도 없음)
                assert client.request.call_count == 1
```

**실행 및 검증** (실패해야 정상):
```bash
pytest tests/contract/test_retry_policy_contract.py -v
```

**예상 결과**: 모든 테스트 **실패** (아직 구현 안 됨)

---

## Phase 3.4: DB 연결 풀 구현

### T008: connection.py에 연결 풀 설정 적용
**파일**: `backend/src/database/connection.py` (수정)
**설명**: SQLAlchemy async engine에 연결 풀 설정을 추가합니다.

**세부 작업**:
1. `backend/src/database/connection.py` 파일 열기
2. 기존 `create_async_engine()` 호출 부분을 다음과 같이 수정:

```python
"""Async SQLAlchemy database session management with connection pooling."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from backend.src.config import settings

DATABASE_URL = settings.database_url

# DB 연결 풀 설정 적용
engine = create_async_engine(
    DATABASE_URL,
    future=True,
    echo=False,
    # 연결 풀 설정
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=settings.db_pool_pre_ping,
    pool_timeout=settings.db_pool_timeout,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@asynccontextmanager
async def session_scope() -> AsyncSession:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_session() -> AsyncSession:
    async with session_scope() as session:
        yield session


__all__ = ["engine", "SessionLocal", "session_scope", "get_session"]
```

**검증**:
```bash
pytest tests/contract/test_db_pool_contract.py::TestDBPoolContract::test_pool_size_configuration -v
```

**예상 결과**: 테스트 **통과**

---

### T009: pool_metrics.py 스텁 생성 (추후 구현 표시)
**파일**: `backend/src/database/pool_metrics.py` (신규)
**설명**: 연결 풀 모니터링 메트릭 수집을 위한 스텁 파일을 생성합니다 (추후 Prometheus 연동 시 구현).

**세부 작업**:
1. `backend/src/database/pool_metrics.py` 파일 생성
2. 다음 스텁 코드 작성:

```python
"""DB 연결 풀 메트릭 수집 (추후 구현)

TODO: Prometheus + Grafana 연동 시 구현
- SQLAlchemy pool events 연결
- Gauge/Counter 메트릭 정의
- /metrics 엔드포인트 연동
"""

# TODO: Prometheus 클라이언트 import
# from prometheus_client import Gauge, Counter

# TODO: 메트릭 정의
# db_pool_size = Gauge('db_pool_size', 'Current pool size')
# db_pool_checked_out = Gauge('db_pool_checked_out', 'Checked out connections')
# db_pool_overflow = Gauge('db_pool_overflow', 'Overflow connections')
# db_pool_timeouts = Counter('db_pool_timeouts_total', 'Pool timeout errors')


def setup_pool_metrics(engine):
    """DB 연결 풀 메트릭 이벤트 리스너 설정 (추후 구현)

    Args:
        engine: SQLAlchemy async engine

    TODO: SQLAlchemy pool events 연결
    - connect: 새 연결 생성 시
    - checkout: 연결 체크아웃 시
    - checkin: 연결 반환 시
    - close: 연결 종료 시
    """
    pass
    # TODO: event.listens_for(engine.pool, "connect") 등록
    # TODO: event.listens_for(engine.pool, "checkout") 등록
    # TODO: event.listens_for(engine.pool, "checkin") 등록
    # TODO: event.listens_for(engine.pool, "close") 등록
```

**검증**: 파일이 생성되고 import 가능한지 확인
```python
from backend.src.database.pool_metrics import setup_pool_metrics
```

---

### T010: DB 연결 풀 Contract Test 실행 및 통과 확인
**파일**: `backend/tests/contract/test_db_pool_contract.py` (실행)
**설명**: T008에서 구현한 DB 연결 풀 설정이 contract test를 통과하는지 확인합니다.

**세부 작업**:
```bash
cd backend
pytest tests/contract/test_db_pool_contract.py -v
```

**예상 결과**: 모든 테스트 **통과** ✅

**실패 시 조치**:
- T008의 설정값 확인
- .env 파일의 환경 변수 확인
- PostgreSQL 서버 실행 확인

---

### T011: DB 연결 풀 Integration Test 작성 및 실행
**파일**: `backend/tests/integration/test_db_pool_integration.py` (신규)
**설명**: DB 연결 풀이 실제 부하 상황에서 올바르게 동작하는지 검증하는 integration test를 작성합니다.

**세부 작업**:
1. `backend/tests/integration/` 디렉토리 생성 (없으면)
2. `test_db_pool_integration.py` 파일 생성
3. 다음 테스트 작성:

```python
"""DB 연결 풀 Integration Tests

실제 DB 연결로 연결 풀 동작 검증
"""
import pytest
import asyncio
from sqlalchemy.exc import TimeoutError
from backend.src.database.connection import SessionLocal, engine


class TestDBPoolIntegration:
    """DB 연결 풀 통합 테스트"""

    @pytest.mark.asyncio
    async def test_concurrent_queries_within_pool_size(self):
        """pool_size(10) 내에서 동시 쿼리 실행 성공"""
        async def run_query(i):
            async with SessionLocal() as session:
                result = await session.execute(f"SELECT {i} as num")
                return result.scalar()

        # 10개 동시 쿼리 (pool_size 내)
        results = await asyncio.gather(*[run_query(i) for i in range(10)])
        assert results == list(range(10))

    @pytest.mark.asyncio
    async def test_concurrent_queries_with_overflow(self):
        """pool_size(10) 초과 시 max_overflow(20) 내에서 확장"""
        async def run_query(i):
            async with SessionLocal() as session:
                await asyncio.sleep(0.1)  # 약간 지연
                result = await session.execute(f"SELECT {i} as num")
                return result.scalar()

        # 25개 동시 쿼리 (pool_size + overflow 일부 사용)
        results = await asyncio.gather(*[run_query(i) for i in range(25)])
        assert len(results) == 25

    @pytest.mark.asyncio
    async def test_pool_timeout_on_exhaustion(self):
        """모든 연결 소진 시 pool_timeout 발생"""
        # 30개 세션 생성 (pool_size + max_overflow)
        sessions = [SessionLocal() for _ in range(30)]

        try:
            # 31번째 연결 시도 - 타임아웃 발생해야 함
            with pytest.raises(TimeoutError):
                extra = SessionLocal()
        finally:
            for session in sessions:
                await session.close()

    @pytest.mark.asyncio
    async def test_pool_connection_reuse(self):
        """연결 재사용 확인 (체크인 후 다시 체크아웃)"""
        # 첫 번째 연결
        async with SessionLocal() as session1:
            result1 = await session1.execute("SELECT 1")
            assert result1.scalar() == 1

        # 두 번째 연결 (첫 번째 연결이 풀로 반환되어 재사용됨)
        async with SessionLocal() as session2:
            result2 = await session2.execute("SELECT 2")
            assert result2.scalar() == 2

        # 풀 크기 확인 (연결이 재사용되므로 크기 유지)
        assert engine.pool.size() <= 10
```

4. 테스트 실행:
```bash
pytest tests/integration/test_db_pool_integration.py -v
```

**예상 결과**: 모든 테스트 **통과** ✅

---

## Phase 3.5: HTTP 클라이언트 구현

### T012 [P]: http_client.py 생성 (AsyncClient 팩토리)
**파일**: `backend/src/integrations/http_client.py` (신규)
**설명**: httpx AsyncClient를 생성하는 팩토리 함수를 구현합니다.

**세부 작업**:
1. `backend/src/integrations/http_client.py` 파일 생성
2. 다음 코드 작성:

```python
"""HTTP 클라이언트 팩토리

httpx AsyncClient를 연결 풀 설정과 함께 생성합니다.
"""
from typing import Literal
import httpx
from backend.src.config import settings


def get_client(api_type: Literal["general", "payment"] = "general") -> httpx.AsyncClient:
    """API 타입에 맞는 httpx AsyncClient 반환

    Args:
        api_type: "general" (일반 API) 또는 "payment" (결제 API)

    Returns:
        httpx.AsyncClient: 연결 풀과 타임아웃이 설정된 클라이언트

    Examples:
        >>> async with get_client("general") as client:
        ...     response = await client.get("https://api.example.com/data")

        >>> async with get_client("payment") as client:
        ...     response = await client.post("https://api.tosspayments.com/v1/payments")
    """
    # 연결 풀 설정
    limits = httpx.Limits(
        max_connections=settings.http_max_connections,
        max_keepalive_connections=settings.http_max_keepalive_connections,
        keepalive_expiry=settings.http_keepalive_expiry,
    )

    # 타임아웃 설정 (API 타입에 따라 다름)
    if api_type == "payment":
        timeout = httpx.Timeout(
            connect=settings.http_payment_connect_timeout,
            read=settings.http_payment_read_timeout,
            write=settings.http_payment_read_timeout,  # 결제 API는 read와 동일
            pool=settings.http_pool_timeout,
        )
    else:  # general
        timeout = httpx.Timeout(
            connect=settings.http_connect_timeout,
            read=settings.http_read_timeout,
            write=settings.http_write_timeout,
            pool=settings.http_pool_timeout,
        )

    # AsyncClient 생성
    return httpx.AsyncClient(
        limits=limits,
        timeout=timeout,
        http2=True,  # HTTP/2 지원
    )


__all__ = ["get_client"]
```

**검증**:
```python
from backend.src.integrations.http_client import get_client

async with get_client("general") as client:
    assert client._limits.max_connections == 100
```

---

### T013 [P]: retry_policy.py 생성 (tenacity 데코레이터)
**파일**: `backend/src/integrations/retry_policy.py` (신규)
**설명**: tenacity를 사용한 재시도 정책을 구현합니다.

**세부 작업**:
1. `backend/src/integrations/retry_policy.py` 파일 생성
2. 다음 코드 작성:

```python
"""재시도 정책

tenacity를 사용하여 HTTP 요청 재시도 로직을 구현합니다.
"""
from typing import Any
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_fixed,
    retry_if_exception_type,
)
from backend.src.config import settings


# 재시도 가능한 예외 타입
RETRYABLE_EXCEPTIONS = (
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.NetworkError,
)


def is_excluded_domain(url: str) -> bool:
    """재시도 제외 도메인인지 확인

    Args:
        url: 요청 URL

    Returns:
        bool: 재시도 제외 도메인이면 True
    """
    excluded = settings.retry_excluded_domains.split(",")
    return any(domain.strip() in url for domain in excluded)


async def fetch_with_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    **kwargs: Any,
) -> httpx.Response:
    """재시도 정책이 적용된 HTTP 요청

    Args:
        client: httpx.AsyncClient 인스턴스
        method: HTTP 메서드 (GET, POST, PUT, DELETE 등)
        url: 요청 URL
        **kwargs: httpx.request()에 전달할 추가 인자

    Returns:
        httpx.Response: HTTP 응답

    Raises:
        httpx.ConnectTimeout: 재시도 후에도 연결 실패
        httpx.ReadTimeout: 재시도 후에도 읽기 실패
        httpx.NetworkError: 재시도 후에도 네트워크 오류
        httpx.HTTPStatusError: HTTP 4xx/5xx 에러 (재시도 안 함)

    Examples:
        >>> async with get_client("general") as client:
        ...     response = await fetch_with_retry(client, "GET", "https://api.example.com/data")
    """
    # 재시도 제외 도메인 확인
    if is_excluded_domain(url):
        # 재시도 없이 바로 요청
        response = await client.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    # 멱등성 체크 (POST는 idempotency-key 필요)
    if method.upper() == "POST":
        headers = kwargs.get("headers", {})
        if "idempotency-key" not in {k.lower() for k in headers.keys()}:
            # 멱등성 키 없으면 재시도 안 함
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response

    # 재시도 정책 적용
    @retry(
        stop=stop_after_attempt(settings.retry_max_attempts),
        wait=wait_fixed(settings.retry_interval),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        reraise=True,
    )
    async def _request_with_retry():
        response = await client.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    return await _request_with_retry()


__all__ = ["fetch_with_retry", "is_excluded_domain"]
```

**검증**:
```python
from backend.src.integrations.retry_policy import fetch_with_retry, is_excluded_domain

assert is_excluded_domain("https://api.tosspayments.com/v1/payments") == True
assert is_excluded_domain("https://api.example.com") == False
```

---

### T014: HTTP 연결 풀 Contract Test 실행 및 통과 확인
**파일**: `backend/tests/contract/test_http_pool_contract.py` (실행)
**설명**: T012에서 구현한 HTTP 클라이언트가 contract test를 통과하는지 확인합니다.

**세부 작업**:
```bash
cd backend
pytest tests/contract/test_http_pool_contract.py -v
```

**예상 결과**: 모든 테스트 **통과** ✅

---

### T015: 재시도 정책 Contract Test 실행 및 통과 확인
**파일**: `backend/tests/contract/test_retry_policy_contract.py` (실행)
**설명**: T013에서 구현한 재시도 정책이 contract test를 통과하는지 확인합니다.

**세부 작업**:
```bash
cd backend
pytest tests/contract/test_retry_policy_contract.py -v
```

**예상 결과**: 모든 테스트 **통과** ✅

---

### T016: HTTP 연결 풀 Integration Test 작성 및 실행
**파일**: `backend/tests/integration/test_http_pool_integration.py` (신규)
**설명**: HTTP 클라이언트가 실제 외부 API 호출 시 올바르게 동작하는지 검증하는 integration test를 작성합니다.

**세부 작업**:
1. `test_http_pool_integration.py` 파일 생성
2. 다음 테스트 작성:

```python
"""HTTP 연결 풀 Integration Tests

실제 HTTP 요청으로 연결 풀 동작 검증
"""
import pytest
import asyncio
from backend.src.integrations.http_client import get_client
from backend.src.integrations.retry_policy import fetch_with_retry


class TestHttpPoolIntegration:
    """HTTP 클라이언트 연결 풀 통합 테스트"""

    @pytest.mark.asyncio
    async def test_concurrent_requests_with_keepalive(self):
        """Keep-Alive로 여러 요청 재사용"""
        async with get_client("general") as client:
            # 같은 호스트로 여러 요청 (Keep-Alive 재사용)
            urls = [f"https://httpbin.org/delay/{i}" for i in range(1, 4)]

            async def fetch(url):
                response = await client.get(url)
                return response.status_code

            results = await asyncio.gather(*[fetch(url) for url in urls])
            assert all(status == 200 for status in results)

    @pytest.mark.asyncio
    async def test_timeout_for_slow_response(self):
        """읽기 타임아웃 (8초) 초과 시 에러"""
        async with get_client("general") as client:
            # 10초 지연 (read_timeout=8초 초과)
            with pytest.raises(Exception):  # ReadTimeout or TimeoutException
                await client.get("https://httpbin.org/delay/10")

    @pytest.mark.asyncio
    async def test_payment_api_longer_timeout(self):
        """결제 API는 180초 타임아웃"""
        async with get_client("payment") as client:
            # 결제 클라이언트는 180초 타임아웃
            assert client.timeout.read == 180.0

            # 짧은 요청도 정상 동작
            response = await client.get("https://httpbin.org/delay/1")
            assert response.status_code == 200
```

3. 테스트 실행:
```bash
pytest tests/integration/test_http_pool_integration.py -v
```

**예상 결과**: 모든 테스트 **통과** ✅

---

## Phase 3.6: 재시도 Integration Test

### T017: 재시도 Integration Test 작성 및 실행
**파일**: `backend/tests/integration/test_retry_integration.py` (신규)
**설명**: 재시도 정책이 실제 네트워크 에러 상황에서 올바르게 동작하는지 검증합니다.

**세부 작업**:
1. `test_retry_integration.py` 파일 생성
2. 다음 테스트 작성:

```python
"""재시도 정책 Integration Tests

실제 네트워크 에러 시나리오에서 재시도 동작 검증
"""
import pytest
from unittest.mock import AsyncMock, patch
import httpx
from backend.src.integrations.http_client import get_client
from backend.src.integrations.retry_policy import fetch_with_retry


class TestRetryIntegration:
    """재시도 정책 통합 테스트"""

    @pytest.mark.asyncio
    async def test_retry_on_network_error(self):
        """네트워크 에러 발생 시 재시도 (최대 3회)"""
        async with get_client("general") as client:
            with patch.object(
                client, 'request',
                side_effect=[
                    httpx.ConnectTimeout("1st attempt"),
                    httpx.ConnectTimeout("2nd attempt"),
                    AsyncMock(status_code=200, text="success")  # 3번째 성공
                ]
            ) as mock_request:
                response = await fetch_with_retry(client, "GET", "http://example.com")

                # 3회 시도 확인
                assert mock_request.call_count == 3
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_no_retry_for_payment_domain(self):
        """결제 도메인은 재시도 안 함"""
        async with get_client("general") as client:
            with patch.object(
                client, 'request',
                side_effect=httpx.ConnectTimeout("Timeout")
            ) as mock_request:
                with pytest.raises(httpx.ConnectTimeout):
                    await fetch_with_retry(
                        client, "GET", "https://api.tosspayments.com/v1/test"
                    )

                # 1회만 시도
                assert mock_request.call_count == 1

    @pytest.mark.asyncio
    async def test_idempotent_post_with_key(self):
        """멱등성 키 있는 POST는 재시도"""
        async with get_client("general") as client:
            with patch.object(
                client, 'request',
                side_effect=[
                    httpx.ReadTimeout("1st"),
                    AsyncMock(status_code=201)  # 2번째 성공
                ]
            ) as mock_request:
                response = await fetch_with_retry(
                    client, "POST", "http://example.com",
                    headers={"idempotency-key": "test-key"},
                    json={"data": "test"}
                )

                # 2회 시도
                assert mock_request.call_count == 2
                assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_no_retry_for_post_without_key(self):
        """멱등성 키 없는 POST는 재시도 안 함"""
        async with get_client("general") as client:
            with patch.object(
                client, 'request',
                side_effect=httpx.ConnectTimeout("Timeout")
            ) as mock_request:
                with pytest.raises(httpx.ConnectTimeout):
                    await fetch_with_retry(
                        client, "POST", "http://example.com",
                        json={"data": "test"}
                    )

                # 1회만 시도
                assert mock_request.call_count == 1
```

3. 테스트 실행:
```bash
pytest tests/integration/test_retry_integration.py -v
```

**예상 결과**: 모든 테스트 **통과** ✅

---

## Phase 3.7: 기존 코드 통합 및 리팩토링

### T018: 기존 HTTP 호출을 http_client로 리팩토링
**파일**: `backend/src/integrations/toss_payments.py`, `backend/src/integrations/naver_news.py` 등 (수정)
**설명**: 기존 코드에서 직접 httpx를 사용하는 부분을 http_client와 retry_policy를 사용하도록 리팩토링합니다.

**세부 작업**:
1. 기존 HTTP 호출 코드 검색:
   ```bash
   cd backend
   grep -r "httpx\|aiohttp\|requests" src/integrations/ --include="*.py"
   ```

2. 예시: `backend/src/integrations/toss_payments.py` 수정
   - **Before**:
     ```python
     import httpx

     async def call_payment_api(data):
         async with httpx.AsyncClient() as client:
             response = await client.post(
                 "https://api.tosspayments.com/v1/payments",
                 json=data
             )
             return response.json()
     ```

   - **After**:
     ```python
     from backend.src.integrations.http_client import get_client
     # 재시도 정책은 결제 API에 적용하지 않음 (excluded_domains)

     async def call_payment_api(data):
         async with get_client("payment") as client:
             response = await client.post(
                 "https://api.tosspayments.com/v1/payments",
                 json=data
             )
             response.raise_for_status()
             return response.json()
     ```

3. 예시: `backend/src/integrations/naver_news.py` 수정
   - **Before**:
     ```python
     import httpx

     async def fetch_news(url):
         async with httpx.AsyncClient() as client:
             response = await client.get(url)
             return response.text
     ```

   - **After**:
     ```python
     from backend.src.integrations.http_client import get_client
     from backend.src.integrations.retry_policy import fetch_with_retry

     async def fetch_news(url):
         async with get_client("general") as client:
             response = await fetch_with_retry(client, "GET", url)
             return response.text
     ```

**검증**: 기존 통합 테스트 실행
```bash
pytest tests/integration/ -v
```

---

### T019: quickstart.md 1-4단계 실행 및 검증
**파일**: `specs/003-db-http/quickstart.md` (실행)
**설명**: quickstart.md의 1-4단계를 실행하여 연결 풀 설정이 올바르게 동작하는지 수동 검증합니다.

**세부 작업**:
1. 1단계: 의존성 확인
   ```bash
   pip list | grep -E "httpx|tenacity|sqlalchemy"
   ```

2. 2단계: 환경 변수 확인
   ```bash
   cat backend/.env | grep -E "DB_POOL|HTTP_|RETRY_"
   ```

3. 3단계: DB 연결 풀 테스트
   - quickstart.md의 3.1~3.3 Python 코드 실행
   - 예상 출력 확인

4. 4단계: HTTP 연결 풀 테스트
   - quickstart.md의 4.1~4.3 Python 코드 실행
   - 예상 출력 확인

**검증 체크리스트**:
- [ ] DB pool_size = 10 확인
- [ ] pool_timeout 동작 확인 (0.4초)
- [ ] HTTP max_connections = 100 확인
- [ ] 재시도 정책 동작 확인

---

### T020: Unit Tests 작성 (설정 검증)
**파일**: `backend/tests/unit/test_pool_config.py` (신규)
**설명**: 연결 풀 설정값이 올바르게 로드되는지 검증하는 unit test를 작성합니다.

**세부 작업**:
1. `backend/tests/unit/` 디렉토리 생성 (없으면)
2. `test_pool_config.py` 파일 생성
3. 다음 테스트 작성:

```python
"""연결 풀 설정 Unit Tests"""
import pytest
from backend.src.config import settings


class TestPoolConfig:
    """연결 풀 설정 로드 검증"""

    def test_db_pool_settings_loaded(self):
        """DB 연결 풀 설정 로드 확인"""
        assert settings.db_pool_size == 10
        assert settings.db_max_overflow == 20
        assert settings.db_pool_recycle == 3600
        assert settings.db_pool_pre_ping is True
        assert settings.db_pool_timeout == 0.4

    def test_http_pool_settings_loaded(self):
        """HTTP 연결 풀 설정 로드 확인"""
        assert settings.http_max_connections == 100
        assert settings.http_max_keepalive_connections == 20
        assert settings.http_keepalive_expiry == 60.0

    def test_http_timeout_settings_loaded(self):
        """HTTP 타임아웃 설정 로드 확인"""
        assert settings.http_connect_timeout == 4.0
        assert settings.http_read_timeout == 8.0
        assert settings.http_write_timeout == 10.0
        assert settings.http_payment_connect_timeout == 180.0

    def test_retry_policy_settings_loaded(self):
        """재시도 정책 설정 로드 확인"""
        assert settings.retry_max_attempts == 3
        assert settings.retry_interval == 4.0
        assert "api.tosspayments.com" in settings.retry_excluded_domains
```

4. 테스트 실행:
```bash
pytest tests/unit/test_pool_config.py -v
```

**예상 결과**: 모든 테스트 **통과** ✅

---

### T021 [P]: Unit Tests 작성 (재시도 정책 유틸)
**파일**: `backend/tests/unit/test_retry_policy.py` (신규)
**설명**: 재시도 정책의 유틸리티 함수들을 unit test로 검증합니다.

**세부 작업**:
1. `test_retry_policy.py` 파일 생성
2. 다음 테스트 작성:

```python
"""재시도 정책 Unit Tests"""
import pytest
from backend.src.integrations.retry_policy import is_excluded_domain


class TestRetryPolicyUtils:
    """재시도 정책 유틸리티 함수 검증"""

    def test_is_excluded_domain_for_payment_api(self):
        """결제 API 도메인 제외 확인"""
        assert is_excluded_domain("https://api.tosspayments.com/v1/payments") is True
        assert is_excluded_domain("https://pay.naver.com/api/test") is True

    def test_is_excluded_domain_for_general_api(self):
        """일반 API 도메인은 제외 안 됨"""
        assert is_excluded_domain("https://api.example.com") is False
        assert is_excluded_domain("https://httpbin.org/get") is False

    def test_is_excluded_domain_partial_match(self):
        """부분 일치도 제외됨"""
        # "api.tosspayments.com"이 URL에 포함되면 제외
        assert is_excluded_domain("https://test.api.tosspayments.com/v1") is True
```

3. 테스트 실행:
```bash
pytest tests/unit/test_retry_policy.py -v
```

**예상 결과**: 모든 테스트 **통과** ✅

---

## Phase 3.8: 부하 테스트

### T022: K6 부하 테스트 스크립트 작성
**파일**: `backend/tests/performance/connection_pool_load_test.js` (신규)
**설명**: K6를 사용한 부하 테스트 스크립트를 작성합니다.

**세부 작업**:
1. `backend/tests/performance/` 디렉토리 생성
2. `connection_pool_load_test.js` 파일 생성
3. 다음 스크립트 작성:

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
  check(res1, {
    'health check status is 200': (r) => r.status === 200
  });

  // 외부 API 호출 시뮬레이션 (HTTP 연결 풀 테스트)
  // TODO: 실제 외부 API 엔드포인트로 교체
  // let res2 = http.get('http://localhost:8080/api/external/test');
  // check(res2, {
  //   'external API status is 200': (r) => r.status === 200
  // });

  sleep(1);
}
```

**검증**: 파일이 생성되었는지 확인

---

### T023: K6 부하 테스트 실행
**파일**: K6 실행
**설명**: 백엔드 서버를 실행하고 K6 부하 테스트를 실행합니다.

**세부 작업**:
1. 백엔드 서버 실행:
   ```bash
   cd backend
   uvicorn src.main:app --host 0.0.0.0 --port 8080
   ```

2. 새 터미널에서 K6 테스트 실행:
   ```bash
   k6 run backend/tests/performance/connection_pool_load_test.js
   ```

3. 결과 확인:
   - http_req_duration p(95) < 5000ms
   - http_req_failed < 1%
   - 연결 풀 타임아웃 에러 없음

**예상 출력**:
```
✓ health check status is 200

checks.........................: 100.00% ✓ 12000 ✗ 0
http_req_duration..............: avg=150ms p(95)=300ms
http_req_failed................: 0.00%   ✓ 0     ✗ 12000
```

---

### T024: 성능 결과 분석 및 튜닝
**파일**: 없음 (분석 작업)
**설명**: K6 부하 테스트 결과를 분석하고 필요 시 연결 풀 설정을 튜닝합니다.

**세부 작업**:
1. K6 결과 분석:
   - p(95) 응답 시간이 5초 이내인가?
   - 에러율이 1% 미만인가?
   - DB 연결 풀 타임아웃이 발생했는가?

2. 병목 지점 확인:
   - DB 연결 풀 부족: pool_size 또는 max_overflow 증가
   - HTTP 연결 풀 부족: max_connections 증가
   - 타임아웃 너무 짧음: 타임아웃 값 증가

3. 튜닝 필요 시:
   - `backend/.env` 파일 수정
   - 서버 재시작 후 K6 재실행
   - 결과 비교

**성공 기준**:
- p(95) < 5초
- 에러율 < 1%
- 타임아웃 에러 없음

---

## Phase 3.9: 문서화 및 정리

### T025: 모든 테스트 실행 및 커버리지 확인
**파일**: pytest 실행
**설명**: 모든 테스트를 실행하고 코드 커버리지가 80% 이상인지 확인합니다.

**세부 작업**:
1. 전체 테스트 실행:
   ```bash
   cd backend
   pytest --cov=src --cov-report=term --cov-report=html -v
   ```

2. 커버리지 확인:
   - 전체 커버리지 >= 80%
   - 새로 추가한 파일들 (http_client.py, retry_policy.py 등) >= 90%

3. 커버리지 부족 시:
   - 누락된 테스트 케이스 추가
   - Edge case 테스트 추가

**예상 출력**:
```
---------- coverage: platform linux, python 3.11.x -----------
Name                                     Stmts   Miss  Cover
------------------------------------------------------------
src/config.py                               45      2    96%
src/database/connection.py                  28      1    96%
src/integrations/http_client.py             35      2    94%
src/integrations/retry_policy.py            42      3    93%
------------------------------------------------------------
TOTAL                                      150     8    95%
```

---

### T026 [P]: ARCHITECTURE.md 업데이트
**파일**: `ARCHITECTURE.md` (수정)
**설명**: ARCHITECTURE.md에 연결 풀 섹션을 추가합니다.

**세부 작업**:
1. `ARCHITECTURE.md` 파일 열기
2. "인프라" 또는 "데이터베이스" 섹션에 다음 내용 추가:

```markdown
## 연결 풀 (Connection Pooling)

### DB 연결 풀
- **라이브러리**: SQLAlchemy 2.0 async engine
- **설정**:
  - pool_size: 10 (기본 연결)
  - max_overflow: 20 (최대 확장)
  - pool_recycle: 3600초 (1시간)
  - pool_pre_ping: True (연결 유효성 검증)
  - pool_timeout: 0.4초
- **모니터링**: pool_metrics.py (추후 Prometheus 연동)

### HTTP 연결 풀
- **라이브러리**: httpx AsyncClient
- **설정**:
  - max_connections: 100
  - max_keepalive_connections: 20
  - 일반 API: connect=4s, read=8s
  - 결제 API: connect=180s, read=180s
- **재시도 정책**: tenacity (최대 3회, 간격 4초)

### 관련 파일
- `backend/src/database/connection.py`: DB 연결 풀
- `backend/src/integrations/http_client.py`: HTTP 클라이언트 팩토리
- `backend/src/integrations/retry_policy.py`: 재시도 정책
- `specs/003-db-http/`: 설계 문서
```

**검증**: ARCHITECTURE.md에 섹션이 추가되었는지 확인

---

### T027 [P]: README.md 업데이트
**파일**: `README.md` (수정)
**설명**: README.md에 새로운 환경 변수 설명을 추가합니다.

**세부 작업**:
1. `README.md` 파일 열기
2. "환경 변수" 섹션에 다음 내용 추가:

```markdown
### DB 연결 풀 설정
- `DB_POOL_SIZE`: 기본 연결 수 (기본값: 10)
- `DB_MAX_OVERFLOW`: 추가 확장 연결 수 (기본값: 20)
- `DB_POOL_RECYCLE`: 연결 재활용 시간 초 (기본값: 3600)
- `DB_POOL_PRE_PING`: 연결 유효성 검증 (기본값: true)
- `DB_POOL_TIMEOUT`: 연결 대기 타임아웃 초 (기본값: 0.4)

### HTTP 연결 풀 설정
- `HTTP_MAX_CONNECTIONS`: 전체 최대 연결 수 (기본값: 100)
- `HTTP_MAX_KEEPALIVE_CONNECTIONS`: Keep-Alive 연결 수 (기본값: 20)
- `HTTP_CONNECT_TIMEOUT`: 연결 타임아웃 초 (기본값: 4.0)
- `HTTP_READ_TIMEOUT`: 읽기 타임아웃 초 (기본값: 8.0)
- `HTTP_PAYMENT_CONNECT_TIMEOUT`: 결제 API 연결 타임아웃 초 (기본값: 180.0)

### 재시도 설정
- `RETRY_MAX_ATTEMPTS`: 최대 시도 횟수 (기본값: 3)
- `RETRY_INTERVAL`: 재시도 간격 초 (기본값: 4.0)
- `RETRY_EXCLUDED_DOMAINS`: 재시도 제외 도메인 (쉼표 구분)

자세한 내용은 [specs/003-db-http/](specs/003-db-http/) 참조
```

**검증**: README.md에 섹션이 추가되었는지 확인

---

### T028: 최종 검증 및 정리
**파일**: 없음 (검증 작업)
**설명**: 모든 태스크가 완료되었는지 최종 검증하고 정리합니다.

**세부 작업**:
1. 체크리스트 확인:
   - [ ] 모든 contract tests 통과
   - [ ] 모든 integration tests 통과
   - [ ] K6 부하 테스트 통과 (p95 < 5s, 에러 < 1%)
   - [ ] 코드 커버리지 >= 80%
   - [ ] quickstart.md 검증 완료
   - [ ] ARCHITECTURE.md 업데이트
   - [ ] README.md 업데이트

2. Git commit 및 push:
   ```bash
   git add .
   git commit -m "[T001-T028] DB 및 HTTP 연결 풀 설정 완료

   - SQLAlchemy async engine 연결 풀 설정
   - httpx AsyncClient 연결 풀 및 재시도 정책
   - Contract tests, Integration tests, Unit tests
   - K6 부하 테스트
   - 문서화

   🤖 Generated with Claude Code"

   git push origin 003-db-http
   ```

3. Pull Request 생성 (선택사항):
   - 제목: "[003-db-http] DB 및 HTTP 연결 풀 설정"
   - 본문: specs/003-db-http/plan.md 요약
   - 리뷰어 지정

**최종 산출물**:
- 코드 파일 5개 (수정/신규)
- 테스트 파일 8개
- 문서 3개 (ARCHITECTURE.md, README.md, .env.example)
- K6 스크립트 1개

---

## Dependencies (의존성 그래프)

```
환경 준비 (T001-T003)
    ↓
Config 설정 (T004)
    ↓
Contract Tests 작성 [P] (T005, T006, T007)
    ↓
DB 구현 (T008, T009)
    ↓
DB Contract Test 통과 (T010)
    ↓
DB Integration Test (T011)

HTTP 구현 [P] (T012, T013) ← T004 완료 후
    ↓
HTTP Contract Tests 통과 (T014, T015)
    ↓
HTTP Integration Test (T016)
    ↓
재시도 Integration Test (T017)
    ↓
기존 코드 통합 (T018)
    ↓
Quickstart 검증 (T019)
    ↓
Unit Tests [P] (T020, T021)
    ↓
K6 스크립트 작성 (T022)
    ↓
K6 실행 (T023)
    ↓
성능 튜닝 (T024)
    ↓
전체 테스트 실행 (T025)
    ↓
문서화 [P] (T026, T027)
    ↓
최종 검증 (T028)
```

---

## Parallel Execution Examples (병렬 실행 예시)

### 예시 1: Contract Tests 병렬 작성 (T005, T006, T007)
T004 완료 후 다음 3개 태스크를 병렬 실행 가능:

```bash
# 터미널 1
# T005: DB 연결 풀 Contract Test 작성
vi backend/tests/contract/test_db_pool_contract.py

# 터미널 2
# T006: HTTP 연결 풀 Contract Test 작성
vi backend/tests/contract/test_http_pool_contract.py

# 터미널 3
# T007: 재시도 정책 Contract Test 작성
vi backend/tests/contract/test_retry_policy_contract.py
```

모두 독립적인 파일이므로 충돌 없음.

---

### 예시 2: HTTP 구현 병렬 작성 (T012, T013)
T004 완료 후 다음 2개 태스크를 병렬 실행 가능:

```bash
# 터미널 1
# T012: http_client.py 생성
vi backend/src/integrations/http_client.py

# 터미널 2
# T013: retry_policy.py 생성
vi backend/src/integrations/retry_policy.py
```

다른 파일이므로 충돌 없음.

---

### 예시 3: Unit Tests 병렬 작성 (T020, T021)
T019 완료 후 다음 2개 태스크를 병렬 실행 가능:

```bash
# 터미널 1
# T020: 설정 검증 Unit Test
vi backend/tests/unit/test_pool_config.py

# 터미널 2
# T021: 재시도 정책 유틸 Unit Test
vi backend/tests/unit/test_retry_policy.py
```

---

### 예시 4: 문서화 병렬 작성 (T026, T027)
T025 완료 후 다음 2개 태스크를 병렬 실행 가능:

```bash
# 터미널 1
# T026: ARCHITECTURE.md 업데이트
vi ARCHITECTURE.md

# 터미널 2
# T027: README.md 업데이트
vi README.md
```

---

## Notes (주의사항)

### TDD 원칙 준수
- **반드시 Contract Tests (T005-T007)를 먼저 작성**하고 실패 확인 후 구현 시작
- 테스트가 실패하지 않으면 TDD가 아님

### 파일 충돌 방지
- `[P]` 표시가 없는 태스크는 순차 실행
- 같은 파일을 수정하는 태스크는 병렬 실행 금지

### Commit 권장사항
- 각 태스크 완료 후 commit 권장
- Commit 메시지: `[T###] 태스크 설명`

### 추후 구현 항목
- pool_metrics.py 완전 구현 (Prometheus 연동)
- AlertManager 연동
- Grafana 대시보드

### 테스트 실행 순서
1. Contract tests (T005-T007 작성 후 바로 실행, 실패 확인)
2. 구현 (T008-T013)
3. Contract tests 재실행 (통과 확인)
4. Integration tests (T011, T016, T017)
5. Unit tests (T020, T021)
6. 전체 테스트 (T025)

---

## Validation Checklist (검증 체크리스트)

**GATE: 모든 태스크 완료 전 확인**

- [x] 모든 contracts에 대응하는 테스트 존재
  - db-pool-config.yaml → test_db_pool_contract.py
  - http-client-config.yaml → test_http_pool_contract.py

- [x] 모든 엔티티에 모델/구현 태스크 존재
  - DatabasePoolConfig → config.py (T004)
  - HttpClientConfig → http_client.py (T012)
  - RetryPolicyConfig → retry_policy.py (T013)

- [x] 모든 테스트가 구현 전에 위치
  - T005-T007 (Contract tests) → T008-T013 (구현)

- [x] 병렬 태스크가 진정으로 독립적
  - T005, T006, T007: 다른 파일
  - T012, T013: 다른 파일
  - T020, T021: 다른 파일
  - T026, T027: 다른 파일

- [x] 각 태스크가 정확한 파일 경로 명시
  - 모든 태스크에 파일 경로 포함

- [x] [P] 태스크가 같은 파일 수정하지 않음
  - 검증 완료

---

**총 태스크 수**: 28개
**예상 소요 시간**: 8-12시간 (테스트 + 구현 + 문서화)
**병렬 실행 가능**: 10개 태스크 (T005-T007, T012-T013, T020-T021, T026-T027)

---

**문서 작성**: 2025-10-16
**기반 문서**: plan.md, research.md, data-model.md, contracts/, quickstart.md
**준비 상태**: ✅ 즉시 실행 가능
