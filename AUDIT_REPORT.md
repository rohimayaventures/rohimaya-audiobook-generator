# AuthorFlow Studios - Phase 1 Audit Report

**Date:** November 27, 2025
**Auditor:** Claude Code
**Status:** Phase 1 - High-Level Audit (READ-ONLY)

---

## Executive Summary

This audit reviews the implementation status of all major features in the AuthorFlow Studios audiobook generation platform. The codebase spans:
- **Backend:** FastAPI (`apps/engine/api/`)
- **Pipelines:** Audio generation pipelines (`apps/engine/pipelines/`)
- **Frontend:** Next.js 14 App Router (`apps/web/`)
- **Infrastructure:** Supabase (DB/Auth), Cloudflare R2 (Storage), Stripe (Billing)

---

## A. STRIPE BILLING

### Backend (`apps/engine/api/billing/`)

| Feature | Status | File | Notes |
|---------|--------|------|-------|
| Stripe Client Setup | ✅ | `stripe_client.py:30-45` | Configured via `STRIPE_SECRET_KEY` |
| Customer Management | ✅ | `stripe_client.py:99-172` | Get or create customer, stores `supabase_user_id` in metadata |
| Checkout Session Creation | ✅ | `stripe_client.py:179-239` | Supports trial days, promotion codes |
| Billing Portal Session | ✅ | `stripe_client.py:246-278` | Opens Stripe-hosted portal |
| Price ID Mapping | ✅ | `stripe_client.py:52-92` | Reads from env vars: `STRIPE_PRICE_{PLAN}_{PERIOD}` |
| Webhook Signature Verification | ✅ | `stripe_client.py:362-390` | Uses `STRIPE_WEBHOOK_SECRET` |
| Webhook Event Handler | ✅ | `webhook.py:1-443` | Handles all key events |
| Plan Entitlements | ✅ | `entitlements.py:1-305` | Complete entitlements system with all 5 plans |
| Billing Routes | ✅ | `routes.py:1-373` | `/billing/me`, `/billing/plans`, checkout, portal |
| Usage Tracking | ✅ | `database.py:350-420` | `get_user_usage_current_period`, `increment_user_usage` |
| Limit Enforcement | ✅ | `main.py:238-282` | Checks projects/month, findaway, dual-voice before job creation |

#### Webhook Events Handled:
| Event | Status | Notes |
|-------|--------|-------|
| `checkout.session.completed` | ✅ | Creates/updates billing record |
| `customer.subscription.created` | ✅ | Upserts billing with plan_id |
| `customer.subscription.updated` | ✅ | Updates status, period_end, cancel_at |
| `customer.subscription.deleted` | ✅ | Resets to free plan |
| `invoice.payment_failed` | ✅ | Sets status to past_due |
| `invoice.paid` | ✅ | Resets to active status |

### Frontend (`apps/web/`)

| Feature | Status | File | Notes |
|---------|--------|------|-------|
| Billing API Client | ✅ | `lib/billing.ts:1-262` | All endpoints covered |
| Pricing Page | ✅ | `app/pricing/page.tsx:1-236` | Displays 4 plans, handles checkout |
| Billing Management Page | ✅ | `app/billing/page.tsx:1-235` | Shows status, entitlements, portal link |
| Success Page | ✅ | `app/billing/success/page.tsx:1-108` | Post-checkout confirmation |
| Cancel Page | ✅ | `app/billing/cancel/page.tsx:1-60` | Checkout cancellation |
| Dashboard Plan Banner | ✅ | `app/dashboard/page.tsx:201-257` | Shows current plan and usage |

### Stripe Billing Sanity Check:
- ✅ Webhook signature verification implemented
- ✅ `supabase_user_id` stored in customer metadata for linking
- ✅ All CRUD operations for billing records
- ✅ Graceful fallback to free plan
- ⚠️ **Missing:** Stripe CLI webhook testing instructions in docs
- ⚠️ **Missing:** Database migration for `user_billing` and `user_usage` tables

---

## B. AUDIOBOOK ENGINE / CORE FEATURES

### Worker (`apps/engine/api/worker.py`)

| Feature | Status | File | Notes |
|---------|--------|------|-------|
| Background Worker Loop | ✅ | `worker.py:1-462` | Asyncio-based queue processing |
| Job Queue Management | ✅ | `worker.py:30-50` | In-memory asyncio.Queue |
| Single Voice Mode | ✅ | `worker.py:200-250` | Calls `SingleVoicePipeline` |
| Dual Voice Mode | ⚠️ | `worker.py:250-280` | Pipeline exists but untested |
| Findaway Mode | ✅ | `worker.py:280-350` | Calls `FindawayPipeline` |
| Progress Updates | ✅ | `worker.py:150-180` | Updates DB with progress_percent |
| Error Handling | ✅ | `worker.py:380-420` | Marks job as failed with error_message |
| Job Retry Logic | ✅ | `main.py:458-518` | `/jobs/{id}/retry` endpoint |

### Pipelines (`apps/engine/pipelines/`)

| Feature | Status | File | Notes |
|---------|--------|------|-------|
| Single Voice Pipeline | ✅ | `standard_single_voice.py:1-263` | OpenAI TTS, chapter parsing, audio merging |
| Findaway Pipeline | ✅ | `findaway_pipeline.py:1-606` | Full Findaway-compliant package generation |
| Chapter Detection | ✅ | `standard_single_voice.py:80-120` | Regex-based chapter parsing |
| Audio Merging | ✅ | `standard_single_voice.py:200-250` | pydub AudioSegment concatenation |
| Manifest Generation | ✅ | `findaway_pipeline.py:450-500` | JSON manifest with all metadata |
| Retail Sample Selection | ✅ | `findaway_pipeline.py:180-220` | Default and "spicy" sample modes |
| Cover Generation | ✅ | `findaway_pipeline.py:280-320` | Calls cover_generator module |
| ZIP Package Creation | ✅ | `findaway_pipeline.py:520-580` | Complete Findaway package |

### TTS Integration

| Feature | Status | File | Notes |
|---------|--------|------|-------|
| OpenAI TTS | ✅ | `standard_single_voice.py:130-180` | Uses `gpt-4o-mini-tts` model |
| ElevenLabs TTS | ❌ | - | Not implemented (placeholder in voices list) |
| Inworld TTS | ❌ | - | Not implemented (placeholder in voices list) |

### Sanity Check:
- ✅ Worker starts on app startup (`main.py:645-653`)
- ✅ Jobs stored in Supabase database
- ✅ Audio files uploaded to R2
- ⚠️ **Missing:** Worker health check / heartbeat endpoint
- ⚠️ **Missing:** Dead letter queue for repeatedly failed jobs
- ⚠️ **Concern:** In-memory queue - jobs lost on restart

---

## C. R2 INTEGRATION (Cloudflare Storage)

### Storage Client (`apps/engine/api/storage_r2.py`)

| Feature | Status | File | Notes |
|---------|--------|------|-------|
| S3 Client Setup | ✅ | `storage_r2.py:40-80` | boto3 with `signature_version='s3v4'` |
| Upload Manuscript | ✅ | `storage_r2.py:100-140` | Path: `manuscripts/{user_id}/{filename}` |
| Download Manuscript | ✅ | `storage_r2.py:150-180` | Returns bytes |
| Upload Audiobook | ✅ | `storage_r2.py:190-230` | Path: `audiobooks/{user_id}/{job_id}/{filename}` |
| Presigned URLs | ✅ | `storage_r2.py:240-280` | 1-hour expiration default |
| Delete File | ✅ | `storage_r2.py:290-320` | Delete manuscript/audiobook |

### Environment Variables Required:
```
R2_ACCOUNT_ID
R2_ACCESS_KEY_ID
R2_SECRET_ACCESS_KEY
R2_BUCKET_NAME
R2_PUBLIC_URL (optional)
```

### Sanity Check:
- ✅ Proper S3-compatible client configuration
- ✅ Presigned URL generation for downloads
- ✅ Integration with database.py wrapper
- ⚠️ **Missing:** R2 bucket CORS configuration in docs
- ⚠️ **Missing:** Lifecycle rules for cleanup of old files

---

## D. SUPABASE AUTH + OAUTH

### Backend Auth (`apps/engine/api/auth.py`)

| Feature | Status | File | Notes |
|---------|--------|------|-------|
| JWT Verification | ✅ | `auth.py` | Validates Supabase JWT tokens |
| `get_current_user` Dependency | ✅ | `auth.py` | FastAPI Depends() for protected routes |
| Admin Role Check | ✅ | `main.py:243-248` | Reads from `user_metadata.role` |

### Frontend Auth (`apps/web/lib/`)

| Feature | Status | File | Notes |
|---------|--------|------|-------|
| Supabase Client | ✅ | `supabaseClient.ts` | Browser client setup |
| Email/Password Sign In | ✅ | `auth.ts` | `signIn()` function |
| Email/Password Sign Up | ✅ | `auth.ts` | `signUp()` function |
| Sign Out | ✅ | `auth.ts` | `signOut()` function |
| OAuth (Google) | ✅ | `auth.ts:80-110` | `signInWithOAuth('google')` |
| OAuth (GitHub) | ✅ | `auth.ts:80-110` | `signInWithOAuth('github')` |
| OAuth Callback | ✅ | `app/auth/callback/route.ts:1-44` | Exchanges code for session |
| Auth Wrapper | ✅ | `components/layout/AuthWrapper.tsx` | Protects routes |
| Get Current User | ✅ | `supabaseClient.ts` | `getCurrentUser()` helper |

### Auth Pages

| Page | Status | File | Notes |
|------|--------|------|-------|
| Login Page | ✅ | `app/login/page.tsx` | Email/password + OAuth buttons |
| Signup Page | ✅ | `app/signup/page.tsx` | Email/password + OAuth buttons |

### Sanity Check:
- ✅ JWT verification on all protected routes
- ✅ OAuth flow complete with callback handler
- ✅ User metadata access for admin role
- ⚠️ **Check:** OAuth redirect URLs configured in Supabase dashboard?
- ⚠️ **Missing:** Password reset flow

---

## E. COVER GENERATION

### Cover Generator (`apps/engine/core/cover_generator.py`)

| Feature | Status | File | Notes |
|---------|--------|------|-------|
| OpenAI DALL-E Provider | ✅ | `cover_generator.py:50-150` | Uses DALL-E 3 |
| Generate Cover Image | ✅ | `cover_generator.py:160-220` | Returns image bytes |
| Save Cover to File | ✅ | `cover_generator.py:230-280` | Saves to local path |
| Genre-Based Prompts | ✅ | `cover_generator.py:290-340` | Dynamic prompt generation |
| NanoBanana Provider | ⚠️ | `cover_generator.py:50` | Placeholder only, not implemented |

### Integration Points:
- ✅ Called from Findaway pipeline (`findaway_pipeline.py:280-320`)
- ✅ Uses `cover_vibe` parameter for style customization
- ✅ Fallback if cover generation fails (pipeline continues)

### Sanity Check:
- ✅ OpenAI API key required (`OPENAI_API_KEY`)
- ✅ Proper error handling
- ⚠️ **Note:** Only DALL-E provider is functional

---

## F. GOOGLE DRIVE / DOCS INTEGRATION

| Feature | Status | Notes |
|---------|--------|-------|
| Google Drive Import | ❌ | **NOT IMPLEMENTED** |
| Google Docs Import | ❌ | **NOT IMPLEMENTED** |

**Files searched:** No files matching `*drive*` or `*google*` patterns found in the codebase (excluding auth).

The `source_type` field in `JobCreateRequest` includes `"google_drive"` as a valid option, but there is **no implementation** for this feature.

---

## Summary Table

| Feature Area | Status | Critical Issues |
|--------------|--------|-----------------|
| **A. Stripe Billing** | ✅ Complete | Missing DB migration docs |
| **B. Audiobook Engine** | ⚠️ Mostly Complete | In-memory queue, ElevenLabs/Inworld not implemented |
| **C. R2 Integration** | ✅ Complete | Missing CORS/lifecycle docs |
| **D. Supabase Auth + OAuth** | ✅ Complete | Missing password reset |
| **E. Cover Generation** | ✅ Complete | Only DALL-E provider works |
| **F. Google Drive** | ❌ Not Implemented | Listed in API but not built |

---

## Critical Findings

### 1. In-Memory Job Queue (High Priority)
**File:** `apps/engine/api/worker.py`
**Issue:** Jobs are stored in an in-memory `asyncio.Queue`. If the server restarts, all pending jobs are lost.
**Impact:** Jobs can be permanently lost during deployments or crashes.

### 2. Google Drive Listed but Not Implemented
**File:** `apps/engine/api/main.py:67`
**Issue:** `source_type: "google_drive"` is accepted but will fail silently.
**Impact:** Users may select this option and get confusing errors.

### 3. ElevenLabs/Inworld TTS Not Implemented
**File:** `apps/engine/api/main.py:224`
**Issue:** TTS providers are validated but only OpenAI works.
**Impact:** Selecting these providers will cause job failures.

### 4. Missing Database Migrations
**Issue:** No SQL migration files found for `user_billing` and `user_usage` tables.
**Impact:** New deployments may fail without manual DB setup.

### 5. Missing Worker Health Check
**File:** `apps/engine/api/main.py`
**Issue:** No endpoint to verify worker is running and processing jobs.
**Impact:** Hard to diagnose production issues.

---

## Recommendations (for Phase 2)

### Critical (Must Fix)
1. **Remove or disable Google Drive option** until implemented
2. **Remove or disable ElevenLabs/Inworld providers** until implemented
3. **Add database migration files** for billing tables

### Important (Should Fix)
4. **Add worker health endpoint** (`/worker/health`)
5. **Document R2 CORS configuration** for frontend uploads
6. **Add password reset flow** to auth system

### Nice to Have
7. Consider Redis-backed queue for job persistence
8. Add dead letter queue for failed jobs
9. Add ElevenLabs TTS implementation
10. Add Google Drive import

---

## Files Read During Audit

1. `apps/engine/api/main.py` - FastAPI application
2. `apps/engine/api/worker.py` - Background job processor
3. `apps/engine/api/database.py` - Supabase database wrapper
4. `apps/engine/api/storage_r2.py` - R2 storage client
5. `apps/engine/api/billing/routes.py` - Billing API routes
6. `apps/engine/api/billing/webhook.py` - Stripe webhook handler
7. `apps/engine/api/billing/stripe_client.py` - Stripe SDK wrapper
8. `apps/engine/api/billing/entitlements.py` - Plan entitlements
9. `apps/engine/pipelines/standard_single_voice.py` - Single voice pipeline
10. `apps/engine/pipelines/findaway_pipeline.py` - Findaway pipeline
11. `apps/engine/core/cover_generator.py` - Cover image generation
12. `apps/web/lib/billing.ts` - Frontend billing client
13. `apps/web/lib/auth.ts` - Frontend auth helpers
14. `apps/web/app/dashboard/page.tsx` - Dashboard page
15. `apps/web/app/pricing/page.tsx` - Pricing page
16. `apps/web/app/billing/page.tsx` - Billing management page
17. `apps/web/app/billing/success/page.tsx` - Checkout success page
18. `apps/web/app/billing/cancel/page.tsx` - Checkout cancel page
19. `apps/web/app/job/[id]/page.tsx` - Job detail page
20. `apps/web/app/auth/callback/route.ts` - OAuth callback

---

**END OF PHASE 1 AUDIT**

**Next Step:** Review this report and provide feedback before proceeding to Phase 2 (Prioritized Fix Plan).
