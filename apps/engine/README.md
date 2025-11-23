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

### CLI Mode
```bash
cd apps/engine
python -m src.main
```

### Streamlit UI (Experimental)
```bash
cd apps/engine/experimental/streamlit
streamlit run streamlit_app.py
```

**Note:** Streamlit apps are for local testing only. Production will use the Next.js frontend with a FastAPI/Flask HTTP API wrapper.

## Deployment

### Railway (Backend API)
- **Platform:** Railway
- **Runtime:** Python 3.11+
- **Entry Point:** TBD (FastAPI wrapper)
- **Environment Variables:** See `env/.env.example`

### Future: HTTP API
A FastAPI wrapper will expose these endpoints:
- `POST /api/jobs` - Create audiobook generation job
- `GET /api/jobs/{job_id}` - Get job status
- `GET /api/jobs/{job_id}/download` - Download audiobook
- `POST /api/preview` - Generate voice preview

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
- [ ] Phoenix & Peacock dual-voice mode (from husband's repo)
- [ ] Chapter-based generation
- [ ] Regeneration of specific chapters
- [ ] FastAPI HTTP wrapper
- [ ] Supabase integration (jobs table, file storage)
- [ ] Progress tracking (WebSocket/SSE)
- [ ] Audio post-processing (normalization, noise reduction)

---
**Last Updated:** 2025-11-22
