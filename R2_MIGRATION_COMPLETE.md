# ✅ Cloudflare R2 Migration Complete

## Summary

Successfully migrated all file storage from **Supabase Storage** to **Cloudflare R2**.

**Migration Date:** 2025-11-26
**Status:** ✅ Complete - Ready for Deployment

---

## What Changed

### ✅ Storage Provider Switch

**Before:**
- Manuscripts → Supabase Storage (`manuscripts` bucket)
- Audiobooks → Supabase Storage (`audiobooks` bucket)
- **Cost:** $25/month (Supabase Pro) or 1GB limit (free)
- **Bandwidth:** Charged per GB

**After:**
- Manuscripts → Cloudflare R2 (`manuscripts` bucket)
- Audiobooks → Cloudflare R2 (`audiobooks` bucket)
- **Cost:** ~$1.50/100GB/month
- **Bandwidth:** **FREE** (zero egress fees)

### ✅ Database & Auth (Unchanged)

Supabase is still used for:
- PostgreSQL database (`jobs`, `job_files` tables)
- User authentication (JWT tokens)
- API endpoints protection

---

## Files Modified

### Backend Code

1. **`apps/engine/api/storage_r2.py`** (NEW - 350 lines)
   - R2 storage client using boto3
   - Upload/download for manuscripts and audiobooks
   - Presigned URL generation
   - Bucket validation helpers

2. **`apps/engine/api/database.py`** (MODIFIED)
   - Removed Supabase Storage calls
   - Delegated storage operations to R2 client
   - Database operations unchanged
   - Storage methods now proxy to `storage_r2.py`

3. **`apps/engine/requirements.txt`** (MODIFIED)
   - Added: `boto3==1.34.0`

### Configuration

4. **`env/.env.example`** (MODIFIED)
   - Added R2 environment variables:
     - `R2_ACCOUNT_ID`
     - `R2_ACCESS_KEY_ID`
     - `R2_SECRET_ACCESS_KEY`
     - `R2_BUCKET_MANUSCRIPTS`
     - `R2_BUCKET_AUDIOBOOKS`
     - `R2_ENDPOINT`
     - `R2_PUBLIC_URL` (optional)
   - Deprecated Supabase bucket vars

### Documentation

5. **`STORAGE_ARCHITECTURE.md`** (NEW - 500+ lines)
   - Complete R2 architecture documentation
   - Cost analysis and comparisons
   - Security considerations
   - Frontend integration guide
   - Troubleshooting section

6. **`DEPLOYMENT_GUIDE.md`** (MODIFIED)
   - Added R2 setup instructions
   - Updated environment variable sections
   - Removed Supabase Storage bucket creation steps

7. **`R2_MIGRATION_COMPLETE.md`** (NEW - this file)
   - Migration summary and checklist

---

## Environment Variables

### Required for R2

You MUST set these in Railway (backend):

```bash
# Cloudflare R2
R2_ACCOUNT_ID=your_cloudflare_account_id
R2_ACCESS_KEY_ID=your_r2_access_key_here
R2_SECRET_ACCESS_KEY=your_r2_secret_key_here
R2_BUCKET_MANUSCRIPTS=manuscripts
R2_BUCKET_AUDIOBOOKS=audiobooks
R2_ENDPOINT=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
```

### Optional

```bash
R2_PUBLIC_URL=https://pub-xxxx.r2.dev  # If you enable R2 public access
```

### No Longer Needed (Deprecated)

```bash
# These can be removed from Railway
SUPABASE_BUCKET_MANUSCRIPTS=manuscripts
SUPABASE_BUCKET_AUDIOBOOKS=audiobooks
```

---

## Setup Instructions for You

### Step 1: Create R2 Buckets

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com) → **R2**
2. Create two buckets:
   - `manuscripts`
   - `audiobooks`
3. Keep them **private** (default)

### Step 2: Generate R2 API Token

1. In R2, click **Manage R2 API Tokens**
2. Click **Create API Token**
3. Configure:
   - Name: `rohimaya-backend`
   - Permissions: **Object Read & Write**
   - Buckets: Select both `manuscripts` and `audiobooks`
4. Click **Create**
5. Copy the credentials:
   - Access Key ID
   - Secret Access Key

### Step 3: Get Account ID

1. Look at your R2 dashboard URL or page header
2. Copy the Account ID (usually in format: `abc123...`)

### Step 4: Add Variables to Railway

Go to your Railway project → Variables → Add:

```bash
R2_ACCOUNT_ID=<your_account_id>
R2_ACCESS_KEY_ID=<your_access_key>
R2_SECRET_ACCESS_KEY=<your_secret_key>
R2_BUCKET_MANUSCRIPTS=manuscripts
R2_BUCKET_AUDIOBOOKS=audiobooks
R2_ENDPOINT=https://<your_account_id>.r2.cloudflarestorage.com
```

### Step 5: Deploy & Test

1. Railway will auto-redeploy with new env vars
2. Check logs for: `✅ R2 Storage initialized`
3. Test upload/download via API

---

## Code Flow

### Manuscript Upload Flow

```
1. User pastes text in frontend
2. Frontend → POST /jobs (with manuscript_text)
3. Backend (main.py:215):
   db.upload_manuscript(user_id, filename, content, job_id)
4. database.py:177:
   storage.upload_manuscript(...)  # Proxies to R2
5. storage_r2.py:71:
   boto3.put_object(Bucket='manuscripts', Key='manuscripts/user123/job456/book.txt')
6. Returns object key: "manuscripts/user123/job456/book.txt"
7. Saved to database: jobs.source_path = object_key
```

### Audiobook Download Flow

```
1. User clicks download in frontend
2. Frontend → GET /jobs/{id}/download
3. Backend (main.py:349):
   download_url = db.get_download_url(job.audio_path)
4. database.py:223:
   storage.generate_presigned_url(object_key, 3600)
5. storage_r2.py:192:
   boto3.generate_presigned_url('get_object', ...)
6. Returns: "https://<account>.r2.cloudflarestorage.com/audiobooks/...?signature=..."
7. Frontend redirects user to R2 URL
8. User downloads directly from R2 (no backend proxy)
```

---

## Database Schema

**No changes required!** Object keys are still stored as strings:

```sql
-- jobs table
CREATE TABLE jobs (
  source_path TEXT,  -- Now stores R2 key: "manuscripts/user123/book.txt"
  audio_path TEXT,   -- Now stores R2 key: "audiobooks/user123/job456/final.mp3"
  ...
);
```

---

## Testing Checklist

After deployment, test these scenarios:

### ✅ Backend Tests

- [ ] Health check returns 200: `GET /health`
- [ ] R2 initialization log appears: `✅ R2 Storage initialized`
- [ ] No R2-related errors in logs

### ✅ Upload Tests

- [ ] Create job with pasted text
- [ ] Verify manuscript uploaded to R2 (`manuscripts/` folder)
- [ ] Check database: `jobs.source_path` contains R2 key

### ✅ Processing Tests

- [ ] Job processes successfully
- [ ] Audiobook uploaded to R2 (`audiobooks/` folder)
- [ ] Check database: `jobs.audio_path` contains R2 key

### ✅ Download Tests

- [ ] GET `/jobs/{id}/download` returns presigned URL
- [ ] Presigned URL works (downloads file)
- [ ] URL expires after 1 hour

### ✅ Deletion Tests

- [ ] DELETE `/jobs/{id}` removes R2 objects
- [ ] Verify files deleted in R2 dashboard

---

## Rollback Plan

If R2 migration causes issues:

### Option 1: Quick Rollback

1. Restore old `database.py` from git:
   ```bash
   git show HEAD~1:apps/engine/api/database.py > apps/engine/api/database.py
   ```

2. Remove R2 import from `database.py`

3. Add back Supabase bucket env vars in Railway

4. Redeploy

### Option 2: Hybrid Mode

Keep R2 code but add fallback to Supabase:

```python
# In database.py
try:
    return self.storage.upload_manuscript(...)  # Try R2
except Exception as e:
    return self._upload_to_supabase(...)  # Fallback
```

---

## Cost Comparison

### Before (Supabase Storage)

| Tier | Storage | Bandwidth | Cost/month |
|------|---------|-----------|------------|
| Free | 1 GB | 2 GB | $0 |
| Pro | 100 GB | 200 GB | $25 |

**Limitation:** 50 MB max file size on free tier

### After (Cloudflare R2)

| Usage | Storage | Bandwidth | Cost/month |
|-------|---------|-----------|------------|
| 100 audiobooks (100 GB) | $1.50 | **$0** | **$1.50** |
| 1000 downloads (100 GB) | - | **$0** | **$0** |

**Total:** ~$1.50/month for 100GB + unlimited bandwidth

**Savings:** $23.50/month (vs Supabase Pro)

---

## Known Differences

### Presigned URLs

**Supabase:**
```
https://uiqjtiacuegfhfkrbngu.supabase.co/storage/v1/object/sign/audiobooks/...
```

**R2:**
```
https://abc123.r2.cloudflarestorage.com/audiobooks/...?X-Amz-Signature=...
```

Frontend doesn't care - both are just download URLs.

### Object Keys

**Supabase:** `user123/job456/file.mp3`
**R2:** `audiobooks/user123/job456/file.mp3` (includes bucket prefix)

Database stores full R2 key for clarity.

---

## Security Notes

### ✅ Private Buckets

Both R2 buckets are **private by default**:
- No anonymous access
- All downloads require presigned URLs
- URLs expire after 1 hour

### ✅ Credentials

R2 credentials stored as environment variables:
- Not in code
- Not in git
- Only in Railway backend

### ✅ User Isolation

Object keys include user ID:
- `manuscripts/{user_id}/{job_id}/...`
- Easy to enforce ownership
- Clear audit trail

---

## Support Resources

### Documentation

- **Storage Architecture:** See `STORAGE_ARCHITECTURE.md`
- **Deployment Guide:** See `DEPLOYMENT_GUIDE.md` (R2 section)
- **R2 Official Docs:** https://developers.cloudflare.com/r2/

### Troubleshooting

**Issue:** "NoSuchBucket" error
**Fix:** Create `manuscripts` and `audiobooks` buckets in Cloudflare

**Issue:** "AccessDenied" error
**Fix:** Verify R2 API token has "Object Read & Write" permissions

**Issue:** Presigned URL returns 403
**Fix:** URL expired - regenerate from backend

**Issue:** Upload succeeds but file not visible
**Fix:** Check correct bucket name and account ID

---

## Next Steps

1. ✅ Create R2 buckets in Cloudflare
2. ✅ Generate R2 API token
3. ✅ Add env vars to Railway
4. ✅ Redeploy backend
5. ✅ Test upload → process → download flow
6. ✅ Monitor costs in Cloudflare dashboard

---

**Migration completed successfully!** 🎉

Storage costs reduced by **94%** ($25 → $1.50/month) while removing file size limits.

