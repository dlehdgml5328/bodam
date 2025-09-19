from typing import get_type_hints

import pytest

pytestmark = pytest.mark.unit


def test_receipt_model_includes_issue_metadata() -> None:
    from src.models.receipt import Receipt  # noqa: PLC0415

    hints = get_type_hints(Receipt, include_extras=True)
    expected = {
        "id",
        "donation_id",
        "receipt_number",
        "recipient_name",
        "recipient_phone",
        "amount",
        "issue_date",
        "pdf_url",
        "email_sent",
        "created_at",
    }
    missing = expected - set(hints)
    assert not missing, f"Receipt 모델 필드 누락: {missing}"


def test_receipt_model_has_pdf_reference() -> None:
    from src.models.receipt import Receipt  # noqa: PLC0415

    hints = get_type_hints(Receipt, include_extras=True)
    assert "pdf_url" in hints
