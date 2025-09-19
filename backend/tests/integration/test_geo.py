import pytest
from httpx import AsyncClient

from src.main import app

pytestmark = pytest.mark.asyncio


async def test_geo_search_endpoint() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/geo/search", params={"address": "서울"})

    assert response.status_code == 200
