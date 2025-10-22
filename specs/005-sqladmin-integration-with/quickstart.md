# 빠른 시작 가이드: SQLAdmin + Llama AI 채팅

이 가이드는 SQLAdmin 관리자 인터페이스와 Llama AI 채팅 기능을 빠르게 시작하는 방법을 설명합니다.

## 사전 요구사항

### 1. 환경 변수 설정
`.env` 파일에 다음 변수를 추가하세요:

```bash
# Together AI API 키
TOGETHER_AI_API_KEY=your_together_ai_api_key_here

# SQLAdmin 설정
ADMIN_SECRET_KEY=your_secret_key_for_session_encryption

# Redis (Semantic Cache용)
REDIS_URL=redis://localhost:6379/1

# 데이터베이스 (기존)
DATABASE_URL=postgresql+asyncpg://user:password@localhost/bodam
```

### 2. 의존성 설치
```bash
cd backend
pip install sqladmin>=0.16.0 together>=1.0.0
```

### 3. 관리자 계정 생성
데이터베이스에 관리자 계정이 없다면 생성하세요:

```python
# scripts/create_admin.py
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.models.user import User, UserRole
from passlib.hash import bcrypt

async def create_admin_user():
    engine = create_async_engine("postgresql+asyncpg://user:password@localhost/bodam")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        admin = User(
            email="admin@bodam.example.com",
            password_hash=bcrypt.hash("your_secure_password"),
            name="관리자",
            role=UserRole.ADMIN,
            is_active=True
        )
        session.add(admin)
        await session.commit()
        print(f"관리자 계정 생성 완료: {admin.email}")

asyncio.run(create_admin_user())
```

### 4. 서버 시작
```bash
cd backend
uvicorn src.main:app --reload --port 8000
```

---

## 1. 관리자 로그인

### 1.1 로그인 페이지 접속
브라우저에서 다음 URL로 이동:
```
http://localhost:8000/admin/login
```

### 1.2 자격 증명 입력
- **이메일**: admin@bodam.example.com
- **비밀번호**: your_secure_password

### 1.3 대시보드 확인
로그인 성공 시 관리자 대시보드로 리다이렉트됩니다:
```
http://localhost:8000/admin
```

**대시보드에서 확인할 수 있는 정보:**
- 총 사용자 수
- 총 기부 금액
- 대기 중 환불 건수
- 활성 구독 수
- 최근 활동 로그

---

## 2. 사용자 관리 테스트

### 2.1 사용자 목록 조회
왼쪽 메뉴에서 **User** 클릭:
```
http://localhost:8000/admin/user
```

**확인 사항:**
- 사용자 목록이 테이블 형태로 표시됨
- 페이지네이션 동작 (기본 20개씩)
- 검색 기능 테스트 (이메일 또는 이름으로)

### 2.2 필터링 테스트
상단 필터 옵션 사용:
- **Role**: `donor` 선택 → 기부자만 표시
- **Tier**: `1` 선택 → 1등급 사용자만 표시
- **Is Active**: `true` 선택 → 활성 사용자만 표시

### 2.3 사용자 상세 조회
목록에서 사용자 한 명 클릭:
```
http://localhost:8000/admin/user/{user_id}
```

**확인 사항:**
- 모든 필드 표시 (`password_hash`는 숨김)
- 관련 기부 내역 표시
- 수정 가능 (이름, 전화번호, tier 등)

### 2.4 사용자 정보 수정
1. 상세 페이지에서 **Edit** 버튼 클릭
2. `tier` 값을 `1`에서 `2`로 변경
3. **Save** 버튼 클릭
4. 목록 페이지로 돌아가서 변경 사항 확인

---

## 3. Llama AI 채팅 테스트

### 3.1 채팅 인터페이스 접속
대시보드 우측 상단의 **AI Chat** 버튼 클릭 또는:
```
http://localhost:8000/admin
```
(대시보드에 임베디드된 채팅 위젯 사용)

### 3.2 간단한 통계 쿼리
채팅창에 다음 질문 입력:
```
최근 30일 기부 총액은?
```

**예상 응답:**
```
최근 30일간 총 12,500,000원의 기부가 완료되었습니다.

[실행된 SQL]
SELECT SUM(amount) as total
FROM donations
WHERE created_at >= NOW() - INTERVAL '30 days'
  AND status = 'completed'

[실행 시간] 45.2ms
```

### 3.3 검색 쿼리
```
서울에 있는 소방서 목록 보여줘
```

**예상 응답:**
```
서울에는 현재 2개의 활성 소방서가 있습니다:

1. 종로소방서 (02-1234-5678)
   - 주소: 서울특별시 종로구...

2. 중구소방서 (02-2345-6789)
   - 주소: 서울특별시 중구...

[실행 시간] 28.7ms
```

### 3.4 분석 쿼리
```
상위 10명의 기부자는?
```

**예상 응답:**
```
상위 10명의 기부자 목록입니다:

1. 홍길동 (hong@example.com) - 5,000,000원
2. 김철수 (kim@example.com) - 3,500,000원
3. 이영희 (lee@example.com) - 2,800,000원
...

[실행 시간] 32.1ms
```

### 3.5 관계 쿼리
```
user ID가 {특정 UUID}인 사용자의 모든 기부 내역 보여줘
```

**예상 응답:**
```
해당 사용자의 기부 내역 총 5건:

1. 2025-10-15 - 100,000원 (종로소방서) - 완료
2. 2025-09-20 - 50,000원 (중구소방서) - 완료
3. 2025-08-10 - 200,000원 (강남소방서) - 완료
...

[실행 시간] 18.9ms
```

### 3.6 대화 기록 확인
1. 채팅창 우측 상단 **History** 버튼 클릭
2. 이전 질문과 답변 목록 확인
3. 특정 질문 클릭 시 해당 시점으로 이동

### 3.7 대화 기록 초기화
1. 채팅창 우측 상단 **Clear** 버튼 클릭
2. 확인 다이얼로그에서 **OK** 클릭
3. 대화 기록이 모두 삭제됨

---

## 4. 환불 bulk 승인 테스트

### 4.1 환불 목록 조회
왼쪽 메뉴에서 **Refund** 클릭:
```
http://localhost:8000/admin/refund
```

### 4.2 대기 중 환불 필터링
상단 필터에서 **Status**: `pending` 선택

**확인 사항:**
- 대기 중 환불 요청만 표시됨
- 각 항목에 체크박스 표시됨

### 4.3 여러 환불 선택
1. 승인할 환불 요청 3개 체크박스 선택
2. 목록 상단의 **Bulk Actions** 드롭다운 클릭
3. **Approve Selected** 선택

### 4.4 승인 사유 입력
모달 창이 나타나면:
1. **Reason** 필드에 입력:
   ```
   정상적인 환불 요청으로 확인됨
   ```
2. **Confirm** 버튼 클릭

### 4.5 결과 확인
**성공 시:**
```
성공: 3건의 환불이 승인되었습니다.
- f47ac10b-58cc-4372-a567-0e02b2c3d479 ✓
- f47ac10b-58cc-4372-a567-0e02b2c3d480 ✓
- f47ac10b-58cc-4372-a567-0e02b2c3d481 ✓
```

**부분 성공 시:**
```
경고: 2건 승인, 1건 실패
성공:
- f47ac10b-58cc-4372-a567-0e02b2c3d479 ✓
- f47ac10b-58cc-4372-a567-0e02b2c3d481 ✓

실패:
- f47ac10b-58cc-4372-a567-0e02b2c3d480 ✗
  이유: Toss API 오류 - 이미 환불된 결제입니다.
```

### 4.6 감사 로그 확인
1. 왼쪽 메뉴에서 **Audit Logs** → **Refunds** 클릭
2. 방금 수행한 bulk 승인 액션 확인:
   - 액션 유형: `bulk_approve`
   - 처리자: `admin@bodam.example.com`
   - 처리 시각
   - 성공/실패 건수

---

## 5. Semantic Cache 확인

Semantic Cache는 유사한 질문을 빠르게 응답하기 위한 기능입니다.

### 5.1 첫 번째 쿼리
채팅창에 입력:
```
최근 30일 기부 총액은?
```

**응답 확인:**
```
...
[실행 시간] 45.2ms
[캐시됨] 아니오
```

### 5.2 유사한 쿼리 (즉시)
곧바로 다음 질문 입력:
```
최근 한 달 기부 금액 합계는?
```

**응답 확인:**
```
...
[실행 시간] 2.1ms  ← 훨씬 빠름!
[캐시됨] 예 (유사도: 0.97)
```

**설명:**
- 두 질문의 의미가 동일함 (임베딩 유사도 > 0.95)
- 캐시된 결과를 즉시 반환
- 실행 시간이 20배 이상 단축

### 5.3 다른 표현 테스트
다양한 표현으로 같은 질문 테스트:
```
지난 30일간 총 기부액은 얼마야?
최근 1개월 동안 받은 기부 총액 알려줘
```

**모두 캐시에서 응답됨 (2-3ms)**

### 5.4 캐시 TTL 확인
1. 5분 대기 (캐시 TTL)
2. 동일한 질문 다시 입력
3. 캐시 미스 → 다시 DB 쿼리 실행 (45ms)

---

## 6. 문제 해결

### 6.1 로그인 실패
**증상:** "Invalid credentials" 에러

**해결 방법:**
1. 관리자 계정 존재 확인:
   ```sql
   SELECT email, role FROM users WHERE role = 'admin';
   ```
2. 비밀번호 재설정:
   ```python
   # scripts/reset_admin_password.py
   from passlib.hash import bcrypt
   # ... (관리자 계정의 password_hash 업데이트)
   ```

### 6.2 Llama AI 응답 없음
**증상:** 채팅 입력 후 오랜 시간 대기

**해결 방법:**
1. Together AI API 키 확인:
   ```bash
   echo $TOGETHER_AI_API_KEY
   ```
2. API 키 유효성 테스트:
   ```bash
   curl -H "Authorization: Bearer $TOGETHER_AI_API_KEY" \
     https://api.together.xyz/v1/models
   ```
3. 로그 확인:
   ```bash
   tail -f backend/logs/app.log | grep "together"
   ```

### 6.3 SQL 에러 발생
**증상:** "Unsafe query detected" 에러

**원인:** Llama AI가 읽기 전용이 아닌 쿼리 생성 (UPDATE, DELETE 등)

**해결 방법:**
1. 질문을 더 명확하게 수정:
   - 잘못된 예: "사용자 tier를 2로 바꿔줘"
   - 올바른 예: "tier가 2인 사용자 목록 보여줘"
2. 로그에서 생성된 SQL 확인
3. 필요 시 수동으로 SQLAdmin UI에서 수정

### 6.4 캐시 동작 안 함
**증상:** 유사한 질문도 항상 DB 쿼리 실행

**해결 방법:**
1. Redis 연결 확인:
   ```bash
   redis-cli -u $REDIS_URL ping
   ```
2. Redis 캐시 키 확인:
   ```bash
   redis-cli -u $REDIS_URL --scan --pattern "llama_cache:*"
   ```
3. 캐시 수동 초기화:
   ```bash
   redis-cli -u $REDIS_URL FLUSHDB
   ```

### 6.5 환불 승인 실패
**증상:** "Toss API error" 메시지

**해결 방법:**
1. Toss API 키 확인:
   ```bash
   echo $TOSS_SECRET_KEY
   ```
2. 기부 정보 확인:
   ```sql
   SELECT toss_payment_key, toss_order_id, status
   FROM donations
   WHERE id = '{donation_id}';
   ```
3. 이미 환불된 경우 → 환불 요청 거부 처리

### 6.6 페이지 로딩 느림
**증상:** 사용자 목록 페이지가 10초 이상 걸림

**해결 방법:**
1. 데이터베이스 인덱스 확인:
   ```sql
   SELECT indexname, indexdef
   FROM pg_indexes
   WHERE tablename = 'users';
   ```
2. 필요 시 인덱스 추가:
   ```sql
   CREATE INDEX idx_users_email ON users(email);
   CREATE INDEX idx_users_role ON users(role);
   ```
3. SQLAdmin 페이지네이션 크기 조정:
   - 기본 20개 → 10개로 감소

---

## 7. 다음 단계

### 7.1 고급 쿼리 작성
Llama AI에게 더 복잡한 질문 시도:
```
지난 3개월간 월별 기부 추이를 보여줘
```
```
서울에서 기부를 가장 많이 받은 소방서 Top 5는?
```
```
정기 기부 구독자 중 30일 이상 활동 없는 사람은?
```

### 7.2 커스텀 뷰 추가
특정 모델에 대한 SQLAdmin 뷰 커스터마이징:
- `backend/src/admin/views/user.py` 수정
- 커스텀 필터, 정렬, 액션 추가

### 7.3 알림 설정
환불 승인/거부 시 사용자에게 이메일 또는 SMS 알림 전송

### 7.4 권한 세분화
- `moderator` 역할: NewsContent 검토만 가능
- `admin` 역할: 모든 뷰 접근 가능

### 7.5 모니터링 대시보드
Grafana 또는 Metabase 연동으로 고급 분석 대시보드 구축

---

## 참고 자료

### 공식 문서
- [SQLAdmin 문서](https://aminalaee.dev/sqladmin/)
- [Together AI API 문서](https://docs.together.ai/)
- [Llama 3.3 70B 모델](https://www.llama.com/)

### 프로젝트 문서
- `/home/eugene/bodam/specs/005-sqladmin-integration-with/spec.md`
- `/home/eugene/bodam/specs/005-sqladmin-integration-with/plan.md`
- `/home/eugene/bodam/specs/005-sqladmin-integration-with/data-model.md`

### 계약서
- `/home/eugene/bodam/specs/005-sqladmin-integration-with/contracts/admin-ui-routes.yaml`
- `/home/eugene/bodam/specs/005-sqladmin-integration-with/contracts/admin-chat-api.yaml`
- `/home/eugene/bodam/specs/005-sqladmin-integration-with/contracts/admin-refund-actions.yaml`

---

## 지원

문제가 발생하면:
1. 로그 파일 확인: `backend/logs/app.log`
2. 이슈 생성: GitHub Issues
3. 팀 Slack 채널에 문의

---

**축하합니다!** SQLAdmin + Llama AI 채팅 기능을 성공적으로 테스트하셨습니다.
