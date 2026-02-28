from pydantic import BaseModel


# ── kept for the original teaching-analysis endpoint ─────────────────────────
class FluctuationWindow(BaseModel):
    timestamp_start: float
    timestamp_end: float
    fluctuation_score: float


class AnalysisResponse(BaseModel):
    status: str = "success"
    transcript: str
    fluctuation_timeline: list[FluctuationWindow]


# ── new: matches the TranscriptResult type in the frontend ───────────────────
class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str


class TranscriptResult(BaseModel):
    job_id: str
    language: str
    duration: float          # seconds
    full_text: str
    segments: list[TranscriptSegment]
    srt_content: str


# ── YouTube request body ──────────────────────────────────────────────────────
class YouTubeRequest(BaseModel):
    url: str
    language: str = "auto"
