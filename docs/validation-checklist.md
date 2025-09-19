# 검증 체크리스트 실행 계획

## T108 quickstart.md 검증 시나리오
1. `.env.example`을 복사해 환경 변수 설정
2. `docker-compose up --build`
3. 백엔드 `/healthz`, 프론트엔드 `http://localhost:3000` 확인

## T109 테스트 커버리지 ≥70%
- 백엔드: `pytest --cov=src` 실행, 결과 보고서 첨부
- 프론트엔드: `npm run test -- --coverage`

## T110 성능 검증
- `k6 run tests/performance/donations.js`
- 결과에서 p95 응답 시간 확인 (<300ms 목표)

## T111 보안 감사 체크리스트
- BOLA, 입력 검증, SQL Injection 테스트 수행
- OAuth 리디렉션, 쿠키 설정 검사

## T112 프로덕션 준비
- Alembic 마이그레이션 적용 여부 확인
- Prometheus/Grafana 구성 점검
- 릴리즈 노트 작성

