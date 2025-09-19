import uuid

import pytest
from httpx import AsyncClient

from src.main import app

pytestmark = pytest.mark.asyncio


async def test_signup_contract_creates_user_record() -> None:
    payload = {
        "email": "firefighter@example.com",
        "password": "strongpass!",
        "name": "홍길동",
        "phone": "01012345678",
    }
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/auth/signup", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert isinstance(body.get("user_id"), str)
    assert uuid.UUID(body["user_id"])  # raises if invalid
    assert body.get("email") == payload["email"]
    assert "message" in body


async def test_login_contract_sets_session_cookie() -> None:
    payload = {"email": "firefighter@example.com", "password": "strongpass!"}
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/auth/login", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert "user" in body
    assert "access_token" in body
    assert "set-cookie" in {k.lower(): v for k, v in response.headers.items()}


async def test_logout_contract_clears_cookie() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/auth/logout")

    assert response.status_code == 200
    assert "set-cookie" in {k.lower(): v for k, v in response.headers.items()}


async def test_refresh_contract_returns_new_token() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/auth/refresh")

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body


async def test_social_login_redirects_to_provider() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/auth/social/kakao")

    assert response.status_code == 302
    assert response.headers.get("location")


async def test_social_callback_redirects_frontend() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/auth/social/kakao/callback", params={"code": "abc123"})

    assert response.status_code == 302
    assert response.headers.get("location")
