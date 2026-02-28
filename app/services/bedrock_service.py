import base64
import json
import logging
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import Settings

logger = logging.getLogger(__name__)


class BedrockTranscriptionService:
    """Client wrapper for AWS Bedrock speech-to-text transcription.

    The payload structure below is a placeholder that follows the expected
    Bedrock invoke_model contract.  Swap the field names / nesting once the
    exact model schema is finalized.
    """

    def __init__(self, settings: Settings) -> None:
        self._model_id = settings.bedrock_model_id
        self._client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )

    def transcribe(self, audio_path: str) -> str:
        """Send a WAV file to Bedrock and return the transcribed text."""
        audio_bytes = Path(audio_path).read_bytes()
        base64_audio = base64.b64encode(audio_bytes).decode("utf-8")

        # ------------------------------------------------------------------
        # Placeholder payload — update keys to match the real model's schema.
        # ------------------------------------------------------------------
        payload = {
            "inputAudio": {
                "format": "wav",
                "data": base64_audio,
            },
            "taskType": "transcription",
            "outputConfig": {"textFormat": "plain"},
        }

        try:
            response = self._client.invoke_model(
                modelId=self._model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload),
            )
        except (ClientError, BotoCoreError) as exc:
            logger.error("Bedrock invocation failed: %s", exc)
            raise RuntimeError(f"AWS Bedrock transcription error: {exc}") from exc

        response_body = json.loads(response["body"].read())

        # ------------------------------------------------------------------
        # Extract the transcript — adjust the key path for the real model.
        # ------------------------------------------------------------------
        transcript: str = response_body.get("transcript", response_body.get("text", ""))
        return transcript
