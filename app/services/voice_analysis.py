"""Voice fluctuation analysis using librosa.

Algorithm overview
------------------
The recording is split into fixed-width windows (default 3 minutes).  For each
window we measure two kinds of vocal variation:

1.  **Pitch variation** — the Coefficient of Variation (CV) of the fundamental
    frequency f0, ignoring unvoiced frames.
        CV_pitch = std(f0) / mean(f0)

2.  **Energy variation** — the CV of the RMS energy envelope.
        CV_energy = std(E) / mean(E)

The two are combined into a single raw score:
    S = 0.6 * CV_pitch + 0.4 * CV_energy

After all windows are scored, the raw values are min-max normalised to the
[0, 100] range so the frontend receives an intuitive scale.
"""

from __future__ import annotations

import logging

import librosa
import numpy as np

logger = logging.getLogger(__name__)

# Human speech typically falls in the 65-600 Hz range.
_FMIN = 65.0
_FMAX = 600.0
# Minimum number of voiced frames needed to trust a pitch CV estimate.
_MIN_VOICED_FRAMES = 5


def _compute_cv_pitch(y: np.ndarray, sr: int) -> float:
    """Return the Coefficient of Variation of the fundamental frequency.

    Uses the probabilistic YIN estimator (pyin) which returns NaN for frames
    it considers unvoiced, making it straightforward to filter silence.

    Parameters
    ----------
    y  : audio time-series (mono)
    sr : sample rate

    Returns
    -------
    CV of f0, or 0.0 when there are too few voiced frames.
    """
    f0, voiced_flag, _ = librosa.pyin(
        y, fmin=_FMIN, fmax=_FMAX, sr=sr,
    )

    # Keep only voiced frames (non-NaN, positive f0).
    voiced = f0[np.isfinite(f0) & (f0 > 0)]

    if len(voiced) < _MIN_VOICED_FRAMES:
        return 0.0

    mean_f0 = float(np.mean(voiced))
    if mean_f0 == 0:
        return 0.0

    return float(np.std(voiced) / mean_f0)


def _compute_cv_energy(y: np.ndarray) -> float:
    """Return the Coefficient of Variation of the RMS energy envelope.

    librosa.feature.rms returns a 2-D array of shape (1, n_frames); we
    flatten it before computing statistics.

    Parameters
    ----------
    y : audio time-series (mono)

    Returns
    -------
    CV of E, or 0.0 when mean energy is near zero (silence).
    """
    rms = librosa.feature.rms(y=y).flatten()
    mean_e = float(np.mean(rms))

    if mean_e < 1e-8:
        return 0.0

    return float(np.std(rms) / mean_e)


def calculate_fluctuation_timeline(
    wav_path: str,
    window_sec: int = 180,
    sr: int = 16000,
) -> list[dict]:
    """Compute a voice-fluctuation score for each window of the recording.

    Parameters
    ----------
    wav_path   : path to a mono WAV file
    window_sec : window length in seconds (default 180 = 3 minutes)
    sr         : sample rate to load at

    Returns
    -------
    List of dicts with keys ``timestamp_start``, ``timestamp_end``, and
    ``fluctuation_score`` (0-100 normalised).
    """
    y, sr = librosa.load(wav_path, sr=sr, mono=True)
    total_samples = len(y)
    window_samples = window_sec * sr
    total_duration = total_samples / sr

    raw_scores: list[float] = []
    windows: list[tuple[float, float]] = []

    offset = 0
    while offset < total_samples:
        end = min(offset + window_samples, total_samples)
        chunk = y[offset:end]

        t_start = offset / sr
        t_end = end / sr

        cv_pitch = _compute_cv_pitch(chunk, sr)
        cv_energy = _compute_cv_energy(chunk)

        raw_score = 0.6 * cv_pitch + 0.4 * cv_energy

        raw_scores.append(raw_score)
        windows.append((t_start, t_end))

        offset = end

    # --- Min-max normalisation to [0, 100] ---
    scores_arr = np.array(raw_scores)
    s_min = float(scores_arr.min())
    s_max = float(scores_arr.max())

    if s_max - s_min < 1e-9:
        normalised = [50.0] * len(raw_scores)
    else:
        normalised = [
            round(float((s - s_min) / (s_max - s_min)) * 100, 2)
            for s in raw_scores
        ]

    timeline = [
        {
            "timestamp_start": round(t_start, 2),
            "timestamp_end": round(t_end, 2),
            "fluctuation_score": score,
        }
        for (t_start, t_end), score in zip(windows, normalised)
    ]

    logger.info(
        "Computed fluctuation for %.1fs audio: %d windows", total_duration, len(timeline),
    )
    return timeline
