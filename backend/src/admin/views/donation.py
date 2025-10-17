"""기부 관리 Admin View"""

from sqladmin import ModelView

from src.models.donation import Donation


class DonationAdmin(ModelView, model=Donation):
    """기부 관리 Admin View"""

    # 기본 설정
    name = "기부"
    name_plural = "기부 목록"
    icon = "fa-solid fa-hand-holding-heart"

    # 목록 페이지 설정
    column_list = [
        Donation.id,
        "user.name",  # relationship 필드
        "fire_station.name",  # relationship 필드
        Donation.amount,
        Donation.payment_method,
        Donation.status,
        Donation.created_at,
    ]

    # 정렬 가능 필드
    column_sortable_list = [Donation.created_at, Donation.amount, Donation.status]

    # 검색 가능 필드 (relationship 필드 검색)
    column_searchable_list = ["user.name", "user.email"]

    # 필터 설정
    column_filters = [Donation.status, Donation.payment_method, "fire_station.name"]

    # 기본 정렬 (created_at DESC)
    column_default_sort = [(Donation.created_at, True)]

    # 상세 페이지 설정 (모든 필드 표시)
    column_details_list = [
        Donation.id,
        Donation.user_id,
        Donation.fire_station_id,
        Donation.group_id,
        Donation.mode,
        Donation.amount,
        Donation.currency,
        Donation.type,
        Donation.frequency,
        Donation.status,
        Donation.payment_method,
        Donation.toss_payment_key,
        Donation.toss_order_id,
        Donation.billing_customer_key,
        Donation.billing_key,
        Donation.subscription_id,
        Donation.message,
        Donation.donor_display_name,
        Donation.is_anonymous,
        Donation.needs_receipt,
        Donation.is_group_anonymous,
        Donation.metadata_json,
        Donation.receipt_url,
        Donation.created_at,
        Donation.completed_at,
        Donation.refunded_at,
    ]

    # 폼 설정 (생성/수정 가능 필드)
    form_columns = [
        Donation.user_id,
        Donation.fire_station_id,
        Donation.group_id,
        Donation.mode,
        Donation.amount,
        Donation.currency,
        Donation.type,
        Donation.status,
        Donation.payment_method,
        Donation.message,
        Donation.donor_display_name,
        Donation.is_anonymous,
        Donation.needs_receipt,
    ]

    # 권한 설정
    can_create = True
    can_edit = True
    can_delete = False  # 삭제 비활성화

    # 페이지네이션
    page_size = 50

    # 컬럼 라벨 한글화
    column_labels = {
        Donation.id: "ID",
        Donation.user_id: "사용자 ID",
        "user.name": "기부자",
        "user.email": "기부자 이메일",
        Donation.fire_station_id: "소방서 ID",
        "fire_station.name": "소방서",
        Donation.group_id: "그룹 ID",
        Donation.mode: "모드",
        Donation.amount: "금액",
        Donation.currency: "통화",
        Donation.type: "유형",
        Donation.frequency: "빈도",
        Donation.status: "상태",
        Donation.payment_method: "결제 수단",
        Donation.toss_payment_key: "토스 결제 키",
        Donation.toss_order_id: "토스 주문 ID",
        Donation.billing_customer_key: "빌링 고객 키",
        Donation.billing_key: "빌링 키",
        Donation.subscription_id: "구독 ID",
        Donation.message: "메시지",
        Donation.donor_display_name: "기부자 표시명",
        Donation.is_anonymous: "익명 여부",
        Donation.needs_receipt: "영수증 필요",
        Donation.is_group_anonymous: "그룹 익명 여부",
        Donation.metadata_json: "메타데이터",
        Donation.receipt_url: "영수증 URL",
        Donation.created_at: "생성일",
        Donation.completed_at: "완료일",
        Donation.refunded_at: "환불일",
    }
