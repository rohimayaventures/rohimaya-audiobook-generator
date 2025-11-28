# AuthorFlow Studios

> **The Canva of Audiobooks** - AI-powered audiobook creation platform that turns manuscripts into Findaway-ready packages

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)

---

## What is AuthorFlow Studios?

AuthorFlow Studios is a complete audiobook publishing pipeline that transforms your manuscript into a professionally produced, distribution-ready audiobook package - without needing a studio, narrator, engineer, or complex software.

**Built for:**
- Indie authors
- Romance writers
- Publishers
- Ghostwriters
- Content creators

**What you get:**
- Studio-quality audio narration
- Emotional, expressive TTS
- Multi-character voice assignment
- Professional cover art
- Retail samples (including romance-optimized "spicy" excerpts)
- Complete Findaway submission packages
- One-click generation

---

## The Problem We Solve

Authors today face impossible choices:

| Traditional Option | Cost | Time | Complexity |
|---|---|---|---|
| Hire a narrator | $1,500 - $7,000+ | 4-8 weeks | High |
| ACX/Findaway production | $2,000+ | 6-12 weeks | High |
| DIY with AI tools | $50-200 | Days | Very High (editing required) |
| **AuthorFlow Studios** | **$29-249/mo** | **Hours** | **One click** |

**No current competitor offers this level of automation.**

---

## Core Features

### 1. Manuscript Intake (3 Methods)
- **File Upload** - PDF, DOCX, TXT, Markdown
- **Google Drive Import** - Direct OAuth connection to your Drive
- **Text Paste** - Copy/paste directly into the app

### 2. Smart Manuscript Parsing
- Automatic chapter detection
- Dialogue extraction with speaker attribution
- Character identification across the manuscript
- Emotion and tone analysis per segment
- Romance-optimized content detection

### 3. Emotional Narration & Multi-Character Voices
AI-powered detection of:
- Emotion (14 tones: happy, sad, angry, romantic, mysterious, etc.)
- Speaker identity
- Character consistency
- Pacing and tension

Automatic voice switching between narrator and characters.

### 4. Findaway Submission Package (Our Differentiator)
Everything required for audiobook distribution:
- Chapter MP3 files with proper naming
- Retail sample (default, spicy, or ultra-spicy for romance)
- Opening and ending credits
- Metadata manifest (JSON)
- AI-generated cover art (2400x2400)
- Final ZIP archive ready for upload

**No other AI tool offers Findaway packages automatically.**

### 5. Cover Art Generator
Multiple AI providers supported:
- **OpenAI DALL-E 3** (primary)
- Banana.dev SDXL/Flux (cost-effective alternative)

Custom description support - describe your vision and the AI creates it.

### 6. Billing & Subscriptions
- Free trial (7-14 days depending on plan)
- Monthly or yearly billing
- Tiered plans with usage limits
- Stripe-powered checkout
- Admin override for internal use

### 7. Job Management
- **Retry** - Re-run failed jobs with one click
- **Clone** - Duplicate a job with different settings
- **Progress Tracking** - Real-time status updates

### 8. Google Drive Integration
- OAuth 2.0 authorization
- Browse and select files
- Multi-format support (Google Docs, DOCX, PDF, TXT)
- Automatic text extraction

### 9. Admin & Monitoring Tools
- Worker health dashboard
- Queue status monitoring
- Job recovery on server restart
- System status panel

---

## Tech Stack

### Frontend (`apps/web/`)
- **Framework:** Next.js 14 (App Router)
- **Styling:** Tailwind CSS
- **Auth:** Supabase Auth
- **Deployment:** Vercel

### Backend (`apps/engine/`)
- **Framework:** FastAPI (Python 3.11+)
- **TTS Providers:** OpenAI, ElevenLabs
- **Image Generation:** OpenAI DALL-E, Banana.dev
- **Audio Processing:** pydub, ffmpeg
- **Deployment:** Railway

### Database & Storage
- **Database:** Supabase (PostgreSQL)
- **File Storage:** Cloudflare R2
- **Auth:** Supabase Auth + JWT

---

## Repository Structure

```
authorflow-studios/
├── apps/
│   ├── web/                    # Next.js frontend
│   │   ├── app/                # App router pages
│   │   │   ├── dashboard/      # Main audiobook creation UI
│   │   │   ├── billing/        # Subscription management
│   │   │   ├── library/        # User's audiobook library
│   │   │   └── job/[id]/       # Job detail & download
│   │   └── lib/                # API client, utilities
│   │
│   └── engine/                 # Python backend
│       ├── api/                # FastAPI routes & worker
│       │   ├── billing/        # Stripe integration
│       │   ├── main.py         # API endpoints
│       │   └── worker.py       # Background job processor
│       ├── agents/             # AI agents (parsing, emotion, samples)
│       ├── core/               # Core utilities (chunking, covers)
│       └── pipelines/          # Audio generation pipelines
│           ├── standard_single_voice.py
│           ├── phoenix_peacock_dual_voice.py
│           ├── multi_character_pipeline.py
│           └── findaway_pipeline.py
│
├── supabase/
│   └── migrations/             # Database schema
│
├── env/
│   └── .env.example            # Environment template
│
└── docs/                       # Documentation
```

---

## Pricing Plans

| Plan | Price | Projects/Month | Minutes/Book | Key Features |
|------|-------|----------------|--------------|--------------|
| **Free** | $0 | 1 | 5 min | Basic TTS, retail sample |
| **Creator** | $29/mo | 3 | 60 min | Findaway packages, cover art, emotional TTS |
| **Author Pro** | $79/mo | Unlimited | 360 min | Dual-voice, multi-character, spicy samples |
| **Publisher** | $249/mo | Unlimited | Unlimited | Team access (5), priority support, all features |

Yearly billing available (2 months free).

---

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- ffmpeg
- Supabase account
- Cloudflare R2 account
- Stripe account

### 1. Clone & Install
```bash
git clone https://github.com/rohimayaventures/rohimaya-audiobook-generator.git
cd rohimaya-audiobook-generator

# Backend
cd apps/engine
pip install -r requirements.txt

# Frontend
cd ../web
npm install
```

### 2. Environment Setup
```bash
cp env/.env.example env/.env
# Edit env/.env with your API keys
```

### 3. Database Setup
Run migrations in Supabase SQL Editor:
- `supabase/migrations/0001_create_jobs_tables.sql`
- `supabase/migrations/0002_create_storage_buckets.sql`
- `supabase/migrations/0003_google_drive_tokens.sql`
- `supabase/migrations/0004_billing_interval.sql`
- `supabase/migrations/0005_cover_art_columns.sql`

### 4. Run Locally
```bash
# Backend (from apps/engine)
uvicorn api.main:app --reload --port 8000

# Frontend (from apps/web)
npm run dev
```

---

## Environment Variables

### Required
```env
# OpenAI (TTS + Cover Art)
OPENAI_API_KEY=sk-...

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SUPABASE_JWT_SECRET=your-jwt-secret

# Cloudflare R2 Storage
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret-key
R2_BUCKET_NAME=authorflow-storage

# Stripe Billing
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_CREATOR_MONTHLY=price_...
STRIPE_PRICE_AUTHOR_PRO_MONTHLY=price_...
STRIPE_PRICE_PUBLISHER_MONTHLY=price_...
```

### Optional
```env
# ElevenLabs (for dual-voice)
ELEVENLABS_API_KEY=...

# Google Drive Import
GOOGLE_DRIVE_CLIENT_ID=...
GOOGLE_DRIVE_CLIENT_SECRET=...
GOOGLE_DRIVE_REDIRECT_URI=...

# Cover Art (alternative provider)
BANANA_API_KEY=...

# Admin Access
ADMIN_EMAILS=admin@example.com
```

---

## API Endpoints

### Jobs
- `POST /jobs` - Create job (JSON body)
- `POST /jobs/upload` - Create job with file upload
- `GET /jobs/{id}` - Get job details
- `GET /jobs` - List user's jobs
- `POST /jobs/{id}/retry` - Retry failed job
- `POST /jobs/{id}/clone` - Clone job with new settings
- `DELETE /jobs/{id}` - Cancel/delete job

### Billing
- `GET /billing/me` - Get user billing status
- `POST /billing/create-checkout-session` - Start subscription
- `POST /billing/create-portal-session` - Manage subscription
- `GET /billing/plans` - List available plans

### Google Drive
- `GET /google-drive/auth-url` - Get OAuth URL
- `POST /google-drive/callback` - Handle OAuth callback
- `GET /google-drive/files` - List Drive files
- `POST /google-drive/import` - Import file from Drive

### Admin
- `GET /worker/health` - Worker status
- `GET /queue/status` - Queue status
- `GET /admin/status` - Full system status (admin only)

---

## Deployment

### Frontend (Vercel)
```bash
cd apps/web
vercel deploy --prod
```

### Backend (Railway)
Railway auto-deploys from `apps/engine/` using:
- `nixpacks.toml` - Build configuration
- `Procfile` - Start command

### Required Railway Environment Variables
Set all variables from `.env.example` in Railway dashboard.

---

## Documentation

- [Session Summary](docs/NOVEMBER_28_SESSION_SUMMARY.md) - Latest changes
- [Enhancements](docs/ENHANCEMENTS.md) - Planned improvements
- [Engine README](apps/engine/README.md) - Backend details
- [Web README](apps/web/README.md) - Frontend details

---

## Roadmap

### Completed
- [x] Single-voice audiobook generation
- [x] Dual-voice (narrator + character)
- [x] Multi-character voice assignment
- [x] Emotional TTS with AI detection
- [x] Findaway package generation
- [x] AI cover art generation
- [x] Google Drive import
- [x] Stripe billing integration
- [x] Job retry and cloning
- [x] Admin monitoring tools

### In Progress
- [ ] Fix Findaway pipeline section plan bug
- [ ] Email notifications (trial ending, payment failed)
- [ ] Voice preview/demo functionality

### Planned
- [ ] Google Cloud TTS as alternative provider
- [ ] Custom voice cloning integration
- [ ] Batch processing (multiple books)
- [ ] Team collaboration features
- [ ] White-label option for publishers

---

## Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Email: support@authorflowstudios.com

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Credits

- **Rohimaya Ventures** - Product vision and design
- **Pagade Ventures** - Engineering and development

---

**AuthorFlow Studios** - Turning authors into publishers, one audiobook at a time.

*Last Updated: November 28, 2025*
