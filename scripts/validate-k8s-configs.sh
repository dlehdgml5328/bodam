#!/bin/bash

# Kubernetes 설정 파일 유효성 검사 스크립트
# 사용법: ./scripts/validate-k8s-configs.sh

set -e

echo "=========================================="
echo "Kubernetes 설정 파일 유효성 검사"
echo "=========================================="
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 검사 결과 카운터
PASSED=0
FAILED=0
WARNINGS=0

# 함수: 성공 메시지
success() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

# 함수: 실패 메시지
fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

# 함수: 경고 메시지
warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

# kubectl 설치 확인
echo "1. 사전 요구사항 확인"
echo "----------------------------"

if command -v kubectl &> /dev/null; then
    success "kubectl 설치 확인됨 ($(kubectl version --client --short 2>/dev/null))"
else
    fail "kubectl이 설치되지 않음"
fi

if command -v docker &> /dev/null; then
    success "docker 설치 확인됨 ($(docker --version))"
else
    warn "docker가 설치되지 않음 (로컬 테스트에만 필요)"
fi

echo ""

# YAML 파일 검증
echo "2. YAML 파일 구문 검증"
echo "----------------------------"

YAML_FILES=(
    "infra/k8s/backend/backend-deployment.yaml"
    "infra/k8s/backend/backend-hpa.yaml"
    "infra/k8s/backend/celery-worker-hpa.yaml"
    "infra/k8s/backend/configmap.yaml"
    "infra/k8s/cluster-autoscaler/autoscaler-config.yaml"
)

for file in "${YAML_FILES[@]}"; do
    if [ -f "$file" ]; then
        if kubectl apply --dry-run=client -f "$file" &> /dev/null; then
            success "$file - 구문 유효"
        else
            fail "$file - 구문 오류"
        fi
    else
        fail "$file - 파일 없음"
    fi
done

echo ""

# 리소스 계산 검증
echo "3. 리소스 계산 검증"
echo "----------------------------"

CPU_REQUEST_FASTAPI=200
CPU_REQUEST_CELERY=200
MEMORY_REQUEST_FASTAPI=256
MEMORY_REQUEST_CELERY=256

TOTAL_CPU_REQUEST=$((CPU_REQUEST_FASTAPI + CPU_REQUEST_CELERY))
TOTAL_MEMORY_REQUEST=$((MEMORY_REQUEST_FASTAPI + MEMORY_REQUEST_CELERY))

echo "Pod당 리소스 요청:"
echo "  - CPU: ${TOTAL_CPU_REQUEST}m (0.4 CPU)"
echo "  - Memory: ${TOTAL_MEMORY_REQUEST}Mi (512MB)"
echo ""

NODE_CPU=2000  # 2 vCPU = 2000m
NODE_MEMORY=4096  # 4GB = 4096Mi

MAX_PODS_CPU=$((NODE_CPU / TOTAL_CPU_REQUEST))
MAX_PODS_MEMORY=$((NODE_MEMORY / TOTAL_MEMORY_REQUEST))

echo "2vCPU/4GB 노드당 최대 Pod 수:"
echo "  - CPU 기준: ${MAX_PODS_CPU}개"
echo "  - Memory 기준: ${MAX_PODS_MEMORY}개"
echo ""

if [ $MAX_PODS_CPU -ge 4 ] && [ $MAX_PODS_MEMORY -ge 4 ]; then
    success "리소스 계산 적절 (노드당 4개 이상 Pod 실행 가능)"
else
    warn "리소스 계산 재검토 필요 (노드당 4개 미만 Pod만 실행 가능)"
fi

# HPA 설정 검증
HPA_MAX_REPLICAS=3
if [ $HPA_MAX_REPLICAS -le $MAX_PODS_CPU ]; then
    success "HPA 설정 적절 (maxReplicas: $HPA_MAX_REPLICAS ≤ 노드 용량: $MAX_PODS_CPU)"
else
    fail "HPA 설정 과다 (maxReplicas: $HPA_MAX_REPLICAS > 노드 용량: $MAX_PODS_CPU)"
fi

echo ""

# HPA 메트릭 타겟 검증
echo "4. HPA 메트릭 타겟 검증"
echo "----------------------------"

# backend-hpa.yaml에서 메트릭 타겟 추출
if [ -f "infra/k8s/backend/backend-hpa.yaml" ]; then
    CPU_TARGET=$(grep -A 4 "name: cpu" infra/k8s/backend/backend-hpa.yaml | grep "averageUtilization:" | awk '{print $2}')
    MEMORY_TARGET=$(grep -A 4 "name: memory" infra/k8s/backend/backend-hpa.yaml | grep "averageUtilization:" | awk '{print $2}')

    echo "Backend HPA 타겟:"
    echo "  - CPU: ${CPU_TARGET}%"
    echo "  - Memory: ${MEMORY_TARGET}%"
    echo ""

    if [ "$CPU_TARGET" -le 70 ]; then
        success "CPU 타겟 적절 (${CPU_TARGET}% ≤ 70%)"
    else
        warn "CPU 타겟 높음 (${CPU_TARGET}% > 70%)"
    fi

    if [ "$MEMORY_TARGET" -le 80 ]; then
        success "Memory 타겟 적절 (${MEMORY_TARGET}% ≤ 80%)"
    else
        warn "Memory 타겟 높음 (${MEMORY_TARGET}% > 80%)"
    fi
fi

echo ""

# Cluster Autoscaler 설정 검증
echo "5. Cluster Autoscaler 설정 검증"
echo "----------------------------"

if [ -f "infra/k8s/cluster-autoscaler/autoscaler-config.yaml" ]; then
    if grep -q "nodes=1:2:" infra/k8s/cluster-autoscaler/autoscaler-config.yaml; then
        success "노드 범위 설정 확인됨 (1-2 노드)"
    else
        warn "노드 범위 설정 확인 필요"
    fi

    if grep -q "scale-down-delay-after-add=5m" infra/k8s/cluster-autoscaler/autoscaler-config.yaml; then
        success "스케일 다운 지연 설정 확인됨 (5분)"
    else
        warn "스케일 다운 지연 설정 확인 필요"
    fi

    if grep -q "scale-down-unneeded-time=10m" infra/k8s/cluster-autoscaler/autoscaler-config.yaml; then
        success "미사용 시간 설정 확인됨 (10분)"
    else
        warn "미사용 시간 설정 확인 필요"
    fi
fi

echo ""

# GitHub Actions 워크플로우 검증
echo "6. GitHub Actions 워크플로우 검증"
echo "----------------------------"

WORKFLOW_FILES=(
    ".github/workflows/backend-ci-cd.yml"
    ".github/workflows/frontend-ci-cd.yml"
)

for file in "${WORKFLOW_FILES[@]}"; do
    if [ -f "$file" ]; then
        success "$file - 파일 존재"

        # wonuk 브랜치 트리거 확인
        if grep -q "wonuk" "$file"; then
            success "  └─ wonuk 브랜치 트리거 설정됨"
        else
            warn "  └─ wonuk 브랜치 트리거 누락"
        fi

        # donghee 브랜치 트리거 확인
        if grep -q "donghee" "$file"; then
            success "  └─ donghee 브랜치 트리거 설정됨"
        else
            warn "  └─ donghee 브랜치 트리거 누락"
        fi
    else
        fail "$file - 파일 없음"
    fi
done

echo ""

# 문서 검증
echo "7. 문서 검증"
echo "----------------------------"

DOC_FILES=(
    "DEPLOYMENT.md"
    "CI-CD-SETUP-SUMMARY.md"
    "infra/k8s/cluster-autoscaler/README.md"
)

for file in "${DOC_FILES[@]}"; do
    if [ -f "$file" ]; then
        success "$file - 파일 존재"
    else
        warn "$file - 파일 없음"
    fi
done

echo ""

# 최종 결과
echo "=========================================="
echo "검사 결과"
echo "=========================================="
echo -e "${GREEN}통과: $PASSED${NC}"
echo -e "${YELLOW}경고: $WARNINGS${NC}"
echo -e "${RED}실패: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ 모든 필수 검사 통과!${NC}"
    exit 0
else
    echo -e "${RED}✗ 일부 검사 실패. 위 내용을 확인하세요.${NC}"
    exit 1
fi
