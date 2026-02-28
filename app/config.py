import tempfile
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # ── OpenAI Whisper (primary STT) ────────────────────────────────────
    openai_api_key: str = ""
    whisper_model: str = "whisper-1"          # only model Whisper API exposes
    # Max bytes per Whisper API chunk (25 MB hard limit; we use 23 MB to be safe)
    whisper_chunk_bytes: int = 23 * 1024 * 1024

    # ── AWS (kept for voice-analysis / Bedrock features) ────────────────
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    bedrock_model_id: str = "amazon.nova-sonic-v1:0"

    # ── General ─────────────────────────────────────────────────────────
    fluctuation_window_seconds: int = 180
    temp_dir: str = tempfile.gettempdir()
    # Max video file size accepted (bytes).  Default = 500 MB.
    max_upload_bytes: int = 500 * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
