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
- [ ] `DonationService` 다중/정기 기부 로직 구현
- [ ] Toss 결제/빌링 연동 (Sandbox 키 확인 포함)
- [ ] 정기 구독 API(일시정지/재개/해지) 실제 서비스 로직 연결
- [ ] 테스트 데이터 시드 스크립트 작성 (allocations, subscriptions 예시)
- [ ] 프런트 연동 가이드 문서화 (필드 매핑, 에러 코드)
- [ ] QA 체크: 단일/복수/단체/정기 시나리오별 요청/응답 확인
