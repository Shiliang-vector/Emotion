from pathlib import Path

import httpx

from app.core.config import settings


class SpeechService:
    async def analyze(self, task_id: str, audio_path: Path | None, duration_seconds: float) -> dict:
        payload = {
            "task_id": task_id,
            "audio_path": str(audio_path) if audio_path else None,
            "duration_seconds": duration_seconds,
        }
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(f"{settings.sensevoice_url}/analyze", json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            return {
                "speech_detected": False,
                "transcript": "",
                "pitch_summary": "unknown",
                "speech_rate": "unknown",
                "clarity": "unknown",
                "semantic_emotion": "unknown",
                "error": f"SenseVoice 服务调用失败: {exc}",
            }


speech_service = SpeechService()

