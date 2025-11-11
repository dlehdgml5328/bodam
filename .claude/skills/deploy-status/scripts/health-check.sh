#!/bin/bash
# Health Check 스크립트

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_success() { echo -e "${GREEN}✅${NC} $1"; }
log_warn() { echo -e "${YELLOW}⚠️${NC} $1"; }
log_error() { echo -e "${RED}❌${NC} $1"; }

# 환경 파라미터
ENVIRONMENT=${1:-preview}

# API URL 설정
if [ "$ENVIRONMENT" = "production" ]; then
    BACKEND_API_URL="https://api.bodam.website"
    FRONTEND_URL="https://frontend-sigma-pearl-65.vercel.app"
else
    # Preview 환경은 아직 미구성 (나중에 추가 예정)
    BACKEND_API_URL="https://api.bodam.website"
    FRONTEND_URL="https://frontend-sigma-pearl-65.vercel.app"
    log_warn "Preview 환경이 아직 구성되지 않았습니다. Production URL을 사용합니다."
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💚 Health Check ($ENVIRONMENT)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# curl 설치 확인
if ! command -v curl &> /dev/null; then
    log_error "curl이 설치되어 있지 않습니다"
    exit 1
fi

TOTAL_CHECKS=0
PASSED_CHECKS=0

# Backend Health Check
echo "🔍 Backend API Health Check:"
echo ""

# /health 엔드포인트
echo -n "  $BACKEND_API_URL/health ... "
((TOTAL_CHECKS++))

RESPONSE=$(curl -s -o /dev/null -w "%{http_code}|%{time_total}" "$BACKEND_API_URL/health" 2>/dev/null || echo "000|0")
HTTP_CODE=$(echo "$RESPONSE" | cut -d'|' -f1)
RESPONSE_TIME=$(echo "$RESPONSE" | cut -d'|' -f2)

if [ "$HTTP_CODE" = "200" ]; then
    RESPONSE_TIME_MS=$(echo "$RESPONSE_TIME * 1000" | bc)
    log_success "HTTP $HTTP_CODE (${RESPONSE_TIME_MS}ms)"
    ((PASSED_CHECKS++))
else
    log_error "HTTP $HTTP_CODE"
fi

# /api/v1/health 엔드포인트
echo -n "  $BACKEND_API_URL/api/v1/health ... "
((TOTAL_CHECKS++))

RESPONSE=$(curl -s -o /dev/null -w "%{http_code}|%{time_total}" "$BACKEND_API_URL/api/v1/health" 2>/dev/null || echo "000|0")
HTTP_CODE=$(echo "$RESPONSE" | cut -d'|' -f1)
RESPONSE_TIME=$(echo "$RESPONSE" | cut -d'|' -f2)

if [ "$HTTP_CODE" = "200" ]; then
    RESPONSE_TIME_MS=$(echo "$RESPONSE_TIME * 1000" | bc)
    log_success "HTTP $HTTP_CODE (${RESPONSE_TIME_MS}ms)"
    ((PASSED_CHECKS++))

    # 응답 내용 확인
    HEALTH_RESPONSE=$(curl -s "$BACKEND_API_URL/api/v1/health" 2>/dev/null || echo "{}")
    echo "  응답: $HEALTH_RESPONSE"
else
    log_error "HTTP $HTTP_CODE"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Frontend Health Check:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Frontend 홈페이지
echo -n "  $FRONTEND_URL ... "
((TOTAL_CHECKS++))

RESPONSE=$(curl -s -o /dev/null -w "%{http_code}|%{time_total}" "$FRONTEND_URL" 2>/dev/null || echo "000|0")
HTTP_CODE=$(echo "$RESPONSE" | cut -d'|' -f1)
RESPONSE_TIME=$(echo "$RESPONSE" | cut -d'|' -f2)

if [ "$HTTP_CODE" = "200" ]; then
    RESPONSE_TIME_MS=$(echo "$RESPONSE_TIME * 1000" | bc)
    log_success "HTTP $HTTP_CODE (${RESPONSE_TIME_MS}ms)"
    ((PASSED_CHECKS++))

    # 페이지 렌더링 확인
    PAGE_CONTENT=$(curl -s "$FRONTEND_URL" 2>/dev/null)
    if echo "$PAGE_CONTENT" | grep -q "보담"; then
        log_success "페이지 렌더링 정상"
    else
        log_warn "페이지 렌더링 확인 필요"
    fi
else
    log_error "HTTP $HTTP_CODE"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 추가 API 엔드포인트 테스트:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# /api/v1/auth/me (인증 필요, 401 정상)
echo -n "  $BACKEND_API_URL/api/v1/auth/me (인증 테스트) ... "
((TOTAL_CHECKS++))

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_API_URL/api/v1/auth/me" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "401" ]; then
    log_success "HTTP $HTTP_CODE (정상 - 인증 필요)"
    ((PASSED_CHECKS++))
elif [ "$HTTP_CODE" = "200" ]; then
    log_success "HTTP $HTTP_CODE (인증됨)"
    ((PASSED_CHECKS++))
else
    log_error "HTTP $HTTP_CODE (예상: 401 또는 200)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Health Check 결과 요약"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

PASS_RATE=$(echo "scale=1; $PASSED_CHECKS * 100 / $TOTAL_CHECKS" | bc)

echo "통과: $PASSED_CHECKS / $TOTAL_CHECKS (${PASS_RATE}%)"
echo ""

if [ "$PASSED_CHECKS" -eq "$TOTAL_CHECKS" ]; then
    log_success "모든 Health Check 통과"
    echo ""
    echo "✨ 시스템이 정상 동작 중입니다"
    EXIT_CODE=0
elif [ "$PASSED_CHECKS" -ge $((TOTAL_CHECKS * 2 / 3)) ]; then
    log_warn "일부 Health Check 실패"
    echo ""
    echo "⚠️ 일부 서비스에 문제가 있을 수 있습니다"
    echo "   실패한 항목을 확인하세요"
    EXIT_CODE=1
else
    log_error "대부분의 Health Check 실패"
    echo ""
    echo "❌ 시스템에 심각한 문제가 있습니다"
    echo "   즉시 확인이 필요합니다"
    echo ""
    echo "다음 단계:"
    echo "  1. Pod 로그 확인"
    echo "  2. 에러 로그 분석"
    echo "  3. 롤백 검토"
    EXIT_CODE=2
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit $EXIT_CODE
