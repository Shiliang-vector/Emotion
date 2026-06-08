from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from app.schemas.report import Report
from app.services.task_service import task_service

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/videos/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> dict[str, str]:
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="请上传视频文件")

    task = await task_service.create_task(file)
    background_tasks.add_task(task_service.process_task, task.task_id)
    return {
        "task_id": task.task_id,
        "status": task.status,
    }


@router.get("/tasks/{task_id}")
async def get_task(task_id: str) -> dict[str, str | None]:
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return {
        "task_id": task.task_id,
        "status": task.status,
        "error": task.error,
        "report_url": f"/api/reports/{task_id}" if task.status == "completed" else None,
    }


@router.get("/reports/{task_id}", response_model=Report)
async def get_report(task_id: str) -> Report:
    report = task_service.get_report(task_id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在或任务尚未完成")
    return report

