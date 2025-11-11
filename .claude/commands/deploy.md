---
description: 보담 플랫폼 자동 배포 - Backend(K8s) + Frontend(Vercel) 통합 배포
---

보담 플랫폼 배포 자동화를 시작합니다.

**배포 대상 환경**: $ARGUMENTS (기본값: preview)
- preview: wonuk 브랜치 기반 미리보기 환경
- production: donghee 브랜치 기반 프로덕션 환경

## 1단계: 배포 전 검증

1. 현재 브랜치 확인
   ```bash
   git branch --show-current
   ```

2. 작업 디렉토리 상태 확인
   ```bash
   git status
   ```

3. 미커밋된 변경사항이 있다면:
   - 변경사항 리뷰 요청
   - 사용자에게 커밋 또는 스태시 여부 확인

## 2단계: 로컬 테스트 실행

### Backend 테스트
```bash
cd backend
pytest tests/unit/ -v --tb=short
pytest tests/integration/ -v --tb=short
ruff check .
mypy src --ignore-missing-imports
cd ..
```

### Frontend 테스트
```bash
cd frontend
npm run lint
npm run type-check
npm run test:unit
cd ..
```

**테스트 실패 시**: 배포 중단하고 에러 내용 사용자에게 보고

## 3단계: 환경별 배포 설정

### Preview 환경 (wonuk 브랜치)
- Backend: DigitalOcean K8s `bodam-preview` namespace
- Frontend: Vercel Preview
- 브랜치 확인: wonuk인지 체크

### Production 환경 (donghee 브랜치)
- Backend: DigitalOcean K8s `bodam-prod` namespace
- Frontend: Vercel Production
- 브랜치 확인: donghee인지 체크
- **주의**: Production 배포는 추가 확인 필요

## 4단계: 배포 실행

### 환경 변수 확인
다음 시크릿이 GitHub Secrets에 설정되어 있는지 확인 (사용자에게 알림):
- DIGITALOCEAN_TOKEN
- VERCEL_TOKEN
- DATABASE_URL
- JWT_SECRET_KEY
- TOGETHER_AI_API_KEY

### Git Push 트리거 방식
```bash
# 현재 브랜치에 push하여 GitHub Actions 트리거
git push origin $(git branch --show-current)
```

**사용자에게 안내**:
- Backend CI/CD: `.github/workflows/backend-ci-cd.yml` 워크플로우 실행
- Frontend CI/CD: `.github/workflows/frontend-ci-cd.yml` 워크플로우 실행
- GitHub Actions 페이지에서 진행 상황 확인 가능

## 5단계: 배포 모니터링

**GitHub Actions 워크플로우 상태 확인 방법 안내**:
```bash
# gh CLI 설치되어 있다면
gh run list --limit 5
gh run watch
```

**수동 확인 링크 제공**:
- https://github.com/{owner}/{repo}/actions

## 6단계: 배포 후 검증

배포 완료 후 다음 검증 수행:

### Health Check
- Preview: `$PREVIEW_API_URL/health`
- Production: `$PRODUCTION_API_URL/health`

### Smoke Test
- Frontend 홈페이지 렌더링 확인
- Backend API 응답 확인
- Database 연결 상태 확인

## 배포 체크리스트

- [ ] Git 브랜치가 올바른가? (preview=wonuk, production=donghee)
- [ ] 모든 테스트가 통과했는가?
- [ ] 코드 린트/타입 검사 통과했는가?
- [ ] GitHub Secrets이 모두 설정되었는가?
- [ ] Docker 이미지 빌드가 성공했는가?
- [ ] K8s 배포가 성공했는가?
- [ ] Vercel 배포가 성공했는가?
- [ ] Health Check가 통과했는가?
- [ ] Slack 알림이 전송되었는가?

## 롤백 방법

배포 실패 시 `/rollback` 명령어 사용 또는 다음 수동 단계:

### Backend 롤백
```bash
kubectl rollout undo deployment/bodam-backend -n bodam-{env}
```

### Frontend 롤백
Vercel 대시보드에서 이전 배포 버전으로 롤백

## 주의사항

⚠️ **Production 배포 전 필수 확인**:
1. Preview 환경에서 충분한 테스트 완료
2. 데이터베이스 마이그레이션 영향도 검토
3. API Breaking Changes 여부 확인
4. 트래픽이 적은 시간대 배포 권장

⚠️ **배포 중단 조건**:
- 테스트 실패
- 린트/타입 오류
- 빌드 실패
- Health Check 실패
