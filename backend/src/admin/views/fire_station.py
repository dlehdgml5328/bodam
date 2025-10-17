"""소방서 관리 Admin View"""

from sqladmin import ModelView

from src.models.fire_station import FireStation


class FireStationAdmin(ModelView, model=FireStation):
    """소방서 관리 Admin View"""

    # 기본 설정
    name = "소방서"
    name_plural = "소방서 목록"
    icon = "fa-solid fa-fire-extinguisher"

    # 목록 페이지 설정
    column_list = [
        FireStation.id,
        FireStation.name,
        FireStation.region,
        FireStation.address,
        FireStation.total_received,
        FireStation.status,
        FireStation.created_at,
    ]

    # 정렬 가능 필드
    column_sortable_list = [
        FireStation.total_received,
        FireStation.created_at,
        FireStation.donor_count,
    ]

    # 검색 가능 필드
    column_searchable_list = [FireStation.name, FireStation.address]

    # 필터 설정
    column_filters = [FireStation.region, FireStation.status]

    # 기본 정렬 (total_received DESC)
    column_default_sort = [(FireStation.total_received, True)]

    # 상세 페이지 설정 (모든 필드 표시)
    column_details_list = [
        FireStation.id,
        FireStation.name,
        FireStation.address,
        FireStation.location,
        FireStation.phone,
        FireStation.station_code,
        FireStation.region,
        FireStation.district,
        FireStation.status,
        FireStation.total_received,
        FireStation.donor_count,
        FireStation.last_incident_at,
        FireStation.created_at,
        FireStation.updated_at,
    ]

    # 폼 설정 (생성/수정 가능 필드)
    form_columns = [
        FireStation.name,
        FireStation.address,
        FireStation.location,
        FireStation.phone,
        FireStation.station_code,
        FireStation.region,
        FireStation.district,
        FireStation.status,
    ]

    # 권한 설정
    can_create = True
    can_edit = True
    can_delete = False  # 삭제 비활성화

    # 페이지네이션
    page_size = 50

    # 컬럼 라벨 한글화
    column_labels = {
        FireStation.id: "ID",
        FireStation.name: "소방서명",
        FireStation.address: "주소",
        FireStation.location: "위치 (좌표)",
        FireStation.phone: "전화번호",
        FireStation.station_code: "소방서 코드",
        FireStation.region: "지역",
        FireStation.district: "구역",
        FireStation.status: "상태",
        FireStation.total_received: "총 수령액",
        FireStation.donor_count: "기부자 수",
        FireStation.last_incident_at: "마지막 사고 일시",
        FireStation.created_at: "생성일",
        FireStation.updated_at: "수정일",
    }
