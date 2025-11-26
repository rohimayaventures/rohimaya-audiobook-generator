# Rohimaya Audiobook Generator - Python Engine

## Overview

Python-based audiobook generation engine with multi-provider TTS support, intelligent text chunking, and audio post-processing.

## Directory Structure

```
apps/engine/
├── src/                      # Core engine modules
│   ├── chunker.py           # Text chunking (sentence-aware)
│   ├── text_cleaner.py      # Text preprocessing
│   ├── tts_provider.py      # TTS provider abstraction (multi-provider w/ fallback)
│   ├── tts_openai.py        # OpenAI TTS integration
│   ├── tts_elevenlabs.py    # ElevenLabs TTS integration
│   ├── tts_inworld.py       # Inworld TTS integration
│   ├── merge_audio.py       # Audio merging (pydub)
│   ├── rate_limiter.py      # API rate limiting
│   ├── cost_tracker.py      # Cost tracking
│   └── main.py              # CLI entry point
│
├── core/                     # Shared utilities (from husband's code)
│   ├── chapter_parser.py    # Chapter extraction and dialogue detection
│   └── advanced_chunker.py  # Dual-limit chunking algorithm
│
├── pipelines/                # Generation workflows
│   ├── standard_single_voice.py      # Full-book, single narrator
│   └── phoenix_peacock_dual_voice.py # Character-aware dual-voice
│
├── api/                      # FastAPI HTTP wrapper (NEW)
│   ├── __init__.py
│   └── main.py              # Production HTTP API
│
├── experimental/
│   └── streamlit/           # Legacy Streamlit UI apps
│       ├── streamlit_app.py           # Main working app (OpenAI TTS)
│       ├── streamlit_app_v2.py        # Alternative version
│       ├── streamlit_app_ultimate.py  # Enhanced version
│       └── .streamlit/
│           └── secrets.toml.example
│
├── config.yaml              # Application configuration
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Features

### Core Capabilities
- ✅ Multi-provider TTS with automatic fallback
- ✅ Intelligent text chunking (sentence-aware, ~1500 chars)
- ✅ Audio merging with pydub
- ✅ Thread-safe rate limiting (60 RPM default)
- ✅ Cost tracking per provider
- ✅ Support for OpenAI, ElevenLabs, Inworld TTS

### TTS Providers
| Provider | Voices | Cost (per 1K chars) | Quality |
|----------|--------|---------------------|---------|
| OpenAI TTS-1 | alloy, echo, fable, onyx, nova, shimmer | $0.015 | Good |
| ElevenLabs | Custom | Variable | Excellent |
| Inworld | Multiple | $0.15 | Good |

## Installation

```bash
cd apps/engine
pip install -r requirements.txt
```

**Dependencies:**
- Python 3.8+
- ffmpeg (must be in PATH for audio processing)

## Configuration

### 1. Environment Variables
Copy `env/.env.example` to `env/.env` and configure:

```bash
OPENAI_API_KEY=your_key_here
ELEVENLABS_API_KEY=your_key_here  # Optional
INWORLD_API_KEY=your_key_here     # Optional
```

### 2. Application Config
Edit `config.yaml` to configure:
- TTS providers (enabled, priority, rate limits)
- Processing settings (chunk size, max workers, parallel mode)
- Audio output settings (format, bitrate, sample rate)

## Usage

### 1. FastAPI HTTP API (Production)

Run the HTTP API server:

```bash
# From repo root
cd apps/engine
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Or run directly:

```bash
python -m api.main
```

**API Endpoints:**
- `GET /health` - Health check (status, version, timestamp)
- `POST /jobs/test` - Test job creation (validation stub)
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API docs (ReDoc)

**Test the API:**
```bash
# Health check
curl http://localhost:8000/health

# Create test job
curl -X POST http://localhost:8000/jobs/test \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "mode": "single_voice"}'
```

**Environment Variables:**
- `ALLOWED_ORIGINS` - CORS allowed origins (default: `http://localhost:3000`)
- `API_HOST` - API host (default: `0.0.0.0`)
- `API_PORT` - API port (default: `8000`)
- `ENVIRONMENT` - Environment mode (development/production)

### 2. CLI Mode (Legacy)
```bash
cd apps/engine
python -m src.main
```

### 3. Streamlit UI (Experimental)
```bash
cd apps/engine/experimental/streamlit
streamlit run streamlit_app.py
```

**Note:** Streamlit apps are for local testing only. Production uses the Next.js frontend (apps/web) with the FastAPI backend.

## Deployment

### Railway (Backend API)
- **Platform:** Railway
- **Runtime:** Python 3.11+
- **Entry Point:** `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables:** See `env/.env.example`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

**Railway Configuration:**
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn api.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

### Planned API Endpoints (v1.0)
Future production endpoints:
- ✅ `GET /health` - Health check (IMPLEMENTED)
- ✅ `POST /jobs/test` - Test job creation (IMPLEMENTED)
- ⏳ `POST /jobs` - Create audiobook generation job
- ⏳ `GET /jobs/{job_id}` - Get job status
- ⏳ `GET /jobs/{job_id}/download` - Download audiobook
- ⏳ `POST /preview` - Generate voice preview (3-5 seconds)
- ⏳ `GET /voices` - List available TTS voices

## Architecture

### Text Processing Pipeline
1. **Upload** → Manuscript file (TXT, DOCX, PDF)
2. **Clean** → Remove formatting, normalize text
3. **Chunk** → Split into ~1500 char chunks (sentence-aware)
4. **TTS** → Generate audio for each chunk (parallel)
5. **Merge** → Concatenate audio chunks
6. **Export** → Final audiobook (MP3, M4B, etc.)

### TTS Provider Abstraction
```python
from src.tts_provider import TTSManager

config = {
    'openai_api_key': 'sk-...',
    'elevenlabs_api_key': '...'
}

manager = TTSManager(config)
audio_bytes = manager.synthesize_with_fallback(text, voice_id="alloy")
```

## Cost Optimization
- Chunk size: 1500 chars (balances quality vs API calls)
- Rate limiting: 60 RPM (prevents throttling)
- Automatic fallback: Tries cheaper providers first

## Future Enhancements
- [x] Phoenix & Peacock dual-voice mode (IMPLEMENTED in `pipelines/`)
- [x] Chapter-based generation (IMPLEMENTED in `core/chapter_parser.py`)
- [x] FastAPI HTTP wrapper (IMPLEMENTED in `api/main.py`)
- [ ] Full job orchestration (create, poll, download)
- [ ] Supabase integration (jobs table, file storage)
- [ ] Progress tracking (WebSocket/SSE)
- [ ] Audio post-processing (normalization, noise reduction)
- [ ] Regeneration of specific chapters
- [ ] Voice preview generation (3-5 sec samples)

---
**Last Updated:** 2025-11-22
