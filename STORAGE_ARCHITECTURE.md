# 📦 Storage Architecture - Cloudflare R2

## Overview

The Rohimaya Audiobook Generator uses **Cloudflare R2** for all file storage (manuscripts and audiobooks). R2 is an S3-compatible object storage service with **zero egress fees**, making it perfect for serving large audio files.

**Key Decision:** We chose R2 over Supabase Storage due to:
- ✅ **No bandwidth costs** (Supabase charges for egress)
- ✅ **Larger file size limits** (Supabase free tier: 1GB total, R2: pay-per-use)
- ✅ **Better pricing** (~$1.50/100GB vs $25/month for Supabase Pro)
- ✅ **S3-compatible API** (easy migration path, industry standard)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         STORAGE LAYER                                │
└─────────────────────────────────────────────────────────────────────┘

┌────────────────────────┐         ┌────────────────────────────┐
│  SUPABASE (Database)   │         │  CLOUDFLARE R2 (Storage)   │
│                        │         │                            │
│  ✅ jobs table         │         │  📁 manuscripts/           │
│  ✅ job_files table    │         │     {user_id}/             │
│  ✅ User auth (JWT)    │         │       {job_id}/            │
│                        │         │         book.txt           │
│  ❌ Storage (moved →)  │────────▶│                            │
│                        │         │  🎵 audiobooks/            │
│                        │         │     {user_id}/             │
│                        │         │       {job_id}/            │
│                        │         │         final.mp3          │
└────────────────────────┘         └────────────────────────────┘
```

---

## File Organization in R2

### Bucket Structure

We use **two R2 buckets**:

#### 1. `manuscripts` Bucket
Stores uploaded manuscript files (TXT, DOCX, PDF).

**Path Pattern:**
```
manuscripts/
├── {user_id}/
│   ├── {job_id}/
│   │   └── {original_filename}.txt
│   ├── {job_id}/
│   │   └── my-novel.docx
```

**Example:**
```
manuscripts/a1b2c3d4-1234-5678-abcd-1234567890ab/job-uuid-123/The_Great_Adventure.txt
```

#### 2. `audiobooks` Bucket
Stores generated audiobook files (MP3, WAV, FLAC, M4B).

**Path Pattern:**
```
audiobooks/
├── {user_id}/
│   ├── {job_id}/
│   │   └── {title}_COMPLETE.mp3
```

**Example:**
```
audiobooks/a1b2c3d4-1234-5678-abcd-1234567890ab/job-uuid-123/The_Great_Adventure_COMPLETE.mp3
```

---

## Code Implementation

### 1. R2 Storage Client (`apps/engine/api/storage_r2.py`)

The main storage client using boto3 (S3-compatible):

```python
from apps.engine.api.storage_r2 import r2

# Upload manuscript
object_key = r2.upload_manuscript(
    user_id="user-uuid",
    filename="book.txt",
    file_content=b"Once upon a time...",
    job_id="job-uuid"  # Optional
)
# Returns: "manuscripts/user-uuid/job-uuid/book.txt"

# Download manuscript
content = r2.download_manuscript(object_key)

# Upload audiobook
audio_key = r2.upload_audiobook(
    user_id="user-uuid",
    job_id="job-uuid",
    filename="Book_COMPLETE.mp3",
    file_content=audio_bytes
)
# Returns: "audiobooks/user-uuid/job-uuid/Book_COMPLETE.mp3"

# Generate presigned URL (expires in 1 hour by default)
download_url = r2.generate_presigned_url(audio_key, expires_in=3600)

# Delete file
r2.delete_audiobook(audio_key)
```

### 2. Database Layer (`apps/engine/api/database.py`)

The database layer delegates storage operations to R2:

```python
from apps.engine.api.database import db

# All storage operations now use R2 under the hood
source_path = db.upload_manuscript(user_id, filename, content, job_id)
manuscript = db.download_manuscript(source_path)
audio_path = db.upload_audiobook(user_id, job_id, filename, audio_data)
url = db.get_download_url(audio_path)
```

**Database stores only object keys** (not full URLs):
- `jobs.source_path` → R2 object key for manuscript
- `jobs.audio_path` → R2 object key for audiobook

---

## Presigned URLs

### What are Presigned URLs?

Presigned URLs allow temporary, secure access to private R2 objects without exposing credentials.

**How it works:**
1. Backend generates URL with signature using AWS credentials
2. URL is valid for specified duration (default: 1 hour)
3. After expiration, URL no longer works
4. Users can download directly from R2 (no backend proxy needed)

### Generation

```python
# Short-lived (1 hour) - for immediate download
url = r2.generate_presigned_url(object_key, expires_in=3600)

# Long-lived (1 week) - for email links
url = r2.generate_presigned_url(object_key, expires_in=604800)
```

### Example URL

```
https://a1b2c3d4.r2.cloudflarestorage.com/audiobooks/user123/job456/Book.mp3
?X-Amz-Algorithm=AWS4-HMAC-SHA256
&X-Amz-Credential=...
&X-Amz-Date=20250126T120000Z
&X-Amz-Expires=3600
&X-Amz-SignedHeaders=host
&X-Amz-Signature=abc123...
```

---

## Public URLs (Optional)

### R2 Public Buckets

If you want **public URLs** instead of presigned URLs:

1. **Enable R2 Public Access:**
   - Go to Cloudflare Dashboard → R2 → Your Bucket
   - Settings → Allow Public Access
   - Copy the public URL: `https://pub-xxxx.r2.dev`

2. **Set Environment Variable:**
   ```bash
   R2_PUBLIC_URL=https://pub-xxxx.r2.dev
   ```

3. **Use Public URLs:**
   ```python
   # Returns public URL if R2_PUBLIC_URL is set
   url = r2.get_public_url(object_key)
   # Example: https://pub-xxxx.r2.dev/audiobooks/user123/Book.mp3
   ```

**⚠️ Security Note:** Public URLs mean anyone with the link can access files. Use presigned URLs for better security.

---

## Custom Domains (Advanced)

### Option 1: Cloudflare Custom Domain

1. Add custom domain in R2 bucket settings
2. Point DNS CNAME to R2 bucket
3. Update `R2_PUBLIC_URL`:
   ```bash
   R2_PUBLIC_URL=https://audiobooks.yourdomain.com
   ```

### Option 2: Cloudflare Worker Proxy

Create a Worker to proxy R2 requests with custom logic:

```javascript
// worker.js
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const objectKey = url.pathname.slice(1); // Remove leading /

    const object = await env.R2_BUCKET.get(objectKey);
    if (!object) return new Response('Not Found', { status: 404 });

    return new Response(object.body, {
      headers: {
        'Content-Type': object.httpMetadata.contentType,
        'Cache-Control': 'public, max-age=3600'
      }
    });
  }
};
```

---

## Cost Analysis

### Cloudflare R2 Pricing

| Operation | Price | Notes |
|-----------|-------|-------|
| **Storage** | $0.015/GB/month | ~$1.50 for 100 GB |
| **Class A (writes)** | $4.50/million | Uploads, deletes |
| **Class B (reads)** | $0.36/million | Downloads, list |
| **Egress** | **$0** | **FREE!** (biggest advantage) |

### Example Cost Calculation

**Scenario:** 100 audiobooks stored, 1,000 downloads/month

- Storage: 100 GB × $0.015 = **$1.50**
- Uploads: 100 × $0.0000045 = **$0.00045**
- Downloads: 1,000 × $0.00000036 = **$0.00036**
- Egress (100 GB): **$0**

**Total: ~$1.50/month**

**Comparison to Supabase Storage:**
- Supabase Pro (100 GB): **$25/month**
- **Savings: $23.50/month** 💰

---

## Migration from Supabase Storage

### What Changed

**Before (Supabase Storage):**
```python
# Old code (removed)
supabase.storage.from_('audiobooks').upload(path, file)
supabase.storage.from_('audiobooks').download(path)
supabase.storage.from_('audiobooks').create_signed_url(path)
```

**After (Cloudflare R2):**
```python
# New code
r2.upload_audiobook(user_id, job_id, filename, file_content)
r2.download_manuscript(object_key)
r2.generate_presigned_url(object_key)
```

### Database Schema

**No changes needed!** Object keys are still stored as strings:

```sql
-- jobs table (unchanged)
CREATE TABLE jobs (
  source_path TEXT,  -- R2 object key: "manuscripts/user123/book.txt"
  audio_path TEXT,   -- R2 object key: "audiobooks/user123/final.mp3"
  ...
);
```

### Existing Data Migration

If you have existing files in Supabase Storage:

1. **Download from Supabase:**
   ```python
   data = supabase.storage.from_('audiobooks').download(path)
   ```

2. **Upload to R2:**
   ```python
   r2.upload_audiobook(user_id, job_id, filename, data)
   ```

3. **Update database:**
   ```python
   db.update_job(job_id, {"audio_path": new_r2_key})
   ```

---

## Security Considerations

### 1. Private Buckets (Default)

Both buckets are **private by default**:
- No anonymous access
- All reads require presigned URLs or valid AWS credentials

### 2. Presigned URL Expiration

**Best Practices:**
- **Download links:** 1 hour (3600s)
- **Email links:** 1 day (86400s)
- **Long-term access:** Use backend endpoint that generates fresh URLs

### 3. Object Key Structure

User IDs in paths ensure:
- Clear ownership
- Easy cleanup (delete all `user123/*`)
- Future RLS-like policies (via Worker)

### 4. CORS Configuration

Configure R2 bucket CORS for web playback:

```json
[
  {
    "AllowedOrigins": ["https://yourdomain.com"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 3600
  }
]
```

---

## Troubleshooting

### Issue: "NoSuchBucket" Error

**Cause:** R2 bucket doesn't exist

**Solution:**
1. Go to Cloudflare Dashboard → R2
2. Create buckets: `manuscripts`, `audiobooks`
3. Verify with:
   ```python
   r2.check_bucket_exists('manuscripts')  # Should return True
   ```

### Issue: "AccessDenied" Error

**Cause:** Invalid or missing R2 credentials

**Solution:**
1. Verify env vars are set:
   ```bash
   echo $R2_ACCESS_KEY_ID
   echo $R2_SECRET_ACCESS_KEY
   ```
2. Regenerate API token in Cloudflare if needed
3. Ensure token has "Object Read & Write" permissions

### Issue: Presigned URL returns 403

**Cause:** URL expired or signature mismatch

**Solution:**
- Generate new presigned URL (they expire after `expires_in` seconds)
- Verify system clock is correct (affects signatures)

### Issue: Upload succeeds but file not visible

**Cause:** Wrong bucket name or account ID

**Solution:**
1. Verify bucket name:
   ```python
   print(r2.audiobooks_bucket)  # Should match actual R2 bucket
   ```
2. Check R2 dashboard for uploaded objects

---

## Frontend Integration

### Download Audiobook

```typescript
// Frontend (Next.js)
async function downloadAudiobook(jobId: string) {
  // Get presigned URL from backend
  const response = await fetch(`/api/jobs/${jobId}/download`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  // Backend returns presigned R2 URL
  const { download_url } = await response.json();

  // Direct download from R2 (no proxy)
  window.location.href = download_url;
}
```

### Audio Player

```typescript
// Stream from R2
<audio controls src={job.audio_url}>
  Your browser does not support audio playback.
</audio>
```

**Note:** Frontend doesn't know or care that it's R2 - it just receives a URL.

---

## Future Enhancements

### 1. Multipart Uploads

For very large files (>100 MB):

```python
# TODO: Implement multipart upload
def upload_large_audiobook(user_id, job_id, filename, file_path):
    # Use boto3 multipart upload
    # Allows resumable uploads and better performance
    pass
```

### 2. Lifecycle Policies

Auto-delete old files:

```json
{
  "Rules": [{
    "Expiration": { "Days": 90 },
    "Filter": { "Prefix": "audiobooks/" },
    "Status": "Enabled"
  }]
}
```

### 3. CDN Integration

Use Cloudflare CDN for faster global delivery:
- Enable R2 public access
- Configure custom domain
- Set cache headers

### 4. Backup Strategy

Replicate to S3 for disaster recovery:
- Use rclone or AWS DataSync
- Periodic snapshots to S3 Glacier

---

## Summary

| Aspect | Implementation |
|--------|----------------|
| **Storage Provider** | Cloudflare R2 (S3-compatible) |
| **Database Provider** | Supabase Postgres |
| **Auth Provider** | Supabase Auth (JWT) |
| **Client Library** | boto3 (Python) |
| **Bucket Structure** | `manuscripts/`, `audiobooks/` |
| **Access Method** | Presigned URLs (1 hour expiry) |
| **Cost** | ~$1.50/100GB/month |
| **Egress** | **FREE** (unlimited bandwidth) |

---

**Last Updated:** 2025-11-26
**Status:** ✅ Production Ready
**Migration:** ✅ Complete (Supabase Storage → R2)
