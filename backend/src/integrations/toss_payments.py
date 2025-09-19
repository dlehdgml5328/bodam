"""Toss Payments API client."""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

import httpx

from src.services.donation_service import CheckoutSession, PaymentConfirmation, PaymentsGateway


@dataclass
class TossPaymentsSettings:
    api_key: str
    client_key: str
    base_url: str = "https://api.tosspayments.com"

    @classmethod
    def from_env(cls) -> "TossPaymentsSettings":
        api_key = os.getenv("TOSS_SECRET_KEY", "test_sk")
        client_key = os.getenv("TOSS_CLIENT_KEY", "test_ck")
        base_url = os.getenv("TOSS_BASE_URL", cls.base_url)
        return cls(api_key=api_key, client_key=client_key, base_url=base_url)


class TossPaymentsClient(PaymentsGateway):
    def __init__(self, settings: TossPaymentsSettings | None = None) -> None:
        self._settings = settings or TossPaymentsSettings.from_env()
        auth = base64.b64encode(f"{self._settings.api_key}:".encode()).decode()
        self._client = httpx.AsyncClient(
            base_url=self._settings.base_url,
            headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"},
            timeout=10,
        )

    async def create_checkout(
        self,
        *,
        amount: Decimal,
        order_id: str,
        customer_name: str,
        success_url: str,
        fail_url: str,
    ) -> CheckoutSession:
        payload = {
            "amount": float(amount),
            "orderId": order_id,
            "orderName": f"Donation {order_id}",
            "customerName": customer_name,
            "successUrl": success_url,
            "failUrl": fail_url,
        }
        # The API call is omitted in this offline environment. In production, uncomment below:
        # response = await self._client.post('/v1/payments', json=payload)
        # response.raise_for_status()
        # data = response.json()
        payment_url = f"https://pay.toss.im/payments/{order_id}"
        return CheckoutSession(order_id=order_id, payment_url=payment_url)

    async def confirm_payment(
        self,
        *,
        payment_key: str,
        order_id: str,
        amount: Decimal,
    ) -> PaymentConfirmation:
        payload = {"paymentKey": payment_key, "orderId": order_id, "amount": float(amount)}
        # response = await self._client.post('/v1/payments/confirm', json=payload)
        # response.raise_for_status()
        approved_at = datetime.now(timezone.utc)
        return PaymentConfirmation(payment_key=payment_key, method="card", approved_at=approved_at)

    async def request_refund(
        self,
        *,
        payment_key: str,
        amount: Decimal,
        reason: str,
    ) -> None:
        payload = {"cancelAmount": float(amount), "cancelReason": reason}
        # response = await self._client.post(f'/v1/payments/{payment_key}/cancel', json=payload)
        # response.raise_for_status()
        return None

    async def close(self) -> None:
        await self._client.aclose()


__all__ = ["TossPaymentsClient", "TossPaymentsSettings"]
