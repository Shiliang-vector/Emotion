import asyncio
import json
from datetime import datetime, timedelta

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.task import AnalysisTask, ConsultationBinding, CounselorNote, ReportRecord, User
from app.schemas.report import FaceEmotion, FinalPrediction, Report, SpeechFeatures, VideoSummary
from app.services.auth_service import auth_service


DEMO_TASKS = [
    {
        "task_id": "demo-course-001-calm",
        "days_ago": 12,
        "emotion": "neutral",
        "risk": "low",
        "confidence": 0.68,
        "transcript": "最近整体还可以，偶尔会因为课程任务比较紧张。",
        "advice": "目前整体情绪较稳定。建议继续保持规律作息，记录压力来源，并在压力升高时主动寻求同伴或老师支持。",
        "evidence": ["面部表情以中性为主", "语音内容提到轻度课程压力", "声学特征整体平稳"],
        "face": {"neutral": 0.62, "happy": 0.18, "sad": 0.12, "fear": 0.08},
    },
    {
        "task_id": "demo-course-002-stress",
        "days_ago": 6,
        "emotion": "sad",
        "risk": "medium",
        "confidence": 0.76,
        "transcript": "最近项目截止时间比较近，睡眠变少，感觉有点疲惫。",
        "advice": "系统观察到压力和睡眠相关线索。建议优先梳理近期压力源，安排短期可完成任务，并在持续影响生活时寻求专业支持。",
        "evidence": ["悲伤表情比例升高", "语音内容提到睡眠减少", "语速偏慢且能量偏低"],
        "face": {"sad": 0.58, "neutral": 0.3, "fear": 0.08, "happy": 0.04},
    },
    {
        "task_id": "demo-course-003-recovery",
        "days_ago": 1,
        "emotion": "neutral",
        "risk": "low",
        "confidence": 0.72,
        "transcript": "这两天把任务拆开后轻松了一些，也开始按时休息。",
        "advice": "近期状态较前一次有所缓和。建议继续保持任务拆分和睡眠记录，咨询师可进一步了解哪些支持方式最有效。",
        "evidence": ["中性表情占比回升", "语音内容出现积极调节策略", "风险线索较前次减少"],
        "face": {"neutral": 0.57, "happy": 0.22, "sad": 0.16, "fear": 0.05},
    },
]


async def seed_demo_data() -> None:
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    settings.audio_dir.mkdir(parents=True, exist_ok=True)
    settings.frames_dir.mkdir(parents=True, exist_ok=True)

    async with AsyncSessionLocal() as db:
        await auth_service.seed_demo_users(db)
        client = await db.scalar(select(User).where(User.email == "client@example.com"))
        counselor = await db.scalar(select(User).where(User.email == "counselor@example.com"))
        if not client or not counselor:
            raise RuntimeError("演示账号不存在，无法生成演示样例数据")

        binding = await db.scalar(
            select(ConsultationBinding).where(
                ConsultationBinding.client_id == client.id,
                ConsultationBinding.counselor_id == counselor.id,
            )
        )
        if not binding:
            db.add(ConsultationBinding(client_id=client.id, counselor_id=counselor.id))

        now = datetime.utcnow()
        for item in DEMO_TASKS:
            created_at = now - timedelta(days=item["days_ago"])
            video_path = settings.uploads_dir / f"{item['task_id']}.mp4"
            if not video_path.exists():
                video_path.write_text("demo placeholder, not a real private video\n", encoding="utf-8")

            report = _build_report(item, created_at)
            task = AnalysisTask(
                task_id=item["task_id"],
                user_id=client.id,
                status="completed",
                stage="completed",
                progress=100,
                message="演示样例报告已生成",
                error=None,
                video_path=str(video_path),
                created_at=created_at,
                updated_at=created_at,
            )
            record = ReportRecord(
                task_id=item["task_id"],
                report_json=json.dumps(report.model_dump(), ensure_ascii=False),
                expert_advice=report.expert_advice,
                counselor_assistance=(
                    "仅供专业人员参考：该用户样例呈现从课程压力升高到逐步恢复的变化。建议咨询师围绕睡眠、任务拆分、"
                    "可用支持资源和压力源识别进行访谈，并持续观察风险线索。"
                    if item["task_id"] == "demo-course-003-recovery"
                    else None
                ),
                counselor_assistance_created_at=now if item["task_id"] == "demo-course-003-recovery" else None,
                model_name=report.model_name,
                prompt_version=report.prompt_version,
                created_at=created_at,
            )
            await db.merge(task)
            await db.merge(record)
            report_path = settings.reports_dir / f"{item['task_id']}.json"
            report_path.write_text(json.dumps(report.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")

        existing_note = await db.scalar(
            select(CounselorNote).where(
                CounselorNote.counselor_id == counselor.id,
                CounselorNote.client_id == client.id,
                CounselorNote.content.like("演示备注:%"),
            )
        )
        if not existing_note:
            db.add(
                CounselorNote(
                    counselor_id=counselor.id,
                    client_id=client.id,
                    content="演示备注: 先核实睡眠变化和课程压力源，再讨论任务拆分与可用支持资源。",
                    created_at=now,
                )
            )
        await db.commit()

    print("演示样例数据已生成: client@example.com / counselor@example.com")


def _build_report(item: dict, created_at: datetime) -> Report:
    probabilities = item["face"]
    duration_ratio = {key: round(value * 0.95, 2) for key, value in probabilities.items()}
    return Report(
        task_id=item["task_id"],
        video_summary=VideoSummary(
            duration_seconds=42.0,
            detected_faces=1,
            speech_detected=True,
            frame_count=18,
            analyzed_frames=16,
            skipped_frames=2,
            processing_notes=["课程演示模拟报告，不包含真实隐私视频。"],
        ),
        face_emotion=FaceEmotion(
            dominant=item["emotion"],
            probabilities=probabilities,
            duration_ratio=duration_ratio,
            analyzed_frames=16,
            skipped_frames=2,
        ),
        speech_features=SpeechFeatures(
            transcript=item["transcript"],
            pitch_summary="基频处于演示样例范围",
            speech_rate="语速适中" if item["risk"] == "low" else "语速略慢",
            clarity="语音清晰",
            semantic_emotion=item["emotion"],
            duration_seconds=42.0,
            tags=["课程压力", "睡眠", "自我调节"],
            acoustic={"sample_rate": 16000, "duration_seconds": 42.0, "rms": 0.053, "voiced_ratio": 0.68},
            processing_notes=["语音特征为课程演示模拟值。"],
        ),
        final_prediction=FinalPrediction(
            emotion=item["emotion"],
            confidence=item["confidence"],
            risk_level=item["risk"],
            evidence=item["evidence"],
        ),
        expert_advice=item["advice"],
        model_name="demo-seed",
        prompt_version="v1",
        generated_at=created_at.isoformat(),
    )


if __name__ == "__main__":
    asyncio.run(seed_demo_data())
