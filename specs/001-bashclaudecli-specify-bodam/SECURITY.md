# 보담(BoDam) 보안 가이드 🔐

## 개요
보담 플랫폼의 보안 정책, 위협 모델, 보안 통제 방안을 정의합니다. 개인정보보호법(PIPA), 정보통신망법, PCI DSS 준수를 목표로 합니다.

## 🛡️ 보안 원칙

### 1. 다층 보안 (Defense in Depth)
- **네트워크 계층**: WAF, DDoS 보호, VPC 격리
- **애플리케이션 계층**: 입력 검증, CSRF/XSS 방어
- **데이터 계층**: 암호화, 접근 제어, 감사 로깅
- **인프라 계층**: 컨테이너 보안, K8s RBAC

### 2. 최소 권한 원칙 (Principle of Least Privilege)
```yaml
# Kubernetes RBAC 예시
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: bodam-api-role
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get"]
  resourceNames: ["db-credentials", "toss-api-key"]
```

### 3. 보안 by Design
- 개발 단계부터 보안 고려사항 반영
- 정기적인 보안 검토 및 위험 평가
- 자동화된 보안 테스트 통합

## 🔑 인증 및 인가 (Authentication & Authorization)

### JWT & CSRF 토큰 관리
```python
# backend/src/security/session.py
SESSION_COOKIE_NAME = "bodam_session"
CSRF_COOKIE_NAME = "bodam_csrf"
CSRF_HEADER_NAME = "X-CSRF-Token"

def issue_session_tokens(response: Response, user: User) -> dict[str, str]:
    access_token = create_access_token(str(user.id))
    csrf_token = secrets.token_urlsafe(32)

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=access_token,
        httponly=True,
        samesite=settings.cookie_samesite,
        secure=settings.cookie_secure,
    )
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        samesite=settings.cookie_samesite,
        secure=settings.cookie_secure,
    )
    return {"access_token": access_token, "csrf_token": csrf_token}
```

### 토큰 저장 및 전달 방식
- **Access Token**: HttpOnly 쿠키(`bodam_session`) + 응답 JSON 동시 발급 (헤더 전송용)
- **CSRF Token**: Non-HttpOnly 쿠키(`bodam_csrf`)와 `X-CSRF-Token` 헤더 일치 여부 검증 (Double Submit)
- **로그아웃**: `bodam_session`, `bodam_csrf` 동시 삭제
- **결제 API**: `Authorization: Bearer <access_token>` 헤더 필수
- **일반 API**: 쿠키 기반 인증 + CSRF 검사 (SameSite 기본값 `Lax`)

### OAuth2 소셜 로그인 보안
```python
# OAuth2 state 검증
def verify_oauth_state(request_state: str, session_state: str) -> bool:
    return hmac.compare_digest(request_state, session_state)

# 프로필 정보 최소 수집
OAUTH_SCOPES = {
    "google": ["openid", "email", "profile"],
    "kakao": ["account_email", "profile_nickname"],
    "naver": ["email", "nickname"]
}
```

## 🔒 데이터 보안

### 1. 암호화 정책
```sql
-- 개인정보 필드 암호화 (PostgreSQL)
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name_encrypted BYTEA,  -- AES-256 암호화
    phone_encrypted BYTEA, -- AES-256 암호화
    password_hash VARCHAR(255), -- bcrypt
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2. 데이터 마스킹
```python
# PII 데이터 마스킹
def mask_phone(phone: str) -> str:
    if len(phone) >= 11:
        return f"{phone[:3]}****{phone[-4:]}"
    return "****"

def mask_email(email: str) -> str:
    local, domain = email.split("@")
    if len(local) > 2:
        return f"{local[:2]}***@{domain}"
    return f"***@{domain}"
```

### 3. 데이터베이스 보안
```python
# SQLAlchemy 보안 설정
DATABASE_CONFIG = {
    "postgresql_url": "postgresql://user:pass@localhost/bodam",
    "echo": False,  # 프로덕션에서 SQL 로깅 비활성화
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "connect_args": {
        "sslmode": "require",
        "sslcert": "/path/to/client-cert.pem",
        "sslkey": "/path/to/client-key.pem"
    }
}
```

## 🌐 API 보안

### 1. Rate Limiting
```python
# Redis 기반 Rate Limiting
class RateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def is_allowed(self, key: str, limit: int, window: int) -> bool:
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, window)
        return current <= limit

# 엔드포인트별 제한
RATE_LIMITS = {
    "/auth/login": "5/minute",
    "/donations": "10/minute",
    "/api/*": "100/minute"
}
```

### 2. 입력 검증
```python
# Pydantic 모델 검증
class DonationCreate(BaseModel):
    fire_station_id: UUID
    amount: int = Field(ge=1000, le=1000000)  # 1천원~100만원
    message: str = Field(max_length=500)

    @validator('message')
    def validate_message(cls, v):
        # XSS 방지를 위한 HTML 태그 제거
        return bleach.clean(v, tags=[], strip=True)
```

### 3. CORS 및 CSP 설정
```python
# FastAPI CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://bodam.example", "https://app.bodam.example"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"]
)

# Content Security Policy
CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' https://js.toss.im; "
    "img-src 'self' https://maps.naver.com; "
    "connect-src 'self' https://api.bodam.example"
)
```

## 💳 결제 보안 (PCI DSS 준수)

### 1. Toss Payments 연동 보안
```python
# 결제 검증
class PaymentVerifier:
    def verify_payment(self, payment_key: str, order_id: str, amount: int) -> bool:
        # Toss API 검증 요청
        response = requests.post(
            "https://api.tosspayments.com/v1/payments/confirm",
            auth=(self.secret_key, ""),
            json={
                "paymentKey": payment_key,
                "orderId": order_id,
                "amount": amount
            }
        )
        return response.status_code == 200
```

### 2. 카드 정보 미저장 원칙
- 카드 번호, CVV, 만료일 저장 금지
- Toss Payments 토큰 방식 사용
- PCI DSS SAQ-A 수준 준수

## 🚨 보안 모니터링

### 1. 보안 이벤트 로깅
```python
# 보안 로그 구조
SECURITY_LOG_FORMAT = {
    "timestamp": "2025-09-19T12:00:00Z",
    "event_type": "auth_failure",
    "user_id": "uuid",
    "ip_address": "1.2.3.4",
    "user_agent": "Mozilla/5.0...",
    "details": {
        "reason": "invalid_password",
        "attempt_count": 3
    }
}
```

### 2. 이상 행위 탐지
```python
# 의심스러운 로그인 패턴 감지
class AnomalyDetector:
    async def detect_suspicious_login(self, user_id: str, ip: str) -> bool:
        # 1. 지리적 위치 급변 체크
        # 2. 비정상적인 로그인 시간 체크
        # 3. 다중 실패 후 성공 패턴 체크
        # 4. 새로운 디바이스/브라우저 체크
        pass
```

### 3. 실시간 알림
```yaml
# Prometheus 알림 규칙
groups:
- name: security
  rules:
  - alert: HighFailedLogins
    expr: rate(auth_failures_total[5m]) > 10
    for: 2m
    annotations:
      summary: "높은 로그인 실패율 감지"

  - alert: SuspiciousPayment
    expr: rate(payment_failures_total[1m]) > 5
    annotations:
      summary: "의심스러운 결제 패턴 감지"
```

## 🐛 취약점 관리

### 1. OWASP Top 10 대응

#### A1: 주입 공격 (Injection)
```python
# Parameterized Query 사용
async def get_user_donations(user_id: str) -> List[Donation]:
    query = select(Donation).where(Donation.user_id == user_id)
    result = await session.execute(query)
    return result.scalars().all()
```

#### A2: 인증 취약점
```python
# 비밀번호 정책 강화
PASSWORD_REQUIREMENTS = {
    "min_length": 8,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_numbers": True,
    "require_symbols": True
}
```

#### A3: 민감 데이터 노출
```python
# 로그에서 민감 정보 제거
class SecurityFilter:
    SENSITIVE_FIELDS = ["password", "token", "card_number", "ssn"]

    def filter_log(self, data: dict) -> dict:
        return {k: "***" if k in self.SENSITIVE_FIELDS else v
                for k, v in data.items()}
```

### 2. 정기 보안 점검
```bash
# 의존성 취약점 스캔
npm audit
pip-audit
trivy image bodam:latest

# SAST 정적 분석
bandit -r backend/src/
semgrep --config=auto frontend/src/

# 컨테이너 보안 스캔
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image bodam:latest
```

## 🔐 비밀번호 및 시크릿 관리

### 1. Kubernetes Secrets
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: bodam-secrets
type: Opaque
data:
  database-url: <base64-encoded>
  jwt-secret: <base64-encoded>
  toss-secret-key: <base64-encoded>
```

### 2. 환경별 시크릿 분리
```python
# 개발/운영 환경 분리
class Config:
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.secret_manager = self._get_secret_manager()

    def _get_secret_manager(self):
        if self.environment == "production":
            return KubernetesSecretManager()
        else:
            return LocalSecretManager()
```

## 📋 보안 체크리스트

### 개발 단계
- [ ] 입력 검증 구현
- [ ] SQL 인젝션 방지
- [ ] XSS/CSRF 보호
- [ ] 인증/인가 구현
- [ ] 에러 메시지 sanitization

### 배포 전
- [ ] 의존성 취약점 스캔
- [ ] SAST/DAST 테스트 실행
- [ ] 컨테이너 이미지 스캔
- [ ] TLS 인증서 확인
- [ ] 보안 설정 검토

### 운영 중
- [ ] 로그 모니터링 활성화
- [ ] 백업 암호화 확인
- [ ] 접근 권한 정기 검토
- [ ] 보안 패치 적용
- [ ] 침투 테스트 수행

## 🚨 보안 사고 대응

### 1. 사고 분류
- **Level 1**: 정보 수집, 스캔 시도
- **Level 2**: 인증 우회, 권한 상승
- **Level 3**: 데이터 유출, 시스템 장애
- **Level 4**: 대규모 데이터 침해

### 2. 대응 절차
```python
# 자동 차단 시스템
class SecurityIncidentHandler:
    async def handle_incident(self, incident_type: str, details: dict):
        if incident_type == "brute_force":
            await self.block_ip(details["ip_address"], duration="1h")
        elif incident_type == "sql_injection":
            await self.block_ip(details["ip_address"], duration="24h")
            await self.notify_security_team(details)
```

### 3. 복구 계획
1. **즉시 조치**: 피해 차단, 로그 보존
2. **조사**: 침해 경로 분석, 피해 범위 확인
3. **복구**: 시스템 복원, 보안 강화
4. **사후 관리**: 재발 방지, 정책 개선

## 📞 보안 연락처

- **보안팀**: security@bodam.example
- **긴급 연락처**: +82-10-XXXX-XXXX
- **버그 바운티**: bugbounty@bodam.example

---

이 보안 가이드는 지속적으로 업데이트되며, 새로운 위협에 대응하여 보안 정책을 개선해 나갑니다.

**보안은 선택이 아닌 필수입니다.** 🛡️
