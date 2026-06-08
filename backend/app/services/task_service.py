import json
import uuid
from datetime import datetime
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from app.core.config import settings
from app.models.task import Task
from app.schemas.report import Report
from app.services.face_service import face_service
from app.services.fusion_service import fusion_service
from app.services.llm_service import llm_service
from app.services.speech_service import speech_service
from app.services.video_service import video_service


class TaskService:
    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._ensure_storage_dirs()

    async def create_task(self, file: UploadFile) -> Task:
        task_id = str(uuid.uuid4())
        suffix = Path(file.filename or "video.mp4").suffix or ".mp4"
        video_path = settings.uploads_dir / f"{task_id}{suffix}"
        async with aiofiles.open(video_path, "wb") as target:
            while chunk := await file.read(1024 * 1024):
                await target.write(chunk)

        now = datetime.now()
        task = Task(
            task_id=task_id,
            status="queued",
            video_path=video_path,
            stage="queued",
            progress=5,
            message="视频已上传，等待后台分析",
            created_at=now,
            updated_at=now,
        )
        self._tasks[task_id] = task
        return task

    async def process_task(self, task_id: str) -> None:
        task = self._tasks.get(task_id)
        if not task:
            return

        self._update_task(task, "processing", "preparing_video", 10, "正在抽帧并提取音频")
        try:
            video_data = await video_service.prepare_video(
                task_id,
                task.video_path,
                settings.frames_dir,
                settings.audio_dir,
            )
            self._update_task(task, "processing", "analyzing_face", 35, "正在分析人脸表情")
            face_result = await face_service.analyze(
                task_id,
                video_data["frames_dir"],
                video_data["frame_count"],
            )
            self._update_task(task, "processing", "analyzing_speech", 60, "正在分析语音转写和声学特征")
            speech_result = await speech_service.analyze(
                task_id,
                video_data["audio_path"],
                video_data["duration_seconds"],
            )

            self._update_task(task, "processing", "fusing_features", 78, "正在融合视觉和语音特征")
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
            self._update_task(task, "processing", "generating_advice", 88, "正在生成专家意见")
            expert_advice = await llm_service.generate_advice(
                video_summary,
                face_emotion,
                speech_features,
                final_prediction,
            )
            self._update_task(task, "processing", "saving_report", 96, "正在保存分析报告")
            report = Report(
                task_id=task_id,
                video_summary=video_summary,
                face_emotion=face_emotion,
                speech_features=speech_features,
                final_prediction=final_prediction,
                expert_advice=expert_advice,
            )
            self._save_report(report)
            self._update_task(task, "completed", "completed", 100, "分析完成")
        except Exception as exc:
            self._update_task(task, "failed", task.stage or "failed", task.progress, "分析失败")
            task.error = str(exc)

    def get_task(self, task_id: str) -> Task | None:
        task = self._tasks.get(task_id)
        if task:
            return task

        report_path = self._report_path(task_id)
        if report_path.exists():
            task = Task(
                task_id=task_id,
                status="completed",
                video_path=Path(""),
                stage="completed",
                progress=100,
                message="分析完成",
            )
            self._tasks[task_id] = task
            return task
        return None

    def get_report(self, task_id: str) -> Report | None:
        report_path = self._report_path(task_id)
        if not report_path.exists():
            return None
        with report_path.open("r", encoding="utf-8") as source:
            return Report.model_validate(json.load(source))

    def _save_report(self, report: Report) -> None:
        report_path = self._report_path(report.task_id)
        with report_path.open("w", encoding="utf-8") as target:
            json.dump(report.model_dump(), target, ensure_ascii=False, indent=2)

    def _report_path(self, task_id: str) -> Path:
        return settings.reports_dir / f"{task_id}.json"

    def _ensure_storage_dirs(self) -> None:
        for path in (settings.uploads_dir, settings.frames_dir, settings.audio_dir, settings.reports_dir):
            path.mkdir(parents=True, exist_ok=True)

    def _update_task(self, task: Task, status: str, stage: str, progress: int, message: str) -> None:
        task.status = status
        task.stage = stage
        task.progress = max(0, min(progress, 100))
        task.message = message
        task.updated_at = datetime.now()


task_service = TaskService()
