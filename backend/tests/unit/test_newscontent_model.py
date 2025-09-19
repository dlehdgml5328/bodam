from typing import get_type_hints

import pytest

pytestmark = pytest.mark.unit


def test_news_content_model_includes_vector_and_metadata() -> None:
    from src.models.news_content import NewsContent  # noqa: PLC0415

    hints = get_type_hints(NewsContent, include_extras=True)
    expected = {
        "id",
        "title",
        "content",
        "source",
        "source_url",
        "published_at",
        "location",
        "embedding",
        "relevance_score",
        "summary",
        "keywords",
        "status",
        "reviewed_by",
        "reviewed_at",
        "created_at",
    }
    missing = expected - set(hints)
    assert not missing, f"NewsContent 모델 필드 누락: {missing}"


def test_news_content_model_embedding_is_list_like() -> None:
    from src.models.news_content import NewsContent  # noqa: PLC0415

    hints = get_type_hints(NewsContent, include_extras=True)
    assert "embedding" in hints, "임베딩 벡터를 위한 embedding 필드가 필요합니다"
