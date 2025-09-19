import pytest
from httpx import AsyncClient

from src.main import app

pytestmark = pytest.mark.asyncio


async def test_station_search_flow_supports_filters_and_nearby() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        list_response = await client.get(
            "/stations", params={"region": "서울", "district": "강남구", "search": "강남"}
        )
        assert list_response.status_code == 200
        list_body = list_response.json()
        assert "stations" in list_body

        nearby_response = await client.get(
            "/stations/nearby", params={"lat": 37.5, "lng": 127.0, "radius": 3000}
        )
        assert nearby_response.status_code == 200
        nearby_body = nearby_response.json()
        assert "stations" in nearby_body

        if nearby_body["stations"]:
            assert "distance" in nearby_body["stations"][0]
