-- =============================================================================
-- AUTHORFLOW STUDIOS - SUPABASE DATABASE SCHEMA
-- =============================================================================
-- Run this SQL in your Supabase Dashboard → SQL Editor
-- =============================================================================

-- Enable UUID extension (usually already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- JOBS TABLE
-- Stores audiobook conversion jobs
-- =============================================================================
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Job metadata
    title TEXT,
    filename TEXT,
    manuscript_path TEXT,           -- R2 path to uploaded manuscript
    manuscript_text TEXT,           -- Direct text input (if not file)

    -- Book metadata (for Findaway packages)
    author TEXT,
    narrator_name TEXT,
    genre TEXT,
    language TEXT DEFAULT 'en',
    isbn TEXT,
    publisher TEXT,

    -- Processing configuration
    voice_profile TEXT DEFAULT 'warm-narrator',
    narrator_voice_id TEXT,         -- TTS voice ID for narrator
    character_voice_id TEXT,        -- TTS voice ID for character (dual-voice)
    character_name TEXT,            -- Character name (dual-voice)
    tts_provider TEXT DEFAULT 'openai',
    output_format TEXT DEFAULT 'mp3',
    mode TEXT DEFAULT 'single_voice',  -- single_voice, dual_voice, findaway

    -- Findaway-specific options
    sample_style TEXT DEFAULT 'default',  -- 'default' or 'spicy' for romance
    cover_vibe TEXT,                -- Visual vibe for AI cover generation

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    progress_percent DECIMAL(5,2) DEFAULT 0 CHECK (progress_percent >= 0 AND progress_percent <= 100),
    current_step TEXT,
    error_message TEXT,

    -- Output
    audio_path TEXT,                -- R2 path to final audio/ZIP
    audio_url TEXT,                 -- Presigned URL (temporary)
    duration_seconds INTEGER,
    file_size_bytes BIGINT,

    -- Findaway package output
    package_type TEXT,              -- 'findaway' for ZIP packages
    section_count INTEGER,          -- Number of audio sections
    has_cover BOOLEAN DEFAULT FALSE,
    manifest_json TEXT,             -- Full Findaway manifest as JSON

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- =============================================================================
-- JOB_FILES TABLE
-- Stores individual audio chunks/chapters for a job
-- =============================================================================
CREATE TABLE IF NOT EXISTS job_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,

    -- File info
    file_type TEXT NOT NULL CHECK (file_type IN ('chunk', 'chapter', 'final')),
    part_number INTEGER,
    chapter_title TEXT,

    -- Storage
    audio_path TEXT,                -- R2 path
    duration_seconds INTEGER,
    file_size_bytes BIGINT,

    -- Text segment
    text_content TEXT,
    character_count INTEGER,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_files_job_id ON job_files(job_id);

-- =============================================================================
-- AUTO-UPDATE TRIGGER FOR updated_at
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_jobs_updated_at ON jobs;
CREATE TRIGGER update_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- ROW LEVEL SECURITY (RLS)
-- =============================================================================

-- Enable RLS
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_files ENABLE ROW LEVEL SECURITY;

-- Jobs: Users can only see their own jobs
CREATE POLICY "Users can view their own jobs"
    ON jobs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own jobs"
    ON jobs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own jobs"
    ON jobs FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own jobs"
    ON jobs FOR DELETE
    USING (auth.uid() = user_id);

-- Job Files: Users can only access files from their jobs
CREATE POLICY "Users can view their job files"
    ON job_files FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM jobs
            WHERE jobs.id = job_files.job_id
            AND jobs.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert their job files"
    ON job_files FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM jobs
            WHERE jobs.id = job_files.job_id
            AND jobs.user_id = auth.uid()
        )
    );

-- =============================================================================
-- SERVICE ROLE BYPASS (for backend operations)
-- =============================================================================
-- The backend uses service_role key which bypasses RLS automatically.
-- No additional policies needed for backend operations.

-- =============================================================================
-- GRANT PERMISSIONS
-- =============================================================================
GRANT ALL ON jobs TO authenticated;
GRANT ALL ON job_files TO authenticated;
GRANT ALL ON jobs TO service_role;
GRANT ALL ON job_files TO service_role;

-- =============================================================================
-- DONE!
-- =============================================================================
-- Your database is now ready for AuthorFlow Studios.
--
-- Next steps:
-- 1. Configure SMTP in Supabase → Authentication → Email Templates → SMTP Settings
-- 2. Make sure your .env has the correct SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
-- =============================================================================
