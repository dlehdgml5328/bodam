import pytest
from httpx import AsyncClient

from src.main import app

pytestmark = pytest.mark.asyncio


async def test_user_registration_flow_creates_and_logs_in_user() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        signup_payload = {
            "email": "new.donor@example.com",
            "password": "StrongPass!1",
            "name": "보담 기부자",
        }
        signup_response = await client.post("/auth/signup", json=signup_payload)
        assert signup_response.status_code == 201

        login_response = await client.post(
            "/auth/login",
            json={"email": signup_payload["email"], "password": signup_payload["password"]},
        )
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()

        refresh_response = await client.post("/auth/refresh")
        assert refresh_response.status_code == 200
        assert "access_token" in refresh_response.json()
