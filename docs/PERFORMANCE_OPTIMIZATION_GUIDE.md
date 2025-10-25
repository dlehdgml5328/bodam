# BoDam 성능 측정 및 개선 가이드

## 📋 목차
1. [베이스라인 측정](#1-베이스라인-측정)
2. [성능 개선 방법](#2-성능-개선-방법)
3. [개선 후 재측정](#3-개선-후-재측정)
4. [Before/After 비교 분석](#4-beforeafter-비교-분석)

---

## 1. 베이스라인 측정

### 1.1 현재 환경 설정

**날짜**: 2025-10-25
**환경**: Development (docker-compose.dev.yml)
**설정**:
- Rate Limiting: **비활성화** (`ENABLE_RATE_LIMITING=false`)
- DB Pool Size: 10
- K6 VUs: 20-30명 동시 사용자

### 1.2 K6 부하 테스트 실행

```bash
# 기본 부하 테스트 (20명, 15초)
TEST_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
K6_TEST_SCRIPT="k6-donation-race.js" \
K6_VUS=20 \
K6_DURATION=15s \
DONATION_FIRE_STATION_ID="9dc63e0c-df47-4f95-af37-cd284cf32822" \
DONATION_AMOUNT=10000 \
docker compose -f docker-compose.dev.yml --profile test up k6
```

**참고**: JWT 토큰이 만료되면 새로 생성 필요
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"yourpassword"}'
```

### 1.3 베이스라인 결과 (2025-10-25)

#### K6 테스트 결과
```
http_req_duration.....: avg=10.68ms  p(95)=17.41ms  p(99)=50ms
http_reqs.............: 1442         95 RPS
http_req_failed.......: 100.00%      (JWT 토큰 만료)
iteration_duration....: avg=211ms
```

#### Grafana 메트릭 (정상 상태 기준)
- **API p95 응답시간**: ~95ms
- **RPS**: 95 req/s
- **DB 커넥션 풀 사용률**: 70% (7/10)
- **중복 기부 감지**: 17건
- **Celery 작업 성공률**: 85%

#### 문제점 식별
1. ❌ JWT 토큰 만료로 인한 100% 실패
2. ⚠️ API p95 응답시간이 목표(300ms) 대비 양호하지만 개선 가능
3. ⚠️ DB 커넥션 풀 사용률 70% (여유 있음)
4. ⚠️ 중복 기부 감지 발생 (Race condition)

---

## 2. 성능 개선 방법

### 2.1 인증 최적화

#### 문제
- JWT 토큰 만료 시간이 짧음 (15분)
- 매 요청마다 JWT 검증 오버헤드

#### 개선 방안
```python
# backend/src/core/config.py
JWT_EXPIRATION_MINUTES = 60  # 15분 → 60분으로 연장
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7  # 리프레시 토큰 추가
```

**예상 효과**: 토큰 갱신 빈도 75% 감소

---

### 2.2 DB 쿼리 최적화

#### 2.2.1 인덱스 추가

```sql
-- 기부 조회 쿼리 최적화
CREATE INDEX idx_donations_fire_station_created
ON donations(fire_station_id, created_at DESC);

-- 사용자 조회 최적화
CREATE INDEX idx_users_email_active
ON users(email, is_active) WHERE is_active = true;
```

**예상 효과**: SELECT 쿼리 50-70% 속도 향상

#### 2.2.2 N+1 쿼리 제거

```python
# Before: N+1 쿼리 발생
donations = await session.execute(select(Donation))
for donation in donations:
    fire_station = await session.get(FireStation, donation.fire_station_id)  # N번 쿼리

# After: JOIN으로 한 번에 조회
from sqlalchemy.orm import selectinload

donations = await session.execute(
    select(Donation).options(selectinload(Donation.fire_station))
)
```

**예상 효과**: 다건 조회 시 쿼리 수 90% 감소

---

### 2.3 Redis 캐싱 전략

#### 2.3.1 소방서 정보 캐싱

```python
# backend/src/services/cache_service.py
from redis import Redis
import json

redis_client = Redis.from_url(os.getenv("REDIS_CACHE_URL"))

async def get_fire_station_cached(fire_station_id: str):
    # 캐시 확인
    cache_key = f"fire_station:{fire_station_id}"
    cached = redis_client.get(cache_key)

    if cached:
        return json.loads(cached)

    # DB 조회
    fire_station = await get_fire_station_from_db(fire_station_id)

    # 캐시 저장 (TTL: 1시간)
    redis_client.setex(cache_key, 3600, json.dumps(fire_station))

    return fire_station
```

**예상 효과**: 소방서 조회 95% 응답시간 단축

#### 2.3.2 API 응답 캐싱

```python
# backend/src/api/middleware.py
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

@app.get("/fire-stations")
@cache(expire=300)  # 5분 캐싱
async def list_fire_stations():
    return await get_all_fire_stations()
```

**예상 효과**: 정적 데이터 조회 90% 응답시간 단축

---

### 2.4 Connection Pool 튜닝

#### 2.4.1 DB Connection Pool

```python
# backend/src/database/connection.py

# Before
DB_POOL_SIZE = 10
DB_MAX_OVERFLOW = 20

# After (부하 테스트 결과 기반)
DB_POOL_SIZE = 20          # 동시 연결 수 증가
DB_MAX_OVERFLOW = 30       # 버스트 트래픽 대응
DB_POOL_PRE_PING = True    # 연결 유효성 검증
DB_POOL_RECYCLE = 1800     # 30분마다 재활용
```

**예상 효과**: 높은 부하 시 DB 대기 시간 60% 감소

#### 2.4.2 HTTP Client Pool

```python
# backend/src/integrations/http_client.py

# Before
HTTP_MAX_CONNECTIONS = 100

# After
HTTP_MAX_CONNECTIONS = 200
HTTP_MAX_KEEPALIVE_CONNECTIONS = 40  # 20 → 40
HTTP_KEEPALIVE_EXPIRY = 120.0        # 60초 → 120초
```

**예상 효과**: 외부 API 호출 응답시간 30% 개선

---

### 2.5 중복 기부 방지 (Race Condition)

#### 문제
동시에 같은 사용자가 같은 소방서에 기부 시 중복 발생

#### 개선 방안: Redis 분산 락

```python
# backend/src/services/donation_service.py
from redis.lock import Lock

async def create_donation(user_id: str, fire_station_id: str, amount: int):
    # Redis 분산 락 획득
    lock_key = f"donation_lock:{user_id}:{fire_station_id}"
    lock = redis_client.lock(lock_key, timeout=10)

    if not lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="DUPLICATE_DONATION")

    try:
        # 기부 생성
        donation = await create_donation_in_db(user_id, fire_station_id, amount)
        return donation
    finally:
        lock.release()
```

**예상 효과**: 중복 기부 100% 방지

---

### 2.6 비동기 작업 최적화

#### 2.6.1 Celery 작업 병렬 처리

```python
# backend/src/workers/tasks.py
from celery import group

# Before: 순차 처리
for user in users:
    send_email.delay(user.email)

# After: 병렬 처리
job = group(send_email.s(user.email) for user in users)
job.apply_async()
```

**예상 효과**: 대량 작업 처리 시간 70% 단축

---

### 2.7 Rate Limiting 세밀 조정

```python
# backend/src/api/middleware.py

# Before: 전역 Rate Limit
RATE_LIMIT = "100/minute"

# After: 엔드포인트별 차등 적용
rate_limits = {
    "/donations": "50/minute",      # 기부는 제한적
    "/fire-stations": "200/minute",  # 조회는 여유롭게
    "/auth/login": "10/minute",      # 로그인은 엄격하게
}
```

**예상 효과**: 정상 사용자 경험 개선, 악의적 요청 차단

---

## 3. 개선 후 재측정

### 3.1 성능 개선 적용 체크리스트

#### Phase 1: 즉시 적용 가능 (30분)
- [ ] JWT 만료 시간 연장 (60분)
- [ ] DB 인덱스 추가
- [ ] Connection Pool 크기 증가

#### Phase 2: 단기 적용 (2-3시간)
- [ ] Redis 캐싱 구현 (소방서 정보)
- [ ] N+1 쿼리 제거
- [ ] Rate Limiting 세밀 조정

#### Phase 3: 중기 적용 (1-2일)
- [ ] Redis 분산 락 구현
- [ ] Celery 병렬 처리
- [ ] API 응답 캐싱

### 3.2 재측정 방법

#### 동일한 조건으로 테스트

```bash
# 개선 전과 동일한 설정으로 실행
TEST_TOKEN="새로운토큰" \
K6_TEST_SCRIPT="k6-donation-race.js" \
K6_VUS=20 \
K6_DURATION=15s \
DONATION_FIRE_STATION_ID="9dc63e0c-df47-4f95-af37-cd284cf32822" \
DONATION_AMOUNT=10000 \
docker compose -f docker-compose.dev.yml --profile test up k6
```

#### 더 높은 부하로 테스트 (선택)

```bash
# 50명, 1분
K6_VUS=50 K6_DURATION=1m docker compose -f docker-compose.dev.yml --profile test up k6

# 100명, 2분
K6_VUS=100 K6_DURATION=2m docker compose -f docker-compose.dev.yml --profile test up k6
```

### 3.3 결과 수집

#### Grafana에서 메트릭 확인
1. http://localhost:3001 접속
2. **BoDam K6 부하 테스트 대시보드** 선택
3. 시간 범위를 테스트 시간으로 설정
4. 다음 메트릭 스크린샷 저장:
   - API p95 응답시간
   - 전체 HTTP 요청 수
   - DB 커넥션 풀 사용률
   - 중복 기부 감지 횟수

#### K6 결과 저장

```bash
# K6 결과를 JSON으로 저장
K6_VUS=20 K6_DURATION=15s \
docker compose -f docker-compose.dev.yml --profile test up k6 \
  2>&1 | tee k6-results-after-optimization.txt
```

---

## 4. Before/After 비교 분석

### 4.1 비교 표 템플릿

| 메트릭 | Before (개선 전) | After (개선 후) | 개선율 |
|--------|-----------------|----------------|--------|
| **API p95 응답시간** | 95ms | _측정 필요_ | _계산 예정_ |
| **평균 응답시간** | 10.68ms | _측정 필요_ | _계산 예정_ |
| **RPS (초당 요청)** | 95 req/s | _측정 필요_ | _계산 예정_ |
| **성공률** | 0% (토큰 만료) | _측정 필요_ | _계산 예정_ |
| **DB 커넥션 사용률** | 70% (7/10) | _측정 필요_ | _계산 예정_ |
| **중복 기부 감지** | 17건 | _측정 필요_ | _계산 예정_ |

### 4.2 예상 개선 목표

| 메트릭 | 목표 개선율 |
|--------|-----------|
| API p95 응답시간 | **30-50% 단축** (95ms → 50-65ms) |
| 평균 응답시간 | **40-60% 단축** (10.68ms → 5-7ms) |
| RPS | **100-200% 증가** (95 → 190-285 req/s) |
| 성공률 | **100%** (0% → 100%) |
| 중복 기부 | **0건** (100% 방지) |

### 4.3 비교 대시보드 생성

#### Grafana 비교 대시보드 설정

1. **새 대시보드 생성**: "Performance Comparison"
2. **패널 추가**:
   - API p95 Before/After (Time series)
   - RPS Before/After (Time series)
   - 성공률 Before/After (Gauge)
3. **Annotations 추가**:
   - "최적화 적용 시점" 표시

#### PromQL 비교 쿼리 예시

```promql
# Before (특정 시간대)
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket{time_range="2025-10-25T11:00:00"}[5m])) by (le)
) * 1000

# After (최적화 후 시간대)
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket{time_range="2025-10-25T15:00:00"}[5m])) by (le)
) * 1000
```

---

## 5. 성능 개선 적용 가이드

### 5.1 Phase 1: 즉시 적용 (30분)

#### Step 1: JWT 만료 시간 연장

```bash
# .env 파일 수정
echo "JWT_EXPIRATION_MINUTES=60" >> .env

# 백엔드 재시작
docker compose -f docker-compose.dev.yml restart backend
```

#### Step 2: DB 인덱스 추가

```bash
docker exec -i bodam-db-1 psql -U bodam -d bodam <<EOF
CREATE INDEX IF NOT EXISTS idx_donations_fire_station_created
ON donations(fire_station_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_users_email_active
ON users(email, is_active) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_fire_stations_active
ON fire_stations(is_active) WHERE is_active = true;
EOF

echo "✅ 인덱스 추가 완료"
```

#### Step 3: Connection Pool 증가

```bash
# .env 파일에 추가
cat >> .env <<EOF

# DB Pool 최적화
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_PRE_PING=true
DB_POOL_RECYCLE=1800

# HTTP Client Pool 최적화
HTTP_MAX_CONNECTIONS=200
HTTP_MAX_KEEPALIVE_CONNECTIONS=40
HTTP_KEEPALIVE_EXPIRY=120.0
EOF

# 백엔드 재시작
docker compose -f docker-compose.dev.yml restart backend
```

#### Step 4: 즉시 재측정

```bash
# 새 토큰 생성
NEW_TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test1234"}' | jq -r '.access_token')

# K6 테스트 실행
TEST_TOKEN="$NEW_TOKEN" \
K6_VUS=20 K6_DURATION=15s \
DONATION_FIRE_STATION_ID="9dc63e0c-df47-4f95-af37-cd284cf32822" \
DONATION_AMOUNT=10000 \
K6_TEST_SCRIPT="k6-donation-race.js" \
docker compose -f docker-compose.dev.yml --profile test up k6
```

---

### 5.2 Phase 2: Redis 캐싱 구현 (2-3시간)

#### 파일 생성 필요
1. `backend/src/services/cache_service.py` - Redis 캐싱 서비스
2. `backend/src/api/middleware.py` - 캐싱 미들웨어
3. `backend/src/services/donation_service.py` - 분산 락 적용

코드 예시는 위 "2.3 Redis 캐싱 전략" 및 "2.5 중복 기부 방지" 참조

---

## 6. 보고서 작성 템플릿

### 6.1 성능 개선 보고서 (PERFORMANCE_REPORT.md)

```markdown
# BoDam 성능 개선 보고서

**작성일**: 2025-10-25
**작성자**: [이름]

## 요약

- **개선 전 p95**: 95ms
- **개선 후 p95**: [측정값]ms
- **개선율**: [계산값]%

## 1. 베이스라인 측정
[그래프 스크린샷]

## 2. 적용한 개선 방법
- [x] JWT 만료 시간 연장
- [x] DB 인덱스 추가
- [ ] Redis 캐싱
...

## 3. 개선 후 측정 결과
[그래프 스크린샷]

## 4. 비교 분석
[비교 표]

## 5. 결론 및 향후 계획
...
```

---

## 7. 자주 사용하는 명령어 모음

### K6 테스트 실행

```bash
# 기본 테스트 (20명, 15초)
./scripts/run-k6-test.sh basic

# 고부하 테스트 (100명, 2분)
./scripts/run-k6-test.sh stress

# 커스텀 테스트
K6_VUS=50 K6_DURATION=30s ./scripts/run-k6-test.sh custom
```

### Grafana 메트릭 확인

```bash
# Prometheus에서 현재 p95 확인
curl -s -G 'http://localhost:9090/api/v1/query' \
  --data-urlencode 'query=histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) * 1000'

# RPS 확인
curl -s -G 'http://localhost:9090/api/v1/query' \
  --data-urlencode 'query=sum(rate(http_requests_total[1m]))'
```

### DB 성능 확인

```bash
# 느린 쿼리 확인
docker exec bodam-db-1 psql -U bodam -d bodam -c \
  "SELECT query, calls, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# 인덱스 사용률 확인
docker exec bodam-db-1 psql -U bodam -d bodam -c \
  "SELECT schemaname, tablename, indexname, idx_scan FROM pg_stat_user_indexes ORDER BY idx_scan;"
```

---

## 8. 트러블슈팅

### 문제: K6 테스트가 100% 실패

**원인**: JWT 토큰 만료

**해결**:
```bash
# 새 토큰 생성
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"yourpassword"}'
```

### 문제: Grafana에서 메트릭이 안 보임

**원인**: Prometheus가 메트릭을 수집하지 못함

**해결**:
```bash
# Prometheus 타겟 확인
curl http://localhost:9090/api/v1/targets

# 백엔드 메트릭 확인
curl http://localhost:8000/metrics | grep http_request_duration_seconds
```

### 문제: DB 커넥션 풀 고갈

**원인**: Pool size가 부족

**해결**:
```bash
# .env에서 Pool 크기 증가
DB_POOL_SIZE=30
DB_MAX_OVERFLOW=50

# 백엔드 재시작
docker compose -f docker-compose.dev.yml restart backend
```

---

## 9. 참고 자료

### 내부 문서
- [DEPLOYMENT.md](../DEPLOYMENT.md) - 배포 가이드
- [ALERTING_SETUP.md](../infra/k8s/observability/ALERTING_SETUP.md) - 알람 설정
- [CLAUDE.md](../CLAUDE.md) - 프로젝트 개요

### 외부 문서
- [K6 Documentation](https://k6.io/docs/)
- [Prometheus Query Examples](https://prometheus.io/docs/prometheus/latest/querying/examples/)
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/dashboards/best-practices/)
- [FastAPI Performance](https://fastapi.tiangolo.com/deployment/concepts/)
- [PostgreSQL Performance Tuning](https://www.postgresql.org/docs/current/performance-tips.html)

---

**작성일**: 2025-10-25
**최종 수정**: 2025-10-25
**버전**: 1.0
