"""그룹 기부 캠페인 관리 Admin View"""

from sqladmin import ModelView

from src.models.group import Group


class GroupAdmin(ModelView, model=Group):
    """그룹 기부 캠페인 관리 Admin View"""

    # 기본 설정
    name = "그룹 캠페인"
    name_plural = "그룹 캠페인 목록"
    icon = "fa-solid fa-users"

    # 목록 페이지 설정
    column_list = [
        Group.id,
        Group.name,
        Group.description,
        Group.creator_id,  # creator (User relationship)
        Group.current_amount,
        Group.member_count,
        Group.created_at,
    ]

    # 정렬 가능 필드
    column_sortable_list = [
        Group.current_amount,
        Group.created_at,
        Group.member_count,
    ]

    # 검색 가능 필드
    column_searchable_list = [Group.name, Group.description]

    # 필터 설정 (없음)
    column_filters = [Group.status, Group.is_public]

    # 기본 정렬 (current_amount DESC - total_donated 대신)
    column_default_sort = [(Group.current_amount, True)]

    # 상세 페이지 설정 (모든 필드 표시)
    column_details_list = [
        Group.id,
        Group.name,
        Group.description,
        Group.target_amount,
        Group.current_amount,
        Group.fire_station_id,
        Group.creator_id,
        Group.is_public,
        Group.invite_code,
        Group.deadline,
        Group.status,
        Group.member_count,
        Group.created_at,
        Group.completed_at,
    ]

    # 폼 설정 (생성/수정 가능 필드)
    form_columns = [
        Group.name,
        Group.description,
        Group.target_amount,
        Group.fire_station_id,
        Group.creator_id,
        Group.is_public,
        Group.deadline,
        Group.status,
    ]

    # 권한 설정
    can_create = True
    can_edit = True
    can_delete = False  # 삭제 비활성화

    # 페이지네이션
    page_size = 50

    # 컬럼 라벨 한글화
    column_labels = {
        Group.id: "ID",
        Group.name: "캠페인명",
        Group.description: "설명",
        Group.target_amount: "목표 금액",
        Group.current_amount: "현재 금액",
        Group.fire_station_id: "소방서 ID",
        Group.creator_id: "생성자 ID",
        Group.is_public: "공개 여부",
        Group.invite_code: "초대 코드",
        Group.deadline: "마감일",
        Group.status: "상태",
        Group.member_count: "멤버 수",
        Group.created_at: "생성일",
        Group.completed_at: "완료일",
    }
