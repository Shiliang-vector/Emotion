import json
import uuid
from datetime import datetime
from pathlib import Path

import aiofiles
from fastapi import UploadFile
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.task import AnalysisTask, ConsultationBinding, CounselorNote, ReportRecord, User
from app.schemas.report import NoteOut, Report, TaskOut, TrendPointOut
from app.services.face_service import face_service
from app.services.fusion_service import fusion_service
from app.services.llm_service import llm_service
from app.services.speech_service import speech_service
from app.services.video_service import video_service


class TaskService:
    def __init__(self) -> None:
        self._ensure_storage_dirs()

    async def create_task(self, db: AsyncSession, file: UploadFile, user: User) -> AnalysisTask:
        task_id = str(uuid.uuid4())
        suffix = Path(file.filename or "video.mp4").suffix or ".mp4"
        video_path = settings.uploads_dir / f"{task_id}{suffix}"
        async with aiofiles.open(video_path, "wb") as target:
            while chunk := await file.read(1024 * 1024):
                await target.write(chunk)

        now = datetime.utcnow()
        task = AnalysisTask(
            task_id=task_id,
            user_id=user.id,
            status="queued",
            video_path=str(video_path),
            stage="queued",
            progress=5,
            message="视频已上传，等待后台分析",
            created_at=now,
            updated_at=now,
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task

    async def process_task(self, task_id: str) -> None:
        async with AsyncSessionLocal() as db:
            task = await db.get(AnalysisTask, task_id)
            if not task:
                return

            await self._update_task(db, task, "processing", "preparing_video", 10, "正在抽帧并提取音频")
            try:
                video_data = await video_service.prepare_video(
                    task_id,
                    Path(task.video_path),
                    settings.frames_dir,
                    settings.audio_dir,
                )
                await self._update_task(db, task, "processing", "analyzing_face", 35, "正在分析人脸表情")
                face_result = await face_service.analyze(
                    task_id,
                    video_data["frames_dir"],
                    video_data["frame_count"],
                )
                await self._update_task(db, task, "processing", "analyzing_speech", 60, "正在分析语音转写和声学特征")
                speech_result = await speech_service.analyze(
                    task_id,
                    video_data["audio_path"],
                    video_data["duration_seconds"],
                )

                await self._update_task(db, task, "processing", "fusing_features", 78, "正在融合视觉和语音特征")
                video_summary = fusion_service.build_video_summary(
                    video_data["duration_seconds"],
                    face_result,
                    speech_result,
                    video_data["notes"],
                    video_data["frame_count"],
                )
                face_emotion = fusion_service.build_face_emotion(face_result)
                speech_features = fusion_service.build_speech_features(speech_result)
                final_prediction = fusion_service.predict(face_emotion, speech_features)
                await self._update_task(db, task, "processing", "generating_advice", 88, "正在生成专家意见")
                expert_advice = await llm_service.generate_advice(
                    video_summary,
                    face_emotion,
                    speech_features,
                    final_prediction,
                )
                await self._update_task(db, task, "processing", "saving_report", 96, "正在保存分析报告")
                report = Report(
                    task_id=task_id,
                    video_summary=video_summary,
                    face_emotion=face_emotion,
                    speech_features=speech_features,
                    final_prediction=final_prediction,
                    expert_advice=expert_advice,
                )
                await self._save_report(db, report)
                await self._update_task(db, task, "completed", "completed", 100, "分析完成")
            except Exception as exc:
                await self._update_task(db, task, "failed", task.stage or "failed", task.progress, "分析失败", str(exc))

    async def get_task(self, db: AsyncSession, task_id: str) -> AnalysisTask | None:
        return await db.get(AnalysisTask, task_id)

    async def get_report(self, db: AsyncSession, task_id: str) -> Report | None:
        record = await db.get(ReportRecord, task_id)
        if record:
            return Report.model_validate(json.loads(record.report_json))
        report_path = self._report_path(task_id)
        if not report_path.exists():
            return None
        with report_path.open("r", encoding="utf-8") as source:
            return Report.model_validate(json.load(source))

    async def list_user_tasks(self, db: AsyncSession, user: User) -> list[AnalysisTask]:
        return list(
            await db.scalars(
                select(AnalysisTask)
                .where(AnalysisTask.user_id == user.id)
                .order_by(AnalysisTask.created_at.desc())
            )
        )

    async def serialize_task(self, db: AsyncSession, task: AnalysisTask) -> TaskOut:
        record = await db.get(ReportRecord, task.task_id)
        summary = self._report_summary(record)
        return TaskOut(
            task_id=task.task_id,
            status=task.status,
            stage=task.stage,
            progress=task.progress,
            message=task.message,
            error=task.error,
            created_at=task.created_at.isoformat() if task.created_at else None,
            updated_at=task.updated_at.isoformat() if task.updated_at else None,
            report_url=f"/api/reports/{task.task_id}" if task.status == "completed" else None,
            user_id=task.user_id,
            dominant_emotion=summary.get("dominant_emotion"),
            risk_level=summary.get("risk_level"),
            confidence=summary.get("confidence"),
            counselor_assistance=record.counselor_assistance if record else None,
            counselor_assistance_created_at=(
                record.counselor_assistance_created_at.isoformat()
                if record and record.counselor_assistance_created_at
                else None
            ),
        )

    async def list_counselor_clients(self, db: AsyncSession, counselor: User) -> list[tuple[User, int, dict]]:
        bindings = (await db.scalars(
            select(ConsultationBinding)
            .where(ConsultationBinding.counselor_id == counselor.id)
        )).all()
        rows: list[tuple[User, int, dict]] = []
        for binding in bindings:
            client = await db.get(User, binding.client_id)
            if not client:
                continue
            tasks = await self.list_user_tasks(db, client)
            latest_summary = await self.latest_task_summary(db, tasks[0]) if tasks else {}
            rows.append((client, len(tasks), latest_summary))
        return rows

    async def latest_task_summary(self, db: AsyncSession, task: AnalysisTask) -> dict:
        record = await db.get(ReportRecord, task.task_id)
        summary = self._report_summary(record)
        summary["created_at"] = task.created_at.isoformat() if task.created_at else None
        return summary

    async def create_binding(self, db: AsyncSession, counselor: User, client_email: str) -> tuple[User, bool]:
        client = await db.scalar(select(User).where(func.lower(User.email) == client_email.strip().lower()))
        if not client or client.role != "client":
            raise ValueError("未找到普通用户")
        if client.id == counselor.id:
            raise ValueError("不能绑定自己")
        existing = await db.scalar(
            select(ConsultationBinding).where(
                ConsultationBinding.counselor_id == counselor.id,
                ConsultationBinding.client_id == client.id,
            )
        )
        if existing:
            return client, False
        db.add(ConsultationBinding(counselor_id=counselor.id, client_id=client.id))
        await db.commit()
        return client, True

    async def delete_binding(self, db: AsyncSession, counselor: User, client_id: int) -> bool:
        result = await db.execute(
            delete(ConsultationBinding).where(
                ConsultationBinding.counselor_id == counselor.id,
                ConsultationBinding.client_id == client_id,
            )
        )
        await db.commit()
        return bool(result.rowcount)

    async def list_client_counselors(self, db: AsyncSession, client: User) -> list[User]:
        bindings = (await db.scalars(
            select(ConsultationBinding).where(ConsultationBinding.client_id == client.id)
        )).all()
        counselors: list[User] = []
        for binding in bindings:
            counselor = await db.get(User, binding.counselor_id)
            if counselor and counselor.role == "counselor":
                counselors.append(counselor)
        return counselors

    async def get_bound_client(self, db: AsyncSession, counselor: User, user_id: int) -> User | None:
        binding = await db.scalar(
            select(ConsultationBinding).where(
                ConsultationBinding.counselor_id == counselor.id,
                ConsultationBinding.client_id == user_id,
            )
        )
        if not binding:
            return None
        client = await db.get(User, user_id)
        return client if client and client.role == "client" else None

    async def can_access_task(self, db: AsyncSession, user: User, task: AnalysisTask) -> bool:
        if user.role == "client":
            return task.user_id == user.id
        if user.role == "counselor":
            return await self.get_bound_client(db, user, task.user_id) is not None
        return False

    async def generate_counselor_assistance(self, db: AsyncSession, counselor: User, client: User) -> str:
        records = (await db.scalars(
            select(ReportRecord)
            .join(AnalysisTask, AnalysisTask.task_id == ReportRecord.task_id)
            .where(AnalysisTask.user_id == client.id)
            .order_by(ReportRecord.created_at.asc())
        )).all()
        reports = [Report.model_validate(json.loads(record.report_json)) for record in records]
        assistance = await llm_service.generate_counselor_assistance(reports)
        if records:
            latest = records[-1]
            latest.counselor_assistance = assistance
            latest.counselor_assistance_created_at = datetime.utcnow()
            await db.commit()
        return assistance

    async def latest_assistance_record(self, db: AsyncSession, client: User) -> ReportRecord | None:
        records = (await db.scalars(
            select(ReportRecord)
            .join(AnalysisTask, AnalysisTask.task_id == ReportRecord.task_id)
            .where(AnalysisTask.user_id == client.id)
            .order_by(ReportRecord.created_at.desc())
        )).all()
        return next((record for record in records if record.counselor_assistance), None)

    async def add_note(self, db: AsyncSession, counselor: User, client: User, content: str) -> CounselorNote:
        note = CounselorNote(counselor_id=counselor.id, client_id=client.id, content=content.strip())
        db.add(note)
        await db.commit()
        await db.refresh(note)
        return note

    async def list_notes(self, db: AsyncSession, counselor: User, client: User) -> list[CounselorNote]:
        return list(
            await db.scalars(
                select(CounselorNote)
                .where(
                    CounselorNote.counselor_id == counselor.id,
                    CounselorNote.client_id == client.id,
                )
                .order_by(CounselorNote.created_at.desc())
            )
        )

    async def trend_points(self, db: AsyncSession, client: User) -> list[TrendPointOut]:
        tasks = list(
            await db.scalars(
                select(AnalysisTask)
                .where(AnalysisTask.user_id == client.id, AnalysisTask.status == "completed")
                .order_by(AnalysisTask.created_at.asc())
            )
        )
        points: list[TrendPointOut] = []
        for task in tasks:
            record = await db.get(ReportRecord, task.task_id)
            summary = self._report_summary(record)
            points.append(
                TrendPointOut(
                    task_id=task.task_id,
                    created_at=task.created_at.isoformat() if task.created_at else None,
                    emotion=summary.get("dominant_emotion"),
                    risk_level=summary.get("risk_level"),
                    confidence=summary.get("confidence"),
                )
            )
        return points

    async def _save_report(self, db: AsyncSession, report: Report) -> None:
        report_path = self._report_path(report.task_id)
        with report_path.open("w", encoding="utf-8") as target:
            json.dump(report.model_dump(), target, ensure_ascii=False, indent=2)
        record = ReportRecord(
            task_id=report.task_id,
            report_json=json.dumps(report.model_dump(), ensure_ascii=False),
            expert_advice=report.expert_advice,
            model_name=settings.openai_model,
            prompt_version="v1",
        )
        await db.merge(record)
        await db.commit()

    def _report_path(self, task_id: str) -> Path:
        return settings.reports_dir / f"{task_id}.json"

    def _ensure_storage_dirs(self) -> None:
        for path in (settings.uploads_dir, settings.frames_dir, settings.audio_dir, settings.reports_dir):
            path.mkdir(parents=True, exist_ok=True)

    async def _update_task(
        self,
        db: AsyncSession,
        task: AnalysisTask,
        status: str,
        stage: str,
        progress: int,
        message: str,
        error: str | None = None,
    ) -> None:
        task.status = status
        task.stage = stage
        task.progress = max(0, min(progress, 100))
        task.message = message
        task.error = error
        task.updated_at = datetime.utcnow()
        db.add(task)
        await db.commit()

    def _report_summary(self, record: ReportRecord | None) -> dict:
        if not record:
            return {}
        try:
            report = Report.model_validate(json.loads(record.report_json))
        except (ValueError, json.JSONDecodeError):
            return {}
        return {
            "dominant_emotion": report.final_prediction.emotion,
            "risk_level": report.final_prediction.risk_level,
            "confidence": report.final_prediction.confidence,
        }


task_service = TaskService()
