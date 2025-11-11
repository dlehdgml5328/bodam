---
description: 배포 전 종합 체크리스트 검증 - 테스트/린트/빌드/환경 설정 확인
---

배포 전 종합 검증을 시작합니다.

**검증 환경**: $ARGUMENTS (기본값: preview)

## Phase 1: Git 상태 확인

### 1.1 브랜치 확인
```bash
git branch --show-current
```

**검증 기준**:
- Preview 배포: wonuk 브랜치여야 함
- Production 배포: donghee 브랜치여야 함

### 1.2 작업 디렉토리 상태
```bash
git status --short
```

**경고 조건**:
- Untracked files 존재
- Modified but not staged
- Uncommitted changes

### 1.3 원격 브랜치와 동기화 상태
```bash
git fetch origin
git status -uno
```

**확인 사항**:
- 로컬이 원격보다 뒤처져 있는지
- Push 필요한 커밋이 있는지

## Phase 2: Backend 검증

### 2.1 의존성 확인
```bash
cd backend
pip list | grep -E "fastapi|sqlalchemy|httpx|celery"
```

### 2.2 코드 품질 검사
```bash
# Ruff 린트
ruff check . --output-format=concise

# MyPy 타입 검사
mypy src --ignore-missing-imports --no-error-summary
```

**실패 시**: 오류 상세 내용 출력 및 배포 중단 권고

### 2.3 단위 테스트
```bash
pytest tests/unit/ -v --tb=line --no-header -q
```

**메트릭 수집**:
- 총 테스트 개수
- 통과/실패 개수
- 실행 시간

### 2.4 통합 테스트 (옵션)
```bash
# Docker Compose로 로컬 환경 구성 필요
docker compose -f docker-compose.dev.yml up -d postgres redis
sleep 5
pytest tests/integration/ -v --tb=line --no-header -q
docker compose -f docker-compose.dev.yml down
```

### 2.5 보안 취약점 검사
```bash
# pip-audit 설치되어 있다면
pip-audit --require-hashes --disable-pip || echo "pip-audit not installed, skipping"
```

## Phase 3: Frontend 검증

### 3.1 의존성 확인
```bash
cd ../frontend
npm ls --depth=0 | grep -E "next|react|typescript" || true
```

### 3.2 ESLint 검사
```bash
npm run lint 2>&1 | head -50
```

### 3.3 TypeScript 타입 검사
```bash
npm run type-check 2>&1 | head -50
```

### 3.4 단위 테스트
```bash
npm run test:unit -- --passWithNoTests --silent 2>&1 | tail -20
```

### 3.5 빌드 테스트
```bash
NODE_ENV=production npm run build 2>&1 | tail -30
```

**빌드 검증**:
- `.next` 디렉토리 생성 확인
- 빌드 에러 없음
- 빌드 크기 체크

## Phase 4: Infrastructure 검증

### 4.1 Docker 이미지 검증 (로컬)
```bash
cd ..

# Backend Dockerfile 문법 체크
docker build --no-cache -f backend/Dockerfile -t bodam-backend:test backend --dry-run 2>&1 || echo "Dry run not supported, building..."

# Frontend Dockerfile 문법 체크
docker build --no-cache -f frontend/Dockerfile -t bodam-frontend:test frontend --dry-run 2>&1 || echo "Dry run not supported, skipping"
```

### 4.2 K8s 매니페스트 검증
```bash
# YAML 문법 검증
find infra/k8s -name "*.yaml" -exec kubectl apply --dry-run=client -f {} \; 2>&1 | grep -E "error|configured|created" || echo "All manifests valid"
```

### 4.3 환경 변수 체크리스트

**Backend 필수 환경변수** (GitHub Secrets):
- DATABASE_URL
- REDIS_URL
- JWT_SECRET_KEY
- TOGETHER_AI_API_KEY
- ADMIN_SECRET_KEY

**Frontend 필수 환경변수**:
- NEXT_PUBLIC_API_URL
- VERCEL_TOKEN (CI/CD)

**Infrastructure 환경변수**:
- DIGITALOCEAN_TOKEN
- DIGITALOCEAN_CLUSTER_ID_PROD
- DIGITALOCEAN_CLUSTER_ID_PREVIEW

**사용자에게 확인 요청**: 위 시크릿이 GitHub Settings > Secrets에 설정되어 있는지 확인

## Phase 5: 데이터베이스 검증

### 5.1 마이그레이션 상태 확인
```bash
cd backend
# Alembic 사용 시
alembic current 2>&1 || echo "No alembic migrations"
alembic check 2>&1 || echo "Migration check not available"
cd ..
```

### 5.2 마이그레이션 영향도 분석

**사용자에게 질문**:
- 새로운 마이그레이션이 있습니까?
- Breaking changes가 있습니까?
- 데이터 마이그레이션이 필요합니까?

## Phase 6: 모니터링 준비

### 6.1 Grafana/Prometheus 확인
```bash
# Observability stack 상태
docker compose -f docker-compose.observability.yml ps 2>&1 || echo "Observability stack not running"
```

### 6.2 로그 수집 확인
- K8s 로그 수집 설정 확인
- Grafana 알림 설정 확인

## Phase 7: 배포 준비 완료 리포트

### ✅ 검증 통과 기준
- [ ] Git 브랜치가 배포 환경과 일치
- [ ] 모든 코드 품질 검사 통과 (Ruff, MyPy, ESLint, TypeScript)
- [ ] 모든 테스트 통과 (Backend Unit + Integration, Frontend Unit)
- [ ] 빌드 성공 (Backend Docker, Frontend Next.js)
- [ ] K8s 매니페스트 검증 통과
- [ ] 환경 변수 설정 확인 완료
- [ ] 데이터베이스 마이그레이션 검토 완료

### 📊 검증 결과 요약

**사용자에게 제공할 정보**:
1. 검증 통과 항목 수 / 전체 항목 수
2. 실패한 검증 항목 및 상세 에러
3. 경고 항목 (선택적 개선 필요)
4. 배포 진행 여부 권고
   - ✅ 모든 검증 통과 → `/deploy {환경}` 명령어로 배포 진행 가능
   - ⚠️ 일부 경고 → 경고 내용 검토 후 배포 결정
   - ❌ 검증 실패 → 문제 해결 후 재검증 필요

### 🔧 문제 해결 가이드

**공통 이슈**:
- 린트 오류 → 자동 수정: `ruff check . --fix` (Backend), `npm run lint --fix` (Frontend)
- 타입 오류 → 타입 정의 확인 및 수정 필요
- 테스트 실패 → 실패한 테스트 로그 확인 및 수정
- 빌드 실패 → 의존성 또는 설정 파일 확인

**다음 단계**:
- 모든 검증 통과 시: `/deploy {preview|production}`
- 검증 실패 시: 문제 수정 후 `/predeploy {환경}` 재실행
