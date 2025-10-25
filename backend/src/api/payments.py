"""Payment confirmation and callback endpoints."""

from __future__ import annotations

import logging
import os
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_session
from src.integrations.toss_payments import TossPaymentsClient, TossPaymentsError
from src.models.donation import DonationStatus
from src.services.donation_service import DonationService
from src.api.observability import bodam_payment_idempotency_key_hit_total

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])


class PaymentConfirmRequest(BaseModel):
    payment_key: str
    order_id: str
    amount: Decimal


class PaymentConfirmResponse(BaseModel):
    donation_id: uuid.UUID
    status: DonationStatus
    payment_key: str
    approved_at: str


class BillingKeyCallbackRequest(BaseModel):
    customer_key: str
    auth_key: str | None = None


@router.post("/confirm", response_model=PaymentConfirmResponse)
async def confirm_payment(
    payload: PaymentConfirmRequest,
    session: AsyncSession = Depends(get_session),
) -> PaymentConfirmResponse:
    """
    Toss Payments 결제 승인 엔드포인트

    프론트엔드에서 결제 위젯 승인 후 호출됩니다.
    1. Toss API에 결제 승인 요청
    2. DB에 결제 정보 업데이트
    3. 기부 상태를 COMPLETED로 변경
    """
    logger.info(
        "Payment confirmation requested: order_id=%s, payment_key=%s, amount=%s",
        payload.order_id,
        payload.payment_key,
        payload.amount,
    )

    # Toss Payments API 클라이언트
    toss_client = TossPaymentsClient()
    service = DonationService(session, toss_client)

    try:
        # 1. 먼저 DB에서 donation 찾기 (중복 승인 방지)
        donation = await service.get_donation_by_order_id(payload.order_id)

        if donation.status == DonationStatus.COMPLETED:
            logger.warning("Donation already completed: %s", donation.id)
            # 멱등성 키 히트 메트릭 증가
            bodam_payment_idempotency_key_hit_total.inc()
            return PaymentConfirmResponse(
                donation_id=donation.id,
                status=donation.status,
                payment_key=donation.toss_payment_key or payload.payment_key,
                approved_at=donation.updated_at.isoformat() if donation.updated_at else donation.created_at.isoformat(),
            )

        # 2. Toss API로 결제 승인
        confirmation = await toss_client.confirm_payment(
            payment_key=payload.payment_key,
            order_id=payload.order_id,
            amount=payload.amount,
        )

        logger.info(
            "Toss payment confirmed: payment_key=%s, method=%s, approved_at=%s",
            confirmation.payment_key,
            confirmation.method,
            confirmation.approved_at,
        )

        # 3. Donation 상태 업데이트
        await service.complete_donation(
            donation_id=donation.id,
            payment_key=confirmation.payment_key,
            payment_method=confirmation.method,
            approved_at=confirmation.approved_at,
        )

        logger.info("Donation completed: donation_id=%s", donation.id)

        # 4. 기부 완료 FCM 푸시 알림 전송
        if donation.user and donation.user.fcm_token:
            from src.integrations.firebase_messaging import firebase_service

            title = "✅ 기부가 완료되었습니다"
            body = f"{int(donation.amount):,}원 기부해주셔서 감사합니다!"
            url = "/mypage"

            await firebase_service.send_notification(
                token=donation.user.fcm_token,
                title=title,
                body=body,
                url=url,
                data={"donation_id": str(donation.id), "type": "donation_complete"}
            )

            logger.info("Sent donation complete notification to user: %s", donation.user.email)

        return PaymentConfirmResponse(
            donation_id=donation.id,
            status=DonationStatus.COMPLETED,
            payment_key=confirmation.payment_key,
            approved_at=confirmation.approved_at.isoformat(),
        )

    except TossPaymentsError as exc:
        logger.error(
            "Toss payment confirmation failed: %s (code=%s, status=%s)",
            exc,
            exc.code,
            exc.status_code,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": exc.code or "PAYMENT_FAILED",
                "message": str(exc),
            },
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during payment confirmation")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="결제 승인 중 오류가 발생했습니다.",
        ) from exc
    finally:
        await toss_client.close()


@router.get("/success")
async def payment_success(
    payment_key: str = Query(...),
    order_id: str = Query(...),
    amount: str = Query(...),
) -> dict:
    """
    Toss Payments 결제 성공 리다이렉트 핸들러

    프론트엔드에서 이 정보를 받아 /payments/confirm 호출
    """
    return {
        "payment_key": payment_key,
        "order_id": order_id,
        "amount": amount,
        "status": "success",
    }


@router.get("/fail")
async def payment_fail(
    code: str = Query(...),
    message: str = Query(...),
    order_id: str = Query(None),
) -> dict:
    """
    Toss Payments 결제 실패 리다이렉트 핸들러
    """
    logger.warning(
        "Payment failed: code=%s, message=%s, order_id=%s",
        code,
        message,
        order_id,
    )

    return {
        "code": code,
        "message": message,
        "order_id": order_id,
        "status": "failed",
    }


@router.post("/billing/callback")
async def billing_key_callback(
    payload: BillingKeyCallbackRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    정기결제 빌링키 발급 콜백

    Toss에서 빌링키 발급 후 호출됩니다.
    """
    logger.info(
        "Billing key callback: customer_key=%s, auth_key=%s",
        payload.customer_key,
        payload.auth_key,
    )

    toss_client = TossPaymentsClient()
    service = DonationService(session, toss_client)

    try:
        # Subscription 찾기
        subscription = await service.get_subscription_by_customer_key(
            payload.customer_key
        )

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )

        # 빌링키가 이미 발급된 경우
        if subscription.toss_billing_key:
            logger.info(
                "Billing key already exists for subscription: %s",
                subscription.id,
            )
            return {
                "subscription_id": str(subscription.id),
                "status": "already_authorized",
            }

        # Toss API로 빌링키 조회
        if not payload.auth_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="auth_key is required",
            )

        billing_key = await toss_client.get_billing_key(
            customer_key=payload.customer_key,
            auth_key=payload.auth_key,
        )

        # 빌링키 저장
        await service.update_subscription_billing_key(
            subscription_id=subscription.id,
            billing_key=billing_key,
        )

        logger.info("Billing key saved for subscription: %s", subscription.id)

        return {
            "subscription_id": str(subscription.id),
            "status": "authorized",
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error processing billing callback")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="빌링키 처리 중 오류가 발생했습니다.",
        ) from exc
    finally:
        await toss_client.close()


__all__ = ["router"]
