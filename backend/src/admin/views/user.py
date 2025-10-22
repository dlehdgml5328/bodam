"""사용자 관리 Admin View"""

from sqladmin import ModelView

from src.models.user import User


class UserAdmin(ModelView, model=User):
    """사용자 관리 Admin View"""

    # 기본 설정
    name = "사용자"
    name_plural = "사용자 목록"
    icon = "fa-solid fa-user"

    # 목록 페이지 설정
    column_list = [
        User.id,
        User.email,
        User.name,
        User.phone,
        User.role,
        User.is_active,
        User.tier,
        User.total_donated,
        User.created_at,
    ]

    # 정렬 가능 필드
    column_sortable_list = [User.created_at, User.total_donated, User.tier]

    # 검색 가능 필드
    column_searchable_list = [User.email, User.name, User.phone]

    # 필터 설정
    column_filters = [User.role, User.is_active, User.tier]

    # 기본 정렬 (created_at DESC)
    column_default_sort = [(User.created_at, True)]

    # 상세 페이지 설정 (모든 필드 표시)
    column_details_list = [
        User.id,
        User.email,
        User.name,
        User.phone,
        User.role,
        User.social_provider,
        User.social_id,
        User.tier,
        User.total_donated,
        User.is_active,
        User.created_at,
        User.updated_at,
    ]

    # 폼 설정 (생성/수정 가능 필드)
    form_columns = [
        User.email,
        User.name,
        User.phone,
        User.role,
        User.tier,
        User.is_active,
    ]

    # 권한 설정
    can_create = True
    can_edit = True
    can_delete = False  # 삭제 비활성화

    # 페이지네이션
    page_size = 50

    # 컬럼 라벨 한글화
    column_labels = {
        User.id: "ID",
        User.email: "이메일",
        User.name: "이름",
        User.phone: "전화번호",
        User.role: "역할",
        User.social_provider: "소셜 제공자",
        User.social_id: "소셜 ID",
        User.tier: "등급",
        User.total_donated: "총 기부액",
        User.is_active: "활성 상태",
        User.created_at: "생성일",
        User.updated_at: "수정일",
    }
