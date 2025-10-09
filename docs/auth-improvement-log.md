# Auth Improvement Log

## 2025-10-02 – Session Hardening Tasks
- 준비: 회원 인증 흐름 실동작 여부 점검.
- 목표: `/auth/refresh` 엔드포인트가 실제 로그인 사용자를 기준으로 토큰을 돌려주도록 개선하고, 재사용 가능한 현재 사용자 의존성을 추가.
- 진행 1: `src/security/session.py`에 `get_current_user`, `issue_access_token` 헬퍼 추가.
- 진행 2: `/auth/login`, `/auth/refresh`가 헬퍼를 사용하도록 리팩터링.
- 진행 3: 통합 테스트(`/tests/integration/test_user_registration.py`)에 비로그인 상태 401 검증을 추가.
- 테스트: `pytest --override-ini addopts='' backend/tests/integration/test_user_registration.py` 실행 시 `geoalchemy2` 미설치로 수집 단계에서 실패 (기존 환경 제약).
- 추가: `backend/tests/unit/test_auth_session.py`로 `get_current_user`/`issue_session_tokens` 동작 단위 테스트 작성, `pytest --override-ini addopts='' backend/tests/unit/test_auth_session.py` 통과 확인.
- 업데이트: Access Token + CSRF 쿠키 동시 발급(`issue_session_tokens`), 결제 요청은 Bearer 헤더 필수로 변경. `CSRF_HEADER_NAME = "X-CSRF-Token"`.
