"""정기결제 자동 결제 처리 Celery Task"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from src.integrations.toss_payments import TossPaymentsClient
from src.models.donation import (
    Donation,
    DonationStatus,
    DonationSubscription,
    DonationType,
    SubscriptionStatus,
)
from src.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="billing.process_subscriptions")
def process_recurring_donations() -> dict[str, int]:
    """
    정기결제 자동 결제 처리

    매일 실행되며, next_billing_at이 오늘인 구독을 찾아서 자동 결제 진행
    """
    import asyncio

    return asyncio.run(_process_recurring_donations_async())


async def _process_recurring_donations_async() -> dict[str, int]:
    """비동기 정기결제 처리"""
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://bodam:bodam@localhost:5432/bodam")
    engine = create_async_engine(database_url)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    processed = 0
    failed = 0
    skipped = 0

    async with async_session() as session:
        # 오늘 결제해야 할 구독 찾기
        today = datetime.now(timezone.utc).date()
        tomorrow = today + timedelta(days=1)

        result = await session.execute(
            select(DonationSubscription)
            .where(DonationSubscription.status == SubscriptionStatus.ACTIVE)
            .where(DonationSubscription.next_billing_at >= today)
            .where(DonationSubscription.next_billing_at < tomorrow)
        )
        subscriptions = result.scalars().all()

        logger.info(f"Found {len(subscriptions)} subscriptions to process")

        toss_client = TossPaymentsClient()

        for subscription in subscriptions:
            try:
                if not subscription.toss_billing_key:
                    logger.warning(
                        f"Subscription {subscription.id} has no billing key, skipping"
                    )
                    skipped += 1
                    continue

                # Toss API로 빌링키 결제 요청
                order_id = f"recurring_{subscription.id}_{datetime.now(timezone.utc).timestamp()}"

                # Toss Billing API 호출
                payment_data = await _request_billing_payment(
                    toss_client=toss_client,
                    billing_key=subscription.toss_billing_key,
                    customer_key=subscription.toss_customer_key,
                    amount=subscription.amount,
                    order_id=order_id,
                    order_name=f"정기기부 {subscription.cycle.value}",
                )

                # Donation 레코드 생성
                donation = Donation(
                    user_id=subscription.user_id,
                    fire_station_id=subscription.origin_donation.fire_station_id,
                    subscription_id=subscription.id,
                    amount=subscription.amount,
                    currency=subscription.currency,
                    type=DonationType.RECURRING,
                    status=DonationStatus.COMPLETED,
                    payment_method="card",
                    toss_order_id=order_id,
                    toss_payment_key=payment_data["paymentKey"],
                    completed_at=datetime.now(timezone.utc),
                )
                session.add(donation)

                # 다음 결제일 업데이트
                subscription.next_billing_at = _calculate_next_billing_date(
                    subscription.next_billing_at, subscription.cycle
                )

                # 결제 성공 시 실패 카운터 리셋
                if subscription.metadata_json is None:
                    subscription.metadata_json = {}
                subscription.metadata_json["consecutive_failures"] = 0
                subscription.metadata_json["last_success_at"] = datetime.now(timezone.utc).isoformat()

                await session.commit()
                processed += 1

                logger.info(
                    f"Processed subscription {subscription.id}, created donation {donation.id}"
                )

            except Exception as exc:
                logger.exception(
                    f"Failed to process subscription {subscription.id}: {exc}"
                )
                failed += 1
                await session.rollback()

                # 3회 연속 실패 시 구독 일시정지
                if not hasattr(subscription, "metadata_json"):
                    subscription.metadata_json = {}
                if subscription.metadata_json is None:
                    subscription.metadata_json = {}

                fail_count = subscription.metadata_json.get("consecutive_failures", 0) + 1
                subscription.metadata_json["consecutive_failures"] = fail_count
                subscription.metadata_json["last_failure_at"] = datetime.now(timezone.utc).isoformat()
                subscription.metadata_json["last_failure_reason"] = str(exc)

                if fail_count >= 3:
                    subscription.status = SubscriptionStatus.PAUSED
                    subscription.paused_at = datetime.now(timezone.utc)
                    logger.warning(
                        f"Subscription {subscription.id} paused due to {fail_count} consecutive failures"
                    )

                await session.commit()

        await toss_client.close()

    await engine.dispose()

    return {"processed": processed, "failed": failed, "skipped": skipped}


async def _request_billing_payment(
    *,
    toss_client: TossPaymentsClient,
    billing_key: str,
    customer_key: str,
    amount: Decimal,
    order_id: str,
    order_name: str,
) -> dict:
    """Toss Billing API로 결제 요청"""
    import httpx

    url = f"{toss_client._settings.base_url}/v1/billing/{billing_key}"
    payload = {
        "customerKey": customer_key,
        "amount": float(amount),
        "orderId": order_id,
        "orderName": order_name,
    }

    response = await toss_client._client.post(url, json=payload)
    return toss_client._parse_response(response, context="billing payment")


def _calculate_next_billing_date(current_date: datetime, cycle: str) -> datetime:
    """다음 결제일 계산"""
    from src.models.donation import SubscriptionCycle

    if cycle == SubscriptionCycle.MONTHLY:
        # 1개월 후
        next_month = current_date.month + 1
        next_year = current_date.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        return current_date.replace(year=next_year, month=next_month)
    elif cycle == SubscriptionCycle.QUARTERLY:
        # 3개월 후
        return current_date + timedelta(days=90)
    elif cycle == SubscriptionCycle.YEARLY:
        # 1년 후
        return current_date.replace(year=current_date.year + 1)
    else:
        return current_date + timedelta(days=30)


__all__ = ["process_recurring_donations"]
