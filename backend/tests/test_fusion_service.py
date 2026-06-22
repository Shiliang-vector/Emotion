from app.schemas.report import FaceEmotion, SpeechFeatures
from app.services.fusion_service import fusion_service


def test_predict_combines_face_and_speech_features():
    face_emotion = FaceEmotion(
        dominant="sad",
        probabilities={"sad": 0.7, "neutral": 0.3},
        duration_ratio={"sad": 0.6, "neutral": 0.4},
        analyzed_frames=10,
        skipped_frames=0,
    )
    speech_features = SpeechFeatures(
        transcript="最近压力比较大",
        pitch_summary="基频偏低",
        speech_rate="语速偏慢",
        clarity="清晰度中等",
        semantic_emotion="sad",
        duration_seconds=6,
        acoustic={"speech_detected": True},
    )

    result = fusion_service.predict(face_emotion, speech_features)

    assert result.emotion == "sad"
    assert result.confidence >= 0.65
    assert result.risk_level == "high"
    assert result.evidence
    assert any("动态权重" in item for item in result.evidence)


def test_predict_renormalizes_to_face_when_speech_is_unavailable():
    face_emotion = FaceEmotion(
        dominant="neutral",
        probabilities={"neutral": 0.8, "sad": 0.2},
        duration_ratio={"neutral": 0.7, "sad": 0.3},
        analyzed_frames=8,
        skipped_frames=0,
    )
    speech_features = SpeechFeatures(
        transcript="",
        pitch_summary="unknown",
        speech_rate="语速无法估计",
        clarity="unknown",
        semantic_emotion="unknown",
        acoustic={"speech_detected": False},
    )

    result = fusion_service.predict(face_emotion, speech_features)

    assert result.emotion == "neutral"
    assert result.confidence >= 0.7
    assert result.risk_level == "low"


def test_predict_downweights_low_quality_face_signal():
    face_emotion = FaceEmotion(
        dominant="happy",
        probabilities={"happy": 0.9, "sad": 0.1},
        duration_ratio={"happy": 0.9, "sad": 0.1},
        analyzed_frames=1,
        skipped_frames=9,
    )
    speech_features = SpeechFeatures(
        transcript="最近真的很难过",
        pitch_summary="基频偏低",
        speech_rate="语速偏慢",
        clarity="清晰度中等",
        semantic_emotion="sad",
        duration_seconds=5,
        acoustic={"speech_detected": True},
    )

    result = fusion_service.predict(face_emotion, speech_features)

    assert result.emotion == "sad"
    assert result.confidence >= 0.65
    assert result.risk_level == "high"


def test_predict_returns_unknown_when_all_modalities_are_unavailable():
    face_emotion = FaceEmotion(
        dominant="unknown",
        probabilities={"unknown": 1.0},
        duration_ratio={"unknown": 1.0},
        analyzed_frames=0,
        skipped_frames=5,
    )
    speech_features = SpeechFeatures(
        transcript="",
        pitch_summary="unknown",
        speech_rate="语速无法估计",
        clarity="unknown",
        semantic_emotion="unknown",
        acoustic={"speech_detected": False},
    )

    result = fusion_service.predict(face_emotion, speech_features)

    assert result.emotion == "unknown"
    assert result.confidence == 0
    assert result.risk_level == "medium"
