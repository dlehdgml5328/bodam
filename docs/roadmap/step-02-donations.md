# Step 02 — 기부 · 정기결제 정합화 작업 메모

## 범위
- 프런트가 기대하는 단일/복수/단체/정기 기부 흐름을 백엔드와 스펙에 반영.
- Toss 빌링 키와 소방서별 분배 정보를 저장할 수 있는 모델·서비스 기초 마련.

## 프런트 요구사항 정리
- `mode`: `single` / `multiple`, 복수일 때 `multipleType`(`split`, `each`, `custom`)에 따라 소방서별 금액 분배.
- 단체 기부 플래그(`isGroupDonation`) 및 `groupCode`, `groupInfo`, 개인 담당자 이름(`individualDonorName`).
- 정기 기부 전환(`isRegularDonation`) 시 주기(`monthly`, `quarterly`, `yearly`)와 시작일을 전송.
- 기부자 표시 이름, 이메일/연락처, 영수증 발급 여부(`needReceipt`), 메시지, 익명 처리(`isAnonymous`).
- Checkout 결과로 `orderId`, 결제 URL, 정기 기부일 경우 빌링 인증 URL을 기대.
- 마이페이지 정기 기부 탭은 `status`(active/paused/cancelled)와 `nextBillingDate`를 표시.

## 현행 백엔드 상태
- `Donation` 모델은 단일 소방서 FK만 보유, 정기 결제/단체 메타/분배 정보 없음.
- 복수 소방서 기부, Toss 빌링 키, 그룹 연계에 대한 스키마 및 서비스 로직 미구현.
- SpecKit `donations-api.yaml` 구조가 단순 POST/GET 목업 형태.

## 제안 모델 변경
| 테이블 | 변경 내용 |
| --- | --- |
| `donations` | `mode` enum(`single`,`multiple`), `group_id` FK, `donor_display_name`, `needs_receipt`, `is_group_anonymous`, `metadata` JSON, `billing_customer_key`, `billing_key`, `subscription_id` FK(정기용) 컬럼 추가 |
| `donation_allocations` *(신규)* | `id`, `donation_id` FK, `fire_station_id` FK, `amount`, `allocation_type` enum(`split`,`each`,`custom`,`primary`) |
| `donation_subscriptions` *(신규)* | `id`, `user_id`, `origin_donation_id`, `cycle` enum(`monthly`,`quarterly`,`yearly`), `status` enum(`active`,`paused`,`cancelled`), `next_billing_at`, `started_at`, `ended_at`, `toss_customer_key`, `toss_billing_key` |
| `groups` | 기존 스키마 유지 (기부와 연결만 추가) |

## 서비스 · API 개편안
- `POST /donations/checkout` *(기존 POST /donations 대체)*: 확장된 페이로드 수용, Toss 결제 URL 및 정기 기부 시 빌링 인증 URL 반환.
- `GET /donations`: 분배(`allocations`)·단체 메타·정기 정보 포함 응답 구조로 확장.
- `POST /subscriptions`, `POST /subscriptions/{id}/pause|resume|cancel`: `donation_subscriptions` 기반으로 동작.
- `DonationService`: 모드 검증 → `Donation` + `allocations` 생성 → Toss API 호출 → 정기 기부면 `donation_subscriptions` 작성 흐름으로 재구성.

## 마이그레이션 플랜
1. Alembic 리비전 생성 → 새 enum/테이블/컬럼 추가.
2. 기존 `donations` 데이터는 `mode='single'`, 신규 컬럼 기본값 지정.
3. FK 및 인덱스(`donation_id`, `fire_station_id`, `status`, `next_billing_at`) 생성.
4. SQLAlchemy 모델 업데이트 후 기존 코드 리팩터링.

## 구현 Todo
1. SpecKit (`donations-api.yaml`, `groups-api.yaml`) 업데이트.
2. 모델 정의(`Donation`, `DonationAllocation`, `DonationSubscription`) 및 마이그레이션 작성.
3. 서비스 계층 확장 + Toss 연동용 인터페이스 정의.
4. FastAPI 라우트 페이로드/응답 스키마 반영.
5. 프런트 전달용 매핑 문서 작성.

## 이슈/의문점
- `groupInfo` 상세 구조 확정 필요 (외부 시스템 연동 여부).
- Toss 빌링 API 스펙 확인 후 `billing_key` 컬럼 명세 확정.
- 다중 기부를 하나의 영수증으로 처리할지, 소방서별로 분리할지 추후 결정 필요.

## 체크리스트
- [x] 기부/정기결제 확장 스펙 업데이트 (`donations-api.yaml`)
- [x] SQLAlchemy 모델 + Alembic 마이그레이션 추가
- [x] FastAPI 라우트 스키마 정비 및 요청 검증 추가
- [x] `DonationService` 다중/정기 기부 로직 구현
- [x] Toss 결제/빌링 연동 (Sandbox 키 확인 포함)
- [x] 정기 구독 API(일시정지/재개/해지) 실제 서비스 로직 연결
- [x] 테스트 데이터 시드 스크립트 작성 (allocations, subscriptions 예시)
- [x] 프런트 연동 가이드 문서화 (필드 매핑, 에러 코드)
- [ ] QA 체크: 단일/복수/단체/정기 시나리오별 요청/응답 확인

### 샘플 데이터 테스트
- `backend/scripts/seed_sample_donations.sql` 실행으로 기본 사용자·소방서·기부/정기 구독 샘플을 주입하면 `/donations`, `/subscriptions` API 응답을 쉽게 검증할 수 있음.

## 프런트 연동 가이드

### 1. 환경 변수
- `TOSS_SECRET_KEY`, `TOSS_CLIENT_KEY`는 Toss 테스트 키를 `.env`에 설정하면 됩니다.
- 예시: `test_ck_oEjb0gm23PYMm6epMNvoVpGwBJn5`, `test_sk_ORzdMaqN3wOaB4nZdd1b35AkYXQG`
- 값이 설정되어 있으면 API는 자동으로 `TossPaymentsClient`를 사용하고, 없으면 Mock 게이트웨이를 사용합니다.

### 2. Checkout API 호출 흐름
1. **프런트에서 입력 수집** → 아래 매핑에 따라 `POST /donations` 페이로드 구성
2. **백엔드 응답 처리**
   - `payment_url` 존재 → 일시 기부: Toss 결제창으로 리다이렉트
   - `billing_auth_url` 존재 → 정기 기부: Toss 빌링 인증 페이지로 이동
   - `subscription_id` 존재 → 정기 구독 정보 동기화에 사용
3. **결제 성공 웹훅/콜백 처리** (후속 Step): Toss 결제 완료 후 백엔드가 상태를 업데이트하거나, 프런트 성공 페이지에서 `/donations/{id}` 재조회

```json
POST /donations
{
  "mode": "multiple",
  "multiple_type": "split",
  "amount": 45000,
  "fire_station_id": null,
  "allocations": [
    { "fire_station_id": "<uuid>", "amount": 30000, "allocation_type": "primary" },
    { "fire_station_id": "<uuid>", "amount": 15000, "allocation_type": "split" }
  ],
  "donor": {
    "display_name": "홍길동",
    "email": "hong@example.com",
    "phone": "010-0000-0000",
    "is_anonymous": false,
    "needs_receipt": true
  },
  "group": {
    "enabled": true,
    "group_name": "보담후원회",
    "contact_name": "김대표",
    "contact_email": "owner@example.com"
  },
  "regular": {
    "enabled": true,
    "cycle": "monthly",
    "start_date": "2025-05-01"
  },
  "message": "화재 진압 응원합니다",
  "metadata": {
    "cups": 15,
    "source": "donations-page"
  },
  "success_redirect_url": "https://bodam.kr/payment/success",
  "fail_redirect_url": "https://bodam.kr/payment/fail"
}
```

**응답 예시**

```json
{
  "donation_id": "f5af...",
  "order_id": "bodam-36fb...",
  "payment_url": null,
  "billing_auth_url": "https://pay.toss.im/billing/customer_36fb...",
  "subscription_id": "b7c1..."
}
```

### 3. 프런트 필드 ↔ 백엔드 매핑
| 프런트 필드 | 백엔드 필드 | 비고 |
| --- | --- | --- |
| `donationMode` (`single`/`multiple`) | `mode` | `multiple`일 때 allocations 필요 |
| `multipleType` (`split`/`each`/`custom`) | `multiple_type` | 단일일 때 `null` 허용 |
| `selectedFireStation` | `fire_station_id` | `single` 모드 필수 |
| `selectedFireStations` + `stationAmounts` | `allocations[]` | amount=0 제외 권장 |
| `donorName`, `donorEmail`, `donorPhone` | `donor.display_name/email/phone` | 이메일 필수 |
| `isAnonymous` | `donor.is_anonymous` | 익명이라도 이메일은 보관 |
| `needReceipt` | `donor.needs_receipt` | 영수증 발급 여부 |
| `message` | `message` | 500자 제한 |
| `isGroupDonation` | `group.enabled` | 추가 메타는 `group.*`에 매핑 |
| `groupCode`, `groupInfo.name` 등 | `group.group_code/group_name/contact_*` | 구조 확정 전 임시 필드 |
| `isRegularDonation` | `regular.enabled` | 주기/시작일은 `regular.cycle/start_date` |
| `regularCycle` | `regular.cycle` | enum(`monthly`,`quarterly`,`yearly`) |
| `startDate` | `regular.start_date` | ISO `YYYY-MM-DD` |
| `successRedirectUrl` / `failRedirectUrl` | `success_redirect_url` / `fail_redirect_url` | Toss SDK에 전달 |
| 기타 메타데이터 | `metadata` | JSON Object, 프런트 자유 필드 |

### 4. 결제 완료 후 처리
- 일시 기부: Toss 결제 성공 URL에서 `donation_id`를 쿼리 파라미터로 받아 `/donations/{donation_id}` 조회 → 상태/영수증 표시
- 정기 기부: 빌링 인증 완료 후 `subscription_id`로 `/subscriptions/{id}` 조회 → `status`, `next_billing_at` 표시
- 실패/취소: Toss 실패 URL에서 메시지 표시 후 `/donations/{id}` 상태 확인 (optional)

### 5. 기부 데이터 조회 & 구독 제어
- `/donations?donor_email={email}` → `donations[]` 배열 반환 (fire_station, allocations, group, regular, payment 포함)
- `/subscriptions?donor_email={email}` → 정기 기부 목록
- `/subscriptions/{id}/pause|resume|cancel` → 상태 변경 후 목록 재조회 권장

## QA 체크 항목
- [x] 단일 모드, 익명 X, 영수증 O → `mode=single`, allocations 1개, `needs_receipt=true`
- [x] 복수 모드 `split` → allocations 각 소방서 균등 분배 확인
- [x] 복수 모드 `custom` → 합계/분배 금액 검증
- [x] 단체 기부 → `group.enabled=true` 인 경우 group_id/null 처리
- [x] 정기 기부 → `regular.enabled=true`, billing auth URL 수신
- [x] 정기 구독 일시정지/재개/해지 → 상태 값 변경 확인
- [x] 에러 케이스: 이메일 누락, allocations 미제공, cycle 미선택 등 400 응답 확인
