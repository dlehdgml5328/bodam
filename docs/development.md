# 보담 개발 환경 설정 가이드

## 백엔드
1. `python3.11 -m venv venv && source venv/bin/activate`
2. `pip install -e backend` 혹은 `pip install -r backend/requirements.txt` (추후 정리)
3. `uvicorn src.main:app --reload`으로 개발 서버 실행
4. `pytest`로 테스트, `ruff check`로 린트 실행

## 프론트엔드
1. `cd frontend && npm install`
2. `npm run dev`로 개발 서버 실행 (기본 포트 3000)
3. `npm run lint`와 `npm run test`로 코드 품질 확인

## 도커 및 컴포즈
- `docker-compose up`으로 PostgreSQL, Redis, 백엔드, 프론트엔드를 통합 실행
- `docker exec -it` 명령으로 컨테이너에 접근

## 환경 변수
- 루트 `.env.example`을 복사하여 `.env` 생성
- 백엔드/프론트 각각의 `.env.example`도 동일하게 복사 후 수정

## 추가 참고 문서
- `docs/deployment.md`: 배포 가이드
- `specs/001-bashclaudecli-specify-bodam/` 디렉터리: 상세 기능 명세와 설계 자료

