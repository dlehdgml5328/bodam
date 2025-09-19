from typing import get_type_hints

import pytest

pytestmark = pytest.mark.unit


def test_notification_model_defines_delivery_fields() -> None:
    from src.models.notification import Notification  # noqa: PLC0415

    hints = get_type_hints(Notification, include_extras=True)
    expected = {
        "id",
        "user_id",
        "type",
        "title",
        "message",
        "related_id",
        "channels",
        "status",
        "is_read",
        "sent_at",
        "read_at",
        "created_at",
    }
    missing = expected - set(hints)
    assert not missing, f"Notification 모델 필수 필드 누락: {missing}"


def test_notification_model_tracks_channels() -> None:
    from src.models.notification import Notification  # noqa: PLC0415

    hints = get_type_hints(Notification, include_extras=True)
    assert "channels" in hints, "Notification 모델은 channels 리스트를 포함해야 합니다"
