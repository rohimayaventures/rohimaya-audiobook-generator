# Supabase Migrations

## Overview

This directory contains SQL migration files for the Rohimaya Audiobook Generator database schema and storage configuration.

## Migration Files

### ✅ 0001_create_jobs_tables.sql
Creates the core database tables for job tracking:

**jobs table:**
- Tracks audiobook generation jobs from creation to completion
- Fields: id, user_id, status, mode, title, source info, voice config, output paths, progress, timestamps
- Indexes on user_id, status, created_at for query performance
- Auto-updating triggers for updated_at and progress_percent

**job_files table:**
- Tracks individual audio files (chunks, chapters, final output)
- Enables regeneration of specific chapters/parts
- Links to jobs table via foreign key (cascade delete)

### ✅ 0002_create_storage_buckets.sql
Creates Supabase Storage buckets and RLS policies:

**Buckets:**
- `manuscripts` - Private bucket for uploaded book files (TXT, DOCX, PDF)
- `audiobooks` - Private bucket for generated audio files (MP3, WAV, FLAC, M4B)

**Row Level Security (RLS) Policies:**
- Users can only read/write/delete files in their own folders
- Backend service (using service role key) can write to any user's audiobook folder

## Running Migrations

### Prerequisites
1. Install Supabase CLI:
   ```bash
   npm install -g supabase
   ```

2. Link to your Supabase project:
   ```bash
   supabase link --project-ref your-project-ref
   ```

### Apply Migrations

**Option 1: Using Supabase CLI (Recommended)**
```bash
# From repo root
cd supabase

# Apply all pending migrations
supabase db push

# Verify migrations were applied
supabase migration list
```

**Option 2: Manual SQL Execution**
1. Copy the contents of each migration file (in order)
2. Run in Supabase Dashboard SQL Editor:
   - Go to https://app.supabase.com/project/YOUR_PROJECT/sql
   - Paste SQL and click "Run"

### Verify Migrations

Check that tables and buckets were created:

```sql
-- Check tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('jobs', 'job_files');

-- Check storage buckets
SELECT * FROM storage.buckets
WHERE name IN ('manuscripts', 'audiobooks');
```

## Schema Reference

### jobs Table
```sql
id                  UUID PRIMARY KEY
user_id             UUID NOT NULL
status              TEXT (pending|processing|completed|failed|cancelled)
mode                TEXT (single_voice|dual_voice)
title               TEXT NOT NULL
author              TEXT
source_type         TEXT (upload|google_drive|paste|url)
source_path         TEXT
tts_provider        TEXT (openai|elevenlabs|inworld)
narrator_voice_id   TEXT
character_voice_id  TEXT (dual-voice only)
character_name      TEXT (dual-voice only)
audio_format        TEXT (mp3|wav|flac|m4b)
audio_bitrate       TEXT
audio_path          TEXT (nullable until completed)
duration_seconds    INTEGER
file_size_bytes     BIGINT
total_chapters      INTEGER
total_chunks        INTEGER
chunks_completed    INTEGER
progress_percent    NUMERIC(5,2)
error_message       TEXT
retry_count         INTEGER
estimated_cost_usd  NUMERIC(10,4)
actual_cost_usd     NUMERIC(10,4)
created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
started_at          TIMESTAMPTZ
completed_at        TIMESTAMPTZ
```

### job_files Table
```sql
id                 UUID PRIMARY KEY
job_id             UUID REFERENCES jobs(id) ON DELETE CASCADE
file_type          TEXT (chunk|chapter|final)
chapter_number     INTEGER
part_number        INTEGER
audio_path         TEXT NOT NULL
duration_seconds   NUMERIC(10,2)
file_size_bytes    BIGINT
text_content       TEXT (enables regeneration)
word_count         INTEGER
voice_id           TEXT
speaker_type       TEXT (narrator|character|single)
status             TEXT (pending|processing|completed|failed)
error_message      TEXT
created_at         TIMESTAMPTZ
completed_at       TIMESTAMPTZ
```

## Storage Structure

### Manuscripts Bucket
```
manuscripts/
└── {user_id}/
    ├── great_adventure.txt
    ├── mystery_novel.docx
    └── fantasy_epic.pdf
```

### Audiobooks Bucket
```
audiobooks/
└── {user_id}/
    └── {job_id}/
        ├── chunks/
        │   ├── ch1_part1.mp3
        │   ├── ch1_part2.mp3
        │   └── ...
        ├── chapters/
        │   ├── CHAPTER_01.mp3
        │   ├── CHAPTER_02.mp3
        │   └── ...
        └── final/
            └── Great_Adventure_COMPLETE.mp3
```

## Environment Variables

After running migrations, configure these in your env files:

**Backend (env/.env):**
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
SUPABASE_BUCKET_MANUSCRIPTS=manuscripts
SUPABASE_BUCKET_AUDIOBOOKS=audiobooks
```

**Frontend (apps/web/.env.local):**
```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
```

## Troubleshooting

### "Relation already exists" errors
Migrations have already been applied. Use:
```sql
DROP TABLE IF EXISTS job_files CASCADE;
DROP TABLE IF EXISTS jobs CASCADE;
```
Then re-run migrations.

### Storage bucket policy errors
Ensure RLS is enabled on storage.objects:
```sql
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;
```

### Permission denied errors
Verify you're using the correct Supabase service role key for backend operations.

---
**Last Updated:** 2025-11-22
**Migration Version:** 0002
