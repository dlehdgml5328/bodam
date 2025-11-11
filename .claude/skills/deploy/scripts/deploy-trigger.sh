#!/bin/bash
# 보담 플랫폼 배포 트리거 스크립트
# GitHub Actions 워크플로우를 트리거하기 위해 git push 실행

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# 환경 파라미터 (preview 또는 production)
ENVIRONMENT=${1:-preview}

# 현재 브랜치 확인
CURRENT_BRANCH=$(git branch --show-current)

log_step "배포 환경 확인"
echo "요청된 환경: $ENVIRONMENT"
echo "현재 브랜치: $CURRENT_BRANCH"

# 브랜치와 환경 매칭 확인
if [ "$ENVIRONMENT" = "production" ] && [ "$CURRENT_BRANCH" != "donghee" ]; then
    log_error "Production 배포는 donghee 브랜치에서만 가능합니다"
    log_error "현재 브랜치: $CURRENT_BRANCH"
    exit 1
fi

if [ "$ENVIRONMENT" = "preview" ]; then
    log_warn "⚠️ Preview 환경은 아직 구성되지 않았습니다."
    log_warn "Production 환경으로 배포됩니다."
    read -p "계속 진행하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "배포가 취소되었습니다"
        exit 0
    fi
fi

# Git 상태 확인
log_step "Git 상태 확인"
if [[ -n $(git status -s) ]]; then
    log_warn "커밋되지 않은 변경사항이 있습니다:"
    git status -s
    read -p "계속 진행하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "배포가 취소되었습니다"
        log_info "변경사항을 커밋하거나 스태시한 후 다시 시도하세요"
        exit 0
    fi
fi

# 원격 브랜치와 동기화 상태 확인
log_step "원격 저장소 상태 확인"
git fetch origin 2>/dev/null || log_warn "원격 저장소 fetch 실패"

LOCAL=$(git rev-parse @ 2>/dev/null || echo "")
REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")

if [ -n "$REMOTE" ] && [ "$LOCAL" != "$REMOTE" ]; then
    log_warn "로컬과 원격 브랜치가 다릅니다"

    # 로컬이 뒤처져 있는지 확인
    git merge-base --is-ancestor @ @{u} 2>/dev/null
    if [ $? -eq 0 ]; then
        log_warn "로컬 브랜치가 원격보다 뒤처져 있습니다"
        log_info "먼저 'git pull'을 실행하세요"
        exit 1
    fi
fi

# Push 실행
log_step "원격 저장소에 Push하여 GitHub Actions 트리거"
log_info "브랜치: $CURRENT_BRANCH"

git push origin "$CURRENT_BRANCH"

if [ $? -eq 0 ]; then
    log_info "✅ Push 성공! GitHub Actions 워크플로우가 시작됩니다"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🚀 배포가 시작되었습니다!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "배포 환경: $ENVIRONMENT"
    echo "브랜치: $CURRENT_BRANCH"
    echo "커밋: $(git rev-parse --short HEAD)"
    echo ""
    echo "GitHub Actions 워크플로우:"

    # GitHub 저장소 URL 추출
    REPO_URL=$(git config --get remote.origin.url | sed 's/\.git$//' | sed 's/git@github.com:/https:\/\/github.com\//')

    if [ -n "$REPO_URL" ]; then
        echo "- Backend CI/CD: ${REPO_URL}/actions/workflows/backend-ci-cd.yml"
        echo "- Frontend CI/CD: ${REPO_URL}/actions/workflows/frontend-ci-cd.yml"
        echo ""
        echo "배포 상태 확인:"
        echo "- Web: ${REPO_URL}/actions"
    fi

    # gh CLI가 설치되어 있다면 워크플로우 실행 모니터링 안내
    if command -v gh &> /dev/null; then
        echo "- CLI: gh run list --limit 5"
        echo "- CLI: gh run watch"
        echo ""
        log_info "실시간 모니터링: gh run watch"
    else
        echo ""
        log_info "gh CLI를 설치하면 실시간 모니터링이 가능합니다"
        log_info "설치: https://cli.github.com/"
    fi

    echo ""
    echo "예상 소요 시간: 8-12분"
    echo ""
    echo "배포 완료 후 자동 실행:"
    echo "✅ Docker 이미지 빌드 및 푸시"
    echo "✅ Kubernetes 배포"
    echo "✅ Vercel 배포"
    echo "✅ Health Check"
    echo "✅ Smoke Test"
    echo "✅ Slack 알림 (설정된 경우)"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    log_error "❌ Push 실패"
    log_error "원격 저장소 권한을 확인하세요"
    exit 1
fi
