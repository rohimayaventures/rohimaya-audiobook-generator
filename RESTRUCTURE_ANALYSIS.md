# Rohimaya Audiobook Generator - Restructure Analysis

**Date:** 2025-11-22
**Analyzed By:** Claude (VS Code Assistant)
**Status:** Step 1 - Initial Analysis Complete (Awaiting Approval)

---

## 1. Backup Status

✅ **Original Repository Backed Up**
- Location: `_backup_original_repo/`
- Files backed up: 17 Python files + all config/docs/examples
- Status: **Read-only reference - DO NOT MODIFY**

---

## 2. Current Repository Structure

```
rohimaya-audiobook-generator/
├── _backup_original_repo/        [NEW - Complete backup]
│
├── src/                           [ENGINE - Core audiobook generation logic]
│   ├── chunker.py                 ├─ Text chunking (splits text into manageable pieces)
│   ├── text_cleaner.py            ├─ Text preprocessing/cleaning
│   ├── verify_chunks.py           ├─ Chunk validation
│   ├── truncate_sample.py         ├─ Sample text truncation
│   │
│   ├── tts_provider.py            ├─ TTS abstraction layer (multi-provider support)
│   ├── tts_openai.py              ├─ OpenAI TTS integration
│   ├── tts_elevenlabs.py          ├─ ElevenLabs TTS integration
│   ├── tts_inworld.py             ├─ Inworld TTS integration
│   │
│   ├── merge_audio.py             ├─ Audio merging (pydub-based)
│   ├── convert.py                 ├─ Audio conversion utilities
│   │
│   ├── rate_limiter.py            ├─ API rate limiting (thread-safe, 60 RPM default)
│   ├── cost_tracker.py            ├─ Cost tracking per provider
│   │
│   └── main.py                    └─ CLI entry point (orchestrates full workflow)
│
├── streamlit_app.py               [UI - Main working Streamlit app]
├── streamlit_app_v2.py            [UI - Alternative version]
├── streamlit_app_ultimate.py      [UI - Enhanced version]
├── streamlit_app_broken_backup.py [UI - Broken backup (archive candidate)]
├── .streamlit/
│   └── secrets.toml.example       [UI CONFIG - API keys template for Streamlit]
│
├── config.yaml                    [CONFIG - App settings: providers, processing, branding]
├── requirements.txt               [DEPS - Python dependencies (Streamlit, OpenAI, etc.)]
├── requirements_original.txt      [DEPS - Legacy dependencies]
│
├── docs/
│   ├── ARCHITECTURE.md            [DOCS - Architecture documentation]
│   ├── DEPLOYMENT.md              [DOCS - Deployment guide]
│   ├── ENHANCEMENTS.md            [DOCS - Enhancement ideas]
│   └── INTEGRATION_GUIDE.md       [DOCS - Integration guide]
│
├── examples/
│   ├── DEMO_SCRIPT.md             [EXAMPLES - Demo instructions]
│   └── sample_manuscript.txt      [EXAMPLES - Sample input]
│
├── README.md                      [DOCS - Main project overview]
├── QUICKSTART.md                  [DOCS - Quick start guide]
├── EPIC_VICTORY.md                [DOCS - Project narrative/history]
├── LICENSE                        [METADATA]
│
└── AudioBook_TTS_OpenAI_Peacock_Pheonix-main.zip  [HUSBAND'S REPO - To be analyzed in Step 4]
```

---

## 3. Component Analysis

### 3.1 ENGINE CODE (`src/` folder)

**Text Processing Pipeline:**
- **chunker.py** (55 lines)
  - Splits large text into ~1500 character chunks
  - Breaks on sentence boundaries (". " delimiter)
  - Outputs numbered files: `chunk_001.txt`, `chunk_002.txt`, etc.
  - **Import pattern:** None (standalone utility)

- **text_cleaner.py** (referenced in Streamlit apps)
  - Text preprocessing/normalization
  - Called before chunking

- **verify_chunks.py**
  - Validates chunk integrity
  - Ensures no data loss during splitting

- **truncate_sample.py**
  - Generates sample/preview versions

---

**TTS Provider System (Multi-Provider Abstraction):**

- **tts_provider.py** (53 lines) - **CRITICAL ARCHITECTURE**
  - Defines `TTSProvider` abstract base class
  - Implements `TTSManager` with automatic fallback
  - Supports multiple providers with priority ordering
  - **Key Features:**
    - Abstract methods: `synthesize()`, `get_available_voices()`, `estimate_cost()`
    - Fallback logic: tries providers in order until success
    - Dynamic provider initialization based on config

- **tts_openai.py**
  - Implements OpenAI TTS-1 API
  - Voices: alloy, echo, fable, onyx, nova, shimmer
  - Rate: $0.015 per 1K characters

- **tts_elevenlabs.py**
  - ElevenLabs integration
  - Higher quality, higher cost

- **tts_inworld.py**
  - Inworld TTS integration
  - Used in original `main.py` workflow

**Import pattern in tts_provider.py:**
```python
from src.tts_inworld import InworldProvider
from src.tts_openai import OpenAIProvider
from src.tts_elevenlabs import ElevenLabsProvider
```
⚠️ **Will need updating after move to `apps/engine/`**

---

**Audio Processing:**

- **merge_audio.py** (52 lines)
  - Uses `pydub` to concatenate MP3 files
  - Looks for `output_part_*.mp3` pattern
  - Exports final merged audiobook
  - **Dependency:** Requires ffmpeg in PATH

- **convert.py**
  - Audio format conversion utilities

---

**Infrastructure:**

- **rate_limiter.py** (36 lines)
  - Thread-safe rate limiting
  - Default: 60 requests/minute
  - Uses `collections.deque` for sliding window
  - Smart waiting: sleeps only when necessary

- **cost_tracker.py** (51 lines)
  - Tracks costs per provider
  - Hardcoded rates:
    - Inworld: $0.15/1K chars
    - OpenAI: $0.015/1K chars
  - Maintains running totals

---

**Entry Point:**

- **main.py** (62 lines)
  - CLI workflow orchestrator
  - Hardcoded input path: `input/Eclipse_of_Fire_and_Wings_AUDIOBOOK.txt`
  - 3-step workflow:
    1. Chunk text → `chunk_text_file()`
    2. Synthesize audio → `synthesize_with_inworld()`
    3. Merge audio → `merge_audio_files()`
  - **Import pattern:** Relative imports
    ```python
    from chunker import chunk_text_file
    from tts_inworld import synthesize_with_inworld
    from merge_audio import merge_audio_files
    ```
  - ⚠️ **Will need updating after move**

---

### 3.2 STREAMLIT UI CODE

**Four Streamlit Applications:**

1. **streamlit_app.py** (145 lines) - **MAIN WORKING APP**
   - Clean, minimal UI
   - OpenAI TTS only (proven working)
   - Imports from `src.*`:
     ```python
     from src.chunker import chunk_text_file
     from src.text_cleaner import clean_text
     from src.merge_audio import merge_audio_files
     ```
   - Uses Streamlit secrets for API keys: `st.secrets["openai"]["api_key"]`
   - File upload → clean → chunk → TTS → merge → download
   - Voice selection: alloy, echo, fable, onyx, nova, shimmer

2. **streamlit_app_v2.py**
   - Alternative implementation

3. **streamlit_app_ultimate.py**
   - Enhanced version with additional features

4. **streamlit_app_broken_backup.py**
   - Broken version (candidate for archival only)

**Streamlit Config:**
- `.streamlit/secrets.toml.example`
  - Template for API keys (OpenAI, Inworld, ElevenLabs)
  - Used by Streamlit apps to load credentials

---

### 3.3 CONFIGURATION FILES

**config.yaml** (39 lines)
- **Purpose:** Application-level configuration
- **Sections:**
  - `providers`: TTS provider settings (Inworld, OpenAI)
    - Each has: `enabled`, `priority`, `rate_limit`
  - `processing`: Chunk size (1500), max workers (5), parallel settings
  - `output`: Audio format settings (MP3, 192kbps, 44.1kHz, stereo, normalization)
  - `branding`: Rohimaya colors & fonts
    - Phoenix Orange: #FF8C42
    - Peacock Teal: #4A9B9B
    - Midnight Navy: #1A1A2E
    - Cream: #FFF8E7

**requirements.txt** (23 lines)
- Core dependencies:
  - `streamlit==1.29.0` (UI framework)
  - `openai==1.6.1` (TTS provider)
  - `elevenlabs==1.0.0` (TTS provider)
  - `pydub==0.25.1` (audio merging)
  - `ffmpeg-python==0.2.0` (audio processing)
  - `python-docx==1.1.0`, `pypdf2==3.0.1` (document parsing)
  - `requests==2.31.0`, `python-dotenv==1.0.0` (utilities)

---

### 3.4 DOCUMENTATION

**Root-level docs:**
- **README.md** - Project overview
- **QUICKSTART.md** - Getting started guide
- **EPIC_VICTORY.md** - Project narrative (Browser Claude vs ChatGPT story)
- **LICENSE** - MIT License

**docs/ folder:**
- **ARCHITECTURE.md** - System architecture
- **DEPLOYMENT.md** - Deployment instructions
- **ENHANCEMENTS.md** - Future improvement ideas
- **INTEGRATION_GUIDE.md** - Integration documentation

---

### 3.5 EXAMPLES

**examples/ folder:**
- **DEMO_SCRIPT.md** - Demo walkthrough
- **sample_manuscript.txt** - Sample input text (4.6KB)

---

### 3.6 HUSBAND'S CODE (Not Yet Analyzed)

**AudioBook_TTS_OpenAI_Peacock_Pheonix-main.zip** (535 KB)
- To be analyzed in Step 4
- Expected contents:
  - Full-book generation
  - Per-chapter generation
  - Dual-voice Phoenix & Peacock flows
  - Regeneration + merge scripts

---

## 4. Import Dependency Map

### Current Import Patterns:

**In `src/main.py`:**
```python
from chunker import chunk_text_file          # Relative import
from tts_inworld import synthesize_with_inworld
from merge_audio import merge_audio_files
```

**In `src/tts_provider.py`:**
```python
from src.tts_inworld import InworldProvider   # Absolute from src
from src.tts_openai import OpenAIProvider
from src.tts_elevenlabs import ElevenLabsProvider
```

**In Streamlit apps:**
```python
from src.chunker import chunk_text_file       # Absolute from src
from src.text_cleaner import clean_text
from src.merge_audio import merge_audio_files
from openai import OpenAI                      # External library
```

### ⚠️ Import Updates Needed After Restructure:

When moving to `apps/engine/`, imports will need to change:

**Option 1: Keep `src` as internal package name**
```python
# Inside apps/engine/src/main.py
from .chunker import chunk_text_file
from .tts_inworld import synthesize_with_inworld
from .merge_audio import merge_audio_files
```

**Option 2: Flatten to `apps/engine/` (simpler)**
```python
# Inside apps/engine/main.py
from chunker import chunk_text_file
from tts_inworld import synthesize_with_inworld
from merge_audio import merge_audio_files
```

**Recommendation:** Keep the `src/` folder inside `apps/engine/` to maintain structure.

---

## 5. Technical Debt & Improvement Opportunities

### 5.1 Current Issues

❌ **Hardcoded Paths:**
- `main.py` has hardcoded input: `input/Eclipse_of_Fire_and_Wings_AUDIOBOOK.txt`
- Should use command-line arguments or config

❌ **Mixed Import Styles:**
- `main.py`: relative imports
- `tts_provider.py`: absolute `from src.*`
- Streamlit apps: absolute `from src.*`
- Should standardize after restructure

❌ **No Environment Variable Support in Engine:**
- Streamlit apps use `st.secrets`
- Engine code doesn't use `.env` files yet
- Should add `python-dotenv` support in engine

❌ **Multiple Streamlit App Versions:**
- 4 different versions exist
- `streamlit_app_broken_backup.py` should be archived
- Should document which is "canonical"

❌ **No HTTP API Yet:**
- Engine is CLI/library only
- Need FastAPI/Flask wrapper for Railway deployment

---

### 5.2 Strengths to Preserve

✅ **Clean Provider Abstraction:**
- `TTSProvider` ABC is well-designed
- Easy to add new providers
- Automatic fallback is robust

✅ **Modular Text Processing:**
- Chunker is reusable
- Clean separation of concerns

✅ **Cost & Rate Limiting:**
- Production-ready features already exist
- Thread-safe implementation

✅ **Good Documentation:**
- README, QUICKSTART, architecture docs
- Clear examples

---

### 5.3 Recommended Improvements (Future)

**Infrastructure:**
- ✨ Add environment variable support (`.env` files)
- ✨ Create FastAPI wrapper for HTTP endpoints
- ✨ Add structured logging (replace `print()` statements)
- ✨ Add comprehensive error handling
- ✨ Add unit tests for core modules

**Architecture:**
- ✨ Centralize configuration (move from hardcoded to config files)
- ✨ Add job queue system (for async processing)
- ✨ Add progress tracking (for long-running jobs)
- ✨ Integrate with Supabase for:
  - Job management (jobs table)
  - File storage (audio bucket)
  - User management

**Code Quality:**
- ✨ Standardize import style
- ✨ Add type hints throughout
- ✨ Add docstrings to all public functions
- ✨ Remove hardcoded file paths
- ✨ Add input validation

---

## 6. Environment Variables Needed

Based on the code analysis, here are all environment variables needed:

### Supabase (Database & Storage)
```bash
SUPABASE_URL                    # Supabase project URL
SUPABASE_ANON_KEY               # Public anon key (frontend)
SUPABASE_SERVICE_ROLE_KEY       # Service role key (backend only)
SUPABASE_AUDIO_BUCKET           # Bucket for generated audiobooks (e.g. "audiobooks")
SUPABASE_MANUSCRIPTS_BUCKET     # Bucket for uploaded manuscripts (e.g. "manuscripts")
```

### TTS API Keys (Backend)
```bash
OPENAI_API_KEY                  # OpenAI TTS API key
ELEVENLABS_API_KEY              # ElevenLabs API key (optional)
INWORLD_API_KEY                 # Inworld TTS API key (optional)
```

### App Configuration
```bash
NEXT_PUBLIC_ENGINE_API_URL      # Public URL to Railway backend API
FRONTEND_URL                    # Deployed frontend URL (for CORS)
LOG_LEVEL                       # Logging level: debug/info/warn/error
ENVIRONMENT                     # Environment: dev/staging/prod
```

### Processing (Optional)
```bash
CHUNK_SIZE                      # Text chunk size (default: 1500)
MAX_WORKERS                     # Parallel workers (default: 5)
RATE_LIMIT_RPM                  # API rate limit (default: 60)
```

---

## 7. Next Steps (Pending Your Approval)

### Step 2: Monorepo Mapping Plan
Once you approve this analysis, I will:

1. Propose detailed file mapping from current → target structure
2. Identify exactly which imports need updating
3. Create migration checklist
4. Document any risks or edge cases

### Key Questions for You:

1. ✅ Does this analysis accurately capture your current repo?
2. ✅ Should we keep `src/` as a subfolder inside `apps/engine/`, or flatten it?
3. ✅ Which Streamlit app is the "canonical" one? (I assume `streamlit_app.py`)
4. ✅ Are there any other files/folders I missed?

---

## 8. Summary

✅ **Backup Complete:** All original code preserved in `_backup_original_repo/`

✅ **Structure Identified:**
- 13 Python modules in `src/` (clean engine code)
- 4 Streamlit apps (experimental UI)
- Strong TTS provider abstraction
- Good documentation

✅ **Ready for Restructure:**
- Clear separation between engine and UI
- Minimal import dependencies
- No database code yet (clean slate for Supabase)

⏸️ **Awaiting Your Approval** to proceed to Step 2 (Monorepo Mapping Plan)

---

**Status:** ✅ Step 1 Complete - Analysis Ready for Review

---

## 9. Monorepo Mapping Plan (Step 2)

### Target Directory Structure:

```
rohimaya-audiobook-generator/
├── _backup_original_repo/              [✅ CREATED - Original code backup]
├── _backup_peacock_phoenix_repo/       [⏳ TO CREATE - Husband's code backup]
│
├── apps/
│   ├── web/                            [⏳ TO CREATE - Next.js 14 frontend]
│   │   └── README.md                   [Placeholder: "Next.js app coming soon"]
│   │
│   └── engine/                         [⏳ TO CREATE - Python audiobook backend]
│       ├── src/                        [MOVED FROM: ./src/]
│       │   ├── chunker.py
│       │   ├── text_cleaner.py
│       │   ├── verify_chunks.py
│       │   ├── truncate_sample.py
│       │   ├── tts_provider.py
│       │   ├── tts_openai.py
│       │   ├── tts_elevenlabs.py
│       │   ├── tts_inworld.py
│       │   ├── merge_audio.py
│       │   ├── convert.py
│       │   ├── rate_limiter.py
│       │   ├── cost_tracker.py
│       │   └── main.py
│       │
│       ├── experimental/
│       │   └── streamlit/              [MOVED FROM: ./streamlit_app*.py + ./.streamlit/]
│       │       ├── streamlit_app.py
│       │       ├── streamlit_app_v2.py
│       │       ├── streamlit_app_ultimate.py
│       │       ├── streamlit_app_broken_backup.py
│       │       └── .streamlit/
│       │           └── secrets.toml.example
│       │
│       ├── config.yaml                 [MOVED FROM: ./config.yaml]
│       ├── requirements.txt            [MOVED FROM: ./requirements.txt]
│       └── README.md                   [NEW - Engine documentation]
│
├── packages/
│   ├── config/                         [⏳ TO CREATE - Shared config/constants]
│   │   └── README.md                   [Placeholder for shared config]
│   │
│   └── utils/                          [⏳ TO CREATE - Shared utilities]
│       └── README.md                   [Placeholder for shared utils]
│
├── supabase/
│   ├── migrations/                     [⏳ TO CREATE - SQL migrations]
│   │   └── README.md                   [Placeholder for migrations]
│   │
│   └── config.toml                     [⏳ TO CREATE - Supabase CLI config]
│
├── env/
│   └── .env.example                    [⏳ TO CREATE - Environment variables template]
│
├── docs/                               [✅ KEEP AT ROOT - No changes]
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   ├── ENHANCEMENTS.md
│   └── INTEGRATION_GUIDE.md
│
├── examples/                           [✅ KEEP AT ROOT - No changes]
│   ├── DEMO_SCRIPT.md
│   └── sample_manuscript.txt
│
├── README.md                           [🔄 UPDATE - New monorepo overview]
├── QUICKSTART.md                       [✅ KEEP - No changes for now]
├── EPIC_VICTORY.md                     [✅ KEEP - No changes]
├── LICENSE                             [✅ KEEP - No changes]
├── requirements_original.txt           [✅ KEEP - Legacy reference]
│
├── RESTRUCTURE_ANALYSIS.md             [✅ CREATED - This file]
├── RESTRUCTURE_REPORT.md               [⏳ TO CREATE - After restructure]
├── PEACOCK_PHOENIX_ANALYSIS.md         [⏳ TO CREATE - Step 4]
├── PEACOCK_PHOENIX_INTEGRATION_PLAN.md [⏳ TO CREATE - Step 5]
└── PEACOCK_PHOENIX_INTEGRATION_REPORT.md [⏳ TO CREATE - Step 6]
```

### Detailed File Mapping:

| Current Location | New Location | Import Updates Needed? |
|-----------------|--------------|----------------------|
| `src/chunker.py` | `apps/engine/src/chunker.py` | ✅ Yes - `main.py` imports |
| `src/text_cleaner.py` | `apps/engine/src/text_cleaner.py` | ✅ Yes - Streamlit imports |
| `src/verify_chunks.py` | `apps/engine/src/verify_chunks.py` | ❌ No (if unused) |
| `src/truncate_sample.py` | `apps/engine/src/truncate_sample.py` | ❌ No (if unused) |
| `src/tts_provider.py` | `apps/engine/src/tts_provider.py` | ✅ Yes - imports TTS modules |
| `src/tts_openai.py` | `apps/engine/src/tts_openai.py` | ❌ No |
| `src/tts_elevenlabs.py` | `apps/engine/src/tts_elevenlabs.py` | ❌ No |
| `src/tts_inworld.py` | `apps/engine/src/tts_inworld.py` | ✅ Yes - `main.py` imports |
| `src/merge_audio.py` | `apps/engine/src/merge_audio.py` | ✅ Yes - `main.py` + Streamlit |
| `src/convert.py` | `apps/engine/src/convert.py` | ❌ No (if unused) |
| `src/rate_limiter.py` | `apps/engine/src/rate_limiter.py` | ❌ No (if unused) |
| `src/cost_tracker.py` | `apps/engine/src/cost_tracker.py` | ❌ No (if unused) |
| `src/main.py` | `apps/engine/src/main.py` | ✅ Yes - relative imports |
| `streamlit_app.py` | `apps/engine/experimental/streamlit/streamlit_app.py` | ✅ Yes - `from src.*` → `from apps.engine.src.*` |
| `streamlit_app_v2.py` | `apps/engine/experimental/streamlit/streamlit_app_v2.py` | ✅ Yes - same as above |
| `streamlit_app_ultimate.py` | `apps/engine/experimental/streamlit/streamlit_app_ultimate.py` | ✅ Yes - same as above |
| `streamlit_app_broken_backup.py` | `apps/engine/experimental/streamlit/streamlit_app_broken_backup.py` | ⚠️ May need fixing (broken) |
| `.streamlit/secrets.toml.example` | `apps/engine/experimental/streamlit/.streamlit/secrets.toml.example` | ❌ No |
| `config.yaml` | `apps/engine/config.yaml` | ❌ No (path referenced in code) |
| `requirements.txt` | `apps/engine/requirements.txt` | ❌ No |

### Import Updates Required:

**File: `apps/engine/src/main.py`**
```python
# BEFORE (relative imports):
from chunker import chunk_text_file
from tts_inworld import synthesize_with_inworld
from merge_audio import merge_audio_files

# AFTER (relative imports with explicit current package):
from .chunker import chunk_text_file
from .tts_inworld import synthesize_with_inworld
from .merge_audio import merge_audio_files
```

**File: `apps/engine/src/tts_provider.py`**
```python
# BEFORE (absolute from src):
from src.tts_inworld import InworldProvider
from src.tts_openai import OpenAIProvider
from src.tts_elevenlabs import ElevenLabsProvider

# AFTER (relative imports):
from .tts_inworld import InworldProvider
from .tts_openai import OpenAIProvider
from .tts_elevenlabs import ElevenLabsProvider
```

**File: `apps/engine/experimental/streamlit/streamlit_app.py`**
```python
# BEFORE (absolute from src):
from src.chunker import chunk_text_file
from src.text_cleaner import clean_text
from src.merge_audio import merge_audio_files

# AFTER (adjust sys.path or use absolute from apps):
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.chunker import chunk_text_file
from src.text_cleaner import clean_text
from src.merge_audio import merge_audio_files
```

---

**Status:** ✅ Step 2 Complete - Mapping Plan Ready
