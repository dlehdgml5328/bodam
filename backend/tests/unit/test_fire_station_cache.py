from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.cache import fire_station
from src.cache.keys import slugify_token


@pytest.mark.asyncio
async def test_invalidate_after_station_update(monkeypatch: pytest.MonkeyPatch) -> None:
    station = SimpleNamespace(
        id=uuid.uuid4(),
        name="서울소방서",
        region="서울",
        district="강남구",
    )

    delete_mock = AsyncMock(return_value=0)
    semantic_mock = AsyncMock(return_value=0)

    monkeypatch.setattr(fire_station.standard, "delete_pattern", delete_mock)
    monkeypatch.setattr(fire_station.semantic, "soft_invalidate_queries", semantic_mock)

    await fire_station.invalidate_after_station_update(station)

    delete_mock.assert_any_await("cache:stations:list:*")
    delete_mock.assert_any_await("cache:stations:nearby:*")
    delete_mock.assert_any_await(f"cache:emergencies:{slugify_token('서울')}:*")

    semantic_mock.assert_awaited_once()
    kwargs = semantic_mock.await_args.kwargs
    assert kwargs["station_id"] == station.id
    assert kwargs["region"] == station.region
