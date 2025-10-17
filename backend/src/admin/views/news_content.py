"""뉴스 콘텐츠 관리 Admin View"""

from sqladmin import ModelView

from src.models.news_content import NewsContent


class NewsContentAdmin(ModelView, model=NewsContent):
    """뉴스 콘텐츠 관리 Admin View"""

    # 기본 설정
    name = "뉴스 콘텐츠"
    name_plural = "뉴스 콘텐츠 목록"
    icon = "fa-solid fa-newspaper"

    # 목록 페이지 설정
    column_list = [
        NewsContent.id,
        NewsContent.title,
        NewsContent.source,
        NewsContent.relevance_score,
        NewsContent.status,
        NewsContent.published_at,
        NewsContent.created_at,
    ]

    # 정렬 가능 필드
    column_sortable_list = [
        NewsContent.relevance_score,
        NewsContent.published_at,
        NewsContent.created_at,
    ]

    # 검색 가능 필드
    column_searchable_list = [NewsContent.title, NewsContent.content]

    # 필터 설정
    column_filters = [NewsContent.source, NewsContent.status]

    # 기본 정렬 (relevance_score DESC, published_at DESC)
    column_default_sort = [
        (NewsContent.relevance_score, True),
        (NewsContent.published_at, True),
    ]

    # 상세 페이지 설정 (모든 필드 표시)
    column_details_list = [
        NewsContent.id,
        NewsContent.analysis_job_id,
        NewsContent.title,
        NewsContent.content,
        NewsContent.source,
        NewsContent.source_url,
        NewsContent.published_at,
        NewsContent.location,
        NewsContent.relevance_score,
        NewsContent.summary,
        NewsContent.keywords,
        NewsContent.status,
        NewsContent.reviewed_by,
        NewsContent.reviewed_at,
        NewsContent.created_at,
    ]

    # 폼 설정 (생성/수정 가능 필드)
    form_columns = [
        NewsContent.title,
        NewsContent.content,
        NewsContent.source,
        NewsContent.source_url,
        NewsContent.published_at,
        NewsContent.location,
        NewsContent.relevance_score,
        NewsContent.summary,
        NewsContent.keywords,
        NewsContent.status,
        NewsContent.reviewed_by,
    ]

    # 권한 설정
    can_create = True
    can_edit = True
    can_delete = False  # 삭제 비활성화

    # 페이지네이션
    page_size = 50

    # 컬럼 라벨 한글화
    column_labels = {
        NewsContent.id: "ID",
        NewsContent.analysis_job_id: "분석 작업 ID",
        NewsContent.title: "제목",
        NewsContent.content: "내용",
        NewsContent.source: "출처",
        NewsContent.source_url: "출처 URL",
        NewsContent.published_at: "발행일",
        NewsContent.location: "위치",
        NewsContent.embedding: "임베딩",
        NewsContent.relevance_score: "관련성 점수",
        NewsContent.summary: "요약",
        NewsContent.keywords: "키워드",
        NewsContent.status: "상태",
        NewsContent.reviewed_by: "검토자",
        NewsContent.reviewed_at: "검토일",
        NewsContent.created_at: "생성일",
    }
