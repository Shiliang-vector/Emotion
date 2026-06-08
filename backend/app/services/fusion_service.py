from app.schemas.report import FaceEmotion, FinalPrediction, SpeechFeatures, VideoSummary


class FusionService:
    def build_video_summary(
        self,
        duration_seconds: float,
        face_result: dict,
        speech_result: dict,
        notes: list[str],
    ) -> VideoSummary:
        extra_notes = list(notes)
        for result in (face_result, speech_result):
            if result.get("error"):
                extra_notes.append(result["error"])

        return VideoSummary(
            duration_seconds=duration_seconds,
            detected_faces=int(face_result.get("detected_faces", 0)),
            speech_detected=bool(speech_result.get("speech_detected", False)),
            processing_notes=extra_notes,
        )

    def build_face_emotion(self, face_result: dict) -> FaceEmotion:
        return FaceEmotion(
            dominant=face_result.get("dominant", "unknown"),
            probabilities=face_result.get("probabilities", {"unknown": 1.0}),
            duration_ratio=face_result.get("duration_ratio", {"unknown": 1.0}),
        )

    def build_speech_features(self, speech_result: dict) -> SpeechFeatures:
        return SpeechFeatures(
            transcript=speech_result.get("transcript", ""),
            pitch_summary=speech_result.get("pitch_summary", "unknown"),
            speech_rate=speech_result.get("speech_rate", "unknown"),
            clarity=speech_result.get("clarity", "unknown"),
            semantic_emotion=speech_result.get("semantic_emotion", "unknown"),
        )

    def predict(self, face_emotion: FaceEmotion, speech_features: SpeechFeatures) -> FinalPrediction:
        scores: dict[str, float] = {}
        for emotion, probability in face_emotion.probabilities.items():
            scores[emotion] = scores.get(emotion, 0.0) + probability * 0.5
        for emotion, ratio in face_emotion.duration_ratio.items():
            scores[emotion] = scores.get(emotion, 0.0) + ratio * 0.2

        semantic_emotion = speech_features.semantic_emotion or "unknown"
        if semantic_emotion != "unknown":
            scores[semantic_emotion] = scores.get(semantic_emotion, 0.0) + 0.3

        emotion = max(scores, key=scores.get) if scores else "unknown"
        confidence = round(min(scores.get(emotion, 0.0), 1.0), 2)
        risk_level = self._risk_level(emotion, confidence)
        evidence = [
            f"视觉主导情绪为 {face_emotion.dominant}",
            f"语义情绪为 {semantic_emotion}",
            f"语速特征为 {speech_features.speech_rate}",
            f"清晰度为 {speech_features.clarity}",
        ]
        return FinalPrediction(
            emotion=emotion,
            confidence=confidence,
            risk_level=risk_level,
            evidence=evidence,
        )

    def _risk_level(self, emotion: str, confidence: float) -> str:
        if emotion in {"angry", "fear", "sad"} and confidence >= 0.65:
            return "high"
        if emotion in {"angry", "fear", "sad"} or confidence < 0.45:
            return "medium"
        return "low"


fusion_service = FusionService()

