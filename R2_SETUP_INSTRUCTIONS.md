# 🚀 Quick Setup: Cloudflare R2 for Rohimaya Audiobook Generator

## What You Need to Do Now

The code is ready! You just need to set up R2 and configure environment variables.

---

## Step 1: Create Cloudflare R2 Buckets (5 minutes)

### 1.1 Go to Cloudflare R2

1. Visit https://dash.cloudflare.com
2. Login to your account
3. Click **R2** in the left sidebar
4. Click **Create bucket**

### 1.2 Create First Bucket

- **Name:** `manuscripts`
- **Location:** Automatic (recommended)
- Click **Create bucket**

### 1.3 Create Second Bucket

- Click **Create bucket** again
- **Name:** `audiobooks`
- **Location:** Automatic
- Click **Create bucket**

✅ **Result:** You should see two buckets listed in R2

---

## Step 2: Generate R2 API Token (3 minutes)

### 2.1 Create API Token

1. Still in R2, click **Manage R2 API Tokens**
2. Click **Create API Token**
3. Configure the token:
   - **Token name:** `rohimaya-backend`
   - **Permissions:** ✅ **Object Read & Write**
   - **TTL:** Forever (or your preference)
   - **Apply to specific buckets:** ✅ Select both `manuscripts` and `audiobooks`
4. Click **Create API Token**

### 2.2 Save Credentials

**IMPORTANT:** Copy and save these immediately (shown only once!):

```
Access Key ID: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Secret Access Key: yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
```

✅ **Save these somewhere safe** - you'll need them for Railway

---

## Step 3: Get Your Account ID (1 minute)

### Option A: From R2 Dashboard

Look at your R2 page - the Account ID is shown:
- In the page header
- Or in the URL: `dash.cloudflare.com/[ACCOUNT_ID]/r2`

### Option B: From R2 Endpoint

When you created the API token, you saw an endpoint like:
```
https://abc123def456.r2.cloudflarestorage.com
```

The Account ID is: `abc123def456`

✅ **Copy your Account ID**

---

## Step 4: Update Your Local `.env` File (2 minutes)

Open `env/.env` in your project and add these lines:

```bash
# Cloudflare R2 Storage
R2_ACCOUNT_ID=your_account_id_here
R2_ACCESS_KEY_ID=your_access_key_from_step2
R2_SECRET_ACCESS_KEY=your_secret_key_from_step2
R2_BUCKET_MANUSCRIPTS=manuscripts
R2_BUCKET_AUDIOBOOKS=audiobooks
R2_ENDPOINT=https://your_account_id.r2.cloudflarestorage.com
```

**Replace:**
- `your_account_id_here` → Your actual Account ID
- `your_access_key_from_step2` → Access Key ID from Step 2
- `your_secret_key_from_step2` → Secret Access Key from Step 2

✅ **Save the file**

---

## Step 5: Update Railway Environment Variables (5 minutes)

### 5.1 Go to Railway

1. Visit https://railway.app
2. Open your `rohimaya-audiobook-generator` project
3. Click on your backend service
4. Click **Variables** tab

### 5.2 Add R2 Variables

Click **+ New Variable** for each:

| Variable Name | Value |
|--------------|-------|
| `R2_ACCOUNT_ID` | Your Account ID |
| `R2_ACCESS_KEY_ID` | Your Access Key ID |
| `R2_SECRET_ACCESS_KEY` | Your Secret Access Key |
| `R2_BUCKET_MANUSCRIPTS` | `manuscripts` |
| `R2_BUCKET_AUDIOBOOKS` | `audiobooks` |
| `R2_ENDPOINT` | `https://[YOUR_ACCOUNT_ID].r2.cloudflarestorage.com` |

**⚠️ Important:** Replace `[YOUR_ACCOUNT_ID]` with your actual Account ID

### 5.3 Remove Old Variables (Optional)

You can remove these if they exist:
- `SUPABASE_BUCKET_MANUSCRIPTS`
- `SUPABASE_BUCKET_AUDIOBOOKS`

✅ **Railway will auto-redeploy** when you save variables

---

## Step 6: Verify Deployment (2 minutes)

### 6.1 Check Railway Logs

1. Go to **Deployments** tab in Railway
2. Click on the latest deployment
3. Look for this log line:

```
✅ R2 Storage initialized: https://xxxxx.r2.cloudflarestorage.com
```

### 6.2 Test Health Endpoint

```bash
curl https://your-app.railway.app/health
```

Should return:
```json
{
  "status": "ok",
  "service": "rohimaya-engine",
  "version": "0.2.0"
}
```

✅ **If you see this, R2 is working!**

---

## Step 7: Test Upload/Download (Optional)

### Create a Test Job

```bash
# Replace with your actual Railway URL and JWT token
export API_URL="https://your-app.railway.app"
export TOKEN="your-jwt-token"

curl -X POST $API_URL/jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "Test Book",
    "source_type": "paste",
    "manuscript_text": "Once upon a time, there was a brave knight who went on an adventure.",
    "mode": "single_voice",
    "tts_provider": "openai",
    "narrator_voice_id": "alloy",
    "audio_format": "mp3",
    "audio_bitrate": "128k"
  }'
```

### Verify in R2 Dashboard

1. Go back to Cloudflare R2
2. Click on `manuscripts` bucket
3. You should see a folder: `{user_id}/{job_id}/Test_Book.txt`
4. After job completes, check `audiobooks` bucket
5. You should see: `{user_id}/{job_id}/Test_Book_COMPLETE.mp3`

✅ **Files in R2 = Success!**

---

## Troubleshooting

### Error: "Missing R2 configuration"

**Cause:** Environment variables not set

**Fix:**
1. Verify all 6 R2 variables are in Railway
2. Check for typos in variable names
3. Redeploy if needed

### Error: "NoSuchBucket"

**Cause:** Bucket names don't match

**Fix:**
1. Verify buckets are named exactly `manuscripts` and `audiobooks`
2. Check `R2_BUCKET_*` variables match bucket names

### Error: "AccessDenied"

**Cause:** Invalid or missing API token permissions

**Fix:**
1. Verify API token has "Object Read & Write" permissions
2. Check token is applied to both buckets
3. Regenerate token if needed

### Error: Presigned URL returns 403

**Cause:** URL expired (they last 1 hour)

**Fix:**
- Download URLs are regenerated on each request
- If URL is saved/cached, request a fresh one from `/jobs/{id}/download`

---

## Summary Checklist

Use this to verify everything is set up:

- [ ] Created `manuscripts` bucket in Cloudflare R2
- [ ] Created `audiobooks` bucket in Cloudflare R2
- [ ] Generated R2 API token with "Object Read & Write"
- [ ] Saved Access Key ID and Secret Access Key
- [ ] Found Account ID
- [ ] Added 6 R2 variables to `env/.env` locally
- [ ] Added 6 R2 variables to Railway
- [ ] Railway redeployed successfully
- [ ] Saw "✅ R2 Storage initialized" in logs
- [ ] Health endpoint returns 200
- [ ] (Optional) Tested job creation and verified files in R2

---

## Cost Tracking

Monitor your R2 usage in Cloudflare Dashboard:

1. Go to R2 → Overview
2. View:
   - Storage used (GB)
   - Operations (reads/writes)
   - Estimated cost

**Expected costs:**
- Storage: ~$0.015/GB/month
- Operations: ~$0.00/month (negligible)
- Bandwidth: **$0** (free!)

**Example:** 100 GB of audiobooks = ~$1.50/month

---

## What Changed in the Code

### Before (Supabase Storage)

```python
# Old code (removed)
supabase.storage.from_('audiobooks').upload(...)
```

### After (Cloudflare R2)

```python
# New code
from .storage_r2 import r2
r2.upload_audiobook(user_id, job_id, filename, content)
```

**Frontend doesn't change** - it still just receives a download URL.

---

## Next Steps

1. ✅ Complete setup above
2. ✅ Test with a short manuscript
3. ✅ Verify audiobook downloads work
4. 🚀 Deploy frontend to Vercel (next task)

---

## Support

**Documentation:**
- Full details: See `STORAGE_ARCHITECTURE.md`
- Deployment: See `DEPLOYMENT_GUIDE.md`
- Migration summary: See `R2_MIGRATION_COMPLETE.md`

**Cloudflare R2 Docs:**
- https://developers.cloudflare.com/r2/

**Need help?**
- Check Railway logs for error messages
- Verify all environment variables are set correctly
- Ensure API token has correct permissions

---

**Ready!** 🎉

Total setup time: ~15-20 minutes

Storage cost: ~$1.50/100GB/month (vs $25 for Supabase Pro)

You now have unlimited file storage with zero bandwidth costs!

