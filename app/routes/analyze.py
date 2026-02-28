"""
Two public endpoints:

  POST /api/analyze
    Accepts a video or audio file upload (mp4, mov, mkv, avi, mp3, wav, m4a, webm).
    Extracts audio with ffmpeg, then transcribes with Whisper (with auto-chunking
    for long videos).  Returns TranscriptResult JSON.

  POST /api/analyze/youtube
    Accepts { url, language } JSON body.
    Downloads audio via yt-dlp, then transcribes with Whisper.
    Returns TranscriptResult JSON.

Legacy endpoint kept for backward compat:
  POST /api/v1/analyze-teaching
"""
import asyncio
import logging
import os
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from app.config import get_settings
from app.schemas.response import (
    AnalysisResponse,
    FluctuationWindow,
    TranscriptResult,
    TranscriptSegment,
    YouTubeRequest,
)
from app.services.audio_utils import extract_audio
from app.services.bedrock_service import BedrockTranscriptionService
from app.services.voice_analysis import calculate_fluctuation_timeline
from app.services.whisper_service import WhisperService
from app.services.youtube_service import YouTubeDownloader, is_valid_youtube_url

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analysis"])

ALLOWED_EXTENSIONS = {
    ".mp4", ".mov", ".mkv", ".avi",
    ".mp3", ".wav", ".m4a", ".webm", ".ogg", ".flac",
}


# ─────────────────────────────────────────────────────────────────────────────
#  Helper: convert WhisperService result → API response
# ─────────────────────────────────────────────────────────────────────────────
def _build_response(ws_result, job_id: str) -> TranscriptResult:
    segments = [
        TranscriptSegment(start=s.start, end=s.end, text=s.text)
        for s in ws_result.segments
    ]
    return TranscriptResult(
        job_id=job_id,
        language=ws_result.language,
        duration=round(ws_result.duration, 2),
        full_text=ws_result.full_text,
        segments=segments,
        srt_content=ws_result.srt_content,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  POST /api/analyze  — file upload
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/api/analyze", response_model=TranscriptResult)
async def analyze_file(
    file: UploadFile,
    language: str = "auto",
) -> TranscriptResult:
    """Accept a video/audio upload and return a full transcript with timestamps."""
    settings = get_settings()

    # ── Validate filename ──────────────────────────────────────────────────
    filename = file.filename or "upload"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. "
                   f"Accepted: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    job_id = uuid.uuid4().hex
    tmp_dir = Path(settings.temp_dir) / f"vt_{job_id}"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    raw_path = str(tmp_dir / f"input{ext}")
    wav_path = str(tmp_dir / "audio.wav")

    try:
        # ── Save upload ────────────────────────────────────────────────────
        contents = await file.read()
        if len(contents) > settings.max_upload_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds the {settings.max_upload_bytes // (1024*1024)} MB limit.",
            )
        Path(raw_path).write_bytes(contents)
        logger.info("[%s] Saved upload: %s (%.1f MB)", job_id, filename, len(contents) / 1e6)

        # ── Extract audio (if video) ───────────────────────────────────────
        if ext in {".wav", ".mp3", ".m4a", ".ogg", ".flac"}:
            # Already audio — still normalize to 16kHz mono WAV
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, extract_audio, raw_path, wav_path)
        else:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, extract_audio, raw_path, wav_path)

        logger.info("[%s] Audio extracted → %s", job_id, wav_path)

        # ── Transcribe ────────────────────────────────────────────────────
        svc = WhisperService(settings)
        loop = asyncio.get_running_loop()
        ws_result = await loop.run_in_executor(None, svc.transcribe, wav_path, language)

        logger.info("[%s] Transcription done: %d segments, lang=%s",
                    job_id, len(ws_result.segments), ws_result.language)

        return _build_response(ws_result, job_id)

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        logger.error("[%s] Runtime error: %s", job_id, exc)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        # ── Cleanup ───────────────────────────────────────────────────────
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
#  POST /api/analyze/youtube  — YouTube URL
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/api/analyze/youtube", response_model=TranscriptResult)
async def analyze_youtube(body: YouTubeRequest) -> TranscriptResult:
    """Download audio from a YouTube URL and return a full transcript."""
    settings = get_settings()

    if not is_valid_youtube_url(body.url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL.")

    job_id = uuid.uuid4().hex
    tmp_dir: Path | None = None

    try:
        downloader = YouTubeDownloader(settings)

        # yt-dlp is blocking — run in executor
        loop = asyncio.get_running_loop()
        wav_path = await loop.run_in_executor(
            None, downloader.download_audio, body.url, job_id
        )
        tmp_dir = Path(wav_path).parent

        logger.info("[%s] YouTube audio ready: %s", job_id, wav_path)

        svc = WhisperService(settings)
        ws_result = await loop.run_in_executor(
            None, svc.transcribe, wav_path, body.language
        )

        logger.info("[%s] Transcription done: %d segments, lang=%s",
                    job_id, len(ws_result.segments), ws_result.language)

        return _build_response(ws_result, job_id)

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        logger.error("[%s] Runtime error: %s", job_id, exc)
        raise HTTPException(status_code=502, detail=str(exc))
    finally:
        if tmp_dir and tmp_dir.exists():
            try:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────────────────────
#  POST /api/v1/analyze-teaching  — original endpoint (unchanged behaviour)
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/api/v1/analyze-teaching", response_model=AnalysisResponse)
async def analyze_teaching(file: UploadFile) -> AnalysisResponse:
    """Accept an MP4 classroom recording and return transcript + fluctuation scores."""
    settings = get_settings()

    filename = file.filename or ""
    if not filename.lower().endswith(".mp4"):
        raise HTTPException(status_code=400, detail="Only .mp4 files are accepted.")

    job_id = uuid.uuid4().hex
    temp_dir = Path(settings.temp_dir) / f"hte_{job_id}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    mp4_path = str(temp_dir / f"{job_id}.mp4")
    wav_path = str(temp_dir / f"{job_id}.wav")

    try:
        contents = await file.read()
        Path(mp4_path).write_bytes(contents)

        try:
            extract_audio(mp4_path, wav_path)
        except (RuntimeError, FileNotFoundError) as exc:
            raise HTTPException(status_code=500, detail=str(exc))

        loop = asyncio.get_running_loop()
        bedrock_svc = BedrockTranscriptionService(settings)

        transcript_future = loop.run_in_executor(None, bedrock_svc.transcribe, wav_path)
        analysis_future = loop.run_in_executor(
            None,
            calculate_fluctuation_timeline,
            wav_path,
            settings.fluctuation_window_seconds,
        )

        try:
            transcript, timeline_raw = await asyncio.gather(
                transcript_future, analysis_future,
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc))

        timeline = [FluctuationWindow(**w) for w in timeline_raw]
        return AnalysisResponse(status="success", transcript=transcript,
                                fluctuation_timeline=timeline)
    finally:
        for p in (wav_path, mp4_path):
            try:
                os.remove(p)
            except OSError:
                pass
        try:
            temp_dir.rmdir()
        except OSError:
            pass
