from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Task:
    task_id: str
    status: str
    video_path: Path
    stage: str = "queued"
    progress: int = 0
    message: str = "任务已创建，等待处理"
    error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
