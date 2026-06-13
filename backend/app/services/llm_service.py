import httpx

from app.core.config import settings
from app.schemas.report import FaceEmotion, FinalPrediction, Report, SpeechFeatures, VideoSummary


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

    async def generate_counselor_assistance(self, reports: list[Report]) -> str:
        if not reports:
            return "暂无可用分析历史，建议先完成至少一次视频分析后再生成辅助建议。"

        latest = reports[-1]
        if not settings.openai_api_key:
            return self._fallback_counselor_assistance(latest, len(reports))

        history = [
            {
                "task_id": report.task_id,
                "prediction": report.final_prediction.model_dump(),
                "speech": {
                    "semantic_emotion": report.speech_features.semantic_emotion,
                    "speech_rate": report.speech_features.speech_rate,
                    "clarity": report.speech_features.clarity,
                },
                "expert_advice": report.expert_advice,
            }
            for report in reports[-5:]
        ]
        payload = {
            "model": settings.openai_model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是心理咨询师的辅助分析系统。输出只供专业人员参考，不能替代诊断或治疗。",
                },
                {
                    "role": "user",
                    "content": (
                        "请基于该用户最近的多模态情绪分析历史，生成给心理咨询师的辅助工作草稿。"
                        "包含：需要优先核实的线索、沟通切入点、风险提醒、下一次咨询可观察事项。"
                        f"分析历史：{history}"
                    ),
                },
            ],
            "temperature": 0.2,
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
            return f"{self._fallback_counselor_assistance(latest, len(reports))}\n\nLLM 调用失败：{exc}"

    def _fallback_counselor_assistance(self, latest: Report, report_count: int) -> str:
        prediction = latest.final_prediction
        return (
            "仅供专业人员参考，不能替代诊断或治疗。\n"
            f"该用户已有 {report_count} 次系统分析记录。最近一次主要情绪为 {prediction.emotion}，"
            f"置信度 {prediction.confidence}，风险等级 {prediction.risk_level}。"
            "建议咨询师先核实视频场景、近期压力源、睡眠和社交支持情况，再结合访谈判断是否需要进一步干预。"
        )


llm_service = LlmService()
