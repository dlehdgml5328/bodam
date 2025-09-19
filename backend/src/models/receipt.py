"""Receipt model for tax documentation."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    donation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("donations.id", ondelete="CASCADE"), nullable=False
    )
    receipt_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    recipient_name: Mapped[str] = mapped_column(String(120), nullable=False)
    recipient_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    pdf_url: Mapped[str] = mapped_column(String(255), nullable=False)
    email_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    donation = relationship("Donation", backref="receipt", uselist=False)

    def __repr__(self) -> str:
        return f"Receipt(id={self.id}, receipt_number={self.receipt_number!r})"
