#!/bin/bash
# Kubernetes 매니페스트 검증 스크립트

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_success() { echo -e "${GREEN}✅${NC} $1"; }
log_error() { echo -e "${RED}❌${NC} $1"; }

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "☸️  Kubernetes 매니페스트 검증"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

K8S_DIR="/home/donghee/bodam/infra/k8s"
ERROR_COUNT=0
SUCCESS_COUNT=0

# K8s 디렉토리 존재 확인
if [ ! -d "$K8S_DIR" ]; then
    log_error "K8s 매니페스트 디렉토리를 찾을 수 없습니다: $K8S_DIR"
    exit 1
fi

# kubectl 설치 확인
if ! command -v kubectl &> /dev/null; then
    log_error "kubectl이 설치되어 있지 않습니다"
    echo "설치 방법: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# 모든 YAML 파일 검증
echo "YAML 파일 검증 중..."
echo ""

while IFS= read -r -d '' yaml_file; do
    relative_path="${yaml_file#$K8S_DIR/}"

    # kubectl dry-run으로 문법 검증
    if kubectl apply --dry-run=client -f "$yaml_file" &>/dev/null; then
        log_success "$relative_path"
        ((SUCCESS_COUNT++))
    else
        log_error "$relative_path"
        echo "   오류 상세:"
        kubectl apply --dry-run=client -f "$yaml_file" 2>&1 | sed 's/^/   /'
        ((ERROR_COUNT++))
    fi
done < <(find "$K8S_DIR" -name "*.yaml" -o -name "*.yml" -print0)

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "검증 결과:"
echo "  성공: $SUCCESS_COUNT"
echo "  실패: $ERROR_COUNT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $ERROR_COUNT -gt 0 ]; then
    exit 1
fi
