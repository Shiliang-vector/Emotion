from app.schemas.report import FaceEmotion, SpeechFeatures
from app.services.fusion_service import fusion_service


def test_predict_combines_face_and_speech_features():
    face_emotion = FaceEmotion(
        dominant="sad",
        probabilities={"sad": 0.7, "neutral": 0.3},
        duration_ratio={"sad": 0.6, "neutral": 0.4},
    )
    speech_features = SpeechFeatures(
        transcript="最近压力比较大",
        pitch_summary="基频偏低",
        speech_rate="语速偏慢",
        clarity="清晰度中等",
        semantic_emotion="sad",
    )

    result = fusion_service.predict(face_emotion, speech_features)

    assert result.emotion == "sad"
    assert result.confidence >= 0.65
    assert result.risk_level == "high"
    assert result.evidence

