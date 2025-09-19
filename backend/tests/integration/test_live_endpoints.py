import pytest
from httpx import AsyncClient

from src.main import app

pytestmark = pytest.mark.asyncio


async def test_live_news_endpoint() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/live/news")

    assert response.status_code == 200


async def test_live_alerts_endpoint() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/live/alerts")

    assert response.status_code == 200
