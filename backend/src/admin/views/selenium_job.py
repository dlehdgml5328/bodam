"""Selenium 크롤 작업 관리 Admin View (읽기 전용)"""

from sqladmin import ModelView

from src.models.selenium_crawl_job import SeleniumCrawlJob


class SeleniumCrawlJobAdmin(ModelView, model=SeleniumCrawlJob):
    """Selenium 크롤 작업 관리 Admin View (읽기 전용)

    크롤링 작업은 시스템에서 자동으로 생성되므로,
    관리자 페이지에서는 조회만 가능합니다.
    """

    # 기본 설정
    name = "Selenium 크롤 작업"
    name_plural = "Selenium 크롤 작업 목록"
    icon = "fa-solid fa-spider"

    # 목록 페이지 설정
    column_list = [
        SeleniumCrawlJob.id,
        SeleniumCrawlJob.url,
        SeleniumCrawlJob.browser_type,
        SeleniumCrawlJob.status,
        SeleniumCrawlJob.retry_count,
        SeleniumCrawlJob.created_at,
        SeleniumCrawlJob.started_at,
        SeleniumCrawlJob.completed_at,
    ]

    # 정렬 가능 필드
    column_sortable_list = [
        SeleniumCrawlJob.created_at,
        SeleniumCrawlJob.started_at,
        SeleniumCrawlJob.completed_at,
        SeleniumCrawlJob.status,
    ]

    # 검색 가능 필드
    column_searchable_list = [SeleniumCrawlJob.url]

    # 필터 설정
    column_filters = [SeleniumCrawlJob.status, SeleniumCrawlJob.browser_type]

    # 기본 정렬 (created_at DESC)
    column_default_sort = [(SeleniumCrawlJob.created_at, True)]

    # 상세 페이지 설정 (모든 필드 표시)
    column_details_list = [
        SeleniumCrawlJob.id,
        SeleniumCrawlJob.url,
        SeleniumCrawlJob.browser_type,
        SeleniumCrawlJob.wait_conditions,
        SeleniumCrawlJob.retry_count,
        SeleniumCrawlJob.max_retries,
        SeleniumCrawlJob.status,
        SeleniumCrawlJob.created_at,
        SeleniumCrawlJob.started_at,
        SeleniumCrawlJob.completed_at,
        SeleniumCrawlJob.error_message,
        SeleniumCrawlJob.job_metadata,
    ]

    # 폼 설정 (읽기 전용이므로 비어있음)
    form_columns = []

    # 권한 설정 (읽기 전용)
    can_create = False  # 생성 불가
    can_edit = False  # 수정 불가
    can_delete = False  # 삭제 불가
    can_view_details = True  # 상세 보기만 가능

    # 페이지네이션
    page_size = 50

    # 컬럼 라벨 한글화
    column_labels = {
        SeleniumCrawlJob.id: "ID",
        SeleniumCrawlJob.url: "크롤링 URL",
        SeleniumCrawlJob.browser_type: "브라우저 타입",
        SeleniumCrawlJob.wait_conditions: "대기 조건",
        SeleniumCrawlJob.retry_count: "재시도 횟수",
        SeleniumCrawlJob.max_retries: "최대 재시도",
        SeleniumCrawlJob.status: "상태",
        SeleniumCrawlJob.created_at: "생성일",
        SeleniumCrawlJob.started_at: "시작일",
        SeleniumCrawlJob.completed_at: "완료일",
        SeleniumCrawlJob.error_message: "오류 메시지",
        SeleniumCrawlJob.job_metadata: "작업 메타데이터",
    }
