import asyncio
import shutil
from pathlib import Path


class VideoService:
    async def prepare_video(self, task_id: str, video_path: Path, frames_root: Path, audio_root: Path) -> dict:
        notes: list[str] = []
        frames_dir = frames_root / task_id
        frames_dir.mkdir(parents=True, exist_ok=True)
        audio_path = audio_root / f"{task_id}.wav"
        audio_path.parent.mkdir(parents=True, exist_ok=True)

        ffmpeg_available = shutil.which("ffmpeg") is not None
        ffprobe_available = shutil.which("ffprobe") is not None

        duration_seconds = await self._probe_duration(video_path) if ffprobe_available else 0.0
        if not ffprobe_available:
            notes.append("未检测到 ffprobe，视频时长使用默认值 0")

        if ffmpeg_available:
            frame_pattern = frames_dir / "frame_%04d.jpg"
            await self._run_command(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(video_path),
                    "-vf",
                    "fps=1",
                    str(frame_pattern),
                ],
                notes,
                "抽帧失败",
            )
            await self._run_command(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(video_path),
                    "-vn",
                    "-acodec",
                    "pcm_s16le",
                    "-ar",
                    "16000",
                    "-ac",
                    "1",
                    str(audio_path),
                ],
                notes,
                "音频提取失败",
            )
        else:
            notes.append("未检测到 ffmpeg，跳过抽帧和音频提取")

        frame_paths = sorted(frames_dir.glob("*.jpg"))
        return {
            "duration_seconds": duration_seconds,
            "frames_dir": frames_dir,
            "frame_count": len(frame_paths),
            "audio_path": audio_path if audio_path.exists() else None,
            "notes": notes,
        }

    async def _probe_duration(self, video_path: Path) -> float:
        process = await asyncio.create_subprocess_exec(
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await process.communicate()
        if process.returncode != 0:
            return 0.0
        try:
            return round(float(stdout.decode().strip()), 2)
        except ValueError:
            return 0.0

    async def _run_command(self, command: list[str], notes: list[str], error_message: str) -> None:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()
        if process.returncode != 0:
            detail = stderr.decode(errors="ignore").strip()
            notes.append(f"{error_message}: {detail[-240:]}")


video_service = VideoService()

