#!/bin/bash
# Git 상태 확인 스크립트

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_success() { echo -e "${GREEN}✅${NC} $1"; }
log_warn() { echo -e "${YELLOW}⚠️${NC} $1"; }
log_error() { echo -e "${RED}❌${NC} $1"; }

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 Git 상태 확인"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 현재 브랜치 확인
CURRENT_BRANCH=$(git branch --show-current)
echo "현재 브랜치: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" = "wonuk" ]; then
    log_success "Preview 환경 배포 브랜치 (wonuk)"
elif [ "$CURRENT_BRANCH" = "donghee" ]; then
    log_success "Production 환경 배포 브랜치 (donghee)"
else
    log_warn "알 수 없는 브랜치입니다. 배포 환경을 명시해야 합니다."
fi

echo ""

# 작업 디렉토리 상태 확인
echo "작업 디렉토리 상태:"
STATUS_OUTPUT=$(git status --short)

if [ -z "$STATUS_OUTPUT" ]; then
    log_success "작업 디렉토리가 깨끗합니다"
else
    log_warn "커밋되지 않은 변경사항이 있습니다:"
    echo "$STATUS_OUTPUT"
    echo ""
    log_warn "배포 전 변경사항을 커밋하거나 스태시하는 것을 권장합니다"
fi

echo ""

# 원격 브랜치와 동기화 상태 확인
echo "원격 저장소 동기화 상태 확인..."
git fetch origin 2>&1 >/dev/null || log_warn "원격 저장소 fetch 실패"

LOCAL=$(git rev-parse @ 2>/dev/null || echo "")
REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")
BASE=$(git merge-base @ @{u} 2>/dev/null || echo "")

if [ -z "$REMOTE" ]; then
    log_warn "원격 브랜치를 추적하지 않습니다"
    log_warn "Push가 필요할 수 있습니다"
elif [ "$LOCAL" = "$REMOTE" ]; then
    log_success "로컬과 원격이 동기화되어 있습니다"
elif [ "$LOCAL" = "$BASE" ]; then
    log_error "로컬이 원격보다 뒤처져 있습니다"
    log_error "먼저 'git pull'을 실행하세요"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 1
elif [ "$REMOTE" = "$BASE" ]; then
    log_success "로컬에 Push할 커밋이 있습니다"
    echo "로컬 커밋 개수: $(git rev-list --count @{u}..@)"
else
    log_warn "로컬과 원격이 분기되었습니다"
    log_warn "병합이 필요할 수 있습니다"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Git 상태 확인 완료"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
