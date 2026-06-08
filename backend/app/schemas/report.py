from pydantic import BaseModel, Field


class VideoSummary(BaseModel):
    duration_seconds: float
    detected_faces: int
    speech_detected: bool
    processing_notes: list[str] = Field(default_factory=list)


class FaceEmotion(BaseModel):
    dominant: str
    probabilities: dict[str, float]
    duration_ratio: dict[str, float]


class SpeechFeatures(BaseModel):
    transcript: str
    pitch_summary: str
    speech_rate: str
    clarity: str
    semantic_emotion: str


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

