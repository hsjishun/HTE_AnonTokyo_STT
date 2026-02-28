"""Smoke-test: extract audio from the sample video and run the voice
fluctuation scoring pipeline.  Bedrock transcription is skipped (no AWS
credentials needed).
"""

import json
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(__file__))

from app.services.audio_utils import extract_audio
from app.services.voice_analysis import calculate_fluctuation_timeline

VIDEO_PATH = os.path.join(os.path.dirname(__file__), "class observation.mp4")


def main() -> None:
    if not os.path.isfile(VIDEO_PATH):
        print(f"ERROR: video not found at {VIDEO_PATH}")
        sys.exit(1)

    size_mb = os.path.getsize(VIDEO_PATH) / (1024 * 1024)
    print(f"Video: {VIDEO_PATH}  ({size_mb:.1f} MB)")

    with tempfile.TemporaryDirectory(prefix="hte_test_") as tmp:
        wav_path = os.path.join(tmp, "audio.wav")

        # --- Step 1: extract audio ---
        print("\n[1/2] Extracting audio …")
        t0 = time.perf_counter()
        extract_audio(VIDEO_PATH, wav_path)
        t1 = time.perf_counter()

        wav_mb = os.path.getsize(wav_path) / (1024 * 1024)
        print(f"  Done in {t1 - t0:.1f}s  →  {wav_path}  ({wav_mb:.1f} MB)")

        # --- Step 2: voice fluctuation scoring ---
        print("\n[2/2] Computing voice fluctuation scores (3-min windows) …")
        t0 = time.perf_counter()
        timeline = calculate_fluctuation_timeline(wav_path, window_sec=180, sr=16000)
        t1 = time.perf_counter()
        print(f"  Done in {t1 - t0:.1f}s  →  {len(timeline)} window(s)\n")

        print(json.dumps(timeline, indent=2))


if __name__ == "__main__":
    main()
