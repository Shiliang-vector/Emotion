import os
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

test_db_path = Path("storage/test_emotion.db")
if test_db_path.exists():
    test_db_path.unlink()
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{test_db_path.as_posix()}"
os.environ["AUTH_SECRET_KEY"] = "test-secret-for-fastapi-users-jwt-32"

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def auth_headers(client, email: str, password: str) -> dict[str, str]:
    response = client.post("/api/auth/jwt/login", data={"username": email, "password": password})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_check(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_auth_me_returns_demo_client(client):
    headers = auth_headers(client, "client@example.com", "client123")

    response = client.get("/api/users/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["role"] == "client"
    assert response.json()["email"] == "client@example.com"


def test_register_client_user(client):
    email = f"client-{uuid.uuid4().hex[:8]}@example.com"

    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "client123",
            "role": "client",
            "display_name": "测试普通用户",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == email
    assert response.json()["role"] == "client"


def test_upload_requires_login(client):
    response = client.post(
        "/api/videos/upload",
        files={"file": ("sample.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 401


def test_upload_rejects_non_video_file_for_client(client):
    headers = auth_headers(client, "client@example.com", "client123")

    response = client.post(
        "/api/videos/upload",
        headers=headers,
        files={"file": ("sample.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400


def test_counselor_can_list_bound_clients(client):
    headers = auth_headers(client, "counselor@example.com", "counselor123")

    response = client.get("/api/counselor/clients", headers=headers)

    assert response.status_code == 200
    assert any(item["email"] == "client@example.com" for item in response.json())


def test_client_cannot_access_counselor_clients(client):
    headers = auth_headers(client, "client@example.com", "client123")

    response = client.get("/api/counselor/clients", headers=headers)

    assert response.status_code == 403


def register_user(client, role: str) -> tuple[str, dict[str, str], int]:
    email = f"{role}-{uuid.uuid4().hex[:8]}@example.com"
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "client123",
            "role": role,
            "display_name": f"测试{role}",
        },
    )
    assert response.status_code == 201
    user_id = response.json()["id"]
    return email, auth_headers(client, email, "client123"), user_id


def test_counselor_binding_lifecycle_and_authorized_counselors(client):
    client_email, client_headers, client_id = register_user(client, "client")
    _, counselor_headers, _ = register_user(client, "counselor")

    before_history = client.get(f"/api/counselor/users/{client_id}/history", headers=counselor_headers)
    assert before_history.status_code == 404

    create_response = client.post(
        "/api/counselor/bindings",
        headers=counselor_headers,
        json={"client_email": client_email},
    )
    assert create_response.status_code == 200
    assert create_response.json()["created"] is True
    assert create_response.json()["client"]["email"] == client_email

    history_response = client.get(f"/api/counselor/users/{client_id}/history", headers=counselor_headers)
    assert history_response.status_code == 200
    assert history_response.json()["email"] == client_email

    counselors_response = client.get("/api/me/counselors", headers=client_headers)
    assert counselors_response.status_code == 200
    assert len(counselors_response.json()) == 1

    delete_response = client.delete(f"/api/counselor/bindings/{client_id}", headers=counselor_headers)
    assert delete_response.status_code == 204

    after_history = client.get(f"/api/counselor/users/{client_id}/history", headers=counselor_headers)
    assert after_history.status_code == 404


def test_counselor_notes_and_empty_trend_require_binding(client):
    client_email, _, client_id = register_user(client, "client")
    _, counselor_headers, _ = register_user(client, "counselor")

    bind_response = client.post(
        "/api/counselor/bindings",
        headers=counselor_headers,
        json={"client_email": client_email},
    )
    assert bind_response.status_code == 200

    note_response = client.post(
        f"/api/counselor/users/{client_id}/notes",
        headers=counselor_headers,
        json={"content": "下次咨询优先核实睡眠和近期压力源。"},
    )
    assert note_response.status_code == 200
    assert note_response.json()["client_id"] == client_id

    notes_response = client.get(f"/api/counselor/users/{client_id}/notes", headers=counselor_headers)
    assert notes_response.status_code == 200
    assert len(notes_response.json()) == 1

    trend_response = client.get(f"/api/counselor/users/{client_id}/trend", headers=counselor_headers)
    assert trend_response.status_code == 200
    assert trend_response.json() == {"user_id": client_id, "points": []}
