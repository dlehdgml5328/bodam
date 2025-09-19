import pytest
from httpx import AsyncClient

from src.main import app

pytestmark = pytest.mark.asyncio


async def test_admin_search_contract() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/admin/search", params={"q": "소방서"})

    assert response.status_code == 200


async def test_admin_refunds_contract() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/admin/refunds")

    assert response.status_code == 200
