from __future__ import annotations

import re

from src.cache import keys


def test_list_stations_key_structure() -> None:
    key = keys.list_stations_key(
        region="서울",
        district="강남구",
        search="테스트",
        limit=20,
        offset=0,
    )
    assert key.startswith("cache:stations:list:서울:강남구:")
    assert re.fullmatch(r"cache:stations:list:[^:]+:[^:]+:[0-9a-f]{40}", key)


def test_nearby_key_contains_geohash_bucket() -> None:
    key = keys.nearby_stations_key(
        latitude=37.1234567,
        longitude=127.7654321,
        radius_meters=550,
        limit=5,
    )
    # Radius bucket should be rounded up to nearest 100
    assert ":600:" in key
    assert key.startswith("cache:stations:nearby:37.123457:127.765432:")


def test_emergency_key_structure() -> None:
    key = keys.emergency_status_key(
        region="부산",
        priority="HIGH",
        limit=10,
    )
    assert key.startswith("cache:emergencies:부산:high:")
    assert re.fullmatch(r"cache:emergencies:[^:]+:[^:]+:[0-9a-f]{40}", key)


def test_slugify_token_handles_unicode() -> None:
    assert keys.slugify_token("서울시 강남구") == "서울시-강남구"
    assert keys.slugify_token(" Rescue / Station ") == "rescue-station"
