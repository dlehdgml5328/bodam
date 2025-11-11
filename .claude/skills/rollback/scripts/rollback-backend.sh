#!/bin/bash
# Backend 롤백 스크립트 (Kubernetes)

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

# 환경 파라미터
ENVIRONMENT=${1:-preview}

# 네임스페이스 설정
if [ "$ENVIRONMENT" = "production" ]; then
    NAMESPACE="bodam-prod"
else
    # Preview는 나중에 추가 예정
    NAMESPACE="bodam-prod"
    log_warn "Preview 환경 미구성, Production namespace 사용"
fi

DEPLOYMENT_NAME="bodam-backend"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 Backend 롤백 시작"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "환경: $ENVIRONMENT"
echo "네임스페이스: $NAMESPACE"
echo "Deployment: $DEPLOYMENT_NAME"
echo ""

# kubectl 설치 확인
if ! command -v kubectl &> /dev/null; then
    log_error "kubectl이 설치되어 있지 않습니다"
    exit 1
fi

# 네임스페이스 존재 확인
if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
    log_error "네임스페이스를 찾을 수 없습니다: $NAMESPACE"
    log_error "Kubernetes 클러스터 연결을 확인하세요"
    exit 1
fi

# Deployment 존재 확인
if ! kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" &>/dev/null; then
    log_error "Deployment를 찾을 수 없습니다: $DEPLOYMENT_NAME"
    exit 1
fi

# 현재 배포 상태 확인
log_step "현재 배포 상태 확인"
echo ""
kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE"
echo ""

# 현재 이미지 태그 확인
CURRENT_IMAGE=$(kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.template.spec.containers[0].image}')
log_info "현재 이미지: $CURRENT_IMAGE"
echo ""

# 배포 히스토리 확인
log_step "배포 히스토리 확인"
echo ""
kubectl rollout history deployment/"$DEPLOYMENT_NAME" -n "$NAMESPACE"
echo ""

# 사용자 확인
read -p "이전 버전으로 롤백하시겠습니까? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "롤백이 취소되었습니다"
    exit 0
fi

echo ""

# 롤백 실행
log_step "롤백 실행 중..."
if kubectl rollout undo deployment/"$DEPLOYMENT_NAME" -n "$NAMESPACE"; then
    log_info "✅ 롤백 명령이 실행되었습니다"
else
    log_error "❌ 롤백 실행에 실패했습니다"
    exit 1
fi

echo ""

# 롤백 상태 모니터링
log_step "롤백 상태 모니터링 (최대 5분 대기)"
if kubectl rollout status deployment/"$DEPLOYMENT_NAME" -n "$NAMESPACE" --timeout=5m; then
    log_info "✅ 롤백이 성공적으로 완료되었습니다"
else
    log_error "❌ 롤백이 실패했거나 타임아웃되었습니다"
    log_error "Pod 상태를 확인하세요"
    kubectl get pods -n "$NAMESPACE" -l app=bodam-backend
    exit 1
fi

echo ""

# 롤백 후 상태 확인
log_step "롤백 후 상태 확인"
echo ""

# 새 이미지 태그 확인
NEW_IMAGE=$(kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.template.spec.containers[0].image}')
log_info "이전 이미지: $CURRENT_IMAGE"
log_info "현재 이미지: $NEW_IMAGE"
echo ""

# Pod 상태 확인
echo "Pod 상태:"
kubectl get pods -n "$NAMESPACE" -l app=bodam-backend
echo ""

# 최근 이벤트 확인
log_step "최근 이벤트 확인"
kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' | grep "$DEPLOYMENT_NAME" | tail -10 || echo "관련 이벤트 없음"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 Backend 롤백 완료"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
log_info "다음 단계:"
echo "  1. Health Check 실행"
echo "  2. API 응답 테스트"
echo "  3. 모니터링 대시보드 확인"
echo "  4. 롤백 원인 분석"
echo ""
