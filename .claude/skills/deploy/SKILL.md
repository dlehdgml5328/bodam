---
name: deploy
description: 보담 플랫폼 자동 배포 - Backend(K8s)와 Frontend(Vercel)를 통합 배포. 사용자가 배포 요청 시 또는 "deploy to preview/production" 같은 요청 시 사용.
---

# 보담 플랫폼 자동 배포 Skill

이 Skill은 보담 플랫폼의 Backend와 Frontend를 자동으로 배포합니다.

## 배포 환경

- **preview**: wonuk 브랜치 기반 미리보기 환경 (DigitalOcean K8s + Vercel Preview)
- **production**: donghee 브랜치 기반 프로덕션 환경 (DigitalOcean K8s + Vercel Production)

## 사용 시점

다음과 같은 요청을 받았을 때 이 Skill을 사용하세요:
- "배포해줘", "deploy", "production 배포"
- "preview 환경에 배포"
- "최신 코드를 서버에 올려줘"
- "변경사항을 반영해줘"

## 실행 단계

### 1단계: 환경 확인

먼저 배포 환경을 결정하세요:
- 사용자가 명시한 환경 사용 (preview/production)
- 명시되지 않은 경우 현재 브랜치로 판단:
  - wonuk 브랜치 → preview
  - donghee 브랜치 → production

```bash
CURRENT_BRANCH=$(git branch --show-current)
echo "현재 브랜치: $CURRENT_BRANCH"
```

### 2단계: 배포 전 검증 실행

`predeploy` Skill을 먼저 실행하여 배포 가능 여부를 확인하세요.

**검증 항목**:
- Git 상태 (커밋되지 않은 변경사항)
- 테스트 통과 여부
- 코드 품질 검사 (lint, type check)
- 빌드 성공 여부

검증 실패 시 **배포를 중단**하고 사용자에게 오류를 알려주세요.

### 3단계: Production 배포 특별 확인

만약 **production** 환경 배포라면:

사용자에게 다음을 확인하세요:
```
⚠️ Production 환경에 배포하려고 합니다.

확인 사항:
- Preview 환경에서 충분히 테스트했나요?
- 데이터베이스 마이그레이션 영향도를 검토했나요?
- API Breaking Changes가 있나요?
- 트래픽이 적은 시간대인가요?

계속 진행하시겠습니까? (yes/no)
```

사용자가 "no" 또는 확신하지 못하면 배포를 중단하세요.

### 4단계: GitHub Secrets 확인

사용자에게 다음 Secrets이 설정되어 있는지 확인하도록 안내하세요:

**필수 Secrets**:
- `DIGITALOCEAN_TOKEN`: DigitalOcean API 토큰
- `VERCEL_TOKEN`: Vercel 배포 토큰
- `DATABASE_URL`: 데이터베이스 연결 URL
- `JWT_SECRET_KEY`: JWT 시크릿 키
- `TOGETHER_AI_API_KEY`: Together AI API 키
- `ADMIN_SECRET_KEY`: 관리자 시크릿 키

환경별 추가 Secrets:
- Preview: `DIGITALOCEAN_CLUSTER_ID_PREVIEW`, `PREVIEW_API_URL`
- Production: `DIGITALOCEAN_CLUSTER_ID_PROD`, `PRODUCTION_API_URL`

### 5단계: 배포 스크립트 실행

`scripts/deploy-trigger.sh` 스크립트를 실행하여 GitHub Actions를 트리거하세요:

```bash
bash /home/donghee/bodam/.claude/skills/deploy/scripts/deploy-trigger.sh {preview|production}
```

이 스크립트는:
1. 현재 브랜치 확인
2. 원격 저장소에 push하여 GitHub Actions 트리거
3. 워크플로우 실행 링크 출력

### 6단계: 배포 진행 상황 안내

사용자에게 다음 정보를 제공하세요:

```
🚀 배포가 시작되었습니다!

배포 환경: {preview/production}
브랜치: {브랜치명}
커밋: {커밋 SHA}

GitHub Actions 워크플로우:
- Backend CI/CD: https://github.com/{owner}/{repo}/actions/workflows/backend-ci-cd.yml
- Frontend CI/CD: https://github.com/{owner}/{repo}/actions/workflows/frontend-ci-cd.yml

배포 상태 확인:
- CLI: gh run list --limit 5
- CLI: gh run watch
- Web: https://github.com/{owner}/{repo}/actions

예상 소요 시간: 8-12분

배포 완료 후 다음이 자동 실행됩니다:
✅ Docker 이미지 빌드 및 푸시
✅ Kubernetes 배포
✅ Vercel 배포
✅ Health Check
✅ Smoke Test
✅ Slack 알림 (설정된 경우)
```

### 7단계: 배포 후 검증 (선택)

배포가 완료된 후 (약 10분 후) 사용자에게 검증을 제안하세요:

```
배포가 완료되었을 것으로 예상됩니다.
배포 상태를 확인하시겠습니까?

확인하려면 `deploy-status` Skill을 사용하세요.
```

## 오류 처리

### 검증 실패
- 테스트 실패 → 오류 로그 출력 및 수정 필요
- 린트/타입 오류 → 오류 위치와 내용 출력
- 빌드 실패 → 빌드 로그 확인 필요

### 배포 실패
- GitHub Actions 워크플로우 실패 시:
  - 워크플로우 로그 확인 링크 제공
  - `rollback` Skill 사용 안내

### 권한 오류
- GitHub Secrets 미설정 → 설정 방법 안내
- DigitalOcean 권한 오류 → 토큰 확인 필요

## 참고 파일

- Backend CI/CD: `.github/workflows/backend-ci-cd.yml`
- Frontend CI/CD: `.github/workflows/frontend-ci-cd.yml`
- K8s Manifests: `infra/k8s/`
- Deployment Script: `scripts/deploy.sh`

## 배포 워크플로우 다이어그램

```
[사용자 요청]
    ↓
[환경 결정] (preview/production)
    ↓
[배포 전 검증] (predeploy Skill)
    ↓
[Production 확인] (production만)
    ↓
[Secrets 확인 안내]
    ↓
[Git Push → GitHub Actions 트리거]
    ↓
[배포 진행 상황 안내]
    ↓
[배포 완료 대기]
    ↓
[배포 후 검증 제안] (deploy-status Skill)
```

## 관련 Skills

- `predeploy`: 배포 전 종합 검증
- `rollback`: 배포 실패 시 롤백
- `deploy-status`: 배포 상태 모니터링
