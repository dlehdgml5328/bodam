"""Toss Payments API client implementation."""

from __future__ import annotations

import base64
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import httpx

from src.services.donation_service import (
    BillingAuthorization,
    CheckoutSession,
    PaymentConfirmation,
    PaymentsGateway,
)


logger = logging.getLogger(__name__)


class TossPaymentsError(RuntimeError):
    """Raised when Toss Payments responds with an error."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
        response_body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.response_body = response_body or {}


@dataclass
class TossPaymentsSettings:
    api_key: str
    client_key: str
    base_url: str = "https://api.tosspayments.com"
    timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> "TossPaymentsSettings":
        api_key = os.getenv("TOSS_SECRET_KEY", "test_sk")
        client_key = os.getenv("TOSS_CLIENT_KEY", "test_ck")
        base_url = os.getenv("TOSS_BASE_URL", cls.base_url)
        timeout = float(os.getenv("TOSS_TIMEOUT", cls.timeout_seconds))
        return cls(api_key=api_key, client_key=client_key, base_url=base_url, timeout_seconds=timeout)


class TossPaymentsClient(PaymentsGateway):
    def __init__(self, settings: TossPaymentsSettings | None = None) -> None:
        self._settings = settings or TossPaymentsSettings.from_env()
        auth = base64.b64encode(f"{self._settings.api_key}:".encode()).decode()
        self._client = httpx.AsyncClient(
            base_url=self._settings.base_url.rstrip("/"),
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/json",
            },
            timeout=self._settings.timeout_seconds,
        )

    async def create_checkout(
        self,
        *,
        amount: Decimal,
        order_id: str,
        customer_name: str,
        success_url: str | None,
        fail_url: str | None,
        metadata: dict[str, object] | None = None,
    ) -> CheckoutSession:
        payload: dict[str, Any] = {
            "amount": float(amount),
            "orderId": order_id,
            "orderName": f"Donation {order_id}",
            "customerName": customer_name,
            "successUrl": success_url or "https://app.bodam.example/payment/success",
            "failUrl": fail_url or "https://app.bodam.example/payment/fail",
        }
        if metadata:
            payload["metadata"] = metadata

        data = await self._post("/v1/payments", payload, context="create checkout")

        payment_url = (
            _dig(data, "checkout", "url")
            or data.get("checkoutUrl")
            or _dig(data, "links", "checkout")
            or _dig(data, "nextAction", "url")
        )
        if not payment_url:
            raise TossPaymentsError(
                "Toss response did not include a checkout URL",
                status_code=200,
                response_body=data,
            )

        order_id_out = data.get("orderId", order_id)
        return CheckoutSession(order_id=order_id_out, payment_url=payment_url)

    async def confirm_payment(
        self,
        *,
        payment_key: str,
        order_id: str,
        amount: Decimal,
    ) -> PaymentConfirmation:
        payload = {
            "paymentKey": payment_key,
            "orderId": order_id,
            "amount": float(amount),
        }
        data = await self._post("/v1/payments/confirm", payload, context="confirm payment")

        approved_at = _parse_iso_datetime(data.get("approvedAt")) or datetime.now(timezone.utc)
        method = data.get("method")
        if not method and isinstance(data.get("card"), dict):
            method = "card"
        method = method or "card"

        payment_key_out = data.get("paymentKey", payment_key)
        return PaymentConfirmation(payment_key=payment_key_out, method=method, approved_at=approved_at)

    async def request_refund(
        self,
        *,
        payment_key: str,
        amount: Decimal,
        reason: str,
    ) -> None:
        payload = {
            "cancelAmount": float(amount),
            "cancelReason": reason,
        }
        await self._post(
            f"/v1/payments/{payment_key}/cancel",
            payload,
            context="request refund",
        )

    async def create_billing_authorization(
        self,
        *,
        customer_key: str | None,
        success_url: str | None,
        fail_url: str | None,
    ) -> BillingAuthorization:
        generated_customer_key = customer_key or f"customer_{uuid.uuid4()}"
        payload = {
            "customerKey": generated_customer_key,
            "successUrl": success_url or "https://app.bodam.example/payment/success",
            "failUrl": fail_url or "https://app.bodam.example/payment/fail",
        }
        data = await self._post(
            "/v1/billing/authorizations/card",
            payload,
            context="create billing authorization",
        )

        billing_auth_url = (
            data.get("checkoutUrl")
            or data.get("url")
            or _dig(data, "links", "checkout")
        )
        billing_key = data.get("billingKey")
        customer_key_out = data.get("customerKey", generated_customer_key)

        if billing_auth_url is None and billing_key is None:
            raise TossPaymentsError(
                "Toss response missing billing authorization data",
                status_code=200,
                response_body=data,
            )

        return BillingAuthorization(
            billing_auth_url=billing_auth_url,
            customer_key=customer_key_out,
            billing_key=billing_key,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _post(self, path: str, payload: dict[str, Any], *, context: str) -> dict[str, Any]:
        try:
            response = await self._client.post(path, json=payload)
        except httpx.HTTPError as exc:  # pragma: no cover - network failure guard
            message = f"Failed to call Toss Payments API during {context}: {exc}"
            logger.exception(message)
            raise TossPaymentsError(message) from exc

        return self._parse_response(response, context=context)

    def _parse_response(self, response: httpx.Response, *, context: str) -> dict[str, Any]:
        try:
            data = response.json()
        except ValueError:
            data = None

        if response.is_error:
            error_message = "Toss Payments API error"
            error_code = None
            if isinstance(data, dict):
                error_message = data.get("message") or error_message
                error_code = data.get("code")
            logger.error(
                "%s (status=%s, code=%s, context=%s)",
                error_message,
                response.status_code,
                error_code,
                context,
            )
            raise TossPaymentsError(
                error_message,
                status_code=response.status_code,
                code=error_code,
                response_body=data if isinstance(data, dict) else None,
            )

        if not isinstance(data, dict):
            raise TossPaymentsError(
                "Unexpected Toss Payments response type",
                status_code=response.status_code,
            )
        return data


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        logger.warning("Failed to parse datetime from Toss response: %s", value)
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _dig(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


__all__ = [
    "TossPaymentsClient",
    "TossPaymentsSettings",
    "TossPaymentsError",
]
