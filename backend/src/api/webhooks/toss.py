"""Toss Payments webhook endpoint."""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_session
from src.integrations.toss_payments import TossPaymentsClient
from src.models.donation import DonationStatus
from src.services.donation_service import DonationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/toss", tags=["webhooks"])


@router.post("/payment")
async def handle_toss_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session),
    x_toss_signature: str | None = Header(default=None, alias="X-Toss-Signature"),
) -> dict:
    """
    Toss Payments Webhook 이벤트 처리

    Toss에서 결제 상태 변경 시 호출됩니다:
    - PAYMENT_CONFIRMED: 결제 승인 완료
    - PAYMENT_CANCELED: 결제 취소
    - PAYMENT_FAILED: 결제 실패
    """
    # 1. Webhook signature 검증
    body = await request.body()
    if not _verify_webhook_signature(body, x_toss_signature):
        logger.warning("Invalid webhook signature")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature",
        )

    payload = await request.json()
    event_type = payload.get("eventType", "unknown")
    data = payload.get("data", {})

    logger.info(
        "Toss webhook received: event=%s, order_id=%s",
        event_type,
        data.get("orderId"),
    )

    # 2. 이벤트 타입별 처리
    try:
        if event_type == "PAYMENT_CONFIRMED":
            await _handle_payment_confirmed(session, data)
        elif event_type == "PAYMENT_CANCELED":
            await _handle_payment_canceled(session, data)
        elif event_type == "PAYMENT_FAILED":
            await _handle_payment_failed(session, data)
        else:
            logger.warning("Unknown webhook event type: %s", event_type)

        return {"received": True, "event_type": event_type}

    except Exception as exc:
        logger.exception("Error processing webhook event: %s", event_type)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed",
        ) from exc


async def _handle_payment_confirmed(session: AsyncSession, data: dict) -> None:
    """결제 승인 완료 이벤트 처리"""
    order_id = data.get("orderId")
    payment_key = data.get("paymentKey")
    method = data.get("method", "card")
    approved_at_str = data.get("approvedAt")

    if not order_id or not payment_key:
        logger.error("Missing order_id or payment_key in webhook data")
        return

    # Parse approved_at
    approved_at = datetime.now(timezone.utc)
    if approved_at_str:
        try:
            approved_at = datetime.fromisoformat(
                approved_at_str.replace("Z", "+00:00")
            )
        except ValueError:
            logger.warning("Failed to parse approvedAt: %s", approved_at_str)

    toss_client = TossPaymentsClient()
    service = DonationService(session, toss_client)

    try:
        donation = await service.get_donation_by_order_id(order_id)

        # 이미 완료된 경우 스킵
        if donation.status == DonationStatus.COMPLETED:
            logger.info("Donation already completed: %s", donation.id)
            return

        # 기부 완료 처리
        await service.complete_donation(
            donation_id=donation.id,
            payment_key=payment_key,
            payment_method=method,
            approved_at=approved_at,
        )
        await session.commit()

        logger.info(
            "Payment confirmed via webhook: donation_id=%s, order_id=%s",
            donation.id,
            order_id,
        )

    except Exception as exc:
        logger.exception("Failed to process payment confirmation webhook")
        await session.rollback()
        raise exc
    finally:
        await toss_client.close()


async def _handle_payment_canceled(session: AsyncSession, data: dict) -> None:
    """결제 취소 이벤트 처리"""
    order_id = data.get("orderId")
    if not order_id:
        logger.error("Missing order_id in cancel webhook")
        return

    toss_client = TossPaymentsClient()
    service = DonationService(session, toss_client)

    try:
        donation = await service.get_donation_by_order_id(order_id)
        donation.status = DonationStatus.REFUNDED
        donation.refunded_at = datetime.now(timezone.utc)
        await session.commit()

        logger.info(
            "Payment canceled via webhook: donation_id=%s, order_id=%s",
            donation.id,
            order_id,
        )

    except Exception as exc:
        logger.exception("Failed to process payment cancel webhook")
        await session.rollback()
        raise exc
    finally:
        await toss_client.close()


async def _handle_payment_failed(session: AsyncSession, data: dict) -> None:
    """결제 실패 이벤트 처리"""
    order_id = data.get("orderId")
    if not order_id:
        logger.error("Missing order_id in fail webhook")
        return

    toss_client = TossPaymentsClient()
    service = DonationService(session, toss_client)

    try:
        donation = await service.get_donation_by_order_id(order_id)
        donation.status = DonationStatus.FAILED
        await session.commit()

        logger.info(
            "Payment failed via webhook: donation_id=%s, order_id=%s",
            donation.id,
            order_id,
        )

    except Exception as exc:
        logger.exception("Failed to process payment fail webhook")
        await session.rollback()
        raise exc
    finally:
        await toss_client.close()


def _verify_webhook_signature(body: bytes, signature: str | None) -> bool:
    """
    Webhook 서명 검증

    Toss는 X-Toss-Signature 헤더로 HMAC-SHA256 서명을 전송합니다.
    """
    if signature is None:
        # 개발 환경에서는 서명 검증 스킵 가능
        if os.getenv("DEBUG", "false").lower() == "true":
            logger.warning("Webhook signature verification skipped (DEBUG mode)")
            return True
        return False

    webhook_secret = os.getenv("TOSS_WEBHOOK_SECRET", "")
    if not webhook_secret:
        logger.warning("TOSS_WEBHOOK_SECRET not configured")
        return os.getenv("DEBUG", "false").lower() == "true"

    # HMAC-SHA256 서명 생성
    expected_signature = hmac.new(
        webhook_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    # 타이밍 공격 방지를 위한 constant-time 비교
    return hmac.compare_digest(signature, expected_signature)


__all__ = ["router"]
