# 🚀 Deployment Guide - Rohimaya Audiobook Generator

## Overview

Your app has 3 components that need to be deployed:

1. **Backend API** (FastAPI) → **Railway**
2. **Frontend** (Next.js) → **Vercel**
3. **Database & Storage** → **Supabase** (already set up)

---

## ✅ Backend API Deployment - Railway

### Step 1: Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Click "Start a New Project"
3. Choose "Deploy from GitHub repo"
4. Select your repository: `rohimaya-audiobook-generator`
5. Railway will detect the `railway.json` file automatically

### Step 2: Configure Root Directory

Since this is a monorepo, you need to set the root directory:

1. Go to your Railway project settings
2. Click on "Settings" → "Deploy"
3. Set **Root Directory**: `apps/engine`
4. Click "Save"

### Step 3: Add Environment Variables

Go to "Variables" tab and add these (copy from your `env/.env` file):

```bash
# Supabase
SUPABASE_URL=https://uiqjtiacuegfhfkrbngu.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_BUCKET_MANUSCRIPTS=manuscripts
SUPABASE_BUCKET_AUDIOBOOKS=audiobooks

# TTS API Keys
OPENAI_API_KEY=sk-proj-...
ELEVENLABS_API_KEY=sk_...
INWORLD_WORKSPACE_ID=default-...
INWORLD_JWT_KEY=C7nqMaZXdvxRzjCwqwh60K4OcQeoBJR4
INWORLD_JWT_SECRET=aA1MOCT7ami3doQm0ErrLbOM0CxYN8TIPEa8r3AhZkN4H4eQvnuVyM2E4RQaEXEu
INWORLD_BASIC_AUTH=Qzd...

# Application URLs (will update after deployment)
NEXT_PUBLIC_ENGINE_API_URL=${{RAILWAY_PUBLIC_DOMAIN}}
FRONTEND_URL=https://your-app.vercel.app

# CORS (will update after Vercel deployment)
ALLOWED_ORIGINS=https://your-app.vercel.app,http://localhost:3000

# Configuration
LOG_LEVEL=info
ENVIRONMENT=production
CHUNK_SIZE=1500
MAX_WORKERS=5
RATE_LIMIT_RPM=60

# Server config (Railway provides PORT automatically)
API_HOST=0.0.0.0
```

### Step 4: Deploy

1. Click "Deploy" button
2. Railway will:
   - Install Python dependencies from `requirements.txt`
   - Start the FastAPI server with `uvicorn`
   - Expose it on a public URL

3. Once deployed, you'll get a URL like: `https://your-app.up.railway.app`

### Step 5: Test Backend

```bash
# Health check
curl https://your-app.up.railway.app/health

# Should return:
{
  "status": "ok",
  "service": "rohimaya-engine",
  "version": "0.2.0",
  "timestamp": "2025-11-26T..."
}

# View API docs
open https://your-app.up.railway.app/docs
```

### Step 6: Update Frontend URL

Go back to Railway → Variables and update:
```bash
FRONTEND_URL=https://your-actual-app.vercel.app
ALLOWED_ORIGINS=https://your-actual-app.vercel.app,http://localhost:3000
```

---

## ✅ Frontend Deployment - Vercel

### Step 1: Create Vercel Project

1. Go to [vercel.com](https://vercel.com)
2. Click "Add New" → "Project"
3. Import your GitHub repository: `rohimaya-audiobook-generator`

### Step 2: Configure Build Settings

Since this is a monorepo:

1. **Framework Preset**: Next.js
2. **Root Directory**: `apps/web`
3. **Build Command**: `npm run build`
4. **Output Directory**: `.next`
5. **Install Command**: `npm install`

### Step 3: Add Environment Variables

Click "Environment Variables" and add these:

```bash
# App Basics
NEXT_PUBLIC_APP_NAME=Rohimaya Audiobook Generator
NEXT_PUBLIC_APP_URL=https://your-app.vercel.app
NEXT_PUBLIC_MARKETING_SITE_URL=https://your-app.vercel.app

# Backend API (use your Railway URL)
NEXT_PUBLIC_ENGINE_API_URL=https://your-app.up.railway.app

# Supabase (safe for frontend)
NEXT_PUBLIC_SUPABASE_URL=https://uiqjtiacuegfhfkrbngu.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Service role key (server-side only)
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Important**: Make sure to add these for all environments (Production, Preview, Development)

### Step 4: Deploy

1. Click "Deploy"
2. Vercel will:
   - Install npm dependencies
   - Build Next.js app
   - Deploy to CDN

3. You'll get a URL like: `https://your-app.vercel.app`

### Step 5: Update Backend CORS

Go back to Railway and update the CORS variable with your Vercel URL:
```bash
ALLOWED_ORIGINS=https://your-app.vercel.app
```

---

## ✅ Database Setup - Supabase

### Step 1: Apply Migrations

Your database tables need to be created. You have 2 options:

#### Option A: Using Supabase Dashboard (Easiest)

1. Go to [app.supabase.com](https://app.supabase.com)
2. Open your project
3. Go to "SQL Editor"
4. Click "New Query"
5. Copy the contents of `supabase/migrations/0001_create_jobs_tables.sql`
6. Paste and click "Run"
7. Repeat for `0002_create_storage_buckets.sql`

#### Option B: Using Supabase CLI

```bash
# Install Supabase CLI
npm install -g supabase

# Link to your project
supabase link --project-ref uiqjtiacuegfhfkrbngu

# Apply migrations
cd supabase
supabase db push

# Verify
supabase migration list
```

### Step 2: Create Storage Buckets

If not created by migration, manually create:

1. Go to Supabase → Storage
2. Create bucket `manuscripts` (Private)
3. Create bucket `audiobooks` (Private)
4. Apply RLS policies from migration file

### Step 3: Verify Tables Exist

Go to Supabase → Table Editor and verify:
- ✅ `jobs` table with all columns
- ✅ `job_files` table with all columns

---

## 🧪 Testing Full Stack

### Test 1: Backend Health Check

```bash
curl https://your-app.up.railway.app/health
```

Expected: `{"status": "ok", ...}`

### Test 2: Backend API Docs

Visit: `https://your-app.up.railway.app/docs`

Expected: Interactive Swagger UI showing all endpoints

### Test 3: Frontend Loads

Visit: `https://your-app.vercel.app`

Expected: Landing page loads correctly

### Test 4: Frontend → Backend Connection

1. Visit `https://your-app.vercel.app/app`
2. Check browser console for errors
3. Should see "Backend API: Connected" badge (if implemented)

### Test 5: Create Test Job (After Auth is Built)

```bash
# Get auth token from Supabase (temporary - will be via login later)
TOKEN="your-supabase-jwt-token"

# Create test job
curl -X POST https://your-app.up.railway.app/jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "Test Book",
    "author": "Test Author",
    "source_type": "paste",
    "manuscript_text": "Once upon a time, there was a brave knight...",
    "mode": "single_voice",
    "tts_provider": "openai",
    "narrator_voice_id": "alloy",
    "audio_format": "mp3",
    "audio_bitrate": "128k"
  }'
```

---

## 📊 Monitoring & Logs

### Railway Logs

1. Go to Railway project
2. Click "Deployments" tab
3. Click on latest deployment
4. View real-time logs

Look for:
```
🚀 Rohimaya Audiobook Engine API starting...
📝 Environment: production
🔗 CORS Origins: https://your-app.vercel.app
👷 Background worker started
✅ API ready
```

### Vercel Logs

1. Go to Vercel project
2. Click "Logs" tab
3. Monitor build and runtime logs

### Supabase Logs

1. Go to Supabase project
2. Click "Logs" → "API"
3. Monitor database queries and errors

---

## 🔒 Security Checklist

### ✅ Environment Variables

- [ ] All API keys are set as environment variables (NOT in code)
- [ ] `.env` files are gitignored
- [ ] Service role keys are only on backend (Railway)
- [ ] Anon keys are safe for frontend (Vercel)

### ✅ CORS

- [ ] Railway `ALLOWED_ORIGINS` includes only your Vercel URL
- [ ] No wildcard `*` in production CORS

### ✅ Supabase RLS

- [ ] RLS policies are enabled on `jobs` and `job_files` tables
- [ ] Users can only access their own jobs
- [ ] Storage buckets are private

### ✅ JWT Verification

- [ ] All protected endpoints use `Depends(get_current_user)`
- [ ] JWT secret matches Supabase project
- [ ] Token expiration is configured

---

## 🐛 Troubleshooting

### Issue: Backend fails to start

**Check Railway logs for:**
- Missing environment variables
- Python dependency installation errors
- Port binding issues

**Solution:**
1. Verify all env vars are set
2. Check `requirements.txt` has correct versions
3. Ensure `PORT` env var is used (Railway provides it)

### Issue: Frontend can't connect to backend

**Check:**
- CORS settings on backend include your Vercel URL
- `NEXT_PUBLIC_ENGINE_API_URL` is set correctly
- Backend is actually deployed and healthy

**Solution:**
```bash
# Test from browser console:
fetch('https://your-app.up.railway.app/health')
  .then(r => r.json())
  .then(console.log)
```

### Issue: Database connection fails

**Check:**
- Supabase URL and keys are correct
- Tables exist (run migrations)
- RLS policies allow service role access

**Solution:**
1. Verify connection string in Railway logs
2. Test query in Supabase SQL editor
3. Check service role key has full access

### Issue: TTS API errors

**Check:**
- API keys are valid and have credits
- Rate limits not exceeded
- Network connectivity from Railway

**Solution:**
1. Test API keys locally first
2. Check Railway logs for specific error messages
3. Implement retry logic for transient failures

---

## 🎯 Next Steps After Deployment

1. **Build Frontend UI** (Next Phase)
   - Authentication pages (login/signup)
   - Job creation form
   - Progress tracking UI
   - Download page

2. **Add Features**
   - Voice preview endpoint
   - Cost estimation
   - Email notifications
   - Webhook for job completion

3. **Set Up Custom Domain**
   - Buy domain (e.g., authorflow.com)
   - Point to Vercel for frontend
   - Use subdomain for API (api.authorflow.com → Railway)

4. **Monitoring**
   - Set up error tracking (Sentry)
   - Add analytics (PostHog)
   - Configure alerts for failed jobs

---

## 📝 Deployment Summary

| Component | Platform | URL | Status |
|-----------|----------|-----|--------|
| Backend API | Railway | https://your-app.up.railway.app | ✅ Deployed |
| Frontend | Vercel | https://your-app.vercel.app | ✅ Deployed |
| Database | Supabase | Project ID: uiqjtiacuegfhfkrbngu | ✅ Ready |
| Storage | Supabase | Buckets: manuscripts, audiobooks | ✅ Ready |

---

**Last Updated:** 2025-11-26
**Status:** Backend API complete and ready for deployment!

