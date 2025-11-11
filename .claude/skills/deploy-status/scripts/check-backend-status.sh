#!/bin/bash
# Backend (Kubernetes) 상태 확인 스크립트

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

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
echo "☸️  Backend 상태 ($ENVIRONMENT)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# kubectl 설치 확인
if ! command -v kubectl &> /dev/null; then
    log_error "kubectl이 설치되어 있지 않습니다"
    exit 1
fi

# 네임스페이스 존재 확인
if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
    log_warn "네임스페이스를 찾을 수 없습니다: $NAMESPACE"
    log_warn "Kubernetes 클러스터 연결을 확인하세요"
    exit 0
fi

echo "네임스페이스: $NAMESPACE"
echo ""

# Deployment 상태
echo "📦 Deployment 상태:"
if kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" &>/dev/null; then
    kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE"

    # 현재 이미지
    CURRENT_IMAGE=$(kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null)
    echo ""
    echo "현재 이미지: $CURRENT_IMAGE"

    # Replicas 정보
    DESIRED=$(kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null)
    AVAILABLE=$(kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" -o jsonpath='{.status.availableReplicas}' 2>/dev/null)

    echo "Replicas: $AVAILABLE/$DESIRED Available"

    if [ "$AVAILABLE" = "$DESIRED" ]; then
        log_info "✅ 모든 Pod가 정상 동작 중"
    else
        log_warn "⚠️ 일부 Pod가 준비되지 않았습니다"
    fi
else
    log_error "Deployment를 찾을 수 없습니다: $DEPLOYMENT_NAME"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "☸️  Pod 상태:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Pod 목록
if kubectl get pods -n "$NAMESPACE" -l app=bodam-backend &>/dev/null; then
    kubectl get pods -n "$NAMESPACE" -l app=bodam-backend

    echo ""

    # 각 Pod의 재시작 횟수 확인
    RESTART_COUNTS=$(kubectl get pods -n "$NAMESPACE" -l app=bodam-backend -o jsonpath='{.items[*].status.containerStatuses[0].restartCount}' 2>/dev/null)

    if [ -n "$RESTART_COUNTS" ]; then
        MAX_RESTART=0
        for count in $RESTART_COUNTS; do
            if [ "$count" -gt "$MAX_RESTART" ]; then
                MAX_RESTART=$count
            fi
        done

        if [ "$MAX_RESTART" -gt 5 ]; then
            log_warn "⚠️ Pod 재시작 횟수가 높습니다 (최대: $MAX_RESTART회)"
            log_warn "Pod 로그를 확인하세요"
        elif [ "$MAX_RESTART" -gt 0 ]; then
            log_warn "Pod 재시작 발생: $MAX_RESTART회"
        else
            log_info "✅ Pod 재시작 없음"
        fi
    fi
else
    log_warn "Backend Pod를 찾을 수 없습니다"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔌 Service 상태:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Service 정보
if kubectl get service -n "$NAMESPACE" -l app=bodam-backend &>/dev/null; then
    kubectl get service -n "$NAMESPACE" -l app=bodam-backend
    log_info "✅ Service 정상"
else
    log_warn "Backend Service를 찾을 수 없습니다"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 최근 이벤트 (최근 10개):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 최근 이벤트
EVENTS=$(kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' 2>/dev/null | grep -E "$DEPLOYMENT_NAME|bodam-backend" | tail -10 || echo "")

if [ -n "$EVENTS" ]; then
    echo "$EVENTS"
else
    echo "관련 이벤트 없음"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

log_info "Backend 상태 확인 완료"

echo ""
echo "추가 명령어:"
echo "  Pod 로그: kubectl logs -f deployment/$DEPLOYMENT_NAME -n $NAMESPACE"
echo "  Pod 상세: kubectl describe pod {pod-name} -n $NAMESPACE"
echo "  실시간 감시: watch -n 5 kubectl get pods -n $NAMESPACE -l app=bodam-backend"
echo ""
