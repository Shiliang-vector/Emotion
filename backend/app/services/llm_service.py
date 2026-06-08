import httpx

from app.core.config import settings
from app.schemas.report import FaceEmotion, FinalPrediction, SpeechFeatures, VideoSummary


class LlmService:
    async def generate_advice(
        self,
        video_summary: VideoSummary,
        face_emotion: FaceEmotion,
        speech_features: SpeechFeatures,
        final_prediction: FinalPrediction,
    ) -> str:
        if not settings.openai_api_key:
            return self._fallback_advice(final_prediction)

        prompt = self._build_prompt(video_summary, face_emotion, speech_features, final_prediction)
        payload = {
            "model": settings.openai_model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是心理咨询和人机交互场景中的情绪分析助手。请基于结构化特征给出审慎、非诊断性的专家建议。",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
        }
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{settings.openai_base_url.rstrip('/')}/chat/completions",
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            return f"{self._fallback_advice(final_prediction)}\n\nLLM 调用失败：{exc}"

    def _build_prompt(
        self,
        video_summary: VideoSummary,
        face_emotion: FaceEmotion,
        speech_features: SpeechFeatures,
        final_prediction: FinalPrediction,
    ) -> str:
        return (
            "请根据以下交流视频分析结果，给出简洁专家意见，包含情绪判断依据、沟通建议和风险提示。\n"
            f"视频摘要：{video_summary.model_dump()}\n"
            f"人脸表情：{face_emotion.model_dump()}\n"
            f"语音特征：{speech_features.model_dump()}\n"
            f"综合预测：{final_prediction.model_dump()}\n"
        )

    def _fallback_advice(self, final_prediction: FinalPrediction) -> str:
        return (
            f"系统初步判断当前主要情绪为 {final_prediction.emotion}，"
            f"置信度为 {final_prediction.confidence}，风险等级为 {final_prediction.risk_level}。"
            "建议结合实际交流背景复核，不应仅凭自动分析结果作出医学或心理诊断。"
        )


llm_service = LlmService()

