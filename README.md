# Teacher Performance Dashboard — Backend API

FastAPI service that accepts a classroom video recording (`.mp4`), transcribes
the audio via AWS Bedrock, and computes a **Voice Fluctuation Score** measuring
pitch and energy variation over time.

## Prerequisites

- Python 3.10+
- [ffmpeg](https://ffmpeg.org/download.html) installed and available on `PATH`
- AWS credentials with access to Bedrock

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
copy .env.example .env       # Windows
# cp .env.example .env       # macOS / Linux
# Then edit .env with your AWS credentials and model ID
```

## Running the Server

```bash
uvicorn app.main:app --reload
```

The API docs are available at [http://localhost:8000/docs](http://localhost:8000/docs).

## API Usage

### `POST /api/v1/analyze-teaching`

Upload an `.mp4` file and receive the transcript plus a fluctuation timeline.

```bash
curl -X POST http://localhost:8000/api/v1/analyze-teaching \
  -F "file=@classroom_recording.mp4"
```

**Response**

```json
{
  "status": "success",
  "transcript": "Good morning class, today we will...",
  "fluctuation_timeline": [
    {"timestamp_start": 0, "timestamp_end": 180, "fluctuation_score": 75.3},
    {"timestamp_start": 180, "timestamp_end": 360, "fluctuation_score": 62.1}
  ]
}
```

## Project Structure

```
app/
├── main.py               # FastAPI application entry point
├── config.py             # Pydantic Settings (env vars)
├── routes/
│   └── analyze.py        # POST /api/v1/analyze-teaching
├── services/
│   ├── audio_utils.py    # ffmpeg MP4 → WAV extraction
│   ├── bedrock_service.py# AWS Bedrock transcription client
│   └── voice_analysis.py # Librosa pitch/energy fluctuation
└── schemas/
    └── response.py       # Pydantic response models
```
