#!/bin/bash
# GitHub Actions 워크플로우 상태 확인

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 GitHub Actions 워크플로우 상태"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# gh CLI 설치 확인
if ! command -v gh &> /dev/null; then
    log_warn "gh CLI가 설치되어 있지 않습니다"
    echo ""
    echo "gh CLI 설치 방법:"
    echo "  https://cli.github.com/"
    echo ""
    echo "수동 확인:"

    # Git 원격 저장소 URL 추출
    REPO_URL=$(git config --get remote.origin.url 2>/dev/null | sed 's/\.git$//' | sed 's/git@github.com:/https:\/\/github.com\//')

    if [ -n "$REPO_URL" ]; then
        echo "  GitHub Actions: ${REPO_URL}/actions"
    else
        echo "  GitHub 저장소 URL을 확인할 수 없습니다"
    fi

    exit 0
fi

# 인증 확인
if ! gh auth status &>/dev/null; then
    log_error "GitHub 인증이 필요합니다"
    echo ""
    echo "인증 방법:"
    echo "  gh auth login"
    exit 1
fi

# 최근 워크플로우 실행 목록 (최근 5개)
echo "📋 최근 워크플로우 실행 (최근 5개):"
echo ""
gh run list --limit 5

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Backend CI/CD 워크플로우:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Backend CI/CD 워크플로우 상태
BACKEND_RUN=$(gh run list --workflow="backend-ci-cd.yml" --limit 1 --json status,conclusion,displayTitle,createdAt,databaseId 2>/dev/null)

if [ -n "$BACKEND_RUN" ]; then
    STATUS=$(echo "$BACKEND_RUN" | jq -r '.[0].status')
    CONCLUSION=$(echo "$BACKEND_RUN" | jq -r '.[0].conclusion')
    TITLE=$(echo "$BACKEND_RUN" | jq -r '.[0].displayTitle')
    RUN_ID=$(echo "$BACKEND_RUN" | jq -r '.[0].databaseId')

    echo "상태: $STATUS"
    echo "결과: $CONCLUSION"
    echo "커밋: $TITLE"

    if [ "$STATUS" = "completed" ]; then
        if [ "$CONCLUSION" = "success" ]; then
            log_info "✅ Backend 배포 성공"
        else
            log_error "❌ Backend 배포 실패"
            echo ""
            echo "로그 확인:"
            echo "  gh run view $RUN_ID --log"
        fi
    else
        log_warn "🟡 Backend 배포 진행 중..."
        echo ""
        echo "실시간 모니터링:"
        echo "  gh run watch $RUN_ID"
    fi
else
    log_warn "Backend CI/CD 워크플로우 실행 기록이 없습니다"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Frontend CI/CD 워크플로우:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Frontend CI/CD 워크플로우 상태
FRONTEND_RUN=$(gh run list --workflow="frontend-ci-cd.yml" --limit 1 --json status,conclusion,displayTitle,createdAt,databaseId 2>/dev/null)

if [ -n "$FRONTEND_RUN" ]; then
    STATUS=$(echo "$FRONTEND_RUN" | jq -r '.[0].status')
    CONCLUSION=$(echo "$FRONTEND_RUN" | jq -r '.[0].conclusion')
    TITLE=$(echo "$FRONTEND_RUN" | jq -r '.[0].displayTitle')
    RUN_ID=$(echo "$FRONTEND_RUN" | jq -r '.[0].databaseId')

    echo "상태: $STATUS"
    echo "결과: $CONCLUSION"
    echo "커밋: $TITLE"

    if [ "$STATUS" = "completed" ]; then
        if [ "$CONCLUSION" = "success" ]; then
            log_info "✅ Frontend 배포 성공"
        else
            log_error "❌ Frontend 배포 실패"
            echo ""
            echo "로그 확인:"
            echo "  gh run view $RUN_ID --log"
        fi
    else
        log_warn "🟡 Frontend 배포 진행 중..."
        echo ""
        echo "실시간 모니터링:"
        echo "  gh run watch $RUN_ID"
    fi
else
    log_warn "Frontend CI/CD 워크플로우 실행 기록이 없습니다"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
