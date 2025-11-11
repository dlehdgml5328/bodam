#!/bin/bash
# 배포 상태 확인 스크립트

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 파라미터: backend/frontend, preview/production
TARGET=${1:-backend}
ENVIRONMENT=${2:-preview}

if [ "$TARGET" = "backend" ]; then
    # Backend 상태 확인
    if [ "$ENVIRONMENT" = "production" ]; then
        NAMESPACE="bodam-prod"
    else
        NAMESPACE="bodam-preview"
    fi

    DEPLOYMENT_NAME="bodam-backend"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Backend 배포 상태 ($ENVIRONMENT)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # kubectl 설치 확인
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl이 설치되어 있지 않습니다"
        exit 1
    fi

    # Deployment 상태
    echo "📦 Deployment 상태:"
    kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" 2>/dev/null || log_error "Deployment를 찾을 수 없습니다"
    echo ""

    # 현재 이미지
    echo "🖼️  현재 이미지:"
    CURRENT_IMAGE=$(kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || echo "N/A")
    echo "   $CURRENT_IMAGE"
    echo ""

    # Pod 상태
    echo "☸️  Pod 상태:"
    kubectl get pods -n "$NAMESPACE" -l app=bodam-backend 2>/dev/null || log_warn "Pod를 찾을 수 없습니다"
    echo ""

    # 배포 히스토리
    echo "📜 배포 히스토리:"
    kubectl rollout history deployment/"$DEPLOYMENT_NAME" -n "$NAMESPACE" 2>/dev/null || log_warn "배포 히스토리를 가져올 수 없습니다"
    echo ""

    # 최근 이벤트
    echo "📋 최근 이벤트 (최근 5개):"
    kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' 2>/dev/null | grep "$DEPLOYMENT_NAME" | tail -5 || echo "   이벤트 없음"
    echo ""

elif [ "$TARGET" = "frontend" ]; then
    # Frontend 상태 확인
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Frontend 배포 상태 ($ENVIRONMENT)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # vercel CLI 확인
    if command -v vercel &> /dev/null; then
        log_info "Vercel CLI로 배포 상태 확인"
        vercel list 2>/dev/null | head -10 || log_warn "Vercel 배포 목록을 가져올 수 없습니다"
        echo ""
        echo "최근 배포:"
        vercel ls --scope bodam 2>/dev/null | head -10 || log_warn "배포 정보를 가져올 수 없습니다"
    else
        log_warn "Vercel CLI가 설치되어 있지 않습니다"
        echo ""
        echo "Frontend 배포 상태는 Vercel 대시보드에서 확인하세요:"
        echo "https://vercel.com/dashboard"
    fi
    echo ""

else
    log_error "알 수 없는 대상: $TARGET (backend 또는 frontend 사용)"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
