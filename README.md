# AuthorFlow Studios - Monorepo

> **Professional full-stack audiobook generation platform with multi-provider TTS support**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)

---

## 🏗️ Monorepo Structure

This is a full-stack monorepo containing:

```
authorflow-studios/
├── apps/
│   ├── web/               # Next.js 14 frontend (Vercel)
│   └── engine/            # Python audiobook backend (Railway)
│
├── packages/
│   ├── config/            # Shared configuration constants
│   └── utils/             # Shared utilities
│
├── supabase/              # Database schema & migrations
│   ├── migrations/
│   └── config.toml
│
├── env/
│   └── .env.example       # Environment variable template
│
└── docs/                  # Documentation
```

### Applications

#### 🌐 Web Frontend (`apps/web/`)
- **Status:** 🚧 Coming Soon
- **Framework:** Next.js 14 (App Router)
- **Deployment:** Vercel
- **Features:** User auth, manuscript upload, job tracking, voice selection

#### 🎙️ Python Engine (`apps/engine/`)
- **Status:** ✅ Production Ready
- **Framework:** Python 3.8+ with FastAPI (planned)
- **Deployment:** Railway
- **Features:** Multi-provider TTS, text chunking, audio processing

---

## 🚀 Quick Start

### Prerequisites
- **Node.js** 18+ (for frontend)
- **Python** 3.8+ (for backend)
- **ffmpeg** (for audio processing)
- **Supabase** account (for database & storage)

### 1. Clone Repository
```bash
git clone https://github.com/rohimayaventures/rohimaya-audiobook-generator.git
cd rohimaya-audiobook-generator
```

### 2. Environment Setup
```bash
# Copy environment template
cp env/.env.example env/.env

# Edit env/.env with your API keys and configuration
```

### 3. Backend Setup (Python Engine)
```bash
cd apps/engine
pip install -r requirements.txt

# Run CLI version
python -m src.main

# Or run Streamlit UI (experimental)
cd experimental/streamlit
streamlit run streamlit_app.py
```

### 4. Frontend Setup (Coming Soon)
```bash
cd apps/web
npm install
npm run dev
```

---

## ✨ Features

### Current (Python Engine)
- ✅ Multi-provider TTS (OpenAI, ElevenLabs, Inworld)
- ✅ Automatic provider fallback
- ✅ Intelligent text chunking (sentence-aware)
- ✅ Audio merging with pydub
- ✅ Thread-safe rate limiting
- ✅ Cost tracking per provider
- ✅ Streamlit web UI (experimental)

### Planned (Full Stack)
- 🚧 Next.js 14 frontend with modern UI
- 🚧 User authentication (Supabase)
- 🚧 Job queue & progress tracking
- 🚧 Phoenix & Peacock dual-voice mode
- 🚧 Chapter-based generation
- 🚧 Manuscript management
- 🚧 Audiobook library

---

## 🎤 TTS Providers

| Provider | Voices | Cost (per 1K chars) | Quality | Best For |
|----------|--------|---------------------|---------|----------|
| **OpenAI TTS-1** | 6 voices (alloy, echo, fable, onyx, nova, shimmer) | $0.015 | Good | Cost-effective production |
| **ElevenLabs** | Custom voices | Variable | Excellent | Premium quality, fiction |
| **Inworld** | Multiple | $0.15 | Good | Balanced quality/cost |

---

## 🛠️ Architecture

### Text-to-Audiobook Pipeline
1. **Upload** → User uploads manuscript (TXT, DOCX, PDF)
2. **Clean** → Text preprocessing & normalization
3. **Chunk** → Split into ~1500 char chunks (sentence-aware)
4. **TTS** → Generate audio for each chunk (parallel, multi-provider)
5. **Merge** → Concatenate audio chunks into final audiobook
6. **Export** → Download MP3/M4B audiobook

### Tech Stack

**Frontend:**
- Next.js 14 (App Router)
- Tailwind CSS
- shadcn/ui components
- Supabase Auth
- Deployed on **Vercel**

**Backend:**
- Python 3.8+
- FastAPI (planned HTTP wrapper)
- pydub (audio processing)
- OpenAI, ElevenLabs, Inworld SDKs
- Deployed on **Railway**

**Database & Storage:**
- Supabase (PostgreSQL + Storage)
- Jobs table, file metadata
- Audio & manuscript buckets

---

## 📦 Packages

### `packages/config/`
Shared configuration constants (bucket names, API endpoints, etc.)

### `packages/utils/`
Shared utility functions used across apps

---

## 🗄️ Database Schema (Supabase)

### Tables
- **`jobs`** - Audiobook generation jobs
- **`job_files`** - File metadata for manuscripts & audiobooks

### Storage Buckets
- **`manuscripts`** - Uploaded manuscript files
- **`audiobooks`** - Generated audiobook files

See [`supabase/migrations/`](supabase/migrations/) for full schema.

---

## 🔐 Environment Variables

See [`env/.env.example`](env/.env.example) for the complete list.

**Required:**
- `OPENAI_API_KEY` - OpenAI API key
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_ANON_KEY` - Public anon key
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key (backend only)

**Optional:**
- `ELEVENLABS_API_KEY` - ElevenLabs API key
- `INWORLD_API_KEY` - Inworld API key

---

## 📚 Documentation

- [**QUICKSTART.md**](QUICKSTART.md) - Quick start guide
- [**EPIC_VICTORY.md**](EPIC_VICTORY.md) - Project history & narrative
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) - System architecture
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) - Deployment guide
- [`docs/INTEGRATION_GUIDE.md`](docs/INTEGRATION_GUIDE.md) - Integration docs
- [`apps/engine/README.md`](apps/engine/README.md) - Python engine details
- [`apps/web/README.md`](apps/web/README.md) - Frontend details

---

## 🎨 Branding

**Rohimaya Color Palette:**
- **Phoenix Orange:** `#FF8C42`
- **Peacock Teal:** `#4A9B9B`
- **Midnight Navy:** `#1A1A2E`
- **Cream:** `#FFF8E7`

**Fonts:**
- **Headings:** Playfair Display
- **Body:** Inter

---

## 🧪 Development

### Run Backend Locally
```bash
cd apps/engine
python -m src.main  # CLI mode

# Or Streamlit UI
cd experimental/streamlit
streamlit run streamlit_app.py
```

### Run Frontend Locally (Coming Soon)
```bash
cd apps/web
npm run dev
```

### Run Supabase Locally
```bash
supabase start
supabase db push
```

---

## 🚀 Deployment

### Frontend (Vercel)
```bash
cd apps/web
vercel deploy
```

### Backend (Railway)
```bash
cd apps/engine
# Configure Railway project
railway up
```

### Database (Supabase)
```bash
cd supabase
supabase db push
```

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Credits

- **Original Engine:** Prasad's TTS foundation
- **Dual-Voice System:** Husband's Phoenix/Peacock implementation
- **Monorepo Restructure:** Claude (VS Code Assistant)

---

## 📞 Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

**Last Updated:** 2025-11-22
**Status:** Active Development
