from app.schemas.report import FaceEmotion, FinalPrediction, SpeechFeatures, VideoSummary


class FusionService:
    base_weights = {
        "face_probability": 0.5,
        "face_duration": 0.2,
        "speech_semantic": 0.3,
    }

    def build_video_summary(
        self,
        duration_seconds: float,
        face_result: dict,
        speech_result: dict,
        notes: list[str],
        frame_count: int = 0,
    ) -> VideoSummary:
        extra_notes = list(notes)
        for result in (face_result, speech_result):
            if result.get("error"):
                extra_notes.append(result["error"])
            extra_notes.extend(result.get("processing_notes", []))

        return VideoSummary(
            duration_seconds=duration_seconds,
            detected_faces=int(face_result.get("detected_faces", 0)),
            speech_detected=bool(speech_result.get("speech_detected", False)),
            frame_count=frame_count,
            analyzed_frames=int(face_result.get("analyzed_frames", 0)),
            skipped_frames=int(face_result.get("skipped_frames", 0)),
            processing_notes=extra_notes,
        )

    def build_face_emotion(self, face_result: dict) -> FaceEmotion:
        return FaceEmotion(
            dominant=face_result.get("dominant", "unknown"),
            probabilities=face_result.get("probabilities", {"unknown": 1.0}),
            duration_ratio=face_result.get("duration_ratio", {"unknown": 1.0}),
            analyzed_frames=int(face_result.get("analyzed_frames", 0)),
            skipped_frames=int(face_result.get("skipped_frames", 0)),
        )

    def build_speech_features(self, speech_result: dict) -> SpeechFeatures:
        return SpeechFeatures(
            transcript=speech_result.get("transcript", ""),
            pitch_summary=speech_result.get("pitch_summary", "unknown"),
            speech_rate=speech_result.get("speech_rate", "unknown"),
            clarity=speech_result.get("clarity", "unknown"),
            semantic_emotion=speech_result.get("semantic_emotion", "unknown"),
            duration_seconds=float(speech_result.get("duration_seconds", 0) or 0),
            tags=speech_result.get("tags", []),
            acoustic=speech_result.get("acoustic", {}),
            processing_notes=speech_result.get("processing_notes", []),
        )

    def predict(self, face_emotion: FaceEmotion, speech_features: SpeechFeatures) -> FinalPrediction:
        scores: dict[str, float] = {}
        weights = self._dynamic_weights(face_emotion, speech_features)

        for emotion, probability in self._valid_distribution(face_emotion.probabilities).items():
            scores[emotion] = scores.get(emotion, 0.0) + probability * weights["face_probability"]
        for emotion, ratio in self._valid_distribution(face_emotion.duration_ratio).items():
            scores[emotion] = scores.get(emotion, 0.0) + ratio * weights["face_duration"]

        semantic_emotion = speech_features.semantic_emotion or "unknown"
        if semantic_emotion != "unknown":
            scores[semantic_emotion] = scores.get(semantic_emotion, 0.0) + weights["speech_semantic"]

        emotion = max(scores, key=scores.get) if scores else "unknown"
        confidence = round(min(scores.get(emotion, 0.0), 1.0), 2)
        risk_level = self._risk_level(emotion, confidence)
        evidence = [
            f"视觉主导情绪为 {face_emotion.dominant}",
            f"语义情绪为 {semantic_emotion}",
            f"语速特征为 {speech_features.speech_rate}",
            f"清晰度为 {speech_features.clarity}",
            (
                "动态权重为 "
                f"表情概率 {weights['face_probability']:.2f}、"
                f"表情持续 {weights['face_duration']:.2f}、"
                f"语义情绪 {weights['speech_semantic']:.2f}"
            ),
        ]
        return FinalPrediction(
            emotion=emotion,
            confidence=confidence,
            risk_level=risk_level,
            evidence=evidence,
        )

    def _dynamic_weights(self, face_emotion: FaceEmotion, speech_features: SpeechFeatures) -> dict[str, float]:
        face_quality = self._face_quality(face_emotion)
        semantic_quality = self._semantic_quality(speech_features)
        raw_weights = {
            "face_probability": self.base_weights["face_probability"]
            * face_quality
            * self._distribution_quality(face_emotion.probabilities),
            "face_duration": self.base_weights["face_duration"]
            * face_quality
            * self._distribution_quality(face_emotion.duration_ratio),
            "speech_semantic": self.base_weights["speech_semantic"] * semantic_quality,
        }
        total = sum(raw_weights.values())
        if total <= 0:
            return {key: 0.0 for key in self.base_weights}
        return {key: value / total for key, value in raw_weights.items()}

    def _face_quality(self, face_emotion: FaceEmotion) -> float:
        probabilities = self._valid_distribution(face_emotion.probabilities)
        if not probabilities:
            return 0.0

        analyzed_frames = max(face_emotion.analyzed_frames, 0)
        skipped_frames = max(face_emotion.skipped_frames, 0)
        total_frames = analyzed_frames + skipped_frames
        if analyzed_frames <= 0 and total_frames > 0:
            return 0.0
        frame_quality = analyzed_frames / total_frames if total_frames else 1.0

        concentration = max(probabilities.values())
        dominance_quality = 0.6 + 0.4 * concentration
        if face_emotion.dominant == "unknown":
            dominance_quality *= 0.5
        return self._clamp(frame_quality * dominance_quality)

    def _semantic_quality(self, speech_features: SpeechFeatures) -> float:
        semantic_emotion = speech_features.semantic_emotion or "unknown"
        if semantic_emotion == "unknown":
            return 0.0

        quality = 1.0
        transcript = speech_features.transcript.strip()
        if not transcript:
            quality *= 0.55
        elif len(transcript) < 4:
            quality *= 0.75

        duration = speech_features.duration_seconds
        if duration <= 0:
            quality *= 0.75
        elif duration < 1:
            quality *= 0.5
        elif duration < 3:
            quality *= 0.75

        clarity = speech_features.clarity
        if clarity in {"unknown", "语速无法估计"}:
            quality *= 0.5
        elif any(marker in clarity for marker in ("无有效语音", "音量偏低")):
            quality *= 0.25
        elif any(marker in clarity for marker in ("偏弱", "发声比例偏低", "削波失真")):
            quality *= 0.55

        speech_detected = speech_features.acoustic.get("speech_detected")
        if speech_detected is False:
            quality *= 0.35

        if "无法估计" in speech_features.speech_rate:
            quality *= 0.75

        return self._clamp(quality)

    def _distribution_quality(self, values: dict[str, float]) -> float:
        return 1.0 if self._valid_distribution(values) else 0.0

    def _valid_distribution(self, values: dict[str, float]) -> dict[str, float]:
        return {
            emotion: self._clamp(float(value or 0.0))
            for emotion, value in values.items()
            if emotion != "unknown" and float(value or 0.0) > 0
        }

    def _clamp(self, value: float) -> float:
        return max(0.0, min(value, 1.0))

    def _risk_level(self, emotion: str, confidence: float) -> str:
        if emotion in {"angry", "fear", "sad"} and confidence >= 0.65:
            return "high"
        if emotion in {"angry", "fear", "sad"} or confidence < 0.45:
            return "medium"
        return "low"


fusion_service = FusionService()
