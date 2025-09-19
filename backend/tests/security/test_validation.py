import pytest
from httpx import AsyncClient

from src.main import app

pytestmark = pytest.mark.asyncio


async def test_signup_rejects_short_password() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/auth/signup",
            json={"email": "invalid@example.com", "password": "123", "name": "테스트"},
        )

    assert response.status_code in {400, 422}
