from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="SenseVoice Service",
    description="语音转写和语音情绪分析服务占位实现",
    version="0.1.0",
)


class AnalyzeRequest(BaseModel):
    task_id: str
    audio_path: str | None = None
    duration_seconds: float = 0


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(request: AnalyzeRequest) -> dict:
    speech_detected = bool(request.audio_path)
    return {
        "task_id": request.task_id,
        "speech_detected": speech_detected,
        "transcript": "占位转写文本：当前服务接口已跑通，后续替换为真实 SenseVoice 输出。",
        "pitch_summary": "基频整体平稳",
        "speech_rate": "语速中等",
        "clarity": "清晰度中等" if speech_detected else "未检测到可用音频",
        "semantic_emotion": "neutral",
        "duration_seconds": request.duration_seconds,
    }

