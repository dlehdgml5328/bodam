"""Receipt generation service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class ReceiptData:
    donor_name: str
    fire_station_name: str
    amount: float
    issue_date: date
    receipt_number: str


class ReceiptService:
    def render_pdf(self, data: ReceiptData) -> bytes:
        """Return a placeholder PDF payload for the receipt."""
        body = (
            f"Receipt {data.receipt_number}\n"
            f"Donor: {data.donor_name}\n"
            f"Fire Station: {data.fire_station_name}\n"
            f"Amount: {data.amount}\n"
            f"Issued: {data.issue_date.isoformat()}\n"
        )
        return ("%PDF-1.4\n" + body + "\n%%EOF").encode()


__all__ = ["ReceiptService", "ReceiptData"]
