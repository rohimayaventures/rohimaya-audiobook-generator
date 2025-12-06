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

### ✅ 0003_google_drive_tokens.sql
Google Drive OAuth token storage:
- Stores encrypted OAuth tokens per user
- RLS policies for user-only access
- Auto-updating timestamps

### ✅ 0004_billing_interval.sql
Adds billing interval support:
- Monthly and yearly billing options

### ✅ 0005_cover_art_columns.sql (DEPRECATED)
Adds cover art generation fields (no longer used):
- `generate_cover`, `cover_vibe`, `cover_description` - DEPRECATED
- Also adds Findaway mode columns: `package_type`, `section_count`, `manifest_json`, `current_step`

### ✅ 0006_multilingual_tts_columns.sql
Adds multilingual TTS support:
- `input_language_code` - Source language (e.g., "en-US", "hi-IN")
- `output_language_code` - Target language for translation
- `voice_preset_id` - Gemini voice preset ID
- `emotion_style_prompt` - Emotion/style hints for TTS

### ✅ 0007_chapters_table.sql
Adds chapter workflow tables for Findaway-compliant audiobooks:

**chapters table:**
- Individual chapters extracted from manuscripts
- Review/approval workflow before TTS
- Segment types: opening_credits, front_matter, body_chapter, back_matter, closing_credits, retail_sample
- Status: pending_review → approved → processing → completed

**tracks table:**
- Final audio tracks in playback order
- Links to chapters
- Export filename for Findaway

**retail_samples table:**
- AI-suggested and user-confirmed retail samples
- Engagement, emotional intensity, spoiler risk scores

**New job statuses:**
- `parsing` - Manuscript being parsed into chapters
- `chapters_pending` - Chapters extracted, awaiting user review
- `chapters_approved` - User approved chapter order, ready for TTS

### ✅ 0008_findaway_segment_order.sql
Adds strict Findaway segment ordering:

**segment_order column:**
- 0 = Opening Credits (exactly one)
- 1-9 = Front Matter (up to 9 items)
- 10-79 = Body Chapters (up to 70 chapters)
- 80-89 = Back Matter (up to 10 items)
- 98 = Closing Credits (exactly one)
- 99 = Retail Sample (exactly one)

**Helper functions:**
- `get_next_segment_order(job_id, segment_type)` - Get next available order
- `validate_segment_order()` - Trigger to validate segment_order matches segment_type
- `generate_default_credits_text(job_id, credit_type)` - Generate credits text

**View:**
- `job_segments_ordered` - All segments in correct Findaway order with export filenames

### ✅ 0009_bonus_teaser_segments.sql
Adds bonus chapter and teaser chapter segment types:

**New segment types:**
- `bonus_chapter` (segment_order 90-94) - Up to 5 bonus chapters (deleted scenes, extended epilogues, etc.)
- `teaser_chapter` (segment_order 95-97) - Up to 3 teaser chapters (sneak peeks, excerpts, etc.)

**Updated functions:**
- `get_next_segment_order()` - Now supports bonus_chapter and teaser_chapter types
- `validate_segment_order()` - Validates ranges for new segment types

**Updated view:**
- `job_segments_ordered` - Generates filenames like `90_bonus_01.mp3`, `95_teaser_01.mp3`

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

### Apply New Migrations (0007 and 0008)

If you've already run migrations 0001-0006, you only need to run:

```bash
# Option 1: Supabase CLI
supabase db push

# Option 2: Manual (in order)
# 1. Run 0007_chapters_table.sql
# 2. Run 0008_findaway_segment_order.sql
```

### Verify Migrations

Check that new tables and columns were created:

```sql
-- Check chapters table exists
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'chapters';

-- Check tracks table exists
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'tracks';

-- Check segment_order column
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'chapters' AND column_name = 'segment_order';

-- Check new job statuses work
SELECT DISTINCT status FROM jobs;
```

## Schema Reference

### jobs Table (Updated)
```sql
id                    UUID PRIMARY KEY
user_id               UUID NOT NULL
status                TEXT (pending|parsing|chapters_pending|chapters_approved|processing|completed|failed|cancelled)
mode                  TEXT (single_voice|dual_voice|findaway|multi_character)
title                 TEXT NOT NULL
author                TEXT
-- TTS settings
tts_provider          TEXT (openai|google)
narrator_voice_id     TEXT
input_language_code   TEXT
output_language_code  TEXT
voice_preset_id       TEXT
emotion_style_prompt  TEXT
-- Chapter workflow
chapters_parsed_at    TIMESTAMPTZ
chapters_approved_at  TIMESTAMPTZ
-- Credits
narrator_name         TEXT
has_opening_credits   BOOLEAN DEFAULT TRUE
has_closing_credits   BOOLEAN DEFAULT TRUE
author_name           TEXT
opening_credits_text  TEXT
closing_credits_text  TEXT
retail_sample_confirmed BOOLEAN DEFAULT FALSE
-- ... other fields
```

### chapters Table
```sql
id                      UUID PRIMARY KEY
job_id                  UUID REFERENCES jobs(id)
chapter_index           INTEGER (final playback order)
source_order            INTEGER (original manuscript order)
title                   TEXT
text_content            TEXT
segment_type            TEXT (opening_credits|front_matter|body_chapter|back_matter|closing_credits|retail_sample)
segment_order           INTEGER (Findaway order: 0, 1-9, 10-79, 80-89, 98, 99)
display_title           TEXT
status                  TEXT (pending_review|approved|excluded|processing|completed|failed)
word_count              INTEGER
estimated_duration_seconds INTEGER
audio_path              TEXT
audio_duration_seconds  INTEGER
audio_file_size_bytes   BIGINT
created_at              TIMESTAMPTZ
updated_at              TIMESTAMPTZ
approved_at             TIMESTAMPTZ
completed_at            TIMESTAMPTZ
```

### tracks Table
```sql
id                 UUID PRIMARY KEY
job_id             UUID REFERENCES jobs(id)
chapter_id         UUID REFERENCES chapters(id)
track_index        INTEGER
title              TEXT
segment_type       TEXT
segment_order      INTEGER
audio_path         TEXT
duration_seconds   INTEGER
file_size_bytes    BIGINT
export_filename    TEXT (e.g., "10_chapter_01.mp3")
status             TEXT (pending|processing|completed|failed)
```

### retail_samples Table
```sql
id                        UUID PRIMARY KEY
job_id                    UUID REFERENCES jobs(id)
source_chapter_id         UUID REFERENCES chapters(id)
sample_text               TEXT
word_count                INTEGER
engagement_score          NUMERIC(3,2)
emotional_intensity_score NUMERIC(3,2)
spoiler_risk_score        NUMERIC(3,2)
overall_score             NUMERIC(3,2)
is_auto_suggested         BOOLEAN
is_user_confirmed         BOOLEAN
is_final                  BOOLEAN
user_edited_text          TEXT
candidate_rank            INTEGER
```

## Findaway Export Filename Convention

Files are named to sort alphabetically in correct playback order:

```
00_opening_credits.mp3
01_front_matter_01.mp3
02_front_matter_02.mp3
10_chapter_01.mp3
11_chapter_02.mp3
...
79_chapter_70.mp3
80_back_matter_01.mp3
...
98_closing_credits.mp3
99_retail_sample.mp3
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

### Segment order validation errors
The trigger `validate_segment_order` enforces strict ranges. If you get errors:
- `opening_credits` must have segment_order = 0
- `front_matter` must have segment_order between 1-9
- `body_chapter` must have segment_order between 10-79
- `back_matter` must have segment_order between 80-89
- `bonus_chapter` must have segment_order between 90-94
- `teaser_chapter` must have segment_order between 95-97
- `closing_credits` must have segment_order = 98
- `retail_sample` must have segment_order = 99

---
**Last Updated:** 2025-12-04
**Migration Version:** 0009
