# SQLAdmin + Llama AI 채팅 배포 가이드

## 1. 사전 요구사항

### 필수 서비스
- **PostgreSQL 16** (pgvector + PostGIS 확장 설치)
- **Redis 7** (2개 인스턴스 권장)
  - Standard Cache: 일반 캐싱
  - Semantic Cache: Llama AI 쿼리 임베딩 캐시
- **Together AI API Key** (Llama 3.3 70B Instruct + 임베딩 모델)

### 환경 변수 설정

```bash
# 데이터베이스
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/bodam

# Redis 캐시 (2개 인스턴스)
REDIS_CACHE_URL=redis://localhost:6379/0          # 일반 캐시
REDIS_SEMANTIC_URL=redis://localhost:6379/1       # Semantic Cache

# Together AI API
TOGETHER_AI_API_KEY=your_together_api_key_here
TOGETHER_AI_MODEL=meta-llama/Meta-Llama-3.3-70B-Instruct-Turbo

# SQLAdmin 세션
ADMIN_SECRET_KEY=your_32_character_random_secret_key_here  # 최소 32자

# Semantic Cache 설정
SEMANTIC_CACHE_TTL=300                           # 5분 TTL
SEMANTIC_SIMILARITY_THRESHOLD=0.95               # 유사도 임계값

# 채팅 세션 설정
CHAT_SESSION_TIMEOUT=1800                        # 30분
CHAT_MAX_HISTORY=20                              # 최대 메시지 수
```

## 2. 설치

### Python 패키지 설치

```bash
cd backend
pip install -r requirements.txt
```

**핵심 의존성:**
- `sqladmin>=0.16.0` - 관리자 UI
- `together>=1.0.0` - Llama AI API 클라이언트
- `redis>=5.0.0` - Semantic Cache
- `pgvector>=0.2.0` - 임베딩 유사도 계산
- `fastapi>=0.104.0` - 웹 프레임워크
- `sqlalchemy>=2.0.0` + `asyncpg>=0.29.0` - 비동기 ORM

## 3. 데이터베이스 마이그레이션

### Alembic 마이그레이션 실행

```bash
cd backend
alembic upgrade head
```

**확인 사항:**
- `users` 테이블에 `role` 컬럼 (UserRole enum)
- `refunds` 테이블에 `status` 컬럼
- pgvector 확장 활성화: `CREATE EXTENSION IF NOT EXISTS vector;`

## 4. 관리자 계정 생성

### 스크립트를 통한 생성

```bash
cd backend
python scripts/create_admin.py --email admin@bodam.local --name "관리자"
```

**생성되는 계정 정보:**
- Email: `admin@bodam.local`
- Role: `UserRole.ADMIN`
- 임시 비밀번호: 콘솔에 출력됨 (첫 로그인 후 변경 필수)

### 수동 SQL로 생성 (대안)

```sql
-- 비밀번호: 'Admin123!' (예시, 실제로는 bcrypt 해시 사용)
INSERT INTO users (email, name, role, password_hash, is_active, created_at)
VALUES (
  'admin@bodam.local',
  '관리자',
  'admin',
  '$2b$12$...',  -- bcrypt hash
  true,
  NOW()
);
```

## 5. 서비스 실행

### 개발 환경 (로컬)

```bash
cd backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**접속:**
- 관리자 UI: http://localhost:8000/admin
- Swagger API 문서: http://localhost:8000/docs

### 프로덕션 환경 (Gunicorn + Uvicorn Workers)

```bash
cd backend
gunicorn src.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --graceful-timeout 30 \
  --access-logfile - \
  --error-logfile -
```

**권장 설정:**
- Workers: CPU 코어 수 x 2
- Timeout: 120초 (Llama AI API 응답 대기)
- Graceful Timeout: 30초 (안전한 종료)

## 6. 관리자 접속 및 로그인

### 로그인 절차

1. 브라우저에서 `http://your-domain.com/admin` 접속
2. 생성한 관리자 계정으로 로그인
   - Email: `admin@bodam.local`
   - Password: 생성 시 받은 임시 비밀번호
3. 로그인 성공 시 쿠키 기반 세션 생성 (30분 유효)

### 세션 관리

- **세션 만료**: 30분 동안 활동 없으면 자동 로그아웃
- **세션 갱신**: 각 요청마다 자동 갱신
- **쿠키 설정**: HttpOnly, Secure (HTTPS 필수), SameSite=Strict

## 7. 테스트

### Contract Tests (OpenAPI 스펙 검증)

```bash
cd backend
pytest tests/contract/test_admin_ui_routes.py -v
pytest tests/contract/test_admin_chat_api.py -v
pytest tests/contract/test_admin_refund_actions.py -v
```

### Integration Tests (전체 플로우)

```bash
cd backend
pytest tests/integration/test_admin_chat.py -v
pytest tests/integration/test_refund_bulk_actions.py -v
```

### Unit Tests (개별 컴포넌트)

```bash
cd backend
pytest tests/unit/test_llama_query_generator.py -v
pytest tests/unit/test_semantic_cache.py -v
pytest tests/unit/test_audit_logger.py -v
```

### 커버리지 리포트

```bash
cd backend
pytest --cov=src/admin --cov=src/api/admin --cov=src/services/admin --cov-report=html
```

## 8. 모니터링 및 로깅

### 로깅 설정

**구조화된 로그 (structlog 사용):**

```python
import structlog

logger = structlog.get_logger(__name__)

logger.info("admin_login", user_id=user.id, email=user.email)
logger.warning("llama_query_slow", query=query, duration_ms=duration)
logger.error("semantic_cache_error", error=str(e))
```

### 주요 로그 이벤트

1. **인증/권한**
   - `admin_login`: 관리자 로그인
   - `admin_logout`: 관리자 로그아웃
   - `unauthorized_access`: 권한 없는 접근 시도

2. **Llama AI 채팅**
   - `llama_query_start`: 쿼리 시작
   - `llama_query_success`: 쿼리 성공 (실행 시간, 결과 수)
   - `llama_query_error`: 쿼리 실패 (에러 메시지)
   - `semantic_cache_hit`: 캐시 히트 (유사도)
   - `semantic_cache_miss`: 캐시 미스

3. **Bulk Actions**
   - `refund_bulk_approve`: 환불 대량 승인
   - `refund_bulk_reject`: 환불 대량 거부
   - `audit_log_created`: 감사 로그 생성

### 메트릭 수집 (Prometheus)

```python
from prometheus_client import Counter, Histogram

# 관리자 로그인 카운터
admin_logins_total = Counter('admin_logins_total', 'Total admin logins')

# Llama AI 쿼리 레이턴시
llama_query_duration = Histogram(
    'llama_query_duration_seconds',
    'Llama AI query duration',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

# Semantic Cache 히트율
semantic_cache_hits = Counter('semantic_cache_hits_total', 'Semantic cache hits')
semantic_cache_misses = Counter('semantic_cache_misses_total', 'Semantic cache misses')
```

### Grafana 대시보드

**주요 메트릭:**
- 관리자 활성 세션 수
- Llama AI 쿼리 응답 시간 (p50, p95, p99)
- Semantic Cache 히트율 (%)
- 환불 처리 속도 (건/분)
- SQL 쿼리 실행 시간

## 9. 트러블슈팅

### 9.1 Admin 로그인 실패

**증상:**
```
401 Unauthorized: Invalid credentials
```

**해결 방법:**
1. 사용자 계정 확인
   ```sql
   SELECT id, email, role, is_active FROM users WHERE email = 'admin@bodam.local';
   ```
2. Role이 `admin` 또는 `moderator`인지 확인
3. `is_active = true`인지 확인
4. 비밀번호 재설정
   ```bash
   python scripts/reset_admin_password.py --email admin@bodam.local
   ```

### 9.2 Llama AI 응답 없음

**증상:**
```
500 Internal Server Error: Together AI API timeout
```

**해결 방법:**
1. Together AI API Key 확인
   ```bash
   echo $TOGETHER_AI_API_KEY
   ```
2. API Key 테스트
   ```bash
   curl -X POST https://api.together.xyz/v1/chat/completions \
     -H "Authorization: Bearer $TOGETHER_AI_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model": "meta-llama/Meta-Llama-3.3-70B-Instruct-Turbo", "messages": [{"role": "user", "content": "Hello"}]}'
   ```
3. Timeout 설정 확인 (기본: 30초)
   ```python
   # src/services/admin/llm_search_service.py
   async def query_llama(query: str, timeout: int = 30):
       ...
   ```

### 9.3 Semantic Cache 동작 안 함

**증상:**
- 모든 쿼리가 캐시 미스
- 유사한 쿼리에도 캐시 히트 없음

**해결 방법:**
1. Redis 연결 확인
   ```bash
   redis-cli -u $REDIS_SEMANTIC_URL PING
   # 출력: PONG
   ```
2. pgvector 확장 확인
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```
3. 임베딩 생성 확인
   ```python
   from src.services.admin.llm_search_service import generate_embedding

   embedding = await generate_embedding("최근 30일 기부 총액은?")
   print(f"Embedding dimension: {len(embedding)}")  # 출력: 768 또는 1024
   ```
4. 유사도 임계값 조정 (기본: 0.95 → 0.90)
   ```bash
   SEMANTIC_SIMILARITY_THRESHOLD=0.90
   ```

### 9.4 환불 Bulk Action 실패

**증상:**
```
403 Forbidden: Insufficient permissions
```

**해결 방법:**
1. 관리자 Role 확인 (`admin` 필요, `moderator`는 읽기만 가능)
   ```sql
   SELECT role FROM users WHERE email = 'admin@bodam.local';
   ```
2. Refund 상태 확인 (PENDING만 처리 가능)
   ```sql
   SELECT id, status FROM refunds WHERE id IN (123, 456, 789);
   ```
3. Audit Log 확인 (실패 원인)
   ```sql
   SELECT * FROM audit_logs WHERE entity_type = 'refund' ORDER BY created_at DESC LIMIT 10;
   ```

### 9.5 SQL Injection 경고

**증상:**
```
400 Bad Request: SQL query contains forbidden keywords
```

**해결 방법:**
- Llama AI가 생성한 SQL에 `DROP`, `DELETE`, `UPDATE`, `INSERT` 등이 포함되면 자동 차단
- SELECT 쿼리만 허용됨
- 안전한 쿼리로 재작성 요청
  ```
  # 잘못된 쿼리:
  "모든 사용자를 삭제해줘"

  # 올바른 쿼리:
  "삭제 대상 사용자 목록을 보여줘"
  ```

## 10. 보안 체크리스트

### 배포 전 필수 확인 사항

- [ ] **ADMIN_SECRET_KEY** 32자 이상 랜덤 문자열 설정
- [ ] 관리자 계정 비밀번호 **강력하게** 설정 (최소 12자, 대소문자/숫자/특수문자 포함)
- [ ] SQL Injection 방지 확인 (SELECT만 허용, DDL/DML 차단)
- [ ] HTTPS 사용 (프로덕션 환경 필수)
  - 쿠키 `Secure` 플래그 활성화
  - HSTS 헤더 설정
- [ ] Rate Limiting 설정 (Kong Gateway)
  - 로그인: 5회/분
  - Llama AI 쿼리: 10회/분
  - Bulk Actions: 3회/분
- [ ] CORS 정책 설정 (허용 도메인 명시)
- [ ] 민감 정보 필드 마스킹 (`password_hash`, `billing_key`)
- [ ] Audit Logging 활성화 (모든 수정/삭제 액션)
- [ ] 세션 타임아웃 설정 (30분)
- [ ] Redis 인증 설정 (requirepass)
- [ ] PostgreSQL 접근 제어 (pg_hba.conf)

### 추가 보안 강화

```python
# src/admin/config.py

from starlette.middleware.sessions import SessionMiddleware

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.ADMIN_SECRET_KEY,
    session_cookie="bodam_admin_session",
    max_age=1800,  # 30분
    same_site="strict",
    https_only=True  # HTTPS 필수
)
```

## 11. 성능 튜닝

### 11.1 Semantic Cache 최적화

**기본 설정:**
- TTL: 5분 (300초)
- 유사도 임계값: 0.95

**높은 트래픽 환경:**
```bash
SEMANTIC_CACHE_TTL=900              # 15분으로 증가
SEMANTIC_SIMILARITY_THRESHOLD=0.90  # 임계값 낮춰 히트율 증가
```

**메모리 제한 환경:**
```bash
SEMANTIC_CACHE_TTL=180              # 3분으로 감소
SEMANTIC_CACHE_MAX_SIZE=1000        # 최대 캐시 항목 수
```

### 11.2 Llama AI 타임아웃 조정

**기본 타임아웃:**
- 연결 타임아웃: 10초
- 읽기 타임아웃: 30초

**복잡한 쿼리 지원:**
```python
# src/services/admin/llm_search_service.py

LLAMA_CONNECT_TIMEOUT = 15  # 15초
LLAMA_READ_TIMEOUT = 60     # 60초
```

### 11.3 데이터베이스 인덱스

**필수 인덱스:**
```sql
-- 사용자 역할 기반 필터링
CREATE INDEX idx_users_role ON users(role) WHERE role IN ('admin', 'moderator');

-- 기부 날짜 범위 쿼리
CREATE INDEX idx_donations_created_at ON donations(created_at DESC);

-- 환불 상태 필터링
CREATE INDEX idx_refunds_status ON refunds(status) WHERE status = 'PENDING';

-- 소방서 위치 검색 (PostGIS)
CREATE INDEX idx_fire_stations_location ON fire_stations USING GIST(location);

-- 뉴스 임베딩 유사도 검색 (pgvector)
CREATE INDEX idx_news_content_embedding ON news_content USING ivfflat(embedding vector_cosine_ops);
```

## 12. 백업 및 복구

### 12.1 PostgreSQL 백업

```bash
# 일일 백업 (cron)
0 2 * * * pg_dump -h localhost -U postgres -d bodam -F c -b -v -f /backup/bodam_$(date +\%Y\%m\%d).dump

# 복구
pg_restore -h localhost -U postgres -d bodam -v /backup/bodam_20251017.dump
```

### 12.2 Redis 백업

```bash
# Redis RDB 스냅샷 (수동)
redis-cli -u $REDIS_SEMANTIC_URL SAVE

# 자동 스냅샷 설정 (redis.conf)
save 900 1      # 15분마다 1개 이상 변경 시
save 300 10     # 5분마다 10개 이상 변경 시
save 60 10000   # 1분마다 10000개 이상 변경 시
```

## 13. Kubernetes 배포 (프로덕션)

### 13.1 Backend Deployment

```yaml
# infra/k8s/backend/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bodam-backend
  namespace: bodam
spec:
  replicas: 3
  selector:
    matchLabels:
      app: bodam-backend
  template:
    metadata:
      labels:
        app: bodam-backend
    spec:
      containers:
      - name: backend
        image: bodam/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: bodam-secrets
              key: database-url
        - name: TOGETHER_AI_API_KEY
          valueFrom:
            secretKeyRef:
              name: bodam-secrets
              key: together-api-key
        - name: ADMIN_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: bodam-secrets
              key: admin-secret-key
        - name: REDIS_CACHE_URL
          value: redis://redis-cache:6379/0
        - name: REDIS_SEMANTIC_URL
          value: redis://redis-semantic:6379/1
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

### 13.2 Redis Deployment (Semantic Cache)

```yaml
# infra/k8s/redis/semantic-cache-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-semantic
  namespace: bodam
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis-semantic
  template:
    metadata:
      labels:
        app: redis-semantic
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        command:
        - redis-server
        - --requirepass
        - $(REDIS_PASSWORD)
        - --maxmemory
        - 256mb
        - --maxmemory-policy
        - allkeys-lru  # LRU 캐시 정책
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: bodam-secrets
              key: redis-password
        volumeMounts:
        - name: redis-data
          mountPath: /data
      volumes:
      - name: redis-data
        persistentVolumeClaim:
          claimName: redis-semantic-pvc
```

### 13.3 Secrets 생성

```bash
# Kubernetes Secret 생성
kubectl create secret generic bodam-secrets \
  --from-literal=database-url='postgresql+asyncpg://...' \
  --from-literal=together-api-key='your_together_api_key' \
  --from-literal=admin-secret-key='your_32_char_secret' \
  --from-literal=redis-password='your_redis_password' \
  -n bodam
```

## 14. 성능 벤치마크

### 예상 성능 지표

| 메트릭 | 목표 | 측정 방법 |
|--------|------|-----------|
| Semantic Cache Hit | 2-3ms | Redis GET 레이턴시 |
| Semantic Cache Miss | 40-50ms | DB 쿼리 + 임베딩 비교 |
| Llama AI API Latency | 200-500ms | Together AI API 응답 시간 |
| 전체 쿼리 응답 (캐시 히트) | < 100ms | 종단간 API 응답 |
| 전체 쿼리 응답 (캐시 미스) | < 1초 | 종단간 API 응답 |
| 환불 Bulk Action (100건) | < 5초 | 데이터베이스 트랜잭션 |

### 성능 테스트 스크립트

```bash
# K6 부하 테스트
k6 run specs/005-sqladmin-integration-with/contracts/k6-admin-load-test.js

# 결과 예시:
# ✓ llama_query_duration_p95 < 1000ms
# ✓ semantic_cache_hit_rate > 60%
# ✓ admin_login_duration_p95 < 200ms
```

## 15. 운영 체크리스트

### 일일 점검 항목

- [ ] 관리자 로그인 성공/실패 횟수 확인
- [ ] Llama AI 쿼리 응답 시간 모니터링
- [ ] Semantic Cache 히트율 확인 (목표: 60% 이상)
- [ ] 환불 처리 대기 건수 확인
- [ ] 에러 로그 검토 (5XX, SQL 에러)

### 주간 점검 항목

- [ ] Redis 메모리 사용량 확인 (최대 256MB)
- [ ] PostgreSQL 디스크 사용량 확인
- [ ] Together AI API 사용량 및 비용 확인
- [ ] Audit Log 백업 및 아카이빙
- [ ] 관리자 계정 활동 감사

### 월간 점검 항목

- [ ] PostgreSQL 인덱스 재구축 (VACUUM ANALYZE)
- [ ] Redis RDB 스냅샷 백업 검증
- [ ] 관리자 계정 비밀번호 정책 강화
- [ ] 보안 패치 적용 (SQLAdmin, FastAPI, PostgreSQL, Redis)
- [ ] 성능 벤치마크 재실행 및 비교

## 16. 참고 자료

### 공식 문서
- [SQLAdmin Documentation](https://github.com/aminalaee/sqladmin)
- [Together AI API Reference](https://docs.together.ai/reference/chat-completions)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [PostgreSQL pgvector](https://github.com/pgvector/pgvector)

### 내부 문서
- `/home/eugene/bodam/specs/005-sqladmin-integration-with/spec.md` - 전체 스펙
- `/home/eugene/bodam/specs/005-sqladmin-integration-with/quickstart.md` - 빠른 시작
- `/home/eugene/bodam/specs/005-sqladmin-integration-with/contracts/` - OpenAPI 계약

### Contact
- 관리자: admin@bodam.local
- 기술 지원: support@bodam.local
- 보안 이슈: security@bodam.local

---

**마지막 업데이트:** 2025-10-17
**버전:** 1.0.0
**작성자:** BoDam Engineering Team
