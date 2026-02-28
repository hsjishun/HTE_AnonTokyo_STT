"""Amazon Transcribe Streaming integration.

Streams a 16 kHz mono PCM WAV file directly to Amazon Transcribe using the
``amazon-transcribe`` SDK.  No S3 bucket is needed — audio bytes are sent
over a WebSocket-based stream and transcript segments are returned in
near-real-time.
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent

from app.config import Settings

logger = logging.getLogger(__name__)

_CHUNK_SIZE = 16 * 1024  # 16 KB per audio event
_WAV_HEADER_SIZE = 44    # Standard WAV header to skip


class _TranscriptCollector(TranscriptResultStreamHandler):
    """Receives transcript events and keeps only final (non-partial) results."""

    def __init__(self, output_stream) -> None:
        super().__init__(output_stream)
        self.segments: list[str] = []

    async def handle_transcript_event(self, transcript_event: TranscriptEvent) -> None:
        results = transcript_event.transcript.results
        for result in results:
            if not result.is_partial:
                for alt in result.alternatives:
                    self.segments.append(alt.transcript)


class TranscribeService:
    """Thin wrapper around the Amazon Transcribe Streaming SDK."""

    def __init__(self, settings: Settings) -> None:
        self._region = settings.aws_region
        self._language_code = settings.transcribe_language_code

        if settings.aws_access_key_id and settings.aws_secret_access_key:
            os.environ.setdefault("AWS_ACCESS_KEY_ID", settings.aws_access_key_id)
            os.environ.setdefault("AWS_SECRET_ACCESS_KEY", settings.aws_secret_access_key)
        if settings.aws_region:
            os.environ.setdefault("AWS_DEFAULT_REGION", settings.aws_region)

    async def transcribe(self, audio_path: str) -> str:
        """Stream a WAV file to Amazon Transcribe and return the transcript."""
        client = TranscribeStreamingClient(region=self._region)

        stream = await client.start_stream_transcription(
            language_code=self._language_code,
            media_sample_rate_hz=16000,
            media_encoding="pcm",
        )

        async def _send_audio() -> None:
            audio_bytes = Path(audio_path).read_bytes()
            # Skip the 44-byte WAV header so we send raw PCM only.
            raw_pcm = audio_bytes[_WAV_HEADER_SIZE:]

            for offset in range(0, len(raw_pcm), _CHUNK_SIZE):
                chunk = raw_pcm[offset : offset + _CHUNK_SIZE]
                await stream.input_stream.send_audio_event(audio_chunk=chunk)

            await stream.input_stream.end_stream()

        collector = _TranscriptCollector(stream.output_stream)

        await asyncio.gather(_send_audio(), collector.handle_events())

        transcript = " ".join(collector.segments).strip()
        logger.info(
            "Transcription complete: %d segments, %d chars",
            len(collector.segments),
            len(transcript),
        )
        return transcript
