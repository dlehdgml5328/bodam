from typing import get_type_hints

import pytest

pytestmark = pytest.mark.unit


def test_group_model_defines_campaign_fields() -> None:
    from src.models.group import Group  # noqa: PLC0415

    hints = get_type_hints(Group, include_extras=True)
    expected = {
        "id",
        "name",
        "description",
        "target_amount",
        "current_amount",
        "fire_station_id",
        "creator_id",
        "is_public",
        "invite_code",
        "deadline",
        "status",
        "member_count",
        "created_at",
        "completed_at",
    }
    missing = expected - set(hints)
    assert not missing, f"Group 모델에서 누락된 필드: {missing}"


def test_group_model_supports_deadline_optional() -> None:
    from src.models.group import Group  # noqa: PLC0415

    hints = get_type_hints(Group, include_extras=True)
    assert "deadline" in hints, "마감일을 표현하는 deadline 필드가 필요합니다"
