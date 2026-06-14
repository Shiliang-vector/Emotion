import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

test_db_path = Path("storage/test_emotion.db")
if test_db_path.exists():
    test_db_path.unlink()
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{test_db_path.as_posix()}"
os.environ["AUTH_SECRET_KEY"] = "test-secret-for-fastapi-users-jwt-32"

from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.task import AnalysisTask, ReportRecord, User
from app.schemas.report import FaceEmotion, FinalPrediction, Report, SpeechFeatures, VideoSummary


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


def create_completed_task_for_user(email: str) -> str:
    async def _create() -> str:
        async with AsyncSessionLocal() as db:
            user = await db.scalar(select(User).where(User.email == email))
            assert user is not None
            task_id = f"test-{uuid.uuid4().hex[:10]}"
            now = datetime.utcnow()
            report = Report(
                task_id=task_id,
                video_summary=VideoSummary(
                    duration_seconds=18.0,
                    detected_faces=1,
                    speech_detected=True,
                    frame_count=12,
                    analyzed_frames=10,
                    skipped_frames=2,
                    processing_notes=["测试生成的模拟报告，不包含真实隐私视频"],
                ),
                face_emotion=FaceEmotion(
                    dominant="sad",
                    probabilities={"sad": 0.62, "neutral": 0.28, "happy": 0.1},
                    duration_ratio={"sad": 0.58, "neutral": 0.32, "happy": 0.1},
                    analyzed_frames=10,
                    skipped_frames=2,
                ),
                speech_features=SpeechFeatures(
                    transcript="最近压力比较大，睡眠也不太稳定。",
                    pitch_summary="基频略低，波动较小",
                    speech_rate="语速偏慢",
                    clarity="语音清晰",
                    semantic_emotion="sad",
                    duration_seconds=18.0,
                    tags=["压力", "睡眠"],
                    acoustic={"rms": 0.05, "voiced_ratio": 0.62},
                ),
                final_prediction=FinalPrediction(
                    emotion="sad",
                    confidence=0.74,
                    risk_level="medium",
                    evidence=["面部悲伤概率较高", "语音内容提到压力和睡眠"],
                ),
                expert_advice="建议记录近期压力源和睡眠变化，必要时寻求专业支持。",
                model_name="test-model",
                prompt_version="v1",
                generated_at=now.isoformat(),
            )
            task = AnalysisTask(
                task_id=task_id,
                user_id=user.id,
                status="completed",
                stage="completed",
                progress=100,
                message="测试报告已生成",
                video_path=f"storage/uploads/{task_id}.mp4",
                created_at=now,
                updated_at=now,
            )
            record = ReportRecord(
                task_id=task_id,
                report_json=json.dumps(report.model_dump(), ensure_ascii=False),
                expert_advice=report.expert_advice,
                model_name=report.model_name,
                prompt_version=report.prompt_version,
                created_at=now,
            )
            db.add(task)
            db.add(record)
            await db.commit()
            return task_id

    return asyncio.run(_create())


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


def test_client_can_delete_own_completed_task_and_report(client):
    email, headers, _ = register_user(client, "client")
    task_id = create_completed_task_for_user(email)

    report_before = client.get(f"/api/reports/{task_id}", headers=headers)
    assert report_before.status_code == 200

    delete_response = client.delete(f"/api/me/tasks/{task_id}", headers=headers)
    assert delete_response.status_code == 204

    report_after = client.get(f"/api/reports/{task_id}", headers=headers)
    assert report_after.status_code == 404


def test_counselor_cannot_delete_client_task(client):
    client_email, _, _ = register_user(client, "client")
    _, counselor_headers, _ = register_user(client, "counselor")
    task_id = create_completed_task_for_user(client_email)

    response = client.delete(f"/api/me/tasks/{task_id}", headers=counselor_headers)

    assert response.status_code == 403


def test_report_export_denies_unowned_task(client):
    owner_email, _, _ = register_user(client, "client")
    _, other_headers, _ = register_user(client, "client")
    task_id = create_completed_task_for_user(owner_email)

    response = client.get(f"/api/reports/{task_id}/export?format=json", headers=other_headers)

    assert response.status_code == 403
