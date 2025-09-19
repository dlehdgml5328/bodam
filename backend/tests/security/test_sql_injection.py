import pytest
from httpx import AsyncClient

from src.main import app

pytestmark = pytest.mark.asyncio


async def test_station_search_blocks_sql_injection() -> None:
    payload = {"search": "강남'; DROP TABLE users; --"}
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/stations", params=payload)

    assert response.status_code == 200
