"""Refund domain service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.integrations.toss_payments import TossPaymentsClient
from src.models.donation import Donation, DonationStatus
from src.models.refund import Refund, RefundStatus


class RefundService:
    def __init__(self, session: AsyncSession, payments_client: TossPaymentsClient) -> None:
        self._session = session
        self._payments = payments_client

    async def request_refund(
        self, donation: Donation, *, reason: str, amount: Decimal | None = None
    ) -> Refund:
        if donation.status != DonationStatus.COMPLETED:
            raise ValueError("Only completed donations can be refunded")

        refund_amount = amount or donation.amount
        refund = Refund(donation_id=donation.id, reason=reason, amount=refund_amount)
        self._session.add(refund)
        await self._session.flush()

        if donation.toss_payment_key:
            await self._payments.request_refund(
                payment_key=donation.toss_payment_key,
                amount=refund_amount,
                reason=reason,
            )
            refund.status = RefundStatus.APPROVED
            refund.reviewed_at = datetime.now(timezone.utc)
        return refund

    async def approve_refund(self, refund_id: uuid.UUID, reviewer_id: uuid.UUID) -> Refund:
        refund = await self._session.get(Refund, refund_id)
        if refund is None:
            raise ValueError("Refund not found")
        refund.status = RefundStatus.APPROVED
        refund.reviewer_id = reviewer_id
        refund.reviewed_at = datetime.now(timezone.utc)
        await self._session.flush()
        return refund


__all__ = ["RefundService"]
