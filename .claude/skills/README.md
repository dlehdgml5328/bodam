# 보담 플랫폼 배포 자동화 Skills

Claude Code Skills를 이용한 보담 플랫폼 배포 자동화 시스템입니다.

## 📋 Skills 목록

### 1. `deploy` - 자동 배포
**사용 시점**: "배포해줘", "deploy", "production 배포"

Backend(DigitalOcean K8s)와 Frontend(Vercel)를 통합 배포합니다.

**주요 기능**:
- 배포 환경 자동 감지 (preview/production)
- 배포 전 자동 검증 (predeploy Skill 호출)
- Production 배포 안전 확인
- GitHub Actions 워크플로우 트리거
- 배포 진행 상황 안내

**사용 예시**:
```
User: preview 환경에 배포해줘
Claude: [deploy Skill 실행 → 배포 프로세스 진행]

User: production 배포
Claude: [Production 확인 → 사용자 승인 → deploy Skill 실행]
```

---

### 2. `predeploy` - 배포 전 검증
**사용 시점**: "배포해도 될까?", "테스트 실행", "배포 가능한지 확인"

배포하기 전 모든 필수 검증을 자동으로 수행합니다.

**검증 항목**:
- ✅ Git 상태 (커밋, 동기화)
- ✅ Backend 코드 품질 (Ruff, MyPy)
- ✅ Backend 테스트 (단위, 통합)
- ✅ Frontend 코드 품질 (ESLint, TypeScript)
- ✅ Frontend 테스트 및 빌드
- ✅ K8s 매니페스트 검증
- ✅ 환경 변수 확인
- ✅ 데이터베이스 마이그레이션 검토

**사용 예시**:
```
User: 배포 가능한지 확인해줘
Claude: [predeploy Skill 실행 → 종합 검증 리포트 제공]
```

---

### 3. `rollback` - 배포 롤백
**사용 시점**: "롤백", "이전 버전으로", "배포 취소", "문제가 생겼어"

배포 후 문제 발생 시 이전 안정 버전으로 롤백합니다.

**주요 기능**:
- Backend K8s 롤백 (`kubectl rollout undo`)
- Frontend Vercel 롤백 안내
- 롤백 후 자동 검증 (Health Check)
- 롤백 원인 분석 지원
- Production 롤백 특별 확인

**사용 예시**:
```
User: production 롤백해줘
Claude: [Production 확인 → 롤백 실행 → 검증]

User: 배포 후 오류가 생겼어
Claude: [현재 상태 확인 → rollback Skill 제안]
```

---

### 4. `deploy-status` - 배포 상태 모니터링
**사용 시점**: "배포 상태 확인", "서비스 정상 동작해?", "Health Check"

배포 상태를 실시간으로 모니터링하고 Health Check를 수행합니다.

**확인 항목**:
- 🔄 GitHub Actions 워크플로우 진행 상황
- ☸️ K8s Deployment/Pod 상태
- 🌐 Vercel 배포 상태
- 💚 Backend/Frontend Health Check
- 🗄️ 데이터베이스 연결 상태
- 📊 주요 메트릭 확인

**사용 예시**:
```
User: 배포 상태 확인해줘
Claude: [deploy-status Skill 실행 → 종합 상태 리포트]

User: 서비스 정상 동작해?
Claude: [Health Check 실행 → 정상/오류 판단]
```

---

## 🚀 사용 워크플로우

### 일반 배포 프로세스

```
1. 코드 작성 및 커밋
   ↓
2. "배포 가능한지 확인해줘" (predeploy)
   ↓
3. 검증 통과 확인
   ↓
4. "preview 환경에 배포해줘" (deploy)
   ↓
5. 배포 진행 대기 (8-12분)
   ↓
6. "배포 상태 확인해줘" (deploy-status)
   ↓
7. Health Check 통과 확인
   ↓
8. Preview 환경에서 테스트
   ↓
9. "production 배포해줘" (deploy)
   ↓
10. Production 배포 완료
```

### 배포 실패 시 복구 프로세스

```
1. 배포 실패 또는 오류 감지
   ↓
2. "배포 상태 확인해줘" (deploy-status)
   ↓
3. 오류 원인 파악
   ↓
4. "롤백해줘" (rollback)
   ↓
5. 이전 버전으로 복구
   ↓
6. Health Check 재확인
   ↓
7. 문제 수정 후 재배포
```

---

## 🛠️ 설정 요구사항

### GitHub Secrets 설정

다음 Secrets이 GitHub에 설정되어 있어야 합니다:

**Backend**:
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET_KEY`
- `TOGETHER_AI_API_KEY`
- `ADMIN_SECRET_KEY`

**Frontend**:
- `NEXT_PUBLIC_API_URL`
- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

**Infrastructure**:
- `DIGITALOCEAN_TOKEN`
- `DIGITALOCEAN_CLUSTER_ID_PROD`
- `DIGITALOCEAN_CLUSTER_ID_PREVIEW`
- `PRODUCTION_API_URL`
- `PREVIEW_API_URL`

**알림 (선택)**:
- `SLACK_WEBHOOK_URL`

### 필수 도구 설치

**로컬 개발 환경**:
- `kubectl`: Kubernetes 클러스터 관리
- `gh` (GitHub CLI): GitHub Actions 모니터링
- `vercel` (Vercel CLI): Frontend 배포 관리
- `docker`: 로컬 테스트 환경
- `jq`: JSON 파싱 (스크립트에서 사용)
- `bc`: 계산 (스크립트에서 사용)

**설치 방법**:
```bash
# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# gh CLI
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update && sudo apt install gh

# Vercel CLI
npm install -g vercel

# jq, bc
sudo apt install jq bc
```

---

## 📁 디렉토리 구조

```
.claude/skills/
├── deploy/
│   ├── SKILL.md                    # Deploy Skill 정의
│   └── scripts/
│       └── deploy-trigger.sh       # GitHub Actions 트리거 스크립트
├── predeploy/
│   ├── SKILL.md                    # Predeploy Skill 정의
│   └── scripts/
│       ├── check-git-status.sh     # Git 상태 확인
│       └── validate-k8s.sh         # K8s 매니페스트 검증
├── rollback/
│   ├── SKILL.md                    # Rollback Skill 정의
│   └── scripts/
│       ├── rollback-backend.sh     # Backend 롤백
│       └── check-deployment-status.sh  # 배포 상태 확인
├── deploy-status/
│   ├── SKILL.md                    # Deploy Status Skill 정의
│   └── scripts/
│       ├── check-github-actions.sh # GitHub Actions 확인
│       ├── check-backend-status.sh # Backend 상태 확인
│       └── health-check.sh         # Health Check 실행
└── README.md                       # 이 파일
```

---

## 🔧 커스터마이징

### 환경 URL 변경

각 Skill의 스크립트에서 API URL을 수정하세요:

**예시** (`deploy-status/scripts/health-check.sh`):
```bash
if [ "$ENVIRONMENT" = "production" ]; then
    BACKEND_API_URL="https://api.bodam.com"  # 변경
    FRONTEND_URL="https://bodam.com"         # 변경
else
    BACKEND_API_URL="https://preview-api.bodam.com"  # 변경
    FRONTEND_URL="https://preview.bodam.com"         # 변경
fi
```

### K8s 네임스페이스/Deployment 이름 변경

**예시** (`rollback/scripts/rollback-backend.sh`):
```bash
if [ "$ENVIRONMENT" = "production" ]; then
    NAMESPACE="bodam-prod"  # 변경
elif [ "$ENVIRONMENT" = "preview" ]; then
    NAMESPACE="bodam-preview"  # 변경
fi

DEPLOYMENT_NAME="bodam-backend"  # 변경
```

### 추가 검증 단계

`predeploy/SKILL.md`에 검증 단계를 추가하고, 필요한 스크립트를 작성하세요.

---

## 🐛 트러블슈팅

### Skill이 자동으로 실행되지 않음
- **원인**: Skill description이 명확하지 않음
- **해결**: `SKILL.md`의 `description` 필드를 더 구체적으로 작성
- **확인**: Claude에게 "배포 관련 Skills 목록 보여줘" 요청

### 스크립트 실행 권한 오류
```bash
chmod +x .claude/skills/*/scripts/*.sh
```

### kubectl 연결 오류
- DigitalOcean 클러스터 인증 확인:
  ```bash
  doctl kubernetes cluster kubeconfig save {cluster-id}
  ```

### GitHub Actions 워크플로우가 트리거되지 않음
- Push 권한 확인
- 브랜치 이름 확인 (wonuk/donghee)
- GitHub Actions 워크플로우 활성화 상태 확인

---

## 📚 참고 문서

- [Claude Code Skills 공식 문서](https://docs.claude.com/en/docs/claude-code/skills)
- [GitHub Actions 워크플로우](.github/workflows/)
- [Kubernetes 매니페스트](infra/k8s/)
- [프로젝트 README](../../../README.md)
- [보담 프로젝트 구조](../../../CLAUDE.md)

---

## 🎯 다음 단계

1. **테스트**: Preview 환경에서 Skills 테스트
2. **모니터링**: Grafana/Prometheus 대시보드 설정
3. **알림**: Slack 웹훅 연동
4. **문서화**: 팀 온보딩 가이드 작성
5. **개선**: 배포 실패 원인 분석 및 프로세스 개선

---

**작성일**: 2025-11-10
**버전**: 1.0.0
**관리**: 보담 플랫폼 개발팀
