# November 28, 2025 - Session Summary

## What Was Implemented

### Phase 1: Google Drive Backend Routes
Complete OAuth flow and file import functionality.

**New Endpoints Added to `apps/engine/api/main.py`:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/google-drive/auth-url` | GET | Returns OAuth URL to redirect user to Google |
| `/google-drive/callback` | GET | Handles OAuth callback, stores tokens |
| `/google-drive/status` | GET | Check if user has connected Google Drive |
| `/google-drive/files` | GET | List manuscript-compatible files from Drive |
| `/google-drive/import` | POST | Download file from Drive, convert to text, upload to R2 |
| `/google-drive/disconnect` | DELETE | Remove stored tokens |

**New Database Methods in `apps/engine/api/database.py`:**
- `get_google_drive_tokens(user_id)` - Retrieve stored OAuth tokens
- `store_google_drive_tokens(user_id, tokens)` - Save/update OAuth tokens
- `clear_google_drive_tokens(user_id)` - Delete OAuth tokens

**New Migration: `supabase/migrations/0003_google_drive_tokens.sql`**
- Creates `google_drive_tokens` table
- Row Level Security policies
- Auto-update trigger for `updated_at`

---

### Phase 2: Frontend Google Drive Import UX
Added third input mode in job creation.

**Changes to `apps/web/app/dashboard/page.tsx`:**
- Added "Google Drive" tab button (shows only when configured)
- File picker UI showing documents from user's Drive
- Connect/Disconnect functionality
- Import button to download and prepare file for job creation
- Success confirmation after import

**Changes to `apps/web/lib/apiClient.ts`:**
- Added `GoogleDriveStatus`, `GoogleDriveFile`, `GoogleDriveFilesResponse` types
- Added API functions:
  - `getGoogleDriveAuthUrl()`
  - `getGoogleDriveStatus()`
  - `listGoogleDriveFiles()`
  - `importGoogleDriveFile()`
  - `disconnectGoogleDrive()`

---

### Phase 3: Cover Art Generation Backend
Exposed existing cover generator through API.

**New Endpoint in `apps/engine/api/main.py`:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/jobs/{job_id}/cover` | GET | Get presigned URL for job's cover image |

**Updated Models:**
- `JobCreateRequest` - Added `generate_cover`, `cover_vibe`, `cover_image_provider` fields
- `JobResponse` - Added `generate_cover`, `cover_vibe`, `cover_image_provider`, `has_cover`, `cover_image_path` fields
- `CoverArtResponse` - New model with `has_cover`, `cover_url`, `cover_path`

---

### Phase 4: Frontend Cover Art Options
Added cover generation toggle and display.

**Changes to `apps/web/app/dashboard/page.tsx`:**
- Toggle switch for "Generate AI Cover Art"
- Cover vibe/style dropdown (dramatic, minimalist, vintage, fantasy, modern, literary)
- Options sent with job creation payload

**Changes to `apps/web/app/job/[id]/page.tsx`:**
- Cover image display in job header (128x128 thumbnail)
- Loading state while cover generates
- Fetches cover URL from `/jobs/{id}/cover` endpoint

**Changes to `apps/web/lib/apiClient.ts`:**
- Added `CoverArtResponse` type
- Added `getJobCoverUrl()` function
- Updated `Job` interface with cover fields
- Updated `CreateJobPayload` with cover options

---

## Stripe Products Setup

You need to create **3 recurring subscription products** in Stripe:

### Creator Plan
```
Product Name: Creator
Description: Perfect for indie authors - 3 audiobooks/month, up to 1 hour each
Metadata: plan_id = creator
Price: $29.00/month (recurring)
```
After creating, set in Railway: `STRIPE_PRICE_CREATOR_MONTHLY=price_xxx`

### Author Pro Plan
```
Product Name: Author Pro
Description: For serious authors - Unlimited audiobooks, up to 6 hours each
Metadata: plan_id = author_pro
Price: $79.00/month (recurring)
```
After creating, set in Railway: `STRIPE_PRICE_AUTHOR_PRO_MONTHLY=price_xxx`

### Publisher Plan
```
Product Name: Publisher
Description: For publishers & production houses - Unlimited everything + team features
Metadata: plan_id = publisher
Price: $249.00/month (recurring)
```
After creating, set in Railway: `STRIPE_PRICE_PUBLISHER_MONTHLY=price_xxx`

---

## Deployment Checklist

### Before Deploying

1. **Run Database Migration**
   - Go to Supabase Dashboard > SQL Editor
   - Paste contents of `supabase/migrations/0003_google_drive_tokens.sql`
   - Execute the migration

2. **Create Stripe Products**
   - Follow the Stripe Products Setup section above
   - Copy the Price IDs (start with `price_`)

3. **Update Railway Environment Variables**
   ```
   STRIPE_PRICE_CREATOR_MONTHLY=price_xxx
   STRIPE_PRICE_AUTHOR_PRO_MONTHLY=price_xxx
   STRIPE_PRICE_PUBLISHER_MONTHLY=price_xxx
   ```

4. **Verify Google Drive Config (if using)**
   ```
   GOOGLE_DRIVE_CLIENT_ID=xxx.apps.googleusercontent.com
   GOOGLE_DRIVE_CLIENT_SECRET=GOCSPX-xxx
   GOOGLE_DRIVE_REDIRECT_URI=https://api.authorflowstudios.rohimayapublishing.com/api/auth/google-drive/callback
   ```

### Test After Deploying

- [ ] Dashboard loads without errors
- [ ] Google Drive tab appears (if configured)
- [ ] Can connect/disconnect Google Drive
- [ ] Can list and import files from Drive
- [ ] Cover art toggle appears in job creation
- [ ] Cover vibe selector works
- [ ] Job detail page shows cover image
- [ ] Pricing page has correct prices
- [ ] Checkout redirects to Stripe correctly
- [ ] Free trial badge appears after checkout (trialing status)
- [ ] Trial days remaining shown on dashboard
- [ ] Trial days remaining shown on billing page
- [ ] Expired trial blocks job creation with clear message

---

## Phase 5: Free Trial Implementation

Added Stripe free trials using the 2025 Checkout API method.

**Trial Configuration:**
| Plan | Trial Period |
|------|-------------|
| Creator | 7 days |
| Author Pro | 14 days |
| Publisher | 14 days |

**Backend Changes (`apps/engine/api/billing/routes.py`):**
- Added `PLAN_TRIAL_DAYS` dictionary with per-plan trial periods
- Added `get_trial_days_for_plan()` helper function
- Modified checkout session creation to use plan-specific trial days
- Added `TrialInfo` model to `BillingInfoResponse`
- Calculates and returns `trial_days_remaining` in billing info endpoint

**Webhook Handler (`apps/engine/api/billing/webhook.py`):**
- Added handler for `customer.subscription.trial_will_end` event
- Fires 3 days before trial ends (Stripe's default)
- Updates database with trial end date
- Ready for email notification integration

**Trial Enforcement (`apps/engine/api/main.py`):**
- Added subscription status check before job creation
- Users with "trialing" status have full plan access
- Users with expired trials (status != active/trialing) are blocked
- Clear error message directs users to resubscribe

**Frontend Changes:**
- `apps/web/lib/billing.ts`: Added `TrialInfo` interface
- `apps/web/app/dashboard/page.tsx`: Added trial badge showing days remaining
- `apps/web/app/billing/page.tsx`: Added trial badge and days remaining in status text

---

## Phase 6: Yearly Billing Support

Added support for monthly vs yearly billing intervals.

**Yearly Pricing:**
| Plan | Monthly | Yearly | Savings |
|------|---------|--------|---------|
| Creator | $29/mo | $290/yr | 2 months free |
| Author Pro | $79/mo | $790/yr | 2 months free |
| Publisher | $249/mo | $2,490/yr | 2 months free |

**Backend Changes (`apps/engine/api/billing/`):**
- `routes.py`: Added `billing_interval` to BillingInfoResponse
- `stripe_client.py`: Already supported yearly via `get_price_id_for_plan(plan_id, "yearly")`
- `webhook.py`: Added `extract_billing_interval_from_subscription()` helper

**Frontend Changes:**
- `apps/web/lib/billing.ts`: Added yearly prices to PLANS, `billing_interval` to BillingInfo
- `apps/web/app/pricing/page.tsx`: Added monthly/yearly toggle, dynamic price display
- `apps/web/app/billing/page.tsx`: Shows billing interval badge (Monthly/Annual)

**New Migration:**
- `supabase/migrations/0004_billing_interval.sql`: Adds `billing_interval` column to `user_billing`

**Environment Variables (already in Railway):**
```
STRIPE_PRICE_CREATOR_YEARLY=price_1SYUh6A241yxjWZ7zYAt5J71
STRIPE_PRICE_AUTHOR_PRO_YEARLY=price_1SYUgPA241yxjWZ7TmRtup9I
STRIPE_PRICE_PUBLISHER_YEARLY=price_1SYUe2A241yxjWZ7Bg6fhGlz
```

---

## Files Changed This Session

| File | Change Type |
|------|-------------|
| `apps/engine/api/main.py` | Modified - Added Google Drive, Cover endpoints, trial enforcement |
| `apps/engine/api/database.py` | Modified - Added token storage methods |
| `apps/engine/api/billing/routes.py` | Modified - Added trial config, yearly billing, TrialInfo response |
| `apps/engine/api/billing/webhook.py` | Modified - Added trial_will_end handler, billing_interval extraction |
| `apps/engine/api/billing/stripe_client.py` | Modified - Yearly price ID support |
| `apps/web/lib/apiClient.ts` | Modified - Added types & API functions |
| `apps/web/lib/billing.ts` | Modified - Added TrialInfo, yearly prices, billing_interval |
| `apps/web/app/dashboard/page.tsx` | Modified - Added Google Drive tab, cover options, trial badge |
| `apps/web/app/billing/page.tsx` | Modified - Added trial badge, interval badge, status text |
| `apps/web/app/pricing/page.tsx` | Modified - Added monthly/yearly toggle, yearly pricing display |
| `apps/web/app/job/[id]/page.tsx` | Modified - Added cover image display |
| `supabase/migrations/0003_google_drive_tokens.sql` | **NEW** - Database migration |
| `supabase/migrations/0004_billing_interval.sql` | **NEW** - Adds billing_interval column |
| `docs/BILLING.md` | Modified - Added yearly billing and trial documentation |
| `docs/BILLING_TESTING.md` | **NEW** - Testing guide for billing |
| `docs/SESSION_CHANGES_AND_RECOMMENDATIONS.md` | Modified - Updated documentation |
| `docs/NOVEMBER_28_SESSION_SUMMARY.md` | **NEW** - This file |

---

## Suggestions for Going Forward

### High Priority (Before Launch)

1. **Test End-to-End Flow**
   - Create a job with Google Drive import
   - Create a job with cover art enabled
   - Verify billing flow works with Stripe

2. **Error Handling**
   - Add toast notifications for success/failure states
   - Add user-friendly error messages for common failures

3. **Cover Art Integration in Worker**
   - Ensure the worker pipeline calls cover generator when `generate_cover=true`
   - Store generated cover in R2 and update job with `has_cover=true` and `cover_image_path`

### Medium Priority (Post-Launch)

4. **Google Drive Pagination**
   - Currently shows first 20 files only
   - Add "Load More" button for additional files

5. **Cover Art Preview**
   - Show cover preview before job submission
   - Allow user to regenerate if they don't like it

6. **Email Notifications**
   - "Your audiobook is ready" email with cover image
   - "Job failed" email with retry link

### Lower Priority (Future Enhancements)

7. **Multiple Cover Options**
   - Generate 3-4 cover options
   - Let user choose their favorite

8. **Google Docs Real-Time Sync**
   - Allow editing in Google Docs
   - Auto-sync changes to job

9. **Dropbox/OneDrive Integration**
   - Same pattern as Google Drive
   - Additional import sources

---

## Architecture Notes

### Google Drive Flow
```
User clicks "Connect" → Frontend calls /google-drive/auth-url
→ User redirected to Google → User authorizes
→ Google redirects to /google-drive/callback with code
→ Backend exchanges code for tokens → Stores in database
→ Redirects to frontend with success → Frontend refreshes status
→ User can now list and import files
```

### Cover Art Flow
```
User enables cover toggle → Selects vibe → Creates job
→ Job created with generate_cover=true, cover_vibe="dramatic"
→ Worker picks up job → Generates audio
→ Worker calls cover_generator.py with title + vibe
→ Cover image uploaded to R2 → Job updated with cover_image_path
→ Frontend fetches /jobs/{id}/cover → Displays image
```

---

## Support

If you encounter issues:
1. Check Railway logs for backend errors
2. Check browser console for frontend errors
3. Check Supabase Dashboard > Logs for database errors
4. Check Stripe Dashboard > Developers > Webhooks for billing issues

Contact: support@authorflowstudios.rohimayapublishing.com
