# 🔐 Environment Variables Setup Guide

## Quick Start

You need to create **2 environment files** to run this project locally:

1. **`env/.env`** - Backend API keys (Python engine)
2. **`apps/web/.env.local`** - Frontend configuration (Next.js)

Both files are in `.gitignore` and will **never** be committed to git.

---

## Step 1: Backend Environment (`env/.env`)

### Create the file

```bash
# From repo root
cp env/.env.example env/.env
```

Or on Windows:
```cmd
copy env\.env.example env\.env
```

### Fill in your API keys

Open `env/.env` in your editor and add real values:

```bash
# ==============================================================================
# BACKEND ENVIRONMENT VARIABLES
# File: env/.env (NOT TRACKED IN GIT)
# ==============================================================================

# -----------------------------------------------------------------------------
# SUPABASE (Database & Storage)
# Get these from: https://app.supabase.com/project/YOUR_PROJECT/settings/api
# -----------------------------------------------------------------------------
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your_service_role_key_here

# Storage bucket names (match your Supabase buckets)
SUPABASE_BUCKET_MANUSCRIPTS=manuscripts
SUPABASE_BUCKET_AUDIOBOOKS=audiobooks

# -----------------------------------------------------------------------------
# TTS API KEYS (Backend Only - NEVER expose to frontend)
# -----------------------------------------------------------------------------

# OpenAI TTS (Required for single-voice pipeline)
# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# ElevenLabs TTS (Required for dual-voice pipeline)
# Get from: https://elevenlabs.io/app/settings/api-keys
ELEVENLABS_API_KEY=your_elevenlabs_key_here

# Inworld TTS (Optional - both required if using Inworld)
# Get from: https://studio.inworld.ai/
# Note: API key should be Base64 encoded (workspace_key:api_key)
INWORLD_API_KEY=your_inworld_key_here
INWORLD_WORKSPACE_ID=your_workspace_id_here

# -----------------------------------------------------------------------------
# APPLICATION URLS
# -----------------------------------------------------------------------------
NEXT_PUBLIC_ENGINE_API_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# -----------------------------------------------------------------------------
# CORS CONFIGURATION
# Comma-separated list of allowed origins
# -----------------------------------------------------------------------------
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# -----------------------------------------------------------------------------
# GENERAL CONFIGURATION
# -----------------------------------------------------------------------------
LOG_LEVEL=info
ENVIRONMENT=development

# -----------------------------------------------------------------------------
# PROCESSING SETTINGS
# -----------------------------------------------------------------------------
CHUNK_SIZE=1500
MAX_WORKERS=5
RATE_LIMIT_RPM=60

# -----------------------------------------------------------------------------
# API SERVER CONFIGURATION (for Railway deployment)
# -----------------------------------------------------------------------------
API_HOST=0.0.0.0
API_PORT=8000
```

### Where to get API keys

| Service | Where to Get Key | Notes |
|---------|-----------------|-------|
| **OpenAI** | https://platform.openai.com/api-keys | Click "Create new secret key" |
| **ElevenLabs** | https://elevenlabs.io/app/settings/api-keys | Free tier: 10,000 chars/month |
| **Inworld** | https://studio.inworld.ai/ | Optional - Needs both API key and workspace ID |
| **Supabase** | https://app.supabase.com/project/YOUR_PROJECT/settings/api | Copy "Project URL" and both keys |

---

## Step 2: Frontend Environment (`apps/web/.env.local`)

### The file already exists!

I created `apps/web/.env.local` as a template in the previous push. Open it and fill in real values:

```bash
# ==============================================================================
# FRONTEND ENVIRONMENT VARIABLES
# File: apps/web/.env.local (NOT TRACKED IN GIT)
# ==============================================================================

# -----------------------------------------------------------------------------
# App Basics
# -----------------------------------------------------------------------------
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_ENGINE_API_URL=http://localhost:8000

# -----------------------------------------------------------------------------
# Supabase (Public keys safe for frontend)
# Get from: https://app.supabase.com/project/YOUR_PROJECT/settings/api
# -----------------------------------------------------------------------------
NEXT_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your_anon_key_here

# Service role key (ONLY for server-side operations, NEVER use in client code)
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your_service_role_key_here

# -----------------------------------------------------------------------------
# Stripe Billing (Optional - for future payment integration)
# Get from: https://dashboard.stripe.com/apikeys
# -----------------------------------------------------------------------------
STRIPE_SECRET_KEY=sk_test_XXXXXXXXXXXXXXXXXXXXXXXXXXXX
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_XXXXXXXXXXXXXXXXXXXXXXXXXXXX

# -----------------------------------------------------------------------------
# Google OAuth (Optional - for "Sign in with Google")
# Get from: https://console.cloud.google.com/apis/credentials
# -----------------------------------------------------------------------------
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-XXXXXXXXXXXXXXXXXXXX

# -----------------------------------------------------------------------------
# Google Drive API (Optional - for importing from Drive)
# Same project as OAuth above
# -----------------------------------------------------------------------------
NEXT_PUBLIC_GOOGLE_DRIVE_CLIENT_ID=your-client-id.apps.googleusercontent.com
NEXT_PUBLIC_GOOGLE_DRIVE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# -----------------------------------------------------------------------------
# Email / Notifications (Optional)
# -----------------------------------------------------------------------------
RESEND_API_KEY=re_XXXXXXXXXXXXXXXXXXXXXXXXXXXX
EMAIL_FROM=noreply@authorflow.com

# -----------------------------------------------------------------------------
# Analytics (Optional)
# -----------------------------------------------------------------------------
NEXT_PUBLIC_GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
NEXT_PUBLIC_POSTHOG_KEY=phc_XXXXXXXXXXXXXXXXXXXXXXXXXXXX
NEXT_PUBLIC_POSTHOG_HOST=https://app.posthog.com

# -----------------------------------------------------------------------------
# Feature Flags (Optional)
# -----------------------------------------------------------------------------
NEXT_PUBLIC_ENABLE_DUAL_VOICE=true
NEXT_PUBLIC_ENABLE_GOOGLE_DRIVE=false
NEXT_PUBLIC_ENABLE_STRIPE=false
```

---

## Step 3: Verify Setup

### Check that files exist and are ignored

```bash
# From repo root
ls env/.env              # Should exist (your real keys)
ls apps/web/.env.local   # Should exist (your real keys)

git status               # Should NOT show these files (they're ignored)
```

### Test backend API

```bash
cd apps/engine

# Install dependencies (if not already done)
pip install -r requirements.txt

# Run the API
uvicorn api.main:app --reload

# In another terminal, test the health endpoint
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "service": "rohimaya-engine",
  "version": "0.1.0",
  "timestamp": "2025-11-22T..."
}
```

### Test frontend (when Next.js app is created in Step 4)

```bash
cd apps/web

# Install dependencies
npm install

# Run dev server
npm run dev

# Visit http://localhost:3000
```

---

## Security Checklist

### ✅ Files that MUST be in .gitignore
- `env/.env` ✅ (in .gitignore)
- `env/.env.*` ✅ (in .gitignore)
- `apps/web/.env.local` ✅ (in .gitignore)
- `apps/web/.env*.local` ✅ (in .gitignore)

### ✅ Files that ARE committed (templates only)
- `env/.env.example` ✅ (tracked, no real values)
- Templates for apps/web/.env.local (created but ignored)

### ❌ NEVER commit these keys
- OpenAI API keys (start with `sk-`)
- ElevenLabs API keys
- Supabase service role keys (start with `eyJ...`)
- Stripe secret keys (start with `sk_test_` or `sk_live_`)
- Any other API keys or secrets

---

## Troubleshooting

### "Module not found: dotenv"
```bash
cd apps/engine
pip install python-dotenv
```

### "Environment variable not loaded"
Check that:
1. File is named exactly `env/.env` (no `.txt` extension)
2. File is in the correct location (repo root → env/ → .env)
3. No spaces around `=` signs (e.g., `API_KEY=value`, not `API_KEY = value`)

### "CORS error in browser"
Update `ALLOWED_ORIGINS` in `env/.env`:
```bash
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### "Supabase connection failed"
Verify:
1. Project URL is correct (ends with `.supabase.co`)
2. Keys are copied exactly (they're very long)
3. No extra whitespace or quotes

---

## Production Deployment

### Railway (Backend)
Add environment variables in Railway dashboard:
- Go to your project → Variables
- Add all variables from `env/.env.example`
- Fill in real values

### Vercel (Frontend)
Add environment variables in Vercel dashboard:
- Go to Settings → Environment Variables
- Add all variables from `apps/web/.env.local`
- Fill in real values
- Make sure to add for all environments (Production, Preview, Development)

---

## Quick Reference

| File | Purpose | Tracked in Git? | Contains Secrets? |
|------|---------|----------------|-------------------|
| `env/.env.example` | Backend template | ✅ Yes | ❌ No (variable names only) |
| `env/.env` | Backend real values | ❌ No (ignored) | ✅ Yes (YOUR API keys) |
| `apps/web/.env.local` | Frontend real values | ❌ No (ignored) | ✅ Yes (YOUR API keys) |

---

**Last Updated:** 2025-11-22
**Status:** Ready for local development setup
