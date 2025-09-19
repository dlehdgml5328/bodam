from typing import get_type_hints

import pytest

pytestmark = pytest.mark.unit


def test_donation_model_defines_payment_and_status_fields() -> None:
    from src.models.donation import Donation  # noqa: PLC0415

    hints = get_type_hints(Donation, include_extras=True)
    expected = {
        "id",
        "user_id",
        "fire_station_id",
        "amount",
        "type",
        "frequency",
        "status",
        "payment_method",
        "toss_payment_key",
        "toss_order_id",
        "message",
        "is_anonymous",
        "receipt_url",
        "created_at",
        "completed_at",
        "refunded_at",
    }
    missing = expected - set(hints)
    assert not missing, f"Donation 모델 필드 누락: {missing}"


def test_donation_model_supports_optional_frequency() -> None:
    from src.models.donation import Donation  # noqa: PLC0415

    hints = get_type_hints(Donation, include_extras=True)
    assert "frequency" in hints, "정기결제 주기를 나타내는 frequency 필드가 필요합니다"
