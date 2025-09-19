from typing import get_type_hints

import pytest

pytestmark = pytest.mark.unit


def test_user_model_includes_core_fields() -> None:
    """User 모델이 명세서의 필수 컬럼을 정의하는지 확인."""
    from src.models.user import User  # noqa: PLC0415

    hints = get_type_hints(User, include_extras=True)
    expected = {
        "id",
        "email",
        "password_hash",
        "name",
        "phone",
        "role",
        "social_provider",
        "social_id",
        "tier",
        "total_donated",
        "created_at",
        "updated_at",
        "is_active",
    }
    missing = expected - set(hints)
    assert not missing, f"다음 필드를 User 모델에서 찾을 수 없음: {missing}"


def test_user_model_supports_boolean_and_numeric_fields() -> None:
    from src.models.user import User  # noqa: PLC0415

    hints = get_type_hints(User, include_extras=True)
    assert "is_active" in hints
    assert "tier" in hints
    assert "total_donated" in hints
