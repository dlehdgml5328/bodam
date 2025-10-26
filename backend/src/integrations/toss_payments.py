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
        # Toss Payments V1은 Frontend SDK를 통해 결제창을 띄우므로
        # Backend에서는 order_id와 결제 정보만 반환합니다.
        # Frontend에서 tossPayments.requestPayment()를 호출합니다.

        # payment_url은 Frontend에서 사용할 성공/실패 redirect URL을 반환
        success = success_url or "http://localhost:3000/payment/success"

        # Frontend SDK에서 사용할 정보를 URL 파라미터로 전달
        payment_url = f"{success}?orderId={order_id}&amount={amount}"

        return CheckoutSession(order_id=order_id, payment_url=payment_url)

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
        # Toss Payments V1은 Frontend SDK를 통해 빌링키 발급을 진행합니다.
        # Backend에서는 customer_key와 redirect URL만 반환합니다.
        # Frontend에서 tossPayments.requestBillingAuth()를 호출합니다.

        generated_customer_key = customer_key or f"customer_{uuid.uuid4()}"
        success = success_url or "http://localhost:3000/payment/billing-success"

        # Frontend SDK에서 사용할 정보를 auth_url로 전달
        billing_auth_url = f"{success}?customerKey={generated_customer_key}"

        return BillingAuthorization(
            billing_auth_url=billing_auth_url,
            customer_key=generated_customer_key,
            billing_key=None,
        )

    async def get_billing_key(self, *, customer_key: str, auth_key: str) -> str:
        """
        Toss API로 auth_key를 이용해 실제 billing_key 조회

        https://docs.tosspayments.com/reference#빌링키-발급
        GET /v1/billing/authorizations/{authKey}
        """
        url = f"/v1/billing/authorizations/{auth_key}"
        try:
            response = await self._client.get(url)
        except httpx.HTTPError as exc:
            message = f"Failed to get billing key from Toss API: {exc}"
            logger.exception(message)
            raise TossPaymentsError(message) from exc

        data = self._parse_response(response, context="get billing key")

        # Toss API 응답에서 billingKey 추출
        billing_key = data.get("billingKey")
        if not billing_key:
            raise TossPaymentsError(
                "Billing key not found in Toss API response",
                response_body=data,
            )

        return billing_key

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
