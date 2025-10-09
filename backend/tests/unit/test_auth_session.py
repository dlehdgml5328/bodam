import uuid

import pytest
from fastapi import Response

from src.security.session import (
    CSRF_COOKIE_NAME,
    SESSION_COOKIE_NAME,
    CSRF_HEADER_NAME,
    get_current_user,
    get_current_user_from_bearer,
    get_current_user_with_csrf,
    issue_session_tokens,
)
from src.security.tokens import create_access_token


class DummyUser:
    def __init__(self, *, active: bool = True) -> None:
        self.id = uuid.uuid4()
        self.is_active = active
        self.email = "dummy@example.com"
        self.name = "Dummy"


class FakeSession:
    pass


@pytest.mark.asyncio
async def test_get_current_user_returns_user(monkeypatch: pytest.MonkeyPatch) -> None:
    dummy_user = DummyUser()
    token = create_access_token(str(dummy_user.id))

    class FakeUserService:
        def __init__(self, session: FakeSession) -> None:
            self.session = session

        async def get_user(self, user_id: uuid.UUID) -> DummyUser:
            assert user_id == dummy_user.id
            return dummy_user

    monkeypatch.setattr("src.security.session.UserService", FakeUserService)

    request = type("Req", (), {"state": type("State", (), {"token": token})()})()
    user = await get_current_user(request, FakeSession())
    assert user is dummy_user


@pytest.mark.asyncio
async def test_get_current_user_inactive_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    dummy_user = DummyUser(active=False)
    token = create_access_token(str(dummy_user.id))

    class FakeUserService:
        def __init__(self, session: FakeSession) -> None:
            self.session = session

        async def get_user(self, user_id: uuid.UUID) -> DummyUser:
            return dummy_user

    monkeypatch.setattr("src.security.session.UserService", FakeUserService)

    request = type("Req", (), {"state": type("State", (), {"token": token})()})()
    with pytest.raises(Exception) as exc:
        await get_current_user(request, FakeSession())
    assert getattr(exc.value, "status_code", None) == 403


def test_issue_access_token_sets_cookie(monkeypatch: pytest.MonkeyPatch) -> None:
    dummy_user = DummyUser()
    response = Response()
    tokens = issue_session_tokens(response, dummy_user)

    assert tokens["access_token"]
    assert tokens["csrf_token"]
    cookie_headers = [value.decode("latin-1") for key, value in response.raw_headers if key == b"set-cookie"]
    combined = "".join(cookie_headers)
    assert SESSION_COOKIE_NAME in combined
    assert CSRF_COOKIE_NAME in combined


@pytest.mark.asyncio
async def test_get_current_user_from_bearer(monkeypatch: pytest.MonkeyPatch) -> None:
    dummy_user = DummyUser()
    token = create_access_token(str(dummy_user.id))

    class FakeUserService:
        def __init__(self, session: FakeSession) -> None:
            self.session = session

        async def get_user(self, user_id: uuid.UUID) -> DummyUser:
            return dummy_user

    monkeypatch.setattr("src.security.session.UserService", FakeUserService)

    request = type(
        "Req",
        (),
        {"headers": {"Authorization": f"Bearer {token}"}},
    )()
    user = await get_current_user_from_bearer(request, FakeSession())
    assert user is dummy_user


@pytest.mark.asyncio
async def test_csrf_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    dummy_user = DummyUser()
    token = create_access_token(str(dummy_user.id))

    class FakeUserService:
        def __init__(self, session: FakeSession) -> None:
            self.session = session

        async def get_user(self, user_id: uuid.UUID) -> DummyUser:
            return dummy_user

    monkeypatch.setattr("src.security.session.UserService", FakeUserService)

    request = type(
        "Req",
        (),
        {
            "method": "POST",
            "state": type("State", (), {"token": token})(),
            "cookies": {CSRF_COOKIE_NAME: "token"},
            "headers": {CSRF_HEADER_NAME: "token"},
        },
    )()
    user = await get_current_user_with_csrf(request, FakeSession())
    assert user is dummy_user

    bad_request = type(
        "Req",
        (),
        {
            "method": "POST",
            "state": type("State", (), {"token": token})(),
            "cookies": {CSRF_COOKIE_NAME: "token"},
            "headers": {CSRF_HEADER_NAME: "different"},
        },
    )()
    with pytest.raises(Exception) as exc:
        await get_current_user_with_csrf(bad_request, FakeSession())
    assert getattr(exc.value, "status_code", None) == 403
