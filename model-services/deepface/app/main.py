from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="DeepFace Service",
    description="人脸识别和表情分析服务占位实现",
    version="0.1.0",
)


class AnalyzeRequest(BaseModel):
    task_id: str
    frames_dir: str
    frame_count: int = 0


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(request: AnalyzeRequest) -> dict:
    frame_count = max(request.frame_count, 1)
    neutral = 0.65 if request.frame_count else 0.8
    happy = 0.2 if request.frame_count else 0.1
    sad = 0.1
    angry = round(max(0.0, 1.0 - neutral - happy - sad), 2)

    return {
        "task_id": request.task_id,
        "detected_faces": 1 if request.frame_count else 0,
        "dominant": "neutral",
        "probabilities": {
            "happy": happy,
            "sad": sad,
            "angry": angry,
            "neutral": neutral,
        },
        "duration_ratio": {
            "happy": round(happy * frame_count / frame_count, 2),
            "sad": round(sad * frame_count / frame_count, 2),
            "angry": angry,
            "neutral": neutral,
        },
    }

