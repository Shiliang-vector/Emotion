from pathlib import Path

import httpx

from app.core.config import settings


class FaceService:
    async def analyze(self, task_id: str, frames_dir: Path, frame_count: int) -> dict:
        payload = {
            "task_id": task_id,
            "frames_dir": str(frames_dir),
            "frame_count": frame_count,
        }
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(f"{settings.deepface_url}/analyze", json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            return {
                "detected_faces": 0,
                "dominant": "unknown",
                "probabilities": {"unknown": 1.0},
                "duration_ratio": {"unknown": 1.0},
                "error": f"DeepFace 服务调用失败: {exc}",
            }


face_service = FaceService()

