#!/bin/bash
# 보담 플랫폼 배포 스크립트

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 메인 배포 함수
deploy_all() {
    local env=${1:-staging}
    local ns="bodam-$env"
    
    log_info "Deploying to '$env' environment (namespace: $ns)"
    
    # Namespace 생성
    kubectl create namespace "$ns" 2>/dev/null || true
    
    # Secrets
    kubectl create secret generic postgres-secret \
        --from-literal=username=bodam \
        --from-literal=password="${POSTGRES_PASSWORD:-changeme}" \
        -n "$ns" 2>/dev/null || log_warn "postgres-secret already exists"
    
    # ConfigMaps 및 리소스 배포
    kubectl apply -f infra/k8s/backend/configmap.yaml -n "$ns"
    kubectl apply -f infra/k8s/database/ -n "$ns"
    kubectl apply -f infra/k8s/backend/backend-deployment.yaml -n "$ns"
    kubectl apply -f infra/k8s/kong/ -n "$ns"
    kubectl apply -f infra/k8s/nginx/ -n "$ns"
    
    log_info "Deployment complete! Check status with: kubectl get pods -n $ns"
}

deploy_all "$@"
