# AuthorFlow Studios - Implementation Summary

This document summarizes all major features implemented in recent development sessions.

---

## Part 1: Findaway Pipeline & App Upgrades

### Phase 1: Manuscript Parser Agent
**File:** `apps/engine/core/manuscript_parser.py`

- AI-powered manuscript parsing using GPT-4
- Detects chapters, sections, and dialogue
- Identifies character names and speaking patterns
- Returns structured JSON for TTS processing

### Phase 2: Retail Sample Selection Agent
**File:** `apps/engine/agents/retail_sample_agent.py`

- AI agent that selects the best 5-minute sample for retail preview
- Analyzes manuscript for engaging excerpts
- Supports "default" and "spicy" sample styles (for romance genre)
- Returns timestamp ranges for sample extraction

### Phase 3: Findaway Pipeline
**File:** `apps/engine/pipelines/findaway_pipeline.py`

Complete Findaway-ready audiobook generation pipeline:
- Integrates manuscript parsing
- Retail sample selection
- Credits generation (opening/closing)
- Cover image generation via DALL-E
- Creates ZIP package with manifest.json
- Findaway-compliant file structure

### Phase 4: Worker Updates
**File:** `apps/engine/api/worker.py`

- Added "findaway" mode to job processing
- Progress callback integration for real-time updates
- ZIP package upload to R2 storage
- Findaway-specific job fields handling

### Phase 5: Cover Generation
**File:** `apps/engine/agents/cover_generator.py`

- DALL-E 3 integration for AI cover art
- Genre-aware cover generation
- Custom "vibe" descriptions support
- High-resolution output (1024x1024)

### Phase 6: OAuth Integration
**Files:**
- `apps/web/lib/auth.ts` - Added `signInWithOAuth()` function
- `apps/web/app/login/page.tsx` - Google & GitHub OAuth buttons
- `apps/web/app/signup/page.tsx` - Google & GitHub OAuth buttons
- `apps/web/app/auth/callback/route.ts` - OAuth callback handler

### Phase 7: Database Schema Updates
**Files:**
- `supabase-schema.sql` - Updated with Findaway fields
- `supabase-migration-v2.sql` - Migration for existing databases

New columns added to `jobs` table:
- `author`, `narrator_name`, `genre`, `language`, `isbn`, `publisher`
- `narrator_voice_id`, `character_voice_id`, `character_name`, `tts_provider`
- `sample_style`, `cover_vibe`
- `package_type`, `section_count`, `has_cover`, `manifest_json`
- Changed `progress` to `progress_percent` (DECIMAL)

### API Updates
**File:** `apps/engine/api/main.py`

- Updated `JobCreateRequest` with Findaway fields
- Updated `JobResponse` with Findaway output fields
- Added "findaway" to valid modes
- Updated retry endpoint to allow cancelled jobs

### Cleanup
Removed unnecessary MD files (kept `EPIC_VICTORY.md`):
- BACKEND_API_COMPLETE.md
- BACKEND_FLOW_DESIGN.md
- GITHUB_PUSH_SUMMARY.md
- MONOREPO_TRANSFORMATION_COMPLETE.md
- PHASE_2_SUMMARY.md
- R2_MIGRATION_COMPLETE.md
- RESTRUCTURE_ANALYSIS.md
- DEPLOYMENT_AUDIT_REPORT.md
- STORAGE_ARCHITECTURE.md

---

## Part 2: Stripe Billing Integration

### Subscription Tiers

| Plan | Price | Projects/Month | Max Minutes | Key Features |
|------|-------|----------------|-------------|--------------|
| Free | $0 | 1 | 5 min | Basic testing |
| Creator | $29/mo | 3 | 60 min | Findaway, covers |
| Author Pro | $79/mo | Unlimited | 360 min | Dual voice, priority |
| Publisher | $249/mo | Unlimited | Unlimited | Team access (5) |
| Admin | N/A | Unlimited | Unlimited | Full access |

### Backend Implementation

#### Database Schema
**File:** `supabase-billing-schema.sql`

```sql
-- user_billing: Tracks subscription status
CREATE TABLE user_billing (
    user_id UUID REFERENCES auth.users(id),
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    plan_id TEXT DEFAULT 'free',
    status TEXT DEFAULT 'inactive',
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    cancel_at_period_end BOOLEAN
);

-- user_usage: Tracks monthly usage for limits
CREATE TABLE user_usage (
    user_id UUID REFERENCES auth.users(id),
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    projects_created INTEGER,
    minutes_generated INTEGER
);
```

#### Billing Module
**Directory:** `apps/engine/api/billing/`

| File | Purpose |
|------|---------|
| `__init__.py` | Package exports |
| `entitlements.py` | Plan definitions & entitlements mapping |
| `stripe_client.py` | Stripe SDK wrapper functions |
| `routes.py` | FastAPI billing endpoints |
| `webhook.py` | Stripe webhook handler |

#### Entitlements System
**File:** `apps/engine/api/billing/entitlements.py`

```python
PLAN_ENTITLEMENTS = {
    "free": Entitlements(max_projects_per_month=1, max_minutes_per_book=5, ...),
    "creator": Entitlements(max_projects_per_month=3, findaway_package=True, ...),
    "author_pro": Entitlements(max_projects_per_month=None, dual_voice=True, ...),
    "publisher": Entitlements(max_projects_per_month=None, team_access=True, ...),
    "admin": Entitlements(max_projects_per_month=None, ...)  # Full access
}
```

#### API Endpoints
**File:** `apps/engine/api/billing/routes.py`

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/billing/plans` | GET | No | Get available plans |
| `/billing/me` | GET | Yes | Get user's billing info + usage |
| `/billing/create-checkout-session` | POST | Yes | Start Stripe Checkout |
| `/billing/create-portal-session` | POST | Yes | Access Billing Portal |
| `/billing/webhook` | POST | No | Stripe webhook handler |

#### Webhook Events Handled
**File:** `apps/engine/api/billing/webhook.py`

- `checkout.session.completed` - New subscription
- `customer.subscription.created` - Subscription created
- `customer.subscription.updated` - Plan changes
- `customer.subscription.deleted` - Cancellation
- `invoice.payment_failed` - Payment failure
- `invoice.paid` - Successful payment

#### Limit Enforcement
**File:** `apps/engine/api/main.py` (lines 237-282)

Added to `create_job` endpoint:
- Checks monthly project limits before job creation
- Validates Findaway mode access (Creator+ only)
- Validates dual-voice access (Author Pro+ only)
- Increments usage counters after job creation
- Admin bypass for users with `role: "admin"` in metadata

#### Database Methods
**File:** `apps/engine/api/database.py`

New methods added:
- `get_user()` - Get user info from Supabase Auth
- `get_user_billing()` - Get billing record
- `get_user_billing_by_customer()` - Lookup by Stripe customer ID
- `get_user_billing_by_subscription()` - Lookup by subscription ID
- `upsert_user_billing()` - Create/update billing record
- `get_user_usage_current_period()` - Get current month's usage
- `increment_user_usage()` - Increment usage counters

### Frontend Implementation

#### Billing Library
**File:** `apps/web/lib/billing.ts`

- `getBillingInfo()` - Fetch user's billing status
- `getPlans()` - Fetch available plans
- `createCheckoutSession()` - Start Stripe Checkout
- `createPortalSession()` - Open Billing Portal
- `PLANS` constant - Frontend plan display data
- Helper functions: `hasFeature()`, `formatLimit()`, `getPlanBadgeColor()`

#### Pages Created

| Page | File | Purpose |
|------|------|---------|
| `/pricing` | `apps/web/app/pricing/page.tsx` | Plan comparison & checkout |
| `/billing` | `apps/web/app/billing/page.tsx` | User's billing dashboard |
| `/billing/success` | `apps/web/app/billing/success/page.tsx` | Post-checkout confirmation |
| `/billing/cancel` | `apps/web/app/billing/cancel/page.tsx` | Checkout cancellation |

#### Dashboard Updates
**File:** `apps/web/app/dashboard/page.tsx`

Added plan info banner showing:
- Current plan badge (Free/Creator/Author Pro/Publisher/Admin)
- Usage counter (X / Y projects this month)
- "Upgrade Plan" button (for free users)
- "Manage Billing" button (for paid users)
- Cancellation warning if subscription ending

### Documentation
**File:** `docs/BILLING.md`

Complete setup guide covering:
- Required environment variables
- Stripe product/price setup instructions
- Plan ID metadata mapping
- Webhook configuration
- Admin user setup
- Database table documentation
- API endpoint reference
- Troubleshooting guide

---

## Environment Variables Required

### Backend (Railway)

```bash
# Existing
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
OPENAI_API_KEY=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_ENDPOINT_URL=...

# New for Stripe
STRIPE_SECRET_KEY=sk_live_... or sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_CREATOR_MONTHLY=price_...
STRIPE_PRICE_AUTHORPRO_MONTHLY=price_...
STRIPE_PRICE_PUBLISHER_MONTHLY=price_...
FRONTEND_URL=https://authorflowstudios.rohimayapublishing.com
```

### Frontend (Vercel)

```bash
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
NEXT_PUBLIC_ENGINE_API_URL=https://your-engine.railway.app
```

---

## Files Created/Modified Summary

### New Files
- `apps/engine/pipelines/findaway_pipeline.py`
- `apps/engine/api/billing/__init__.py`
- `apps/engine/api/billing/entitlements.py`
- `apps/engine/api/billing/stripe_client.py`
- `apps/engine/api/billing/routes.py`
- `apps/engine/api/billing/webhook.py`
- `apps/web/lib/billing.ts`
- `apps/web/app/pricing/page.tsx`
- `apps/web/app/billing/page.tsx`
- `apps/web/app/billing/success/page.tsx`
- `apps/web/app/billing/cancel/page.tsx`
- `supabase-billing-schema.sql`
- `supabase-migration-v2.sql`
- `docs/BILLING.md`

### Modified Files
- `apps/engine/api/main.py` - Findaway fields + billing enforcement
- `apps/engine/api/worker.py` - Findaway mode handling
- `apps/engine/api/database.py` - Billing/usage methods
- `apps/web/lib/auth.ts` - OAuth function
- `apps/web/app/login/page.tsx` - OAuth buttons
- `apps/web/app/signup/page.tsx` - OAuth buttons
- `apps/web/app/dashboard/page.tsx` - Plan info banner
- `supabase-schema.sql` - Findaway columns

---

## Next Steps (If Needed)

1. **Deploy billing schema** - Run `supabase-billing-schema.sql` in Supabase
2. **Configure Stripe** - Create products/prices with `plan_id` metadata
3. **Set environment variables** - Add Stripe keys to Railway
4. **Create webhook endpoint** - Add `/billing/webhook` to Stripe Dashboard
5. **Test checkout flow** - Use Stripe test mode with test cards
6. **Make yourself admin** - Set `{"role": "admin"}` in Supabase user metadata
