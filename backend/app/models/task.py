from dataclasses import dataclass
from pathlib import Path


@dataclass
class Task:
    task_id: str
    status: str
    video_path: Path
    error: str | None = None

