import uuid

import pytest
from httpx import AsyncClient

from src.main import app

pytestmark = pytest.mark.asyncio


async def test_list_donations_returns_paginated_response() -> None:
    headers = {"Authorization": "Bearer test-token"}
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/donations", headers=headers, params={"page": 1, "limit": 20})

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body.get("donations"), list)
    assert isinstance(body.get("total"), int)
    assert isinstance(body.get("page"), int)
    assert isinstance(body.get("limit"), int)


async def test_create_donation_returns_payment_url() -> None:
    headers = {"Authorization": "Bearer test-token"}
    payload = {
        "fire_station_id": str(uuid.uuid4()),
        "amount": 15000,
        "type": "one_time",
        "message": "소방대원 응원합니다",
        "is_anonymous": False,
    }
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/donations", headers=headers, json=payload)

    assert response.status_code == 201
    body = response.json()
    assert uuid.UUID(body["donation_id"])
    assert body.get("payment_url")
    assert body.get("order_id")


async def test_get_donation_detail_returns_full_payload() -> None:
    donation_id = str(uuid.uuid4())
    headers = {"Authorization": "Bearer test-token"}
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/donations/{donation_id}", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body.get("id") == donation_id
    assert body.get("fire_station")
    assert body.get("payment_method")


async def test_download_receipt_returns_pdf() -> None:
    donation_id = str(uuid.uuid4())
    headers = {"Authorization": "Bearer test-token"}
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/donations/{donation_id}/receipt", headers=headers)

    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("application/pdf")


async def test_request_refund_returns_acknowledgement() -> None:
    donation_id = str(uuid.uuid4())
    headers = {"Authorization": "Bearer test-token"}
    payload = {"reason": "결제 오류로 인한 환불 요청"}
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(f"/donations/{donation_id}/refund", headers=headers, json=payload)

    assert response.status_code == 201
    body = response.json()
    assert uuid.UUID(body["refund_id"])
    assert body.get("status")
    assert body.get("message")


async def test_list_subscriptions_returns_collection() -> None:
    headers = {"Authorization": "Bearer test-token"}
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/subscriptions", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body.get("subscriptions"), list)


async def test_cancel_subscription_returns_confirmation() -> None:
    subscription_id = str(uuid.uuid4())
    headers = {"Authorization": "Bearer test-token"}
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            f"/subscriptions/{subscription_id}/cancel", headers=headers
        )

    assert response.status_code == 200
    body = response.json()
    assert body.get("message")
