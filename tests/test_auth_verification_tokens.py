import time
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.modules.Auth import routes as auth_routes
from app.modules.Auth.utils import create_url_safe_token, decode_url_safe_token


class DummySession:
    def __init__(self):
        self.committed = False
        self.refreshed = []

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        self.refreshed.append(obj)


@pytest.fixture
def api_client():
    session = DummySession()

    async def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, base_url="http://localhost") as client:
        yield client, session
    app.dependency_overrides.clear()


def test_create_and_decode_url_safe_token_roundtrip():
    token = create_url_safe_token({"email": "student@example.com"})
    decoded = decode_url_safe_token(token, max_age=60)
    assert decoded["email"] == "student@example.com"


def test_decode_url_safe_token_invalid_token():
    with pytest.raises(HTTPException) as exc:
        decode_url_safe_token("not-a-valid-token", max_age=60)

    assert exc.value.status_code == 400


def test_decode_url_safe_token_expired_token():
    token = create_url_safe_token({"email": "student@example.com"})
    time.sleep(1)

    with pytest.raises(HTTPException) as exc:
        decode_url_safe_token(token, max_age=0)

    assert exc.value.status_code == 400
    assert "expired" in exc.value.detail.lower()


def test_register_endpoint_sends_verification_and_notification(monkeypatch, api_client):
    client, _ = api_client
    created_user = SimpleNamespace(
        uid=uuid4(),
        username="jane",
        first_name="Jane",
        last_name="Doe",
        role="user",
        email="jane@example.com",
        is_active=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    sent = {"email": None, "notification": False, "event_type": None}

    async def fake_user_exists(email, _session):
        return False

    async def fake_create_user(_user_data, _hashed_pwd, _session):
        return created_user

    async def fake_send_verification_email(email):
        sent["email"] = email
        return "token"

    async def fake_create_auth_notification(*args, **kwargs):
        sent["notification"] = True
        sent["event_type"] = kwargs.get("event_type")

    monkeypatch.setattr(auth_routes.auth_service, "user_exists", fake_user_exists)
    monkeypatch.setattr(auth_routes.user_service, "create_user", fake_create_user)
    monkeypatch.setattr(auth_routes, "_send_verification_email", fake_send_verification_email)
    monkeypatch.setattr(auth_routes, "_safe_create_auth_notification", fake_create_auth_notification)

    response = client.post(
        "/api/v2/auth/register",
        json={
            "username": "jane",
            "first_name": "Jane",
            "last_name": "Doe",
            "role": "user",
            "email": "jane@example.com",
            "password": "secret123",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "jane@example.com"
    assert sent["email"] == "jane@example.com"
    assert sent["notification"] is True
    assert sent["event_type"] == "auth.verification_email_sent"


def test_verify_endpoint_activates_account_and_commits(monkeypatch, api_client):
    client, session = api_client
    user = SimpleNamespace(uid=uuid4(), email="jane@example.com", is_active=False)
    calls = {"notification": False, "event_type": None}

    def fake_decode(_token):
        return {"email": "jane@example.com"}

    async def fake_get_user_by_email(_email, _session):
        return user

    async def fake_create_auth_notification(*args, **kwargs):
        calls["notification"] = True
        calls["event_type"] = kwargs.get("event_type")

    monkeypatch.setattr(auth_routes, "decode_url_safe_token", fake_decode)
    monkeypatch.setattr(auth_routes.auth_service, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(auth_routes, "_safe_create_auth_notification", fake_create_auth_notification)

    response = client.get("/api/v2/auth/verify/sample-token")

    assert response.status_code == 200
    assert response.json()["message"] == "Account verified successfully"
    assert user.is_active is True
    assert session.committed is True
    assert session.refreshed and session.refreshed[0] is user
    assert calls["notification"] is True
    assert calls["event_type"] == "auth.account_verified"


def test_resend_verification_endpoint_enforces_cooldown(monkeypatch, api_client):
    client, _ = api_client
    user = SimpleNamespace(uid=uuid4(), email="jane@example.com", is_active=False)
    calls = {"email": 0}

    async def fake_get_user_by_email(_email, _session):
        return user

    async def fake_acquire_slot(_email, cooldown_seconds=60):
        return False

    async def fake_send_verification_email(_email):
        calls["email"] += 1
        return "token"

    monkeypatch.setattr(auth_routes.auth_service, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(auth_routes, "acquire_verification_resend_slot", fake_acquire_slot)
    monkeypatch.setattr(auth_routes, "_send_verification_email", fake_send_verification_email)

    response = client.post(
        "/api/v2/auth/resend-verification",
        json={"email": "jane@example.com"},
    )

    assert response.status_code == 429
    assert "Please wait" in response.json()["detail"]
    assert calls["email"] == 0


def test_resend_verification_endpoint_sends_when_slot_available(monkeypatch, api_client):
    client, _ = api_client
    user = SimpleNamespace(uid=uuid4(), email="jane@example.com", is_active=False)
    calls = {"email": 0, "notification": 0, "event_type": None}

    async def fake_get_user_by_email(_email, _session):
        return user

    async def fake_acquire_slot(_email, cooldown_seconds=60):
        return True

    async def fake_send_verification_email(_email):
        calls["email"] += 1
        return "token"

    async def fake_create_auth_notification(*args, **kwargs):
        calls["notification"] += 1
        calls["event_type"] = kwargs.get("event_type")

    monkeypatch.setattr(auth_routes.auth_service, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(auth_routes, "acquire_verification_resend_slot", fake_acquire_slot)
    monkeypatch.setattr(auth_routes, "_send_verification_email", fake_send_verification_email)
    monkeypatch.setattr(auth_routes, "_safe_create_auth_notification", fake_create_auth_notification)

    response = client.post(
        "/api/v2/auth/resend-verification",
        json={"email": "jane@example.com"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Verification email sent"
    assert calls["email"] == 1
    assert calls["notification"] == 1
    assert calls["event_type"] == "auth.verification_email_resent"
