#!/bin/bash
# 기존 배포 전체 정리 스크립트

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧹 기존 배포 전체 정리"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# kubectl 확인
if ! command -v kubectl &> /dev/null; then
    log_error "kubectl이 설치되어 있지 않습니다"
    exit 1
fi

# 클러스터 연결 확인
if ! kubectl cluster-info &>/dev/null; then
    log_error "Kubernetes 클러스터에 연결할 수 없습니다"
    log_error "먼저 클러스터 인증을 해주세요:"
    echo "  doctl kubernetes cluster kubeconfig save d3e14d15-3c77-4620-95d5-ff84a8eee455"
    exit 1
fi

echo "⚠️  다음 namespace의 모든 리소스를 삭제합니다:"
echo "  - bodam-preview"
echo "  - bodam-prod"
echo ""
echo "삭제될 리소스:"
kubectl get all -n bodam-preview 2>/dev/null | grep -E "^(pod|deployment|service|statefulset)" | wc -l | xargs echo "  bodam-preview:"
kubectl get all -n bodam-prod 2>/dev/null | grep -E "^(pod|deployment|service|statefulset)" | wc -l | xargs echo "  bodam-prod:"
echo ""

read -p "정말 삭제하시겠습니까? (yes/NO): " -r
echo

if [[ ! $REPLY = "yes" ]]; then
    log_info "취소되었습니다"
    exit 0
fi

echo ""
log_info "🧹 정리 시작..."
echo ""

# bodam-preview 정리
if kubectl get namespace bodam-preview &>/dev/null; then
    log_info "bodam-preview 정리 중..."

    # 실패한 CronJob 먼저 삭제 (계속 Job 생성하는 것 방지)
    log_info "  CronJob 삭제..."
    kubectl delete cronjob --all -n bodam-preview --ignore-not-found

    # 실패한 Job들 삭제
    log_info "  실패한 Job 삭제..."
    kubectl delete job --all -n bodam-preview --ignore-not-found

    # HPA 삭제
    log_info "  HPA 삭제..."
    kubectl delete hpa --all -n bodam-preview --ignore-not-found

    # Deployment 삭제
    log_info "  Deployment 삭제..."
    kubectl delete deployment --all -n bodam-preview --ignore-not-found

    # StatefulSet 삭제
    log_info "  StatefulSet 삭제..."
    kubectl delete statefulset --all -n bodam-preview --ignore-not-found

    # Service 삭제
    log_info "  Service 삭제..."
    kubectl delete service --all -n bodam-preview --ignore-not-found

    # PVC 삭제 (데이터 삭제 주의!)
    log_info "  PVC 삭제..."
    kubectl delete pvc --all -n bodam-preview --ignore-not-found

    # ConfigMap, Secret 삭제
    log_info "  ConfigMap, Secret 삭제..."
    kubectl delete configmap --all -n bodam-preview --ignore-not-found
    kubectl delete secret --all -n bodam-preview --ignore-not-found

    # Namespace 삭제
    log_info "  Namespace 삭제..."
    kubectl delete namespace bodam-preview --ignore-not-found

    log_info "✅ bodam-preview 정리 완료"
else
    log_warn "bodam-preview namespace가 없습니다"
fi

echo ""

# bodam-prod 정리
if kubectl get namespace bodam-prod &>/dev/null; then
    log_info "bodam-prod 정리 중..."

    # HPA 삭제
    log_info "  HPA 삭제..."
    kubectl delete hpa --all -n bodam-prod --ignore-not-found

    # Deployment 삭제
    log_info "  Deployment 삭제..."
    kubectl delete deployment --all -n bodam-prod --ignore-not-found

    # StatefulSet 삭제
    log_info "  StatefulSet 삭제..."
    kubectl delete statefulset --all -n bodam-prod --ignore-not-found

    # Service 삭제
    log_info "  Service 삭제..."
    kubectl delete service --all -n bodam-prod --ignore-not-found

    # PVC 삭제 (데이터 삭제 주의!)
    log_info "  PVC 삭제..."
    kubectl delete pvc --all -n bodam-prod --ignore-not-found

    # ConfigMap, Secret 삭제
    log_info "  ConfigMap, Secret 삭제..."
    kubectl delete configmap --all -n bodam-prod --ignore-not-found
    kubectl delete secret --all -n bodam-prod --ignore-not-found

    # Namespace 삭제
    log_info "  Namespace 삭제..."
    kubectl delete namespace bodam-prod --ignore-not-found

    log_info "✅ bodam-prod 정리 완료"
else
    log_warn "bodam-prod namespace가 없습니다"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_info "🎉 모든 리소스 정리 완료!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
log_info "남은 리소스 확인:"
kubectl get all -A | grep bodam || echo "  bodam 관련 리소스 없음 ✅"
echo ""
log_info "이제 새로운 배포를 시작할 수 있습니다!"
echo ""
