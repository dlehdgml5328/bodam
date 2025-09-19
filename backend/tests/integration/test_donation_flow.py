import uuid

import pytest
from httpx import AsyncClient

from src.main import app

pytestmark = pytest.mark.asyncio


async def test_donation_creation_flow_handles_payment_and_receipt() -> None:
    headers = {"Authorization": "Bearer test-token"}
    async with AsyncClient(app=app, base_url="http://test") as client:
        create_payload = {
            "fire_station_id": str(uuid.uuid4()),
            "amount": 20000,
            "type": "one_time",
            "message": "보담 소방서 응원",
        }
        create_response = await client.post("/donations", headers=headers, json=create_payload)
        assert create_response.status_code == 201
        data = create_response.json()
        donation_id = data["donation_id"]
        assert data.get("payment_url")

        detail_response = await client.get(f"/donations/{donation_id}", headers=headers)
        assert detail_response.status_code == 200
        detail = detail_response.json()
        assert detail.get("status") in {"pending", "completed"}

        receipt_response = await client.get(
            f"/donations/{donation_id}/receipt", headers=headers
        )
        assert receipt_response.status_code == 200
        assert receipt_response.headers.get("content-type", "").startswith("application/pdf")
