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


class TaskOut(BaseModel):
    task_id: str
    status: str
    stage: str
    progress: int
    message: str
    error: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    report_url: str | None = None
    user_id: int | None = None
    dominant_emotion: str | None = None
    risk_level: str | None = None
    confidence: float | None = None
    counselor_assistance: str | None = None
    counselor_assistance_created_at: str | None = None


class ClientHistoryOut(BaseModel):
    user_id: int
    email: str
    display_name: str | None = None
    tasks: list[TaskOut] = Field(default_factory=list)


class CounselorClientOut(BaseModel):
    id: int
    email: str
    display_name: str | None = None
    task_count: int = 0
    latest_emotion: str | None = None
    latest_risk_level: str | None = None
    latest_task_at: str | None = None


class CounselorOut(BaseModel):
    id: int
    email: str
    display_name: str | None = None
    created_at: str | None = None


class BindingCreate(BaseModel):
    client_email: str


class BindingOut(BaseModel):
    client: CounselorClientOut
    created: bool = False


class AssistanceDraftOut(BaseModel):
    user_id: int
    assistance: str
    generated_at: str | None = None


class NoteCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class NoteOut(BaseModel):
    id: int
    counselor_id: int
    client_id: int
    content: str
    created_at: str


class TrendPointOut(BaseModel):
    task_id: str
    created_at: str | None = None
    emotion: str | None = None
    risk_level: str | None = None
    confidence: float | None = None


class TrendOut(BaseModel):
    user_id: int
    points: list[TrendPointOut] = Field(default_factory=list)
