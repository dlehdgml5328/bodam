import uuid

import pytest
from httpx import AsyncClient

from src.main import app

pytestmark = pytest.mark.asyncio


async def test_list_stations_returns_paginated_collection() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/stations", params={"page": 1, "limit": 20, "region": "서울", "search": "강남"}
        )

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body.get("stations"), list)
    assert isinstance(body.get("total"), int)
    assert body.get("page") == 1
    assert body.get("limit") == 20


async def test_nearby_stations_returns_distances() -> None:
    params = {"lat": 37.5665, "lng": 126.978, "radius": 5000}
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/stations/nearby", params=params)

    assert response.status_code == 200
    body = response.json()
    stations = body.get("stations", [])
    if stations:
        assert "distance" in stations[0]


async def test_station_detail_contains_recent_donations() -> None:
    station_id = str(uuid.uuid4())
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/stations/{station_id}")

    assert response.status_code == 200
    body = response.json()
    assert body.get("id") == station_id
    assert "recent_donations" in body


async def test_station_rankings_returns_period_metadata() -> None:
    station_id = str(uuid.uuid4())
    params = {"period": "monthly", "limit": 10}
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/stations/{station_id}/rankings", params=params)

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body.get("rankings"), list)
    assert body.get("period") == "monthly"
    assert body.get("calculated_at")


async def test_station_incidents_returns_news_items() -> None:
    station_id = str(uuid.uuid4())
    params = {"days": 7}
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/stations/{station_id}/incidents", params=params)

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body.get("incidents"), list)


async def test_favorite_station_creation_requires_auth() -> None:
    station_id = str(uuid.uuid4())
    headers = {"Authorization": "Bearer test-token"}
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(f"/stations/{station_id}/favorites", headers=headers)

    assert response.status_code == 201


async def test_remove_station_favorite_returns_success() -> None:
    station_id = str(uuid.uuid4())
    headers = {"Authorization": "Bearer test-token"}
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.delete(f"/stations/{station_id}/favorites", headers=headers)

    assert response.status_code == 200
