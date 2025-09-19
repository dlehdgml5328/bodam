from typing import get_type_hints

import pytest

pytestmark = pytest.mark.unit


def test_ranking_model_tracks_period_and_rank() -> None:
    from src.models.ranking import Ranking  # noqa: PLC0415

    hints = get_type_hints(Ranking, include_extras=True)
    expected = {
        "id",
        "fire_station_id",
        "user_id",
        "total_amount",
        "donation_count",
        "rank",
        "period",
        "calculated_at",
    }
    missing = expected - set(hints)
    assert not missing, f"Ranking 모델 필수 필드 누락: {missing}"


def test_ranking_model_includes_rank_integer() -> None:
    from src.models.ranking import Ranking  # noqa: PLC0415

    hints = get_type_hints(Ranking, include_extras=True)
    assert "rank" in hints
