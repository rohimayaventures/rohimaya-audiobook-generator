# Backend Flow Design - Rohimaya Audiobook Generator

## Overview

This document describes the complete request flow for audiobook generation, from the user's browser through the Next.js frontend, FastAPI backend, Supabase database/storage, and back to the user.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER'S BROWSER                               │
│                     (http://authorflow.com)                          │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            │ 1. User uploads manuscript
                            │    + selects voice settings
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      NEXT.JS FRONTEND (Vercel)                       │
│                         apps/web/                                    │
│                                                                      │
│  Routes:                                                             │
│  • / - Landing page                                                  │
│  • /app - Dashboard                                                  │
│  • /app/jobs - Job management                                        │
│                                                                      │
│  Responsibilities:                                                   │
│  • User authentication (Supabase Auth)                               │
│  • File upload to Supabase Storage                                   │
│  • HTTP requests to FastAPI backend                                  │
│  • Real-time UI updates (polling or WebSocket)                       │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            │ 2. POST /jobs
                            │    (job creation request)
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND (Railway)                          │
│                      apps/engine/api/                                │
│                                                                      │
│  Endpoints:                                                          │
│  • GET  /health          - Health check                              │
│  • POST /jobs/test       - Test job creation (stub)                  │
│  • POST /jobs            - Create audiobook job (TODO)               │
│  • GET  /jobs/{id}       - Get job status (TODO)                     │
│  • GET  /jobs/{id}/download - Download audiobook (TODO)              │
│                                                                      │
│  Responsibilities:                                                   │
│  • Validate request payload                                          │
│  • Create job row in Supabase                                        │
│  • Orchestrate pipelines (single-voice or dual-voice)                │
│  • Update job progress in database                                   │
│  • Write final audio to Supabase Storage                             │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            │ 3. INSERT INTO jobs
                            │    (create job record)
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   SUPABASE (Database + Storage)                      │
│                                                                      │
│  PostgreSQL Database:                                                │
│  • jobs            - Job metadata & status                           │
│  • job_files       - Per-chapter/chunk audio files                   │
│                                                                      │
│  Storage Buckets:                                                    │
│  • manuscripts     - Uploaded book files (private)                   │
│  • audiobooks      - Generated audio files (private)                 │
│                                                                      │
│  Responsibilities:                                                   │
│  • Persist job state                                                 │
│  • Store uploaded manuscripts                                        │
│  • Store generated audio files                                       │
│  • Enforce Row Level Security (RLS) policies                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Flow: Create Audiobook Job

### Phase 1: User Initiates Job

**User Action:**
1. User navigates to `/app` in the Next.js frontend
2. Clicks "Create New Audiobook"
3. Uploads manuscript file (TXT, DOCX, or PDF) **OR** pastes text directly
4. Selects voice mode:
   - **Single Voice:** One narrator voice for entire book
   - **Dual Voice:** Narrator + character voice (Phoenix & Peacock)
5. Configures settings:
   - TTS Provider (OpenAI, ElevenLabs, Inworld)
   - Voice selection (from dropdown)
   - Audio format (MP3, WAV, FLAC, M4B)
   - Bitrate (128k, 192k, 320k)
6. Clicks "Generate Audiobook"

### Phase 2: Frontend → Supabase (File Upload)

**Frontend (Next.js):**
```typescript
// apps/web/app/app/jobs/create/page.tsx

async function uploadManuscript(file: File, userId: string) {
  // Upload to Supabase Storage using user's folder
  const { data, error } = await supabase.storage
    .from('manuscripts')
    .upload(`${userId}/${file.name}`, file)

  if (error) throw error

  return data.path  // e.g., "user123/my-book.txt"
}
```

**Flow:**
1. Frontend uploads manuscript to `manuscripts/{user_id}/{filename}` in Supabase Storage
2. Receives back storage path: `manuscripts/user123/my-book.txt`
3. This path will be saved in the `jobs` table

### Phase 3: Frontend → Backend API (Job Creation)

**Frontend (Next.js):**
```typescript
// Send job creation request to backend
const response = await fetch(`${process.env.NEXT_PUBLIC_ENGINE_API_URL}/jobs`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${session.access_token}`,  // Supabase JWT
  },
  body: JSON.stringify({
    title: "My Book Title",
    author: "Author Name",
    source_type: "upload",  // or "paste", "google_drive", "url"
    source_path: "manuscripts/user123/my-book.txt",  // from Phase 2
    mode: "single_voice",  // or "dual_voice"
    tts_provider: "openai",  // or "elevenlabs", "inworld"
    narrator_voice_id: "alloy",
    character_voice_id: null,  // only for dual-voice
    character_name: null,      // only for dual-voice
    audio_format: "mp3",
    audio_bitrate: "128k",
  }),
})

const job = await response.json()
// { job_id: "uuid-here", status: "pending", ... }
```

### Phase 4: Backend → Supabase (Create Job Record)

**Backend (FastAPI):**
```python
# apps/engine/api/main.py

@app.post("/jobs", status_code=201)
async def create_job(request: JobCreateRequest):
    """
    Create new audiobook generation job.

    Steps:
    1. Validate request (check user_id, source_path, voice IDs)
    2. Create job row in Supabase
    3. Enqueue job for async processing
    4. Return job ID and initial status
    """

    # 1. Validate request
    user_id = extract_user_id_from_jwt(request.headers['Authorization'])

    # 2. Create job in Supabase
    job_data = {
        'user_id': user_id,
        'status': 'pending',
        'mode': request.mode,
        'title': request.title,
        'author': request.author,
        'source_type': request.source_type,
        'source_path': request.source_path,
        'tts_provider': request.tts_provider,
        'narrator_voice_id': request.narrator_voice_id,
        'character_voice_id': request.character_voice_id,
        'character_name': request.character_name,
        'audio_format': request.audio_format,
        'audio_bitrate': request.audio_bitrate,
    }

    # Insert into Supabase
    result = supabase.table('jobs').insert(job_data).execute()
    job_id = result.data[0]['id']

    # 3. Enqueue job for background processing
    await queue.enqueue_job(job_id)  # Celery, RQ, or asyncio task

    # 4. Return job info
    return {
        'job_id': job_id,
        'status': 'pending',
        'created_at': result.data[0]['created_at'],
    }
```

**Database State After Creation:**
```sql
-- jobs table (1 new row)
id         | user_id  | status  | mode         | title       | source_path
-----------|----------|---------|--------------|-------------|---------------------------
job-uuid-1 | user-123 | pending | single_voice | My Book     | manuscripts/user123/my-book.txt

-- job_files table (empty for now)
-- Will be populated as chunks are generated
```

### Phase 5: Backend Processing (Async)

**Background Worker (FastAPI or Celery):**
```python
# apps/engine/api/workers.py

async def process_job(job_id: str):
    """
    Background task to process audiobook generation.

    Steps:
    1. Fetch job from database
    2. Download manuscript from Supabase Storage
    3. Run appropriate pipeline (single-voice or dual-voice)
    4. Upload chunks and final audio to Supabase Storage
    5. Update job status to 'completed' or 'failed'
    """

    # 1. Fetch job
    job = supabase.table('jobs').select('*').eq('id', job_id).single().execute()

    # 2. Update status to 'processing'
    supabase.table('jobs').update({
        'status': 'processing',
        'started_at': datetime.utcnow().isoformat(),
    }).eq('id', job_id).execute()

    try:
        # 3. Download manuscript
        manuscript_data = supabase.storage.from_('manuscripts').download(job.data['source_path'])
        manuscript_text = manuscript_data.decode('utf-8')

        # 4. Run pipeline
        if job.data['mode'] == 'single_voice':
            from apps.engine.pipelines import SingleVoicePipeline

            pipeline = SingleVoicePipeline(
                api_key=os.getenv('OPENAI_API_KEY'),
                voice_name=job.data['narrator_voice_id'],
            )

            # Generate full audiobook
            output_dir = Path(f'/tmp/{job_id}')
            audio_files = pipeline.generate_full_book(manuscript_text, output_dir)

        elif job.data['mode'] == 'dual_voice':
            from apps.engine.pipelines import DualVoicePipeline

            pipeline = DualVoicePipeline(
                api_key=os.getenv('ELEVENLABS_API_KEY'),
                narrator_voice_id=job.data['narrator_voice_id'],
                character_voice_id=job.data['character_voice_id'],
                character_name=job.data['character_name'],
            )

            # Generate dual-voice audiobook
            output_dir = Path(f'/tmp/{job_id}')
            audio_files = pipeline.generate_full_book(manuscript_text, output_dir)

        # 5. Upload final audiobook to Supabase Storage
        final_audio_path = audio_files[-1]  # Last file is the complete audiobook
        storage_path = f"{job.data['user_id']}/{job_id}/final/{job.data['title']}_COMPLETE.mp3"

        with open(final_audio_path, 'rb') as f:
            supabase.storage.from_('audiobooks').upload(storage_path, f)

        # 6. Update job to completed
        file_size = final_audio_path.stat().st_size

        supabase.table('jobs').update({
            'status': 'completed',
            'audio_path': storage_path,
            'file_size_bytes': file_size,
            'completed_at': datetime.utcnow().isoformat(),
        }).eq('id', job_id).execute()

    except Exception as e:
        # Update job to failed
        supabase.table('jobs').update({
            'status': 'failed',
            'error_message': str(e),
            'completed_at': datetime.utcnow().isoformat(),
        }).eq('id', job_id).execute()
```

### Phase 6: Frontend Polls for Status

**Frontend (Next.js):**
```typescript
// Poll backend API every 5 seconds for job status
async function pollJobStatus(jobId: string) {
  const interval = setInterval(async () => {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_ENGINE_API_URL}/jobs/${jobId}`
    )
    const job = await response.json()

    // Update UI with progress
    setProgress(job.progress_percent)
    setStatus(job.status)

    // If completed or failed, stop polling
    if (job.status === 'completed' || job.status === 'failed') {
      clearInterval(interval)

      if (job.status === 'completed') {
        // Show download button
        setDownloadUrl(job.audio_path)
      } else {
        // Show error message
        setError(job.error_message)
      }
    }
  }, 5000)  // Poll every 5 seconds
}
```

### Phase 7: User Downloads Audiobook

**User Action:**
1. Job completes (status = 'completed')
2. Frontend shows "Download Audiobook" button
3. User clicks download

**Frontend (Next.js):**
```typescript
// Download audiobook from Supabase Storage
async function downloadAudiobook(audioPath: string) {
  // Get signed URL from Supabase (expires in 1 hour)
  const { data, error } = await supabase.storage
    .from('audiobooks')
    .createSignedUrl(audioPath, 3600)

  if (error) throw error

  // Redirect to signed URL (browser downloads file)
  window.location.href = data.signedUrl
}
```

**Alternative: Stream through backend**
```typescript
// Fetch through backend API (adds auth layer)
const response = await fetch(
  `${process.env.NEXT_PUBLIC_ENGINE_API_URL}/jobs/${jobId}/download`,
  {
    headers: {
      'Authorization': `Bearer ${session.access_token}`,
    },
  }
)

const blob = await response.blob()
const url = window.URL.createObjectURL(blob)
const a = document.createElement('a')
a.href = url
a.download = `${title}_COMPLETE.mp3`
a.click()
```

---

## Data Flow Summary

```
┌──────────────┐
│   Browser    │
└──────┬───────┘
       │
       │ 1. Upload manuscript
       ↓
┌──────────────────────┐
│ Supabase Storage     │
│ manuscripts/user123/ │
└──────┬───────────────┘
       │
       │ 2. Create job (POST /jobs)
       ↓
┌──────────────┐      3. Insert job      ┌──────────────────┐
│ FastAPI      │ ──────────────────────→ │ Supabase DB      │
│ Backend      │                          │ jobs table       │
└──────┬───────┘                          └──────────────────┘
       │
       │ 4. Enqueue background task
       ↓
┌───────────────────────┐
│ Background Worker     │
│ (generate audiobook)  │
└──────┬────────────────┘
       │
       │ 5. Download manuscript
       ↓
┌──────────────────────┐
│ Supabase Storage     │
│ manuscripts/user123/ │
└──────┬───────────────┘
       │
       │ 6. Run pipeline (TTS generation)
       ↓
┌──────────────────────┐
│ OpenAI / ElevenLabs  │
│ TTS API              │
└──────┬───────────────┘
       │
       │ 7. Upload final audio
       ↓
┌──────────────────────┐
│ Supabase Storage     │
│ audiobooks/user123/  │
└──────┬───────────────┘
       │
       │ 8. Update job status
       ↓
┌──────────────────────┐
│ Supabase DB          │
│ jobs.status =        │
│ 'completed'          │
└──────┬───────────────┘
       │
       │ 9. Poll for status (GET /jobs/{id})
       ↓
┌──────────────┐
│ FastAPI      │
│ Backend      │
└──────┬───────┘
       │
       │ 10. Return job with audio_path
       ↓
┌──────────────┐
│   Browser    │
│ Show download│
│    button    │
└──────────────┘
```

---

## Security Considerations

### Authentication Flow

1. **User logs in via Supabase Auth**
   - Next.js frontend uses `@supabase/auth-helpers-nextjs`
   - User receives JWT token from Supabase

2. **Frontend → Backend requests include JWT**
   ```typescript
   headers: {
     'Authorization': `Bearer ${session.access_token}`
   }
   ```

3. **Backend verifies JWT with Supabase**
   ```python
   # Verify JWT is valid and extract user_id
   user = supabase.auth.get_user(jwt_token)
   user_id = user.id
   ```

4. **Backend enforces user ownership**
   - Jobs: User can only create/read jobs for themselves
   - Storage: User can only upload to their own folder
   - Downloads: User can only download their own audiobooks

### Row Level Security (RLS)

**Supabase RLS Policies:**
```sql
-- jobs table: Users can only see their own jobs
CREATE POLICY "Users can view own jobs"
ON jobs FOR SELECT
USING (auth.uid() = user_id);

-- jobs table: Service role can see all jobs
CREATE POLICY "Service can view all jobs"
ON jobs FOR ALL
USING (auth.role() = 'service_role');

-- Storage: Users can only read their own files
CREATE POLICY "Users can read own audiobooks"
ON storage.objects FOR SELECT
USING (
  bucket_id = 'audiobooks' AND
  (storage.foldername(name))[1] = auth.uid()::text
);
```

---

## Error Handling

### Common Error Scenarios

| Error | HTTP Code | Handling |
|-------|-----------|----------|
| Invalid JWT token | 401 | Redirect to login |
| User not authorized | 403 | Show error message |
| File upload failed | 500 | Retry upload with exponential backoff |
| TTS API rate limit | 429 | Queue job, retry later |
| TTS API failure | 500 | Mark job as failed, allow retry |
| Supabase connection error | 503 | Show "Service unavailable" |

### Job Status States

```
pending → processing → completed
                    → failed → (manual retry)
```

**Status Definitions:**
- `pending`: Job created, waiting for processing
- `processing`: Currently generating audio
- `completed`: Audiobook ready for download
- `failed`: Generation failed (see error_message)
- `cancelled`: User cancelled job (future feature)

---

## Performance Optimizations

### 1. Parallel Chunk Processing

Generate audio chunks in parallel to reduce total time:

```python
import asyncio

async def generate_chunks_parallel(chunks: List[str]):
    tasks = [
        generate_chunk_audio(chunk, i)
        for i, chunk in enumerate(chunks)
    ]
    return await asyncio.gather(*tasks)
```

### 2. Progress Tracking

Update `jobs.progress_percent` after each chunk completes:

```python
# After each chunk
chunks_completed = job.chunks_completed + 1
progress = (chunks_completed / job.total_chunks) * 100

supabase.table('jobs').update({
    'chunks_completed': chunks_completed,
    'progress_percent': progress,
}).eq('id', job_id).execute()
```

### 3. Caching

Cache TTS voice previews and metadata:
- Store in Redis or Supabase cache table
- Reduce redundant API calls to OpenAI/ElevenLabs

### 4. CDN for Audio Delivery

Use Supabase CDN or Cloudflare for fast audio downloads:
- Enable CDN caching for `audiobooks` bucket
- Use signed URLs with long expiration for trusted users

---

## Future Enhancements

### 1. WebSocket for Real-Time Updates

Replace polling with WebSocket connection:

```typescript
// Frontend
const ws = new WebSocket(`wss://api.authorflow.com/jobs/${jobId}/progress`)

ws.onmessage = (event) => {
  const update = JSON.parse(event.data)
  setProgress(update.progress_percent)
  setStatus(update.status)
}
```

### 2. Resume Failed Jobs

Allow users to resume jobs that failed mid-generation:
- Track which chunks completed successfully
- Only regenerate failed chunks
- Assemble complete audiobook from partial results

### 3. Multi-Chapter Management

Enable per-chapter operations:
- Download individual chapters
- Regenerate specific chapters
- Preview chapters before full generation

### 4. Cost Estimation

Show estimated cost before starting job:
```typescript
const estimatedCost = calculateCost({
  wordCount: manuscript.split(' ').length,
  provider: 'openai',
  voice: 'alloy',
})
// "Estimated cost: $2.45"
```

---

**Last Updated:** 2025-11-22
**Status:** ✅ Architecture documented, ready for implementation
