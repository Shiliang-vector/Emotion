import json

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, require_client, require_counselor
from app.core.database import get_db
from app.models.task import User
from app.schemas.report import (
    AssistanceDraftOut,
    BindingCreate,
    BindingOut,
    ClientHistoryOut,
    CounselorClientOut,
    CounselorOut,
    NoteCreate,
    NoteOut,
    Report,
    TaskOut,
    TrendOut,
)
from app.services.task_service import task_service

router = APIRouter()


async def _serialize_task(db: AsyncSession, task) -> TaskOut:
    return await task_service.serialize_task(db, task)


def _serialize_client(client: User, task_count: int = 0, latest_summary: dict | None = None) -> CounselorClientOut:
    latest_summary = latest_summary or {}
    return CounselorClientOut(
        id=client.id,
        email=client.email,
        display_name=client.display_name,
        task_count=task_count,
        latest_emotion=latest_summary.get("dominant_emotion"),
        latest_risk_level=latest_summary.get("risk_level"),
        latest_task_at=latest_summary.get("created_at"),
    )


def _serialize_counselor(counselor: User) -> CounselorOut:
    return CounselorOut(
        id=counselor.id,
        email=counselor.email,
        display_name=counselor.display_name,
        created_at=counselor.created_at.isoformat() if counselor.created_at else None,
    )


def _serialize_note(note) -> NoteOut:
    return NoteOut(
        id=note.id,
        counselor_id=note.counselor_id,
        client_id=note.client_id,
        content=note.content,
        created_at=note.created_at.isoformat(),
    )


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/videos/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_client),
) -> TaskOut:
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="请上传视频文件")

    task = await task_service.create_task(db, file, user)
    background_tasks.add_task(task_service.process_task, task.task_id)
    return await _serialize_task(db, task)


@router.get("/tasks/{task_id}", response_model=TaskOut)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TaskOut:
    task = await task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if not await task_service.can_access_task(db, user, task):
        raise HTTPException(status_code=403, detail="无权访问该任务")

    return await _serialize_task(db, task)


@router.get("/reports/{task_id}", response_model=Report)
async def get_report(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Report:
    task = await task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if not await task_service.can_access_task(db, user, task):
        raise HTTPException(status_code=403, detail="无权访问该报告")
    report = await task_service.get_report(db, task_id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在或任务尚未完成")
    return report


@router.get("/reports/{task_id}/export")
async def export_report(
    task_id: str,
    format: str = Query(default="json", pattern="^(json|text)$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = await task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if not await task_service.can_access_task(db, user, task):
        raise HTTPException(status_code=403, detail="无权导出该报告")
    report = await task_service.get_report(db, task_id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在或任务尚未完成")

    filename = f"emotion-report-{task_id}.{format}"
    if format == "json":
        return Response(
            content=json.dumps(report.model_dump(), ensure_ascii=False, indent=2),
            media_type="application/json; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    prediction = report.final_prediction
    text = (
        "多模态心理咨询辅助报告\n"
        "仅供辅助参考，不能替代专业诊断或治疗。\n\n"
        f"任务ID：{report.task_id}\n"
        f"综合预判：{prediction.emotion}\n"
        f"置信度：{prediction.confidence}\n"
        f"风险等级：{prediction.risk_level}\n"
        f"证据：{'；'.join(prediction.evidence)}\n\n"
        f"专家意见：\n{report.expert_advice}\n"
    )
    return PlainTextResponse(
        text,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/me/tasks", response_model=list[TaskOut])
async def my_tasks(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_client),
) -> list[TaskOut]:
    return [await _serialize_task(db, task) for task in await task_service.list_user_tasks(db, user)]


@router.get("/me/counselors", response_model=list[CounselorOut])
async def my_counselors(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_client),
) -> list[CounselorOut]:
    return [_serialize_counselor(counselor) for counselor in await task_service.list_client_counselors(db, user)]


@router.get("/counselor/clients", response_model=list[CounselorClientOut])
async def counselor_clients(
    db: AsyncSession = Depends(get_db),
    counselor: User = Depends(require_counselor),
) -> list[CounselorClientOut]:
    return [
        _serialize_client(client, task_count, latest_summary)
        for client, task_count, latest_summary in await task_service.list_counselor_clients(db, counselor)
    ]


@router.post("/counselor/bindings", response_model=BindingOut)
async def create_counselor_binding(
    payload: BindingCreate,
    db: AsyncSession = Depends(get_db),
    counselor: User = Depends(require_counselor),
) -> BindingOut:
    try:
        client, created = await task_service.create_binding(db, counselor, payload.client_email)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    task_count = len(await task_service.list_user_tasks(db, client))
    latest_summary = {}
    tasks = await task_service.list_user_tasks(db, client)
    if tasks:
        latest_summary = await task_service.latest_task_summary(db, tasks[0])
    return BindingOut(client=_serialize_client(client, task_count, latest_summary), created=created)


@router.delete("/counselor/bindings/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_counselor_binding(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    counselor: User = Depends(require_counselor),
) -> None:
    deleted = await task_service.delete_binding(db, counselor, client_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="绑定关系不存在")


@router.get("/counselor/users/{user_id}/history", response_model=ClientHistoryOut)
async def counselor_user_history(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    counselor: User = Depends(require_counselor),
) -> ClientHistoryOut:
    client = await task_service.get_bound_client(db, counselor, user_id)
    if not client:
        raise HTTPException(status_code=404, detail="未找到已关联的普通用户")
    return ClientHistoryOut(
        user_id=client.id,
        email=client.email,
        display_name=client.display_name,
        tasks=[await _serialize_task(db, task) for task in await task_service.list_user_tasks(db, client)],
    )


@router.post("/counselor/users/{user_id}/assistance-draft")
async def counselor_assistance_draft(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    counselor: User = Depends(require_counselor),
) -> AssistanceDraftOut:
    client = await task_service.get_bound_client(db, counselor, user_id)
    if not client:
        raise HTTPException(status_code=404, detail="未找到已关联的普通用户")
    assistance = await task_service.generate_counselor_assistance(db, counselor, client)
    record = await task_service.latest_assistance_record(db, client)
    return AssistanceDraftOut(
        user_id=client.id,
        assistance=assistance,
        generated_at=record.counselor_assistance_created_at.isoformat()
        if record and record.counselor_assistance_created_at
        else None,
    )


@router.get("/counselor/users/{user_id}/notes", response_model=list[NoteOut])
async def counselor_notes(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    counselor: User = Depends(require_counselor),
) -> list[NoteOut]:
    client = await task_service.get_bound_client(db, counselor, user_id)
    if not client:
        raise HTTPException(status_code=404, detail="未找到已关联的普通用户")
    return [_serialize_note(note) for note in await task_service.list_notes(db, counselor, client)]


@router.post("/counselor/users/{user_id}/notes", response_model=NoteOut)
async def create_counselor_note(
    user_id: int,
    payload: NoteCreate,
    db: AsyncSession = Depends(get_db),
    counselor: User = Depends(require_counselor),
) -> NoteOut:
    client = await task_service.get_bound_client(db, counselor, user_id)
    if not client:
        raise HTTPException(status_code=404, detail="未找到已关联的普通用户")
    note = await task_service.add_note(db, counselor, client, payload.content)
    return _serialize_note(note)


@router.get("/counselor/users/{user_id}/trend", response_model=TrendOut)
async def counselor_user_trend(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    counselor: User = Depends(require_counselor),
) -> TrendOut:
    client = await task_service.get_bound_client(db, counselor, user_id)
    if not client:
        raise HTTPException(status_code=404, detail="未找到已关联的普通用户")
    return TrendOut(user_id=client.id, points=await task_service.trend_points(db, client))
