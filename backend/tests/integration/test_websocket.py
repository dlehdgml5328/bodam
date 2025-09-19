import pytest
from starlette.testclient import TestClient

from src.main import app

pytestmark = pytest.mark.integration


def test_websocket_notifications_broadcasts_updates() -> None:
    client = TestClient(app)

    with client.websocket_connect("/ws/notifications?token=test-token") as websocket:
        websocket.send_json({"type": "ping"})
        message = websocket.receive_json()
        assert message.get("type") == "notification"
        assert "payload" in message
