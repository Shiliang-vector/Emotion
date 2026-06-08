from typing import Any

from pydantic import BaseModel, Field


class VideoSummary(BaseModel):
    duration_seconds: float
    detected_faces: int
    speech_detected: bool
    frame_count: int = 0
    analyzed_frames: int = 0
    skipped_frames: int = 0
    processing_notes: list[str] = Field(default_factory=list)


class FaceEmotion(BaseModel):
    dominant: str
    probabilities: dict[str, float]
    duration_ratio: dict[str, float]
    analyzed_frames: int = 0
    skipped_frames: int = 0


class SpeechFeatures(BaseModel):
    transcript: str
    pitch_summary: str
    speech_rate: str
    clarity: str
    semantic_emotion: str
    duration_seconds: float = 0
    tags: list[str] = Field(default_factory=list)
    acoustic: dict[str, Any] = Field(default_factory=dict)
    processing_notes: list[str] = Field(default_factory=list)


class FinalPrediction(BaseModel):
    emotion: str
    confidence: float
    risk_level: str
    evidence: list[str]


class Report(BaseModel):
    task_id: str
    video_summary: VideoSummary
    face_emotion: FaceEmotion
    speech_features: SpeechFeatures
    final_prediction: FinalPrediction
    expert_advice: str
