import math
import os
import re
import wave
from functools import lru_cache
from pathlib import Path
from statistics import mean

import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="SenseVoice Service",
    description="基于 FunASR SenseVoice 的语音转写和语音侧分析服务",
    version="0.1.0",
)

TAG_PATTERN = re.compile(r"<\|([^|]+)\|>")
EMOTION_MAP = {
    "HAPPY": "happy",
    "EMO_HAPPY": "happy",
    "SAD": "sad",
    "EMO_SAD": "sad",
    "ANGRY": "angry",
    "EMO_ANGRY": "angry",
    "NEUTRAL": "neutral",
    "EMO_NEUTRAL": "neutral",
    "FEARFUL": "fear",
    "EMO_FEARFUL": "fear",
    "DISGUSTED": "disgust",
    "EMO_DISGUSTED": "disgust",
    "SURPRISED": "surprise",
    "EMO_SURPRISED": "surprise",
}


class AnalyzeRequest(BaseModel):
    task_id: str
    audio_path: str | None = None
    duration_seconds: float = 0
    language: str = "auto"
    use_itn: bool = True


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
def analyze(request: AnalyzeRequest) -> dict:
    if not request.audio_path:
        return _empty_result(request.task_id, "后端未提供可分析音频")

    audio_path = Path(request.audio_path)
    if not audio_path.exists():
        return _empty_result(request.task_id, f"音频文件不存在: {audio_path}")

    notes: list[str] = []
    acoustic = _extract_acoustic_features(audio_path, request.duration_seconds, notes)

    try:
        raw_result = _model().generate(
            input=str(audio_path),
            cache={},
            language=request.language,
            use_itn=request.use_itn,
            batch_size_s=60,
            merge_vad=True,
            merge_length_s=15,
        )
    except Exception as exc:
        result = _result_from_acoustic(request.task_id, acoustic, notes)
        result["error"] = f"SenseVoice 推理失败: {exc}"
        return result

    transcript, semantic_emotion, tags = _parse_result(raw_result)
    if not transcript:
        notes.append("SenseVoice 未返回有效转写文本")

    return {
        "task_id": request.task_id,
        "speech_detected": bool(transcript) or acoustic["speech_detected"],
        "transcript": transcript,
        "pitch_summary": acoustic["pitch_summary"],
        "speech_rate": _speech_rate_summary(transcript, acoustic["duration_seconds"]),
        "clarity": acoustic["clarity"],
        "semantic_emotion": semantic_emotion,
        "duration_seconds": acoustic["duration_seconds"],
        "tags": tags,
        "acoustic": acoustic,
        "processing_notes": notes,
    }


@lru_cache(maxsize=1)
def _model():
    from funasr import AutoModel

    model_name = os.getenv("FUNASR_MODEL", "iic/SenseVoiceSmall")
    vad_model = os.getenv("FUNASR_VAD_MODEL", "fsmn-vad")
    device = os.getenv("FUNASR_DEVICE", "cpu")
    return AutoModel(
        model=model_name,
        vad_model=vad_model,
        vad_kwargs={"max_single_segment_time": 30000},
        trust_remote_code=True,
        device=device,
    )


def _parse_result(raw_result) -> tuple[str, str, list[str]]:
    segments = raw_result if isinstance(raw_result, list) else [raw_result]
    texts: list[str] = []
    all_tags: list[str] = []
    semantic_emotion = "unknown"

    for segment in segments:
        if not isinstance(segment, dict):
            continue
        raw_text = str(segment.get("text") or "")
        tags = TAG_PATTERN.findall(raw_text)
        all_tags.extend(tags)
        for tag in tags:
            if tag.upper() in EMOTION_MAP:
                semantic_emotion = EMOTION_MAP[tag.upper()]
        clean_text = TAG_PATTERN.sub("", raw_text).strip()
        if clean_text:
            texts.append(clean_text)

    return " ".join(texts).strip(), semantic_emotion, all_tags


def _extract_acoustic_features(audio_path: Path, fallback_duration: float, notes: list[str]) -> dict:
    try:
        with wave.open(str(audio_path), "rb") as source:
            channels = source.getnchannels()
            sample_width = source.getsampwidth()
            sample_rate = source.getframerate()
            frames = source.getnframes()
            raw = source.readframes(frames)
    except Exception as exc:
        notes.append(f"声学特征读取失败: {exc}")
        return _unknown_acoustic(fallback_duration)

    if sample_width != 2:
        notes.append(f"当前仅完整支持 16-bit PCM WAV，实际 sample_width={sample_width}")

    audio = np.frombuffer(raw, dtype=np.int16)
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)
    audio = audio.astype(np.float32)
    duration = round(frames / sample_rate, 2) if sample_rate else round(fallback_duration, 2)
    if audio.size == 0:
        return _unknown_acoustic(duration)

    normalized = audio / 32768.0
    rms = float(np.sqrt(np.mean(np.square(normalized))))
    peak = float(np.max(np.abs(normalized)))
    speech_detected = rms > 0.008
    zero_crossing_rate = _zero_crossing_rate(normalized)
    voiced_ratio = _voiced_ratio(normalized, sample_rate)
    pitch_hz = _estimate_pitch_hz(normalized, sample_rate)

    return {
        "duration_seconds": duration,
        "speech_detected": speech_detected,
        "sample_rate": sample_rate,
        "rms": round(rms, 5),
        "peak": round(peak, 5),
        "zero_crossing_rate": round(zero_crossing_rate, 5),
        "voiced_ratio": round(voiced_ratio, 4),
        "estimated_pitch_hz": round(pitch_hz, 2) if pitch_hz else None,
        "pitch_summary": _pitch_summary(pitch_hz),
        "clarity": _clarity_summary(rms, peak, voiced_ratio),
    }


def _zero_crossing_rate(samples: np.ndarray) -> float:
    if samples.size < 2:
        return 0.0
    signs = np.signbit(samples)
    return float(np.mean(signs[1:] != signs[:-1]))


def _voiced_ratio(samples: np.ndarray, sample_rate: int) -> float:
    if sample_rate <= 0:
        return 0.0
    frame_size = max(int(sample_rate * 0.03), 1)
    energies = [
        float(np.sqrt(np.mean(np.square(samples[index : index + frame_size]))))
        for index in range(0, samples.size, frame_size)
        if samples[index : index + frame_size].size
    ]
    if not energies:
        return 0.0
    threshold = max(0.01, mean(energies) * 0.45)
    voiced = sum(1 for energy in energies if energy >= threshold)
    return voiced / len(energies)


def _estimate_pitch_hz(samples: np.ndarray, sample_rate: int) -> float | None:
    if sample_rate <= 0 or samples.size < sample_rate // 2:
        return None

    frame_size = min(samples.size, int(sample_rate * 1.5))
    frame = samples[:frame_size]
    frame = frame - np.mean(frame)
    if not np.any(frame):
        return None

    corr = np.correlate(frame, frame, mode="full")[frame.size - 1 :]
    min_lag = max(int(sample_rate / 400), 1)
    max_lag = min(int(sample_rate / 70), corr.size - 1)
    if max_lag <= min_lag:
        return None

    segment = corr[min_lag:max_lag]
    if segment.size == 0:
        return None
    lag = int(np.argmax(segment) + min_lag)
    if lag <= 0:
        return None
    pitch = sample_rate / lag
    if not math.isfinite(pitch) or pitch < 70 or pitch > 400:
        return None
    return float(pitch)


def _pitch_summary(pitch_hz: float | None) -> str:
    if pitch_hz is None:
        return "基频不足以稳定估计"
    if pitch_hz < 120:
        return f"基频偏低，约 {pitch_hz:.1f} Hz"
    if pitch_hz > 240:
        return f"基频偏高，约 {pitch_hz:.1f} Hz"
    return f"基频整体平稳，约 {pitch_hz:.1f} Hz"


def _clarity_summary(rms: float, peak: float, voiced_ratio: float) -> str:
    if rms < 0.008 or peak < 0.03:
        return "音量偏低或无有效语音"
    if peak > 0.98:
        return "可能存在削波失真"
    if voiced_ratio < 0.2:
        return "有效发声比例偏低"
    if rms < 0.025:
        return "清晰度偏弱"
    return "清晰度中等"


def _speech_rate_summary(transcript: str, duration_seconds: float) -> str:
    if not transcript or duration_seconds <= 0:
        return "语速无法估计"
    chars = len(re.sub(r"\s+", "", transcript))
    chars_per_second = chars / duration_seconds
    if chars_per_second < 1.5:
        return "语速偏慢"
    if chars_per_second > 5.0:
        return "语速偏快"
    return "语速中等"


def _unknown_acoustic(duration_seconds: float) -> dict:
    return {
        "duration_seconds": round(duration_seconds, 2),
        "speech_detected": False,
        "sample_rate": None,
        "rms": None,
        "peak": None,
        "zero_crossing_rate": None,
        "voiced_ratio": None,
        "estimated_pitch_hz": None,
        "pitch_summary": "unknown",
        "clarity": "unknown",
    }


def _empty_result(task_id: str, note: str) -> dict:
    return {
        "task_id": task_id,
        "speech_detected": False,
        "transcript": "",
        "pitch_summary": "unknown",
        "speech_rate": "unknown",
        "clarity": "unknown",
        "semantic_emotion": "unknown",
        "duration_seconds": 0,
        "processing_notes": [note],
    }


def _result_from_acoustic(task_id: str, acoustic: dict, notes: list[str]) -> dict:
    return {
        "task_id": task_id,
        "speech_detected": acoustic["speech_detected"],
        "transcript": "",
        "pitch_summary": acoustic["pitch_summary"],
        "speech_rate": "语速无法估计",
        "clarity": acoustic["clarity"],
        "semantic_emotion": "unknown",
        "duration_seconds": acoustic["duration_seconds"],
        "acoustic": acoustic,
        "processing_notes": notes,
    }
