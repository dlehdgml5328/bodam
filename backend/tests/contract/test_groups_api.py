import pytest
from httpx import AsyncClient

from src.main import app

pytestmark = pytest.mark.asyncio


async def test_groups_contract_list() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/groups")

    assert response.status_code == 200


async def test_groups_contract_create() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/groups", json={"name": "테스트"})

    assert response.status_code == 200 or response.status_code == 201
