import tempfile
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    transcribe_language_code: str = "en-US"
    fluctuation_window_seconds: int = 180
    temp_dir: str = tempfile.gettempdir()


@lru_cache
def get_settings() -> Settings:
    return Settings()
