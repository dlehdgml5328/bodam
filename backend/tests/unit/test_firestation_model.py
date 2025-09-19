from typing import get_type_hints

import pytest

pytestmark = pytest.mark.unit


def test_fire_station_model_defines_location_and_metadata() -> None:
    from src.models.fire_station import FireStation  # noqa: PLC0415

    hints = get_type_hints(FireStation, include_extras=True)
    expected = {
        "id",
        "name",
        "address",
        "location",
        "phone",
        "station_code",
        "region",
        "district",
        "status",
        "total_received",
        "donor_count",
        "last_incident_at",
        "created_at",
        "updated_at",
    }
    missing = expected - set(hints)
    assert not missing, f"FireStation 모델에서 필수 필드 누락: {missing}"


def test_fire_station_model_has_spatial_point_type() -> None:
    from src.models.fire_station import FireStation  # noqa: PLC0415

    hints = get_type_hints(FireStation, include_extras=True)
    assert "location" in hints, "location 필드가 정의되어야 합니다"
