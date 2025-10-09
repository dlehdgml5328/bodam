import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.security.session import CSRF_COOKIE_NAME, SESSION_COOKIE_NAME

pytestmark = pytest.mark.asyncio


async def test_user_registration_flow_creates_and_logs_in_user() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost"
    ) as client:
        signup_payload = {
            "email": "new.donor@example.com",
            "password": "StrongPass!1",
            "name": "보담 기부자",
        }
        signup_response = await client.post("/auth/signup", json=signup_payload)
        assert signup_response.status_code == 201

        refresh_without_login = await client.post("/auth/refresh")
        assert refresh_without_login.status_code == 401

        login_response = await client.post(
            "/auth/login",
            json={"email": signup_payload["email"], "password": signup_payload["password"]},
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        assert "csrf_token" in login_data
        assert client.cookies.get("bodam_session") is not None
        assert client.cookies.get("bodam_csrf") == login_data["csrf_token"]

        client.headers["cookie"] = (
            f"{SESSION_COOKIE_NAME}={login_data['access_token']}; "
            f"{CSRF_COOKIE_NAME}={login_data['csrf_token']}"
        )

        refresh_response = await client.post("/auth/refresh")
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        assert "access_token" in refresh_data
        assert "csrf_token" in refresh_data
        assert client.cookies.get("bodam_csrf") == refresh_data["csrf_token"]
