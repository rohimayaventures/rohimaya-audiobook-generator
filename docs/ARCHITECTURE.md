# 🏗️ Rohimaya Audiobook Generator - Architecture

## System Overview
```
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT UI LAYER                        │
│  File Upload • Voice Selection • Progress • Download        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              ORCHESTRATION (Prasad's main.py)                │
│  Coordinates entire pipeline • Error recovery                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│           TEXT PROCESSING (Prasad's Core)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ Text Cleaner │→ │Smart Chunker │→ │ Verify Chunks   │  │
│  │ Remove junk  │  │ Preserve     │  │ Quality check   │  │
│  └──────────────┘  │ sentences    │  └─────────────────┘  │
│                    └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│            TTS ABSTRACTION LAYER (Enhanced)                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                  TTS Manager                            │ │
│  │  • Provider selection                                   │ │
│  │  • Automatic fallback                                   │ │
│  │  • Cost optimization                                    │ │
│  └────────────────────────────────────────────────────────┘ │
│         ↓                    ↓                    ↓          │
│  ┌────────────┐      ┌──────────────┐    ┌──────────────┐ │
│  │  Inworld   │      │   OpenAI     │    │ ElevenLabs   │ │
│  │ (Original) │      │   (Added)    │    │  (Future)    │ │
│  └────────────┘      └──────────────┘    └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│         MONITORING & OPTIMIZATION (Enhanced)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │Rate Limiter  │  │Cost Tracker  │  │ Progress Track  │  │
│  │Prevent API   │  │Real-time     │  │ User feedback   │  │
│  │throttling    │  │costs         │  │                 │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│         POST-PROCESSING (Prasad's Core)                      │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ Audio Merger │→ │ ACX Format   │→ Final MP3             │
│  │ Stitch all   │  │ 44.1kHz      │                        │
│  │ chunks       │  │ 192kbps      │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Streamlit UI Layer
**File:** `streamlit_app.py`

**Responsibilities:**
- File upload interface
- Voice selection dropdown
- Settings configuration
- Progress visualization
- Audio preview/download
- Cost display

**Technologies:**
- Streamlit 1.29.0
- Custom CSS (Rohimaya branding)
- Session state management

---

### 2. Text Processing (Prasad's Core)

#### 2.1 Text Cleaner
**File:** `src/text_cleaner.py`

**Functions:**
- Remove formatting artifacts
- Fix punctuation
- Normalize whitespace
- Preserve paragraph structure

#### 2.2 Smart Chunker
**File:** `src/chunker.py`

**Functions:**
- Split text into ~1500 char chunks
- Preserve sentence boundaries
- Maintain paragraph context
- Handle edge cases

#### 2.3 Chunk Verifier
**File:** `src/verify_chunks.py`

**Functions:**
- Validate chunk integrity
- Check for missing content
- Quality assurance

---

### 3. TTS Abstraction Layer (Enhanced)

#### 3.1 TTS Manager
**File:** `src/tts_provider.py`

**Class:** `TTSManager`

**Methods:**
```python
synthesize_with_fallback(text, voice_id) -> bytes
    Try each provider until success

get_cheapest_provider(text) -> TTSProvider
    Return lowest cost provider

get_all_voices() -> Dict
    Get voices from all providers
```

#### 3.2 Provider Implementations

**OpenAI Provider**
**File:** `src/tts_openai.py`
```python
class OpenAIProvider(TTSProvider):
    VOICES = {
        "alloy": "Neutral, balanced",
        "echo": "Male, clear",
        # ... 6 total voices
    }
    
    def synthesize(text, voice_id):
        # Call OpenAI TTS API
        
    def estimate_cost(text):
        # $0.015 per 1K chars
```

**Inworld Provider**
**File:** `src/tts_inworld.py` (Prasad's original)

---

### 4. Monitoring & Optimization (Enhanced)

#### 4.1 Rate Limiter
**File:** `src/rate_limiter.py`

**Purpose:** Prevent API throttling

**Implementation:**
```python
class RateLimiter:
    def __init__(self, max_rpm=60):
        self.request_times = deque()
    
    def wait_if_needed():
        # Sleep if at limit
        # Thread-safe
```

#### 4.2 Cost Tracker
**File:** `src/cost_tracker.py`

**Purpose:** Track real-time costs

**Implementation:**
```python
class CostTracker:
    RATES = {
        'inworld': 0.15,
        'openai': 0.015
    }
    
    def track(provider, text):
        # Record usage
    
    def get_summary():
        # Return totals
```

---

### 5. Audio Post-Processing (Prasad's Core)

#### 5.1 Audio Merger
**File:** `src/merge_audio.py`

**Functions:**
- Concatenate all chunks
- Normalize volume
- Export to MP3

**Dependencies:**
- pydub
- ffmpeg

---

## Data Flow

### Generation Flow
```
1. User uploads manuscript.txt
   ↓
2. Text cleaner removes artifacts
   ↓
3. Smart chunker creates chunk_001.txt, chunk_002.txt, ...
   ↓
4. For each chunk:
   a. Rate limiter checks if safe to proceed
   b. TTS Manager synthesizes → part_001.mp3
   c. Cost tracker records usage
   ↓
5. Audio merger combines all parts → audiobook.mp3
   ↓
6. User downloads final audiobook
```

### Error Handling Flow
```
TTS Request → Provider 1 (Inworld)
              ↓
           FAILS?
              ↓
         Provider 2 (OpenAI)
              ↓
           SUCCESS → Return audio
              ↓
           FAILS?
              ↓
         Raise Exception
```

---

## Configuration

### config.yaml Structure
```yaml
providers:
  inworld:
    enabled: true
    priority: 1
  openai:
    enabled: true
    priority: 2

processing:
  chunk_size: 1500
  parallel: false  # Future

output:
  format: mp3
  sample_rate: 44100
  bitrate: 192
```

---

## API Keys & Secrets

### .streamlit/secrets.toml
```toml
[openai]
api_key = "sk-..."

[inworld]
api_key = "..."
```

**Security:**
- Never commit secrets.toml
- Use .gitignore
- Streamlit Cloud secrets management

---

## Performance Characteristics

### Current Performance
- **Speed:** ~3 seconds per chunk
- **Throughput:** ~20 chunks/minute (rate limited)
- **Cost:** $0.015 per 1K characters (OpenAI)

### Example: 80,000-word novel
- **Characters:** ~400,000
- **Chunks:** ~267
- **Time:** ~13 minutes (sequential)
- **Cost:** ~$6

### Future Optimization
- **Parallel processing:** 5 workers = ~3 minutes
- **Provider optimization:** Choose cheapest = ~$2

---

## Deployment Architecture

### Development
```
Local Machine
├── Python 3.10+
├── pip install -r requirements.txt
└── streamlit run streamlit_app.py
```

### Production (Streamlit Cloud)
```
GitHub Repo
    ↓
Streamlit Cloud
    ├── Auto-deploy on push
    ├── Secrets management
    └── Free hosting
```

---

## Dependencies

### Core (Prasad's)
- requests
- python-dotenv
- pydub
- ffmpeg

### Enhanced
- streamlit
- openai
- python-docx

### Future
- elevenlabs (voice cloning)
- anthropic (Claude for text analysis)

---

## Scalability Considerations

### Current Limits
- Streamlit Cloud: ~1GB RAM
- OpenAI TTS: 500 req/min
- File size: ~50MB manuscripts

### Scale to 1000+ users
- Move to Cloudflare Workers
- Use queue system (Cloudflare Queues)
- Store audio in R2
- CDN delivery

---

## Security

### Current Measures
- API keys in secrets (not code)
- User files in temp directories
- Auto-cleanup after generation

### Future Enhancements
- User authentication (Supabase)
- File encryption at rest
- Rate limiting per user
- Usage quotas

---

## Testing Strategy

### Manual Testing
- Upload various file formats
- Test different voices
- Verify cost calculations
- Check audio quality

### Automated Testing (Future)
- Unit tests for each module
- Integration tests
- Load testing
- Audio quality metrics

---

## Monitoring & Observability

### Current
- Streamlit progress bars
- Console logging
- Cost tracking in UI

### Future
- Error tracking (Sentry)
- Usage analytics
- Performance monitoring
- User feedback system

---

## Questions & Feedback

For Prasad or contributors:

1. **Architecture:** Does the abstraction layer make sense?
2. **Performance:** Any optimization suggestions?
3. **Code Quality:** Improvements needed?
4. **Features:** What should we add next?

**Contact:** rohimayapublishing@gmail.com

---

**Documentation Version:** 1.0  
**Last Updated:** November 2025  
**Maintained By:** Rohimaya Publishing Team
