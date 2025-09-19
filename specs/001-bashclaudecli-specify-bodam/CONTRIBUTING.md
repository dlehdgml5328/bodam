# 기여 가이드 🤝

## 개요
보담(BoDam) 프로젝트에 기여하는 방법, 개발 프로세스, 코드 리뷰 가이드라인을 정의합니다.

## 🌟 기여 방법

### 1. 프로젝트 참여 전 준비
- [개발 환경 설정](./DEVELOPMENT.md)을 완료해주세요
- [행동 강령](#행동-강령)을 읽고 동의해주세요
- 이슈 트래커에서 작업할 이슈를 선택하거나 새로운 아이디어를 제안해주세요

### 2. 기여 유형
```markdown
🐛 버그 수정 (Bug Fix)
✨ 새로운 기능 (Feature)
📚 문서화 (Documentation)
🎨 디자인 개선 (UI/UX)
⚡ 성능 개선 (Performance)
🔒 보안 개선 (Security)
🧪 테스트 추가 (Testing)
♻️ 리팩토링 (Refactoring)
```

## 🔄 개발 워크플로우

### 1. 이슈 생성
```markdown
이슈 생성 시 다음 정보를 포함해주세요:

**이슈 유형**: Bug / Feature / Enhancement / Documentation

**설명**:
간단명료한 이슈 설명

**재현 단계** (버그인 경우):
1. ...
2. ...
3. ...

**기대 결과**:
어떤 결과를 기대했는지

**실제 결과**:
실제로 어떤 일이 발생했는지

**환경 정보**:
- OS: [예: Ubuntu 20.04]
- Node.js: [예: 18.16.0]
- Python: [예: 3.11.2]
- 브라우저: [예: Chrome 114.0]

**추가 정보**:
스크린샷, 로그, 관련 링크 등
```

### 2. 브랜치 전략
```bash
# 메인 브랜치
main           # 프로덕션 배포용 안정 버전
develop        # 개발 통합 브랜치

# 기능 브랜치 네이밍
feature/issue-123-recurring-donations    # 새로운 기능
bugfix/issue-456-payment-validation      # 버그 수정
hotfix/critical-security-patch           # 긴급 수정
docs/update-api-documentation            # 문서화
refactor/user-service-cleanup            # 리팩토링

# 브랜치 생성 예시
git checkout develop
git pull origin develop
git checkout -b feature/issue-123-recurring-donations
```

### 3. 커밋 메시지 규칙
```bash
# 커밋 메시지 형식
<type>(<scope>): <subject>

<body>

<footer>

# 예시
feat(donations): add recurring donation functionality

- Add monthly/yearly subscription options
- Integrate with Toss Payments billing API
- Add subscription management UI
- Include email notifications for billing

Closes #123
```

#### 커밋 타입
```markdown
feat:     새로운 기능
fix:      버그 수정
docs:     문서화
style:    코드 스타일 (포맷팅, 세미콜론 누락 등)
refactor: 리팩토링
test:     테스트 추가/수정
chore:    빌드, 패키지 관리 등
perf:     성능 개선
security: 보안 개선
```

#### 스코프 예시
```markdown
auth:         인증/인가
donations:    기부 관련
stations:     소방서 관련
payments:     결제 관련
notifications: 알림 관련
ui:           사용자 인터페이스
api:          API 관련
db:           데이터베이스
infra:        인프라/배포
```

## 📝 Pull Request 가이드라인

### 1. PR 생성 전 체크리스트
```markdown
- [ ] 관련 이슈가 존재하는가? (없다면 이슈부터 생성)
- [ ] 로컬에서 모든 테스트가 통과하는가?
- [ ] 코드 스타일 가이드를 준수했는가?
- [ ] 새로운 기능에 대한 테스트를 작성했는가?
- [ ] 문서를 업데이트했는가? (API 변경, 새 기능 등)
- [ ] 브레이킹 체인지가 있다면 명시했는가?
```

### 2. PR 템플릿
```markdown
## 📋 요약
이 PR에서 무엇을 변경했는지 간단히 설명

## 🔗 관련 이슈
Closes #123
Fixes #456
Related to #789

## 🚀 변경 사항
- [ ] 새로운 기능 추가
- [ ] 버그 수정
- [ ] 성능 개선
- [ ] 리팩토링
- [ ] 문서 업데이트
- [ ] 기타: ___

### 상세 설명
변경 사항에 대한 상세한 설명

## 🧪 테스트
- [ ] 새로운 테스트 추가
- [ ] 기존 테스트 수정
- [ ] 수동 테스트 완료

### 테스트 시나리오
1. ...
2. ...

## 📸 스크린샷/녹화 (UI 변경 시)
변경 전/후 스크린샷 또는 동작 영상

## 🔍 리뷰어 체크포인트
- 코드 품질과 가독성
- 성능 영향도
- 보안 고려사항
- 테스트 커버리지

## 📝 추가 정보
배포 시 주의사항, 환경 변수 변경 등
```

### 3. PR 크기 가이드라인
```markdown
Small (권장):
- 파일 10개 미만
- 변경 라인 300줄 미만
- 단일 책임, 단일 목적

Medium:
- 파일 20개 미만
- 변경 라인 800줄 미만
- 관련된 여러 컴포넌트 변경

Large (지양):
- 파일 20개 이상
- 변경 라인 800줄 이상
- 가능하면 작은 PR로 분할 권장
```

## 🔍 코드 리뷰 프로세스

### 1. 리뷰어 지정
```markdown
자동 지정:
- CODEOWNERS 파일 기반 자동 할당
- 최소 2명의 리뷰어 필요 (코어 멤버 1명 포함)

수동 지정:
- 특정 영역 전문가
- 기능 소유자
- 멘토/시니어 개발자
```

### 2. 리뷰 가이드라인

#### 리뷰어를 위한 체크리스트
```markdown
코드 품질:
- [ ] 코드가 명확하고 이해하기 쉬운가?
- [ ] 변수명과 함수명이 의미를 잘 전달하는가?
- [ ] 복잡한 로직에 주석이 적절히 작성되었는가?
- [ ] DRY 원칙을 잘 지켰는가?

기능성:
- [ ] 요구사항을 정확히 구현했는가?
- [ ] 에지 케이스를 고려했는가?
- [ ] 에러 핸들링이 적절한가?

성능:
- [ ] 불필요한 리소스 사용은 없는가?
- [ ] 데이터베이스 쿼리가 최적화되었는가?
- [ ] 메모리 누수 가능성은 없는가?

보안:
- [ ] 입력 검증이 적절한가?
- [ ] 인증/인가가 올바르게 구현되었는가?
- [ ] 민감한 정보가 로그에 노출되지 않는가?

테스트:
- [ ] 테스트 커버리지가 충분한가?
- [ ] 테스트가 실제 의미 있는 검증을 하는가?
- [ ] 통합 테스트가 필요한 경우 작성되었는가?
```

#### 리뷰 코멘트 가이드
```markdown
건설적인 피드백:
✅ "이 함수는 너무 길어서 가독성이 떨어집니다. 작은 함수들로 분리하는 것이 어떨까요?"
❌ "이 코드는 엉망입니다."

구체적인 제안:
✅ "async/await를 사용하면 더 읽기 쉬울 것 같습니다. 예: await fetchUser(id)"
❌ "이 부분을 개선해주세요."

긍정적인 피드백:
✅ "에러 핸들링이 잘 되어있네요! 👍"
✅ "테스트 커버리지가 훌륭합니다."
```

### 3. 리뷰 상태
```markdown
✅ Approved: 승인, 머지 가능
🔄 Changes Requested: 수정 요청
💬 Comment: 일반적인 피드백 (머지 블로킹 아님)
```

## 🧪 테스트 가이드라인

### 1. 테스트 작성 원칙
```python
# 백엔드 테스트 예시
class TestDonationService:
    """기부 서비스 테스트"""

    async def test_create_donation_success(self, db_session, sample_user):
        """기부 생성 성공 테스트"""
        # Given
        donation_data = {
            "fire_station_id": "test-station-id",
            "amount": 10000,
            "message": "응원합니다!"
        }

        # When
        service = DonationService(db_session)
        result = await service.create_donation(sample_user.id, donation_data)

        # Then
        assert result.amount == 10000
        assert result.user_id == sample_user.id
        assert result.status == "pending"

    async def test_create_donation_invalid_amount(self, db_session, sample_user):
        """기부 금액 유효성 검사 테스트"""
        # Given
        donation_data = {"amount": 500}  # 최소 금액 미달

        # When & Then
        service = DonationService(db_session)
        with pytest.raises(ValidationError) as exc_info:
            await service.create_donation(sample_user.id, donation_data)

        assert "최소 기부 금액은 1,000원입니다" in str(exc_info.value)
```

```typescript
// 프론트엔드 테스트 예시
describe('DonationForm', () => {
  it('should submit donation with valid data', async () => {
    // Given
    const mockSubmit = vi.fn();
    render(<DonationForm onSubmit={mockSubmit} />);

    // When
    await user.type(screen.getByLabelText('기부 금액'), '10000');
    await user.type(screen.getByLabelText('응원 메시지'), '소방관들을 응원합니다!');
    await user.click(screen.getByRole('button', { name: '기부하기' }));

    // Then
    expect(mockSubmit).toHaveBeenCalledWith({
      amount: 10000,
      message: '소방관들을 응원합니다!'
    });
  });

  it('should show error for invalid amount', async () => {
    // Given
    render(<DonationForm onSubmit={vi.fn()} />);

    // When
    await user.type(screen.getByLabelText('기부 금액'), '500');
    await user.click(screen.getByRole('button', { name: '기부하기' }));

    // Then
    expect(screen.getByText('최소 기부 금액은 1,000원입니다')).toBeInTheDocument();
  });
});
```

### 2. 테스트 커버리지 목표
```markdown
백엔드:
- 전체 커버리지: ≥70%
- 핵심 비즈니스 로직: ≥99%
- API 엔드포인트: 100%

프론트엔드:
- 전체 커버리지: ≥80%
- 컴포넌트: ≥90%
- 유틸리티 함수: 100%

E2E 테스트:
- 주요 사용자 플로우: 100%
- 결제 플로우: 100%
- 인증 플로우: 100%
```

## 📚 문서화 가이드라인

### 1. API 문서화
```python
# FastAPI 자동 문서화 활용
@app.post("/donations", response_model=DonationResponse)
async def create_donation(
    donation_data: DonationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    새로운 기부를 생성합니다.

    - **fire_station_id**: 기부 대상 소방서 ID
    - **amount**: 기부 금액 (최소 1,000원)
    - **type**: 기부 유형 (one_time, recurring)
    - **message**: 응원 메시지 (선택사항)

    **Returns**: 생성된 기부 정보와 결제 URL
    """
    return await donation_service.create_donation(current_user.id, donation_data)
```

### 2. 컴포넌트 문서화
```typescript
/**
 * 기부 폼 컴포넌트
 *
 * @param fireStationId - 기부 대상 소방서 ID
 * @param onSubmit - 기부 데이터 제출 시 호출되는 콜백
 * @param initialAmount - 초기 기부 금액 (선택사항)
 *
 * @example
 * ```tsx
 * <DonationForm
 *   fireStationId="station-123"
 *   onSubmit={handleDonationSubmit}
 *   initialAmount={10000}
 * />
 * ```
 */
export interface DonationFormProps {
  fireStationId: string;
  onSubmit: (data: DonationData) => void;
  initialAmount?: number;
}
```

## 🎯 이슈 라벨 시스템

```markdown
Priority (우선순위):
🔴 critical    - 서비스 중단, 보안 취약점
🟠 high        - 주요 기능 버그, 성능 문제
🟡 medium      - 일반 버그, 기능 개선
🟢 low         - 사소한 개선, 문서화

Type (유형):
🐛 bug         - 버그 수정
✨ feature     - 새로운 기능
📚 docs        - 문서화
🎨 ui/ux       - 디자인 개선
⚡ performance - 성능 개선
🔒 security    - 보안 개선
🧪 testing     - 테스트 관련

Status (상태):
🆕 new         - 새로운 이슈
🔍 investigating - 조사 중
✅ ready       - 작업 준비 완료
🚧 in-progress - 진행 중
👀 review      - 리뷰 중
✅ done        - 완료

Area (영역):
backend        - 백엔드 관련
frontend       - 프론트엔드 관련
infra          - 인프라/배포
api            - API 관련
database       - 데이터베이스
```

## 🏆 기여자 인정

### 1. 기여자 레벨
```markdown
🌱 Contributor: 첫 기여 (PR 머지)
🌿 Regular: 5+ PR 머지
🌳 Core: 20+ PR 머지 + 코드 리뷰 권한
🌟 Maintainer: 프로젝트 관리 권한
```

### 2. 인정 방식
- **README.md** Contributors 섹션에 추가
- **릴리즈 노트**에 기여자 언급
- **소셜 미디어**에서 기여 감사 표현
- **기여자 뱃지** 발급

## 📞 소통 채널

```markdown
💬 일반 질문: GitHub Discussions
🐛 버그 리포트: GitHub Issues
💡 기능 제안: GitHub Issues (feature 라벨)
🔒 보안 문제: security@bodam.example
📧 일반 문의: contact@bodam.example
```

## 📋 행동 강령

### 우리의 약속
보담 프로젝트 커뮤니티는 모든 참여자에게 괴롭힘 없는 경험을 제공하기 위해 노력합니다.

### 기대하는 행동
- 서로 다른 관점을 존중하고 이해하기
- 건설적인 비판을 우아하게 주고받기
- 커뮤니티에 가장 도움이 되는 것에 집중하기
- 다른 커뮤니티 구성원에게 공감하기

### 받아들일 수 없는 행동
- 성적/정치적 이미지나 언어 사용
- 개인 공격이나 모욕적/경멸적 댓글
- 공적/사적 괴롭힘
- 명시적 허가 없이 다른 사람의 개인정보 공개

---

보담 프로젝트에 기여해주셔서 감사합니다! 함께 더 나은 플랫폼을 만들어가요. 🔥☕