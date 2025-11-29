# AuthorFlow Studios - Full Audit Report

> Comprehensive analysis of implementation gaps between vision and current state

**Date:** November 28, 2025
**Status:** AUDIT COMPLETE

---

## Executive Summary

AuthorFlow Studios is **85% complete** with solid architecture and most features implemented. However, there are **critical bugs** that must be fixed before production launch, and several features that are partially implemented.

### Overall Status by Category

| Category | Status | Completion |
|----------|--------|------------|
| Manuscript Intake | ✅ PRODUCTION READY | 100% |
| Manuscript Parsing | ⚠️ MOSTLY COMPLETE | 85% |
| TTS & Voice Systems | ⚠️ WORKING BUT LIMITED | 80% |
| Findaway Pipeline | ✅ FIXED | 95% |
| Cover Art Generation | ✅ PRODUCTION READY | 95% |
| Billing & Subscriptions | ⚠️ MOSTLY COMPLETE | 90% |
| Job Management | ✅ PRODUCTION READY | 95% |
| Admin Tools | ✅ WORKING | 90% |

---

## RECENTLY FIXED ISSUES

### 1. Findaway Pipeline Section Plan Bug ✅ FIXED

**Severity:** Was CRITICAL
**File:** `apps/engine/pipelines/findaway_pipeline.py`

**Solution Applied:**
- Now uses `get_sections_for_tts()` to properly flatten the section plan
- Updated `_generate_section_audio()` to handle both `text` and `script` fields
- Updated manifest creation to use correct field names

---

### 2. Romance/Spicy Auto-Detection ✅ FIXED

**File:** `apps/engine/agents/retail_sample_agent.py`

**Solution Applied:**
- Added `detect_romance_heat_level()` function with keyword analysis
- Retail sample selection now defaults to "auto" mode
- Automatically detects romance content and adjusts sample style

---

## REMAINING ISSUES

### 1. Missing Email Notifications

**Severity:** HIGH - Poor user experience
**Files:** `apps/engine/api/billing/webhook.py:364, 403`

**Problems:**
1. Trial ending notification not implemented (marked as TODO)
2. Payment failed notification not implemented (marked as TODO)

**Impact:**
- Users get no warning when trial is about to end
- Users don't know their payment failed
- Increased churn and support tickets

**Fix Required:**
Implement email sending using Brevo/SendGrid/Resend for:
- `handle_trial_will_end()` - Send 3 days before trial ends
- `handle_payment_failed()` - Send immediately with payment update link

---

## HIGH PRIORITY ISSUES

### 3. Billing Interval Not Saved on Subscription Updates

**File:** `apps/engine/api/billing/webhook.py:274`

**Problem:** When a subscription is updated (upgrade/downgrade), the `billing_interval` is not extracted and saved.

**Impact:** Database may show incorrect billing interval after plan changes.

---

### 4. Provider Fallback Not Connected

**Files:** `apps/engine/src/tts_provider.py` (designed but unused)

**Problem:** A `TTSManager` class exists for provider fallback but is never instantiated. Each pipeline is hardcoded to a single provider.

**Impact:**
- If OpenAI is down, all jobs fail
- No automatic fallback to ElevenLabs
- Reduced reliability

---

### 5. ElevenLabs Limited to Dual-Voice Only

**File:** `apps/engine/pipelines/phoenix_peacock_dual_voice.py`

**Problem:** ElevenLabs integration only works in dual-voice mode. Single-voice and multi-character pipelines force OpenAI.

**Impact:** Users can't choose ElevenLabs for standard audiobooks even if they prefer the voice quality.

---

## MEDIUM PRIORITY ISSUES

### 6. Scene Separation is Structural Only

**File:** `apps/engine/core/advanced_chunker.py`

**Current State:** Splits by paragraph breaks and sentence boundaries.
**Missing:** No semantic scene detection (POV changes, time jumps, scene break symbols like `***` or `---`).

**Impact:** Audio pacing may not respect natural scene breaks.

---

### 7. No Retry Limit Enforcement

**File:** `apps/engine/api/main.py:703`

**Problem:** Jobs can be retried infinitely. Comment says "no limit for now during development."

**Impact:** Could allow abuse or infinite loops on certain failure modes.

---

### 9. Admin Dashboard Query Performance

**File:** `apps/engine/api/main.py:1505`

**Problem:** Uses `SELECT * FROM jobs` to count jobs instead of `SELECT COUNT(*)`.

**Impact:** Slow admin dashboard with large job tables.

---

### 10. Inworld TTS is Dead Code

**File:** `apps/engine/src/tts_inworld.py`

**Problem:** Exists but never called in any pipeline. Appears to be abandoned.

**Impact:** Confusing codebase; should be removed or fully implemented.

---

## FEATURE GAPS (Vision vs Reality)

### What Your Vision Promised vs Current State

| Feature | Vision | Current State | Gap |
|---------|--------|---------------|-----|
| Multi-character voices | Automatic character-to-voice mapping | ✅ Works with 6 OpenAI voices | Limited voice variety |
| Emotional narration | AI detects emotion, TTS expresses it | ⚠️ Detection works, expression limited to OpenAI instructions | No prosody control |
| Romance spicy detection | Auto-detect heat level | ❌ Manual mode selection | Need auto-detection |
| Scene separation | Smart scene detection | ⚠️ Paragraph-based only | No semantic detection |
| Provider fallback | Auto-fallback on failure | ❌ Not connected | Single point of failure |
| Findaway packages | Complete ready-to-upload | ❌ BROKEN (section plan bug) | Critical bug |
| Email notifications | Trial/payment alerts | ❌ Not implemented | TODO in code |
| Voice preview | Try voices before generating | ❌ Not implemented | No frontend UI |

---

## WORKING FEATURES (Confirmed Production Ready)

### Fully Implemented & Working

1. **Manuscript Intake**
   - ✅ File upload (PDF, DOCX, TXT, MD)
   - ✅ Google Drive import with OAuth
   - ✅ Text paste

2. **Manuscript Parsing**
   - ✅ Chapter detection (AI + regex fallback)
   - ✅ Dialogue extraction
   - ✅ Character identification with voice suggestions
   - ✅ 14-emotion tone analysis

3. **TTS Generation**
   - ✅ Single-voice (OpenAI)
   - ✅ Dual-voice (ElevenLabs)
   - ✅ Multi-character (OpenAI, up to 4 characters)
   - ✅ Emotional TTS instructions

4. **Cover Art**
   - ✅ OpenAI DALL-E 3 generation
   - ✅ Custom description support
   - ✅ Genre-specific prompting
   - ✅ 2400x2400 Findaway-compliant size

5. **Billing**
   - ✅ Stripe integration
   - ✅ 4 plan tiers
   - ✅ Monthly/yearly billing
   - ✅ Free trial support
   - ✅ Usage tracking
   - ✅ Plan limit enforcement

6. **Job Management**
   - ✅ Retry failed jobs
   - ✅ Clone jobs with new settings
   - ✅ Progress tracking
   - ✅ Worker recovery on restart

7. **Admin Tools**
   - ✅ Worker health endpoint
   - ✅ Queue status monitoring
   - ✅ System status dashboard

---

## RECOMMENDED FIX PRIORITY

### Week 1 (Critical)

1. **Fix Findaway section plan bug** (2-4 hours)
   - Use `get_sections_for_tts()` to flatten section plan
   - Test with full book generation

2. **Add email notifications** (4-6 hours)
   - Integrate email provider (Brevo/SendGrid)
   - Implement trial ending notification
   - Implement payment failed notification

### Week 2 (High Priority)

3. **Fix billing interval on subscription updates** (1-2 hours)
4. **Connect provider fallback system** (4-6 hours)
5. **Enable ElevenLabs for all pipelines** (2-4 hours)

### Week 3 (Medium Priority)

6. **Add retry limits** (1 hour)
7. **Optimize admin dashboard queries** (1-2 hours)
8. **Remove or implement Inworld TTS** (1-2 hours)

### Future Enhancements

- Auto-detect romance heat levels
- Semantic scene detection
- Voice preview/demo
- Google Cloud TTS alternative

---

## DATABASE MIGRATIONS NEEDED

Make sure these migrations have been run in Supabase:

1. ✅ `0001_create_jobs_tables.sql` - Core jobs schema
2. ✅ `0002_create_storage_buckets.sql` - R2 bucket config
3. ✅ `0003_google_drive_tokens.sql` - OAuth token storage
4. ✅ `0004_billing_interval.sql` - Yearly billing support
5. ✅ `0005_cover_art_columns.sql` - Cover generation fields

---

## ENVIRONMENT VARIABLES CHECKLIST

### Required for Basic Operation
- [x] `OPENAI_API_KEY`
- [x] `SUPABASE_URL`
- [x] `SUPABASE_ANON_KEY`
- [x] `SUPABASE_SERVICE_ROLE_KEY`
- [x] `SUPABASE_JWT_SECRET`
- [x] `R2_ACCOUNT_ID`
- [x] `R2_ACCESS_KEY_ID`
- [x] `R2_SECRET_ACCESS_KEY`
- [x] `R2_BUCKET_NAME`

### Required for Billing
- [x] `STRIPE_SECRET_KEY`
- [x] `STRIPE_WEBHOOK_SECRET`
- [x] `STRIPE_PRICE_CREATOR_MONTHLY`
- [x] `STRIPE_PRICE_AUTHOR_PRO_MONTHLY`
- [x] `STRIPE_PRICE_PUBLISHER_MONTHLY`

### Optional Features
- [ ] `ELEVENLABS_API_KEY` - For dual-voice mode
- [ ] `GOOGLE_DRIVE_CLIENT_ID` - For Drive import
- [ ] `GOOGLE_DRIVE_CLIENT_SECRET`
- [ ] `GOOGLE_DRIVE_REDIRECT_URI`
- [ ] `BANANA_API_KEY` - Alternative cover provider
- [ ] `ADMIN_EMAILS` - Admin bypass list

---

## CONCLUSION

AuthorFlow Studios has excellent bones and is close to production-ready. The **critical Findaway bug** is the only blocker preventing the core value proposition from working. Once fixed, along with email notifications, the platform can launch.

**Estimated time to production-ready:** 1-2 weeks of focused development

**Key strengths:**
- Solid architecture
- Comprehensive billing system
- Good error handling
- Worker recovery system
- Multi-provider design (even if not fully connected)

**Key weaknesses:**
- Critical pipeline bug
- Missing email notifications
- Limited voice variety
- No provider fallback in production

---

*Report generated: November 28, 2025*
