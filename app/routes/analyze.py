import asyncio
import logging
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from app.config import get_settings
from app.schemas.response import AnalysisResponse, FluctuationWindow
from app.services.audio_utils import extract_audio
from app.services.evaluation_service import EvaluationService
from app.services.transcribe_service import TranscribeService
from app.services.voice_analysis import calculate_fluctuation_timeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["analysis"])

ALLOWED_CONTENT_TYPES = {"video/mp4"}


@router.post("/analyze-teaching", response_model=AnalysisResponse)
async def analyze_teaching(file: UploadFile) -> AnalysisResponse:
    """Accept an MP4 classroom recording and return transcript + fluctuation scores."""
    settings = get_settings()

    # --- Validate upload -----------------------------------------------
    filename = file.filename or ""
    if not filename.lower().endswith(".mp4"):
        raise HTTPException(status_code=400, detail="Only .mp4 files are accepted.")

    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid content type: {file.content_type}")

    # --- Persist upload to temp dir ------------------------------------
    job_id = uuid.uuid4().hex
    temp_dir = Path(settings.temp_dir) / f"hte_{job_id}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    mp4_path = str(temp_dir / f"{job_id}.mp4")
    wav_path = str(temp_dir / f"{job_id}.wav")

    try:
        contents = await file.read()
        with open(mp4_path, "wb") as f:
            f.write(contents)

        # --- Extract audio ---------------------------------------------
        try:
            extract_audio(mp4_path, wav_path)
        except (RuntimeError, FileNotFoundError) as exc:
            logger.error("Audio extraction error: %s", exc)
            raise HTTPException(status_code=500, detail=str(exc))

        # --- Run transcription and voice analysis concurrently ---------
        loop = asyncio.get_running_loop()

        transcribe_svc = TranscribeService(settings)

        transcript_future = transcribe_svc.transcribe(wav_path)
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
            logger.error("Transcription / analysis error: %s", exc)
            raise HTTPException(status_code=502, detail=str(exc))

        # --- Evaluate transcript against the teaching rubric -----------
        eval_svc = EvaluationService(settings)
        try:
            evaluation = await loop.run_in_executor(
                None, eval_svc.evaluate, transcript,
            )
        except RuntimeError as exc:
            logger.error("Evaluation error: %s", exc)
            raise HTTPException(status_code=502, detail=str(exc))

        timeline = [FluctuationWindow(**w) for w in timeline_raw]

        return AnalysisResponse(
            status="success",
            transcript=transcript,
            fluctuation_timeline=timeline,
            evaluation=evaluation,
        )

    finally:
        # --- Cleanup temp files ----------------------------------------
        for p in (wav_path, mp4_path):
            try:
                os.remove(p)
            except OSError:
                pass
        try:
            temp_dir.rmdir()
        except OSError:
            pass
