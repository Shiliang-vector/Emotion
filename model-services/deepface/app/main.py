from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="DeepFace Service",
    description="基于 DeepFace 的人脸检测和表情分析服务",
    version="0.1.0",
)

EMOTIONS = ("angry", "disgust", "fear", "happy", "sad", "surprise", "neutral")


class AnalyzeRequest(BaseModel):
    task_id: str
    frames_dir: str
    frame_count: int = 0
    detector_backend: str = "opencv"
    enforce_detection: bool = True


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
def analyze(request: AnalyzeRequest) -> dict:
    frame_paths = _frame_paths(Path(request.frames_dir))
    if not frame_paths:
        return _empty_result(request.task_id, "未找到可分析的视频帧")

    from deepface import DeepFace

    probability_sum = {emotion: 0.0 for emotion in EMOTIONS}
    duration_counts = {emotion: 0 for emotion in EMOTIONS}
    analyzed_frames = 0
    skipped_frames = 0
    max_faces = 0
    frame_results: list[dict] = []

    for frame_path in frame_paths:
        try:
            raw_result = DeepFace.analyze(
                img_path=str(frame_path),
                actions=["emotion"],
                detector_backend=request.detector_backend,
                enforce_detection=request.enforce_detection,
                silent=True,
            )
        except Exception as exc:
            skipped_frames += 1
            frame_results.append(
                {
                    "frame": frame_path.name,
                    "status": "failed",
                    "error": str(exc),
                }
            )
            continue

        faces = raw_result if isinstance(raw_result, list) else [raw_result]
        faces = [face for face in faces if isinstance(face, dict)]
        if not faces:
            skipped_frames += 1
            frame_results.append({"frame": frame_path.name, "status": "no_face"})
            continue

        max_faces = max(max_faces, len(faces))
        face = _select_primary_face(faces)
        emotions = _normalize_emotions(face.get("emotion", {}))
        dominant = _dominant_emotion(face, emotions)

        analyzed_frames += 1
        duration_counts[dominant] = duration_counts.get(dominant, 0) + 1
        for emotion, value in emotions.items():
            probability_sum[emotion] = probability_sum.get(emotion, 0.0) + value

        region = face.get("region") or face.get("facial_area") or {}
        frame_results.append(
            {
                "frame": frame_path.name,
                "status": "ok",
                "dominant": dominant,
                "face_count": len(faces),
                "region": region,
            }
        )

    if analyzed_frames == 0:
        result = _empty_result(request.task_id, "DeepFace 未在抽帧中得到有效人脸结果")
        result["skipped_frames"] = skipped_frames
        result["frame_results"] = frame_results
        return result

    probabilities = {
        emotion: round(probability_sum.get(emotion, 0.0) / analyzed_frames, 4)
        for emotion in EMOTIONS
    }
    duration_ratio = {
        emotion: round(duration_counts.get(emotion, 0) / analyzed_frames, 4)
        for emotion in EMOTIONS
    }
    dominant = max(duration_ratio, key=duration_ratio.get)

    return {
        "task_id": request.task_id,
        "detected_faces": max_faces,
        "dominant": dominant,
        "probabilities": probabilities,
        "duration_ratio": duration_ratio,
        "analyzed_frames": analyzed_frames,
        "skipped_frames": skipped_frames,
        "frame_results": frame_results,
    }


def _frame_paths(frames_dir: Path) -> list[Path]:
    if not frames_dir.exists() or not frames_dir.is_dir():
        return []
    return sorted(
        path
        for path in frames_dir.iterdir()
        if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    )


def _select_primary_face(faces: list[dict]) -> dict:
    def area(face: dict) -> int:
        region = face.get("region") or face.get("facial_area") or {}
        return int(region.get("w", 0) or 0) * int(region.get("h", 0) or 0)

    return max(faces, key=area)


def _normalize_emotions(raw_emotions: dict) -> dict[str, float]:
    values = {emotion: float(raw_emotions.get(emotion, 0.0) or 0.0) for emotion in EMOTIONS}
    total = sum(values.values())
    if total <= 0:
        return {emotion: 0.0 for emotion in EMOTIONS}
    return {emotion: values[emotion] / total for emotion in EMOTIONS}


def _dominant_emotion(face: dict, emotions: dict[str, float]) -> str:
    dominant = str(face.get("dominant_emotion") or "").lower()
    if dominant in emotions:
        return dominant
    return max(emotions, key=emotions.get)


def _empty_result(task_id: str, note: str) -> dict:
    return {
        "task_id": task_id,
        "detected_faces": 0,
        "dominant": "unknown",
        "probabilities": {"unknown": 1.0},
        "duration_ratio": {"unknown": 1.0},
        "analyzed_frames": 0,
        "skipped_frames": 0,
        "processing_notes": [note],
    }
