# Local Environment Setup

이 저장소를 처음 받은 사람이 필요한 도구만 설치되어 있다면 `scripts/setup-local.sh` 한 번으로 공통 개발 환경을 맞출 수 있습니다.

## Prerequisites
- Python 3.11 이상 (`python3 --version`)
- Node.js + npm (`npm --version`)
- Docker + Docker Compose plugin (`docker compose version`)

## Usage
```bash
# 저장소 루트에서 실행
bash scripts/setup-local.sh
```

스크립트는 다음을 수행합니다.
1. 리포지토리 루트에 `.venv/` 가 없으면 새 Python 가상환경을 생성하고 활성화합니다.
2. 최신 `pip`으로 올린 뒤 `backend/`의 의존성을 설치합니다.
3. `backend/.env` 가 없으면 `backend/.env.example` 을 복사해 초기 설정을 만듭니다.
4. `npm` 이 있으면 `frontend/`에서 `npm ci` (또는 `npm install`) 로 의존성을 설치합니다.
5. Docker가 있으면 `docker compose build backend`, `docker compose up -d db redis`, `docker compose run --rm backend alembic upgrade head` 를 차례대로 실행해 컨테이너와 데이터베이스 스키마를 준비합니다.

## After Running
- 백엔드 개발 서버: `docker compose up backend`
- 프런트엔드 개발 서버: `cd frontend && npm run dev`

문제가 생기면 스크립트가 빨간 메시지로 중단되며, 필요한 도구를 설치한 뒤 다시 실행하면 됩니다.
