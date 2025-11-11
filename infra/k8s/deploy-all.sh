#!/bin/bash
# 보담 플랫폼 K8s 전체 배포 스크립트 (로컬 개발 환경 구조 반영)

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
ENVIRONMENT=${1:-production}
NAMESPACE="bodam-prod"  # Production만 지원

if [ "$ENVIRONMENT" != "production" ]; then
    log_warn "⚠️ Preview 환경은 아직 구성되지 않았습니다."
    log_warn "Production 환경으로 배포합니다."
    ENVIRONMENT="production"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 보담 플랫폼 K8s 배포"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "환경: $ENVIRONMENT"
echo "네임스페이스: $NAMESPACE"
echo ""

# kubectl 설치 확인
if ! command -v kubectl &> /dev/null; then
    log_error "kubectl이 설치되어 있지 않습니다"
    exit 1
fi

# 네임스페이스 생성
log_step "1. 네임스페이스 생성"
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
log_info "✅ 네임스페이스: $NAMESPACE"
echo ""

# Secrets 생성 (필요한 경우)
log_step "2. Secrets 확인"
if kubectl get secret bodam-secrets -n "$NAMESPACE" &>/dev/null; then
    log_info "✅ bodam-secrets 이미 존재"
else
    log_warn "⚠️ bodam-secrets가 없습니다"
    log_warn "다음 명령어로 Secrets를 생성하세요:"
    echo ""
    echo "kubectl create secret generic bodam-secrets \\"
    echo "  --from-literal=database-url=\$DATABASE_URL \\"
    echo "  --from-literal=jwt-secret=\$JWT_SECRET_KEY \\"
    echo "  --from-literal=together-api-key=\$TOGETHER_AI_API_KEY \\"
    echo "  --from-literal=naver-client-id=\$NAVER_CLIENT_ID \\"
    echo "  --from-literal=naver-client-secret=\$NAVER_CLIENT_SECRET \\"
    echo "  --from-literal=youtube-api-key=\$YOUTUBE_API_KEY \\"
    echo "  --from-literal=toss-client-key=\$TOSS_CLIENT_KEY \\"
    echo "  --from-literal=toss-secret-key=\$TOSS_SECRET_KEY \\"
    echo "  -n $NAMESPACE"
    echo ""
    read -p "Secrets를 생성했습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_error "Secrets 생성 후 다시 실행하세요"
        exit 1
    fi
fi
echo ""

# Docker Registry Secret
log_step "3. Docker Registry Secret 생성"
if kubectl get secret regcred -n "$NAMESPACE" &>/dev/null; then
    log_info "✅ regcred 이미 존재"
else
    log_warn "⚠️ regcred 생성 필요 (DigitalOcean Registry)"
    log_warn "GitHub Actions 워크플로우에서 자동 생성됩니다"
fi
echo ""

# Redis 3개 배포
log_step "4. Redis 3개 배포"
log_info "Redis Cache 배포..."
kubectl apply -f redis/redis-cache-deployment.yaml -n "$NAMESPACE"

log_info "Redis Queue 배포..."
kubectl apply -f redis/redis-queue-deployment.yaml -n "$NAMESPACE"

log_info "Redis Semantic 배포..."
kubectl apply -f redis/redis-semantic-deployment.yaml -n "$NAMESPACE"

log_info "✅ Redis 3개 배포 완료"
echo ""

# Backend 배포
log_step "5. Backend 배포"
kubectl apply -f backend/backend-deployment-v2.yaml -n "$NAMESPACE"
kubectl apply -f backend/configmap.yaml -n "$NAMESPACE" || log_warn "ConfigMap 적용 실패 (선택적)"
log_info "✅ Backend 배포 완료"
echo ""

# Celery Workers 배포
log_step "6. Celery Workers 배포"
log_info "Celery Main Worker 배포..."
kubectl apply -f celery/celery-worker-deployment.yaml -n "$NAMESPACE"

log_info "Celery News Worker 배포..."
kubectl apply -f celery/celery-worker-news-deployment.yaml -n "$NAMESPACE"

log_info "Celery Beat 배포..."
kubectl apply -f celery/celery-beat-deployment.yaml -n "$NAMESPACE"

log_info "✅ Celery Workers 배포 완료"
echo ""

# HPA (Horizontal Pod Autoscaler) 배포
log_step "7. HPA 배포"
kubectl apply -f backend/hpa.yaml -n "$NAMESPACE" || log_warn "Backend HPA 적용 실패 (선택적)"
kubectl apply -f backend/celery-worker-hpa.yaml -n "$NAMESPACE" || log_warn "Celery HPA 적용 실패 (선택적)"
echo ""

# Ingress 배포
log_step "8. Ingress 배포"
kubectl apply -f backend/ingress.yaml -n "$NAMESPACE" || log_warn "Ingress 적용 실패 (선택적)"
echo ""

# 모니터링 스택 배포 (선택적)
log_step "9. 모니터링 스택 배포 (선택적)"
read -p "모니터링 스택을 배포하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Prometheus 배포..."
    kubectl apply -f observability/prometheus/deployment.yaml -n "$NAMESPACE" || log_warn "Prometheus 배포 실패"

    log_info "Grafana 배포..."
    kubectl apply -f observability/grafana/deployment.yaml -n "$NAMESPACE" || log_warn "Grafana 배포 실패"

    log_info "✅ 모니터링 스택 배포 완료"
else
    log_info "모니터링 스택 배포 건너뜀"
fi
echo ""

# 배포 상태 확인
log_step "10. 배포 상태 확인"
echo ""
echo "Deployments:"
kubectl get deployments -n "$NAMESPACE"
echo ""
echo "Services:"
kubectl get services -n "$NAMESPACE"
echo ""
echo "PVCs:"
kubectl get pvc -n "$NAMESPACE"
echo ""

# 롤아웃 상태 확인
log_step "11. 롤아웃 상태 확인 (최대 5분 대기)"
echo ""

DEPLOYMENTS=(
    "redis-cache"
    "redis-queue"
    "redis-semantic"
    "bodam-backend"
    "celery-worker"
    "celery-worker-news"
    "celery-beat"
)

for deployment in "${DEPLOYMENTS[@]}"; do
    if kubectl get deployment "$deployment" -n "$NAMESPACE" &>/dev/null; then
        log_info "롤아웃 확인: $deployment"
        kubectl rollout status deployment/"$deployment" -n "$NAMESPACE" --timeout=5m || log_warn "$deployment 롤아웃 타임아웃"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 배포 완료!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "다음 단계:"
echo "  1. Pod 상태 확인: kubectl get pods -n $NAMESPACE"
echo "  2. 로그 확인: kubectl logs -f deployment/bodam-backend -n $NAMESPACE"
echo "  3. Health Check: curl http://<ingress-url>/health"
echo ""
