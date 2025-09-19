import pytest
from httpx import AsyncClient

from src.main import app

pytestmark = pytest.mark.asyncio


async def test_list_refunds_contract() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/refunds")

    assert response.status_code == 200


async def test_approve_refund_contract() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/refunds/00000000-0000-0000-0000-000000000000/approve")

    assert response.status_code == 200
