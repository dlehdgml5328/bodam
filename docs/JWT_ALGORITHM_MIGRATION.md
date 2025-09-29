# JWT 알고리즘 마이그레이션 가이드

## 개요

BoDam 프로젝트는 개발/프로덕션 환경에 따라 다른 JWT 알고리즘을 사용할 수 있도록 구성되어 있습니다.

- **개발 환경**: HS256 (HMAC with SHA-256)
- **프로덕션 환경**: RS256 (RSA Signature with SHA-256)

## 환경별 설정

### 개발 환경 (HS256)

```bash
# .env.dev
JWT_ALGORITHM=HS256
JWT_SECRET=your-dev-secret-key-must-be-at-least-32-characters-long
```

**장점:**
- 설정이 간단함
- 개발/테스트에 적합
- 성능이 빠름

**단점:**
- 대칭키 방식으로 보안성이 상대적으로 낮음
- 키 공유 시 보안 위험

### 프로덕션 환경 (RS256)

```bash
# .env.prod
JWT_ALGORITHM=RS256
JWT_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
-----END RSA PRIVATE KEY-----"
JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A...
-----END PUBLIC KEY-----"
```

**장점:**
- 비대칭키 방식으로 보안성이 높음
- 키 회전이 용이함
- 분산 환경에서 검증 용이
- 규제/감사 요구사항 충족

**단점:**
- 설정이 복잡함
- 키 관리 필요
- 상대적으로 느림

## RSA 키 생성

### 1. OpenSSL로 키 생성

```bash
# 2048비트 RSA 개인키 생성
openssl genrsa -out private.pem 2048

# 공개키 추출
openssl rsa -in private.pem -pubout -out public.pem

# 개인키 내용 확인
cat private.pem

# 공개키 내용 확인
cat public.pem
```

### 2. 환경변수 설정

생성된 키를 환경변수에 설정할 때는 줄바꿈을 유지해야 합니다:

```bash
# 개인키
export JWT_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA4f5wg5l2hKsTeNem/V41fGnJm6gOdrj8ym3rFkEjWT0Gn6jF
...
-----END RSA PRIVATE KEY-----"

# 공개키
export JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA4f5wg5l2hKsTeNem/V41
...
-----END PUBLIC KEY-----"
```

## 전환 시나리오

### RS256으로 전환해야 하는 경우

1. **토큰 검증 주체 확장**: 백엔드 외부에서도 토큰 검증이 필요한 경우
2. **규제/감사 요구**: 금융 서비스 등에서 강화된 보안 요구사항
3. **제3자 서비스 연동**: 모바일 앱이나 외부 서비스에서 직접 토큰 검증
4. **키 회전 자동화**: 정기적인 키 교체가 필요한 경우

### 전환 절차

1. **키 생성 및 배포**
   ```bash
   # 1. RSA 키 쌍 생성
   openssl genrsa -out private.pem 2048
   openssl rsa -in private.pem -pubout -out public.pem

   # 2. 키 저장소에 등록 (Vault, K8s Secret 등)
   kubectl create secret generic jwt-keys \
     --from-file=private.pem \
     --from-file=public.pem
   ```

2. **환경변수 업데이트**
   ```bash
   # 기존
   JWT_ALGORITHM=HS256
   JWT_SECRET=secret-key

   # 신규
   JWT_ALGORITHM=RS256
   JWT_PRIVATE_KEY="$(cat private.pem)"
   JWT_PUBLIC_KEY="$(cat public.pem)"
   ```

3. **배포 및 검증**
   - 스테이징 환경에서 테스트
   - 토큰 생성/검증 동작 확인
   - 프로덕션 점진적 배포

## 키 관리 모범 사례

### 1. 키 저장

- **개발**: 로컬 파일 또는 환경변수
- **프로덕션**: HashiCorp Vault, AWS Secrets Manager, K8s Secrets

### 2. 키 회전

```bash
# 1. 새 키 생성
openssl genrsa -out private-new.pem 2048
openssl rsa -in private-new.pem -pubout -out public-new.pem

# 2. 점진적 배포 (Blue-Green 또는 Rolling Update)
# - 새 키로 서명, 기존 키로도 검증 가능하도록 설정
# - 모든 인스턴스 업데이트 후 기존 키 제거

# 3. JWKS 엔드포인트 제공 (선택사항)
GET /auth/jwks
{
  "keys": [
    {
      "kty": "RSA",
      "use": "sig",
      "kid": "2024-01",
      "n": "...",
      "e": "AQAB"
    }
  ]
}
```

### 3. 모니터링

- 토큰 검증 실패율 모니터링
- 키 만료 알림 설정
- 비정상적인 토큰 사용 패턴 감지

## 성능 고려사항

### HS256 vs RS256 성능 비교

| 작업 | HS256 | RS256 | 비고 |
|------|-------|-------|------|
| 토큰 생성 | 빠름 | 중간 | RS256이 약 10-20배 느림 |
| 토큰 검증 | 빠름 | 빠름 | 공개키 검증은 빠름 |
| 메모리 사용 | 낮음 | 중간 | RSA 키 크기로 인한 차이 |

### 최적화 방안

1. **토큰 캐싱**: 검증된 토큰을 짧은 시간 캐싱
2. **키 캐싱**: RSA 키를 메모리에 캐싱
3. **토큰 TTL 조정**: 보안과 성능의 균형점 찾기

## 문제 해결

### 일반적인 오류

1. **키 형식 오류**
   ```
   ValueError: Could not deserialize key data
   ```
   → PEM 형식과 줄바꿈 확인

2. **알고리즘 불일치**
   ```
   JWTError: The specified alg value is not allowed
   ```
   → JWT_ALGORITHM 환경변수 확인

3. **키 길이 부족**
   ```
   ValueError: JWT_SECRET must be at least 32 characters long
   ```
   → HS256용 비밀키 길이 확인

### 디버깅 도구

```python
# JWT 디코딩 (검증 없이)
import jwt
payload = jwt.decode(token, options={"verify_signature": False})
print(payload)

# 키 정보 확인
from cryptography.hazmat.primitives import serialization
key = serialization.load_pem_private_key(private_key_bytes, password=None)
print(f"Key size: {key.key_size} bits")
```

## 마이그레이션 체크리스트

- [ ] RSA 키 쌍 생성
- [ ] 키 저장소 설정 (Vault/Secrets Manager)
- [ ] 환경변수 업데이트
- [ ] 스테이징 환경 테스트
- [ ] 모니터링 설정
- [ ] 프로덕션 배포
- [ ] 기존 토큰 만료 대기
- [ ] 키 회전 절차 문서화