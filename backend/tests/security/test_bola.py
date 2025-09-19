import uuid

import pytest
from httpx import AsyncClient

from src.main import app

pytestmark = pytest.mark.asyncio


async def test_user_cannot_access_other_users_donation() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/donations/{uuid.uuid4()}", headers={"Authorization": "Bearer attacker"})

    assert response.status_code in {401, 403}
