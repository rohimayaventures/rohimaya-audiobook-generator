# 🚀 Vercel Deployment Guide - AuthorFlow Studios

## Overview

This guide will help you deploy the AuthorFlow Studios frontend to Vercel with the correct configuration.

**Production URL:** `https://authorflowstudios.rohimayapublishing.com/`

---

## ✅ Prerequisites Completed

- [x] Vercel monorepo configuration added ([vercel.json](vercel.json))
- [x] Frontend code updated with AuthorFlow Studios branding
- [x] Page.tsx fixed with `'use client'` directive
- [x] Environment variables configured
- [x] All changes committed and pushed to GitHub

---

## Step 1: Import Project to Vercel

### 1.1 Connect GitHub Repository

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New..."** → **"Project"**
3. Select **"Import Git Repository"**
4. Find `rohimayaventures/rohimaya-audiobook-generator`
5. Click **"Import"**

### 1.2 Configure Project Settings

**Framework Preset:** Next.js (auto-detected)

**Root Directory:** Already configured in `vercel.json` to point to `apps/web`

**Build Settings:**
- **Build Command:** `npm run build` (auto-detected)
- **Output Directory:** `.next` (auto-detected)
- **Install Command:** `npm install` (auto-detected)

---

## Step 2: Configure Environment Variables

Click **"Environment Variables"** and add the following:

### Required Variables

| Variable Name | Value | Notes |
|--------------|-------|-------|
| `NEXT_PUBLIC_ENGINE_API_URL` | `https://your-backend.railway.app` | Replace with your Railway backend URL once deployed |
| `NODE_ENV` | `production` | Production environment |

### Optional (for later)

| Variable Name | Value | Notes |
|--------------|-------|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | `https://uiqjtiacuegfhfkrbngu.supabase.co` | For client-side auth (when implemented) |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJhbGc...` | Public anon key (safe to expose) |

**Important:** Do NOT add `SUPABASE_SERVICE_ROLE_KEY` to Vercel - it's backend-only!

---

## Step 3: Configure Custom Domain

### 3.1 Add Domain to Vercel

1. In your Vercel project → **Settings** → **Domains**
2. Click **"Add"**
3. Enter: `authorflowstudios.rohimayapublishing.com`
4. Click **"Add"**

### 3.2 Update DNS Records

Vercel will provide DNS records. Go to your domain provider (Cloudflare, Namecheap, etc.) and add:

**CNAME Record:**
```
Type: CNAME
Name: authorflowstudios
Value: cname.vercel-dns.com
TTL: Auto or 3600
```

**Alternative (A Record):**
```
Type: A
Name: authorflowstudios
Value: 76.76.21.21 (Vercel's IP)
TTL: Auto or 3600
```

### 3.3 Wait for DNS Propagation

- DNS changes can take 5 minutes to 48 hours
- Check status in Vercel Dashboard
- Look for green checkmark ✅ next to domain

---

## Step 4: Deploy

1. Click **"Deploy"**
2. Wait for build to complete (~2-3 minutes)
3. Check deployment logs for errors

### Expected Build Output

```
✓ Generating static pages (5/5)
✓ Collecting page data
✓ Finalizing page optimization
✓ Compiled successfully

Route (app)                              Size
┌ ○ /                                    5.2 kB
└ ○ /_not-found                          871 B

○  (Static)  prerendered as static content
```

---

## Step 5: Verify Deployment

### 5.1 Check Health

Visit your deployment URL (e.g., `https://rohimaya-audiobook-generator.vercel.app`)

You should see the AuthorFlow Studios landing page with:
- ✅ "AuthorFlow" branding
- ✅ "Audiobook Engine" tagline
- ✅ Three feature cards
- ✅ "Launch App →" and "Join Waitlist" buttons

### 5.2 Test Custom Domain

Once DNS propagates, visit: `https://authorflowstudios.rohimayapublishing.com/`

Should show the same landing page.

---

## Step 6: Update Backend CORS

After Vercel deployment, update your Railway backend environment variables:

### In Railway Dashboard

Go to your backend service → **Variables** → Add/Update:

```bash
ALLOWED_ORIGINS=https://authorflowstudios.rohimayapublishing.com,http://localhost:3000,http://127.0.0.1:3000
FRONTEND_URL=https://authorflowstudios.rohimayapublishing.com
```

**Redeploy backend** after adding these variables.

---

## Step 7: Update Frontend with Backend URL

Once your Railway backend is deployed:

1. Get your Railway backend URL (e.g., `https://authorflow-backend.railway.app`)
2. Go to Vercel project → **Settings** → **Environment Variables**
3. Update `NEXT_PUBLIC_ENGINE_API_URL` with your Railway URL
4. **Redeploy** frontend

---

## Troubleshooting

### Error: "No Next.js version detected"

**Fix:** Already resolved by adding `vercel.json` configuration.

### Error: Build fails with "Module not found"

**Cause:** Dependencies not installed

**Fix:**
```bash
cd apps/web
npm install
git add package-lock.json
git commit -m "chore: add package-lock.json"
git push
```

### Error: Page shows blank screen

**Cause:** JavaScript errors or missing `'use client'` directive

**Fix:** Already fixed - `page.tsx` has `'use client'` at the top.

### Custom domain shows "404: NOT_FOUND"

**Cause:** DNS not propagated or incorrect CNAME

**Fix:**
1. Wait 5-60 minutes for DNS propagation
2. Verify CNAME points to `cname.vercel-dns.com`
3. Check Vercel Dashboard for domain status

### CORS errors when calling backend

**Cause:** Backend doesn't allow frontend origin

**Fix:**
1. Update Railway `ALLOWED_ORIGINS` to include your Vercel domain
2. Redeploy backend
3. Clear browser cache and retry

---

## Environment Variable Reference

### Frontend (.env.local or Vercel)

```bash
# Public variables (safe to expose)
NEXT_PUBLIC_ENGINE_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_SUPABASE_URL=https://uiqjtiacuegfhfkrbngu.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...

# Node environment
NODE_ENV=production
```

### Backend (Railway)

```bash
# Production URLs
FRONTEND_URL=https://authorflowstudios.rohimayapublishing.com
ALLOWED_ORIGINS=https://authorflowstudios.rohimayapublishing.com,http://localhost:3000

# Supabase (Database & Auth)
SUPABASE_URL=https://uiqjtiacuegfhfkrbngu.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...  # Backend only!

# Cloudflare R2 Storage
R2_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_BUCKET_MANUSCRIPTS=manuscripts
R2_BUCKET_AUDIOBOOKS=audiobooks
R2_ENDPOINT=https://your_account_id.r2.cloudflarestorage.com

# TTS API Keys
OPENAI_API_KEY=sk-proj-...
ELEVENLABS_API_KEY=sk_...
INWORLD_WORKSPACE_ID=default-...
INWORLD_JWT_KEY=...
INWORLD_JWT_SECRET=...
INWORLD_BASIC_AUTH=...

# General
LOG_LEVEL=info
ENVIRONMENT=production
```

---

## Deployment Checklist

- [ ] Repository connected to Vercel
- [ ] `vercel.json` configuration in root
- [ ] Environment variables added to Vercel
- [ ] Custom domain added to Vercel
- [ ] DNS CNAME record updated
- [ ] Frontend deployed successfully
- [ ] Backend CORS updated with frontend URL
- [ ] Backend URL added to frontend env vars
- [ ] Landing page loads at custom domain
- [ ] No console errors in browser

---

## Next Steps

1. ✅ Deploy frontend to Vercel (follow this guide)
2. 🔄 Deploy backend to Railway (see [R2_SETUP_INSTRUCTIONS.md](R2_SETUP_INSTRUCTIONS.md))
3. 🔄 Update frontend with backend URL
4. 🔄 Test end-to-end: Upload → Process → Download

---

## Support

**Vercel Docs:**
- https://vercel.com/docs/frameworks/nextjs
- https://vercel.com/docs/concepts/projects/environment-variables

**Railway Docs:**
- https://docs.railway.app/

**Need help?**
- Check Vercel deployment logs for errors
- Verify all environment variables are set
- Ensure DNS records are correct

---

**Last Updated:** 2025-11-26
**Status:** ✅ Ready for Deployment
