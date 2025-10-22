"""환불 도메인 서비스."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.integrations.toss_payments import TossPaymentsClient, TossPaymentsError
from src.models.donation import Donation, DonationStatus
from src.models.refund import Refund, RefundStatus

logger = logging.getLogger(__name__)


@dataclass
class RefundFailure:
    """환불 처리 실패 정보"""

    refund_id: uuid.UUID
    reason: str


@dataclass
class BulkRefundResult:
    """대량 환불 처리 결과"""

    approved: int
    rejected: int
    failed: list[RefundFailure]


class RefundService:
    """환불 서비스 - 단일 및 대량 환불 승인/거부 처리"""

    def __init__(self, session: AsyncSession, payments_client: TossPaymentsClient) -> None:
        self._session = session
        self._payments = payments_client

    async def request_refund(
        self, donation: Donation, *, reason: str, amount: Decimal | None = None
    ) -> Refund:
        """환불 요청 생성 (사용자용)"""
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

    async def approve_refund(
        self, refund_id: uuid.UUID, admin_id: uuid.UUID, admin_note: str | None = None
    ) -> Refund:
        """단일 환불 승인"""
        refund = await self._session.get(Refund, refund_id)
        if refund is None:
            raise ValueError("Refund not found")

        if refund.status != RefundStatus.PENDING:
            raise ValueError(f"Refund is already {refund.status.value}")

        # Donation 조회
        donation = await self._session.get(Donation, refund.donation_id)
        if donation is None:
            raise ValueError("Associated donation not found")

        # Toss Payments API 호출하여 실제 환불 처리
        if donation.toss_payment_key:
            try:
                await self._payments.request_refund(
                    payment_key=donation.toss_payment_key,
                    amount=refund.amount,
                    reason=admin_note or refund.reason,
                )
            except TossPaymentsError as e:
                logger.error(
                    "Toss Payments refund failed for refund_id=%s: %s", refund_id, str(e)
                )
                raise ValueError(f"Toss Payments API error: {e}") from e

        # Donation 상태 업데이트
        donation.status = DonationStatus.REFUNDED
        donation.refunded_at = datetime.now(timezone.utc)

        # Refund 상태 업데이트
        refund.status = RefundStatus.APPROVED
        refund.reviewer_id = admin_id
        refund.reviewed_at = datetime.now(timezone.utc)

        await self._session.flush()
        return refund

    async def reject_refund(
        self, refund_id: uuid.UUID, admin_id: uuid.UUID, rejection_reason: str
    ) -> Refund:
        """단일 환불 거부"""
        refund = await self._session.get(Refund, refund_id)
        if refund is None:
            raise ValueError("Refund not found")

        if refund.status != RefundStatus.PENDING:
            raise ValueError(f"Refund is already {refund.status.value}")

        refund.status = RefundStatus.REJECTED
        refund.reviewer_id = admin_id
        refund.reviewed_at = datetime.now(timezone.utc)
        # 거부 사유는 별도 필드가 없으므로 로그에만 기록 (향후 Refund 모델 확장 시 추가)
        logger.info(
            "Refund rejected: refund_id=%s, admin_id=%s, reason=%s",
            refund_id,
            admin_id,
            rejection_reason,
        )

        await self._session.flush()
        return refund

    async def bulk_approve(
        self,
        refund_ids: list[uuid.UUID],
        admin_id: uuid.UUID,
        admin_note: str,
    ) -> BulkRefundResult:
        """
        대량 환불 승인 (최대 100개)
        부분 성공 지원: 일부 실패해도 성공한 건은 처리됨
        """
        if len(refund_ids) > 100:
            raise ValueError("Maximum 100 refunds can be processed at once")

        # 환불 요청 조회
        stmt = select(Refund).where(Refund.id.in_(refund_ids))
        result = await self._session.execute(stmt)
        refunds = result.scalars().all()

        # Donation ID 수집 및 조회
        donation_ids = [r.donation_id for r in refunds]
        donation_stmt = select(Donation).where(Donation.id.in_(donation_ids))
        donation_result = await self._session.execute(donation_stmt)
        donations = {d.id: d for d in donation_result.scalars().all()}

        approved_count = 0
        failed: list[RefundFailure] = []

        # 각 환불 요청 처리
        for refund in refunds:
            try:
                # 상태 검증
                if refund.status != RefundStatus.PENDING:
                    failed.append(
                        RefundFailure(
                            refund_id=refund.id,
                            reason=f"Refund is already {refund.status.value}",
                        )
                    )
                    continue

                donation = donations.get(refund.donation_id)
                if donation is None:
                    failed.append(
                        RefundFailure(refund_id=refund.id, reason="Associated donation not found")
                    )
                    continue

                # Toss Payments API 호출
                if donation.toss_payment_key:
                    try:
                        await self._payments.request_refund(
                            payment_key=donation.toss_payment_key,
                            amount=refund.amount,
                            reason=admin_note or refund.reason,
                        )
                    except TossPaymentsError as e:
                        logger.error(
                            "Toss Payments refund failed for refund_id=%s: %s",
                            refund.id,
                            str(e),
                        )
                        failed.append(
                            RefundFailure(refund_id=refund.id, reason=f"Toss API error: {e}")
                        )
                        continue

                # 성공 시 상태 업데이트
                donation.status = DonationStatus.REFUNDED
                donation.refunded_at = datetime.now(timezone.utc)
                refund.status = RefundStatus.APPROVED
                refund.reviewer_id = admin_id
                refund.reviewed_at = datetime.now(timezone.utc)

                approved_count += 1

            except Exception as e:
                logger.exception("Unexpected error processing refund_id=%s", refund.id)
                failed.append(RefundFailure(refund_id=refund.id, reason=str(e)))

        # 트랜잭션 커밋은 호출자가 담당
        await self._session.flush()

        # TODO: 감사 로그 기록
        logger.info(
            "Bulk approve completed: admin_id=%s, approved=%d, failed=%d",
            admin_id,
            approved_count,
            len(failed),
        )

        # TODO: 사용자 알림 발송 (Celery)
        # from src.workers.notification_sender import dispatch_notifications
        # dispatch_notifications.delay(...)

        return BulkRefundResult(approved=approved_count, rejected=0, failed=failed)

    async def bulk_reject(
        self,
        refund_ids: list[uuid.UUID],
        admin_id: uuid.UUID,
        rejection_reason: str,
    ) -> BulkRefundResult:
        """
        대량 환불 거부 (최대 100개)
        Toss Payments API 호출 없음 (거부는 내부 상태만 변경)
        """
        if len(refund_ids) > 100:
            raise ValueError("Maximum 100 refunds can be processed at once")

        # 환불 요청 조회
        stmt = select(Refund).where(Refund.id.in_(refund_ids))
        result = await self._session.execute(stmt)
        refunds = result.scalars().all()

        rejected_count = 0
        failed: list[RefundFailure] = []

        for refund in refunds:
            try:
                if refund.status != RefundStatus.PENDING:
                    failed.append(
                        RefundFailure(
                            refund_id=refund.id,
                            reason=f"Refund is already {refund.status.value}",
                        )
                    )
                    continue

                refund.status = RefundStatus.REJECTED
                refund.reviewer_id = admin_id
                refund.reviewed_at = datetime.now(timezone.utc)

                rejected_count += 1

            except Exception as e:
                logger.exception("Unexpected error rejecting refund_id=%s", refund.id)
                failed.append(RefundFailure(refund_id=refund.id, reason=str(e)))

        await self._session.flush()

        # TODO: 감사 로그 기록
        logger.info(
            "Bulk reject completed: admin_id=%s, rejected=%d, failed=%d, reason=%s",
            admin_id,
            rejected_count,
            len(failed),
            rejection_reason,
        )

        # TODO: 사용자 알림 발송 (Celery)

        return BulkRefundResult(approved=0, rejected=rejected_count, failed=failed)


__all__ = ["RefundService", "BulkRefundResult", "RefundFailure"]
