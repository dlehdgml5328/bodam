# 개발 환경 설정 가이드 🛠️

## 개요
보담(BoDam) 플랫폼의 로컬 개발 환경 구축, 개발 워크플로우, 코딩 표준을 정의합니다.

## 🏗️ 시스템 요구사항

### 기본 요구사항
- **OS**: macOS 12+, Ubuntu 20.04+, Windows 10+ (WSL2)
- **RAM**: 16GB+ 권장
- **Storage**: 50GB+ 여유 공간
- **Network**: 안정적인 인터넷 연결

### 필수 소프트웨어
```bash
# 1. Docker & Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER

# 2. Node.js 18+ (nvm 사용 권장)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18

# 3. Python 3.11+
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev

# 4. PostgreSQL Client (선택사항)
sudo apt install postgresql-client-14

# 5. Git
sudo apt install git
```

## 🐍 백엔드 개발 환경

### 1. Python 가상환경 설정
```bash
cd backend

# Python 가상환경 생성
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements-dev.txt
pip install -e .  # 개발 모드로 패키지 설치
```

### 2. 환경 변수 설정
```bash
# .env 파일 생성
cp .env.example .env

# 환경 변수 설정
cat > .env << 'EOF'
# 데이터베이스
DATABASE_URL=postgresql://bodam_user:bodam_pass@localhost:5432/bodam_dev
REDIS_URL=redis://localhost:6379/0

# JWT 시크릿
JWT_SECRET_KEY=your-super-secret-jwt-key-for-development
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Together AI
TOGETHER_API_KEY=your-together-ai-api-key

# Toss Payments (테스트 키)
TOSS_CLIENT_KEY=test_ck_docs_Ovk5rk1EwkEbP0W43n07xlzm
TOSS_SECRET_KEY=test_sk_docs_e92LAa5PVb3ZdNr3ka1Y5QEmqAe

# 소셜 로그인 (개발용)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
KAKAO_CLIENT_ID=your-kakao-client-id
KAKAO_CLIENT_SECRET=your-kakao-client-secret
NAVER_CLIENT_ID=your-naver-client-id
NAVER_CLIENT_SECRET=your-naver-client-secret

# 기타
ENVIRONMENT=development
LOG_LEVEL=DEBUG
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
EOF
```

### 3. 데이터베이스 설정
```bash
# Docker로 PostgreSQL + Redis 실행
docker-compose -f docker-compose.dev.yml up -d postgres redis

# 데이터베이스 마이그레이션
alembic upgrade head

# 개발용 샘플 데이터 삽입
python scripts/seed_dev_data.py
```

### 4. 백엔드 서버 실행
```bash
# 개발 서버 시작 (핫 리로드 활성화)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 또는 VS Code 디버깅 지원
python -m debugpy --listen 5678 --wait-for-client -m uvicorn src.main:app --reload

# Celery 워커 실행 (별도 터미널)
celery -A src.workers.main worker --loglevel=info --reload

# Celery 모니터링 (선택사항)
celery -A src.workers.main flower --port=5555
```

### 5. API 문서 확인
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## ⚛️ 프론트엔드 개발 환경

### 1. 의존성 설치
```bash
cd frontend

# Node.js 패키지 설치
npm install

# 또는 yarn 사용 시
yarn install
```

### 2. 환경 변수 설정
```bash
# .env.local 파일 생성
cat > .env.local << 'EOF'
# API 엔드포인트
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Naver Maps API
NEXT_PUBLIC_NAVER_MAP_CLIENT_ID=your-naver-map-client-id

# Toss Payments
NEXT_PUBLIC_TOSS_CLIENT_KEY=test_ck_docs_Ovk5rk1EwkEbP0W43n07xlzm

# 소셜 로그인 (클라이언트 키)
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id
NEXT_PUBLIC_KAKAO_CLIENT_ID=your-kakao-client-id
NEXT_PUBLIC_NAVER_CLIENT_ID=your-naver-client-id

# 기타
NEXT_PUBLIC_ENVIRONMENT=development
EOF
```

### 3. 프론트엔드 서버 실행
```bash
# 개발 서버 시작
npm run dev

# 또는 특정 포트로 실행
npm run dev -- --port 3001

# TypeScript 타입 체크 (별도 터미널)
npm run type-check --watch

# Tailwind CSS 빌드 (자동으로 실행됨)
npm run tailwind:watch
```

### 4. 스토리북 실행 (선택사항)
```bash
# 컴포넌트 문서화
npm run storybook

# 스토리북 빌드
npm run build-storybook
```

## 🧪 테스트 환경

### 1. 백엔드 테스트
```bash
cd backend

# 테스트 데이터베이스 설정
export DATABASE_URL=postgresql://bodam_user:bodam_pass@localhost:5432/bodam_test
alembic upgrade head

# 전체 테스트 실행
pytest

# 커버리지 포함 테스트
pytest --cov=src --cov-report=html --cov-report=term

# 특정 테스트 파일 실행
pytest tests/test_auth.py -v

# 테스트 파일 변경 감지 모드
pytest-watch

# 성능 테스트
pytest tests/performance/ --benchmark-only
```

### 2. 프론트엔드 테스트
```bash
cd frontend

# Jest 단위 테스트
npm test

# Jest 감시 모드
npm run test:watch

# E2E 테스트 (Playwright)
npm run test:e2e

# E2E 테스트 UI 모드
npm run test:e2e:ui

# 컴포넌트 테스트 (Testing Library)
npm run test:components
```

### 3. 통합 테스트
```bash
# 전체 스택 통합 테스트
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

# API 통합 테스트
newman run tests/postman/bodam-api-tests.json
```

## 🔧 개발 도구 설정

### 1. VS Code 설정
```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "./backend/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "88"],
  "typescript.preferences.importModuleSpecifier": "relative",
  "eslint.workingDirectories": ["frontend"],
  "tailwindCSS.includeLanguages": {
    "typescript": "javascript",
    "typescriptreact": "javascript"
  }
}
```

### 2. VS Code 확장 프로그램
```json
// .vscode/extensions.json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "ms-playwright.playwright",
    "humao.rest-client"
  ]
}
```

### 3. Git Hooks 설정
```bash
# pre-commit 설치
pip install pre-commit

# pre-commit 설정 (.pre-commit-config.yaml)
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        files: ^backend/

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.284
    hooks:
      - id: ruff
        files: ^backend/

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.0
    hooks:
      - id: prettier
        files: ^frontend/
EOF

# pre-commit 설치
pre-commit install
```

## 📋 코딩 표준

### 1. Python 코딩 스타일
```python
# backend/src/example.py

# 모듈 임포트 순서
import os  # 표준 라이브러리
from datetime import datetime

import httpx  # 서드파티 라이브러리
from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session

from src.models.user import User  # 로컬 모듈


# 클래스 정의
class UserService:
    """사용자 관련 비즈니스 로직 처리 클래스."""

    def __init__(self, db: Session):
        self.db = db

    async def create_user(self, user_data: dict) -> User:
        """새 사용자를 생성합니다.

        Args:
            user_data: 사용자 정보 딕셔너리

        Returns:
            생성된 User 객체

        Raises:
            HTTPException: 이메일이 이미 존재하는 경우
        """
        # 구현 코드...
        pass


# 함수 정의
async def validate_email(email: str) -> bool:
    """이메일 유효성을 검증합니다."""
    # 구현 코드...
    return True


# 상수 정의
MAX_DONATION_AMOUNT = 1_000_000
DEFAULT_PAGE_SIZE = 20
```

### 2. TypeScript 코딩 스타일
```typescript
// frontend/src/types/user.ts

// 타입 정의
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'donor' | 'admin';
  tier: number;
  totalDonated: number;
  createdAt: string;
}

export interface CreateUserRequest {
  email: string;
  password: string;
  name: string;
  phone?: string;
}

// 컴포넌트 정의
import React from 'react';
import { User } from '@/types/user';

interface UserProfileProps {
  user: User;
  onEdit: (userId: string) => void;
}

export const UserProfile: React.FC<UserProfileProps> = ({
  user,
  onEdit
}) => {
  const handleEditClick = () => {
    onEdit(user.id);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold text-gray-900">
        {user.name}
      </h2>
      <p className="text-sm text-gray-600">{user.email}</p>
      <button
        onClick={handleEditClick}
        className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
      >
        프로필 수정
      </button>
    </div>
  );
};
```

### 3. API 네이밍 규칙
```python
# REST API 엔드포인트 네이밍
GET    /api/v1/stations                    # 소방서 목록
GET    /api/v1/stations/{station_id}       # 소방서 상세
POST   /api/v1/stations/{station_id}/favorites  # 즐겨찾기 추가

GET    /api/v1/donations                   # 기부 내역
POST   /api/v1/donations                   # 기부 생성
GET    /api/v1/donations/{donation_id}     # 기부 상세
POST   /api/v1/donations/{donation_id}/refund  # 환불 요청

# 데이터베이스 테이블 네이밍
users                    # 사용자
fire_stations           # 소방서
donations               # 기부
donation_receipts       # 기부 영수증
user_favorites          # 사용자 즐겨찾기
```

## 🐳 Docker 개발 환경

### 1. Docker Compose 설정
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  postgres:
    image: postgis/postgis:15-3.3
    environment:
      POSTGRES_DB: bodam_dev
      POSTGRES_USER: bodam_user
      POSTGRES_PASSWORD: bodam_pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://bodam_user:bodam_pass@postgres:5432/bodam_dev
      REDIS_URL: redis://redis:6379/0
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
      - redis
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev

volumes:
  postgres_data:
  redis_data:
```

### 2. 개발용 Dockerfile
```dockerfile
# backend/Dockerfile.dev
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

# 소스 코드 복사
COPY . .

# 개발 모드로 패키지 설치
RUN pip install -e .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

## 🔄 개발 워크플로우

### 1. 기능 개발 프로세스
```bash
# 1. 새 기능 브랜치 생성
git checkout -b feature/donation-recurring

# 2. 백엔드 API 개발
cd backend
# TDD 방식으로 테스트 먼저 작성
vim tests/test_recurring_donations.py
pytest tests/test_recurring_donations.py  # 실패 확인

# API 구현
vim src/api/donations.py
vim src/services/donation_service.py
pytest tests/test_recurring_donations.py  # 성공 확인

# 3. 프론트엔드 개발
cd ../frontend
# 컴포넌트 개발
vim src/components/RecurringDonationForm.tsx
npm test src/components/RecurringDonationForm.test.tsx

# 4. 통합 테스트
npm run test:e2e tests/recurring-donation.spec.ts

# 5. 코드 리뷰 준비
git add .
git commit -m "feat: add recurring donation functionality"
git push origin feature/donation-recurring
```

### 2. 핫픽스 프로세스
```bash
# 1. 핫픽스 브랜치 생성
git checkout main
git checkout -b hotfix/payment-validation

# 2. 빠른 수정
vim backend/src/services/payment_service.py
pytest tests/test_payment_service.py

# 3. 즉시 배포 가능한 상태로 준비
git commit -m "fix: improve payment validation logic"
git push origin hotfix/payment-validation
```

## 📊 개발 메트릭

### 1. 코드 품질 측정
```bash
# 백엔드 코드 품질
cd backend
ruff check src/          # 린팅
mypy src/               # 타입 체킹
pytest --cov=src --cov-report=html  # 테스트 커버리지

# 프론트엔드 코드 품질
cd frontend
npm run lint            # ESLint
npm run type-check      # TypeScript 체크
npm run test -- --coverage  # 테스트 커버리지
```

### 2. 성능 모니터링
```bash
# API 성능 테스트
cd backend
python scripts/load_test.py

# 프론트엔드 성능
cd frontend
npm run lighthouse      # Lighthouse 감사
npm run bundle-analyzer # 번들 크기 분석
```

## 🐛 디버깅 가이드

### 1. 백엔드 디버깅
```python
# 로깅 설정
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 디버그 포인트 설정
import pdb; pdb.set_trace()

# 또는 VS Code 디버거 사용
# F5로 디버그 시작, 브레이크포인트 설정
```

### 2. 프론트엔드 디버깅
```typescript
// React Developer Tools 사용
// 브라우저 개발자 도구 > Components 탭

// 상태 디버깅
console.log('Current state:', state);

// 성능 디버깅
React.StrictMode를 사용하여 잠재적 문제 감지
```

## 🚨 문제 해결

### 자주 발생하는 문제들

#### 1. 데이터베이스 연결 실패
```bash
# PostgreSQL 상태 확인
docker ps | grep postgres

# 연결 테스트
psql -h localhost -U bodam_user -d bodam_dev

# 권한 문제 해결
sudo chown -R $USER:$USER postgres_data/
```

#### 2. 포트 충돌
```bash
# 포트 사용 확인
lsof -i :8000
lsof -i :3000

# 프로세스 종료
kill -9 <PID>
```

#### 3. 의존성 충돌
```bash
# Python 의존성 초기화
rm -rf backend/venv
python3.11 -m venv backend/venv
pip install -r backend/requirements-dev.txt

# Node.js 의존성 초기화
rm -rf frontend/node_modules
rm frontend/package-lock.json
npm install
```

---

이 개발 가이드를 통해 보담 프로젝트의 효율적인 개발 환경을 구축하고 일관된 코드 품질을 유지할 수 있습니다. 🚀