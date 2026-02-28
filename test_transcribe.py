"""Quick test: extract a 30-second clip from the sample video and run it
through Amazon Transcribe Streaming to verify credentials and connectivity."""

import asyncio
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

from app.config import get_settings
from app.services.audio_utils import extract_audio, FFMPEG_BIN
from app.services.transcribe_service import TranscribeService

import ffmpeg

VIDEO_PATH = os.path.join(os.path.dirname(__file__), "class observation.mp4")
CLIP_SECONDS = 30


def extract_short_clip(input_path: str, output_path: str, duration: int) -> str:
    """Extract the first `duration` seconds of audio as a 16kHz mono WAV."""
    (
        ffmpeg
        .input(input_path, t=duration, err_detect="ignore_err")
        .output(output_path, ac=1, ar=16000, acodec="pcm_s16le")
        .overwrite_output()
        .run(cmd=FFMPEG_BIN, capture_stdout=True, capture_stderr=True)
    )
    return output_path


async def main() -> None:
    settings = get_settings()
    print(f"Region:   {settings.aws_region}")
    print(f"Language: {settings.transcribe_language_code}")
    print(f"Key ID:   {settings.aws_access_key_id[:8]}...")
    print()

    with tempfile.TemporaryDirectory(prefix="hte_ttest_") as tmp:
        wav_path = os.path.join(tmp, "clip.wav")

        print(f"[1/2] Extracting {CLIP_SECONDS}s clip from video ...")
        extract_short_clip(VIDEO_PATH, wav_path, CLIP_SECONDS)
        size_kb = os.path.getsize(wav_path) / 1024
        print(f"  -> {wav_path}  ({size_kb:.0f} KB)\n")

        print("[2/2] Streaming to Amazon Transcribe ...")
        svc = TranscribeService(settings)
        try:
            transcript = await svc.transcribe(wav_path)
        except Exception as exc:
            print(f"\n  ERROR: {exc}")
            raise

        print(f"\n--- Transcript ({len(transcript)} chars) ---")
        print(transcript)


if __name__ == "__main__":
    asyncio.run(main())
