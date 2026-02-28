"""Debug script: print raw CV values per window before normalization so we can
understand why the 3-6 min window scores 0."""

import os
import sys
import tempfile

import librosa
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from app.services.audio_utils import extract_audio
from app.services.voice_analysis import _compute_cv_pitch, _compute_cv_energy

VIDEO_PATH = os.path.join(os.path.dirname(__file__), "class observation.mp4")
WINDOW_SEC = 180
SR = 16000


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="hte_dbg_") as tmp:
        wav_path = os.path.join(tmp, "audio.wav")
        extract_audio(VIDEO_PATH, wav_path)

        y, sr = librosa.load(wav_path, sr=SR, mono=True)
        total_samples = len(y)
        window_samples = WINDOW_SEC * sr
        duration = total_samples / sr

        print(f"Total duration: {duration:.1f}s  ({duration/60:.1f} min)")
        print(f"Window size:    {WINDOW_SEC}s")
        print(f"Sample rate:    {sr}\n")
        print(f"{'Window':<12} {'Time':<14} {'CV_pitch':>10} {'CV_energy':>10} {'Raw S':>10} {'RMS_mean':>10} {'Voiced%':>10}")
        print("-" * 82)

        raw_scores = []
        offset = 0
        win_idx = 0
        while offset < total_samples:
            end = min(offset + window_samples, total_samples)
            chunk = y[offset:end]
            t_start = offset / sr
            t_end = end / sr

            cv_pitch = _compute_cv_pitch(chunk, sr)
            cv_energy = _compute_cv_energy(chunk)
            raw_score = 0.6 * cv_pitch + 0.4 * cv_energy

            # Extra diagnostics
            rms = librosa.feature.rms(y=chunk).flatten()
            rms_mean = float(np.mean(rms))

            f0, voiced_flag, _ = librosa.pyin(chunk, fmin=65, fmax=600, sr=sr)
            voiced = f0[np.isfinite(f0) & (f0 > 0)]
            total_frames = len(f0)
            voiced_pct = (len(voiced) / total_frames * 100) if total_frames > 0 else 0

            time_label = f"{t_start/60:.1f}-{t_end/60:.1f}m"
            print(f"  {win_idx:<10} {time_label:<14} {cv_pitch:>10.4f} {cv_energy:>10.4f} {raw_score:>10.4f} {rms_mean:>10.6f} {voiced_pct:>9.1f}%")

            raw_scores.append(raw_score)
            offset = end
            win_idx += 1

        s_min = min(raw_scores)
        s_max = max(raw_scores)
        print(f"\nRaw score range: [{s_min:.4f}, {s_max:.4f}]  (spread: {s_max - s_min:.4f})")
        print("\nNormalized scores:")
        for i, s in enumerate(raw_scores):
            if s_max - s_min < 1e-9:
                norm = 50.0
            else:
                norm = (s - s_min) / (s_max - s_min) * 100
            print(f"  Window {i}: {norm:.2f}")


if __name__ == "__main__":
    main()
