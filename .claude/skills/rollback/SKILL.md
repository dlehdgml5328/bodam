---
name: rollback
description: 배포 실패 또는 문제 발생 시 이전 버전으로 롤백. Backend(K8s)와 Frontend(Vercel) 롤백 지원. "롤백", "이전 버전으로", "배포 취소" 요청 시 사용.
---

# 배포 롤백 Skill

배포 후 문제가 발생했거나 배포에 실패했을 때 이전 안정 버전으로 롤백합니다.

## 사용 시점

다음과 같은 요청을 받았을 때 이 Skill을 사용하세요:
- "롤백", "이전 버전으로 되돌려줘"
- "배포 취소", "배포 실패했어"
- "문제가 생겼어, 원래대로 돌려줘"
- Health Check 실패 또는 배포 오류 감지 시

## 실행 단계

### 1단계: 환경 확인

먼저 롤백할 환경을 확인하세요:
- 사용자가 명시한 환경 사용 (preview/production)
- 명시되지 않은 경우 현재 브랜치로 판단:
  - wonuk 브랜치 → preview
  - donghee 브랜치 → production

```bash
CURRENT_BRANCH=$(git branch --show-current)
echo "현재 브랜치: $CURRENT_BRANCH"
```

### 2단계: Production 롤백 특별 확인

만약 **production** 환경 롤백이라면:

사용자에게 다음을 확인하세요:
```
⚠️ Production 환경을 롤백하려고 합니다.

확인 사항:
- 현재 어떤 문제가 발생했나요?
- 롤백 대신 Hotfix가 더 나은 선택일 수 있습니다.
- 롤백 시 데이터 손실 가능성을 검토했나요?

계속 진행하시겠습니까? (yes/no)
```

사용자가 "no" 또는 확신하지 못하면 롤백을 중단하세요.

### 3단계: 현재 배포 상태 확인

#### Backend (K8s) 배포 상태
```bash
bash /home/donghee/bodam/.claude/skills/rollback/scripts/check-deployment-status.sh backend {preview|production}
```

**확인 사항**:
- 현재 실행 중인 이미지 태그
- Pod 상태
- 배포 히스토리

#### Frontend (Vercel) 배포 상태
```bash
bash /home/donghee/bodam/.claude/skills/rollback/scripts/check-deployment-status.sh frontend {preview|production}
```

**확인 사항**:
- 현재 배포된 버전
- 최근 배포 히스토리

### 4단계: 롤백 실행

#### Backend 롤백 (K8s)
```bash
bash /home/donghee/bodam/.claude/skills/rollback/scripts/rollback-backend.sh {preview|production}
```

**동작**:
1. Kubernetes Deployment의 이전 ReplicaSet으로 롤백
2. `kubectl rollout undo` 실행
3. 롤아웃 상태 확인
4. Pod 상태 모니터링

**예상 소요 시간**: 2-3분

#### Frontend 롤백 (Vercel)

사용자에게 다음 안내:
```
Frontend는 Vercel에서 롤백해야 합니다.

자동 롤백 방법 (vercel CLI):
1. vercel login
2. vercel rollback --yes

수동 롤백 방법:
1. Vercel 대시보드 접속: https://vercel.com/dashboard
2. 프로젝트 선택
3. Deployments 탭 이동
4. 이전 안정 버전 찾기
5. "..." 메뉴 → "Promote to Production" 클릭

권장: Vercel 대시보드에서 수동 롤백 (더 안전)
```

### 5단계: 롤백 후 검증

#### Health Check
환경에 따라 Health Check 실행:

**Preview**:
```bash
curl -f https://preview-api.bodam.com/health || echo "Health check failed"
```

**Production**:
```bash
curl -f https://api.bodam.com/health || echo "Health check failed"
```

#### 배포 상태 확인
```bash
# Backend Pod 상태
kubectl get pods -n bodam-{env} -l app=bodam-backend

# 최근 이벤트 확인
kubectl get events -n bodam-{env} --sort-by='.lastTimestamp' | tail -20
```

#### Smoke Test
기본 API 엔드포인트 테스트:
```bash
# API 응답 테스트
curl -s -o /dev/null -w "%{http_code}" https://api.bodam.com/api/v1/health
```

**성공 조건**: HTTP 200 응답

### 6단계: 롤백 결과 리포트

롤백 완료 후 사용자에게 다음 형식으로 보고:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 롤백 완료
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

환경: {preview/production}
롤백 대상: {backend/frontend/both}

Backend 롤백:
✅ 이전 버전으로 롤백 완료
   이전 이미지: registry.digitalocean.com/bodam/backend:production-abc123
   현재 이미지: registry.digitalocean.com/bodam/backend:production-xyz789
   Pod 상태: 3/3 Ready

Frontend 롤백:
⏳ Vercel 대시보드에서 수동 롤백 필요
   링크: https://vercel.com/dashboard

검증 결과:
✅ Health Check 통과
✅ API 응답 정상 (HTTP 200)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
다음 단계:
1. 서비스가 정상 동작하는지 모니터링
2. 롤백 원인 분석 및 수정
3. 수정 후 재배포 또는 Hotfix
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 롤백 시나리오별 대응

### 시나리오 1: 배포 직후 오류 발견
- **대응**: 즉시 롤백 (Backend + Frontend)
- **우선순위**: 높음

### 시나리오 2: Health Check 실패
- **대응**: Backend 롤백 우선, Frontend 확인
- **우선순위**: 높음

### 시나리오 3: 특정 기능 오류
- **대응**: Hotfix 검토 후 필요시 롤백
- **우선순위**: 중간

### 시나리오 4: 성능 저하
- **대응**: 모니터링 후 롤백 여부 결정
- **우선순위**: 중간

### 시나리오 5: 데이터베이스 마이그레이션 오류
- **대응**:
  1. 즉시 Backend 롤백
  2. 데이터베이스 마이그레이션 롤백 (별도 작업)
  3. 데이터 정합성 확인
- **우선순위**: 매우 높음
- **경고**: DBA와 협의 필수

## 롤백 실패 시 대응

### Backend 롤백 실패
1. 수동 롤백 시도:
   ```bash
   kubectl rollout undo deployment/bodam-backend -n bodam-{env}
   kubectl rollout status deployment/bodam-backend -n bodam-{env}
   ```

2. 실패 시 특정 리비전으로 롤백:
   ```bash
   kubectl rollout history deployment/bodam-backend -n bodam-{env}
   kubectl rollout undo deployment/bodam-backend --to-revision={N} -n bodam-{env}
   ```

3. 최후의 수단 - Pod 재시작:
   ```bash
   kubectl rollout restart deployment/bodam-backend -n bodam-{env}
   ```

### Frontend 롤백 실패
- Vercel 지원팀 문의: https://vercel.com/support
- GitHub에서 이전 커밋으로 새 배포 트리거

## 롤백 후 조치

### 즉시 조치
1. 모니터링 대시보드 확인 (Grafana)
2. 에러 로그 수집 및 분석
3. 사용자 영향도 파악
4. 관련 팀에 알림 (Slack)

### 사후 조치
1. 롤백 원인 분석
2. 문제 수정 및 테스트
3. Hotfix 또는 새 배포 계획
4. 배포 프로세스 개선

## 롤백 히스토리 관리

롤백 실행 시 다음 정보를 기록:
- 롤백 일시
- 롤백 환경
- 롤백 대상 (Backend/Frontend)
- 롤백 사유
- 이전 버전 정보
- 롤백 후 검증 결과

## 참고 스크립트

- Backend 롤백: `scripts/rollback-backend.sh`
- 배포 상태 확인: `scripts/check-deployment-status.sh`

## 관련 Skills

- `deploy`: 롤백 후 재배포
- `deploy-status`: 롤백 후 상태 모니터링
- `predeploy`: 재배포 전 검증

## 주의사항

⚠️ **중요**:
- Production 롤백은 신중하게 결정
- 데이터베이스 마이그레이션이 있었다면 추가 검토 필요
- 롤백 전 현재 상태 스냅샷 권장
- 롤백은 일시적 조치, 근본 원인 해결 필요
