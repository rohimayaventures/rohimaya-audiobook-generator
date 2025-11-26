-- ============================================================================
-- Rohimaya Audiobook Generator - Database Schema
-- Migration: 0001_create_jobs_tables
-- Created: 2025-11-22
-- ============================================================================

-- Enable UUID extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- TABLE: jobs
-- Purpose: Track audiobook generation jobs from creation to completion
-- ============================================================================

CREATE TABLE IF NOT EXISTS jobs (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- User Association (Supabase Auth)
    user_id UUID NOT NULL,  -- References auth.users(id) in Supabase Auth

    -- Job Status & Mode
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    mode TEXT NOT NULL DEFAULT 'single_voice'
        CHECK (mode IN ('single_voice', 'dual_voice')),

    -- Manuscript Metadata
    title TEXT NOT NULL,
    author TEXT,  -- Optional author name
    source_type TEXT NOT NULL
        CHECK (source_type IN ('upload', 'google_drive', 'paste', 'url')),
    source_path TEXT,  -- Supabase Storage path (bucket:path) or Google Drive file ID

    -- Voice Configuration
    tts_provider TEXT DEFAULT 'openai'
        CHECK (tts_provider IN ('openai', 'elevenlabs', 'inworld')),
    narrator_voice_id TEXT,  -- Primary voice (single-voice) or narrator (dual-voice)
    character_voice_id TEXT,  -- Only for dual-voice mode
    character_name TEXT,      -- Character name for dual-voice dialogue detection

    -- Output Configuration
    audio_format TEXT DEFAULT 'mp3'
        CHECK (audio_format IN ('mp3', 'wav', 'flac', 'm4b')),
    audio_bitrate TEXT DEFAULT '128k',  -- e.g., '128k', '192k', '320k'

    -- Results
    audio_path TEXT,  -- Final audiobook file path in Supabase Storage (nullable until completed)
    duration_seconds INTEGER,  -- Total audiobook duration (calculated after generation)
    file_size_bytes BIGINT,    -- Final file size

    -- Processing Metadata
    total_chapters INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 0,
    chunks_completed INTEGER DEFAULT 0,
    progress_percent NUMERIC(5,2) DEFAULT 0.00,  -- 0.00 to 100.00

    -- Error Handling
    error_message TEXT,  -- Error details if status = 'failed'
    retry_count INTEGER DEFAULT 0,  -- Number of retry attempts

    -- Cost Tracking
    estimated_cost_usd NUMERIC(10,4),  -- Estimated cost before processing
    actual_cost_usd NUMERIC(10,4),     -- Actual cost after processing

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,   -- When processing actually began
    completed_at TIMESTAMPTZ  -- When job finished (success or failure)
);

-- Indexes for performance
CREATE INDEX idx_jobs_user_id ON jobs(user_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_jobs_user_status ON jobs(user_id, status);

-- Comments for documentation
COMMENT ON TABLE jobs IS 'Audiobook generation jobs with status tracking and metadata';
COMMENT ON COLUMN jobs.user_id IS 'References auth.users(id) from Supabase Auth';
COMMENT ON COLUMN jobs.status IS 'Job lifecycle: pending → processing → completed/failed';
COMMENT ON COLUMN jobs.mode IS 'Generation mode: single_voice (narrator only) or dual_voice (narrator + character)';
COMMENT ON COLUMN jobs.source_path IS 'File location: Supabase Storage path (manuscripts/user123/book.txt) or Google Drive ID';
COMMENT ON COLUMN jobs.audio_path IS 'Final audiobook location in Supabase Storage (audiobooks/job123/final.mp3)';


-- ============================================================================
-- TABLE: job_files
-- Purpose: Track per-chapter and per-chunk audio files for each job
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_files (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Foreign Key to jobs table
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,

    -- File Organization
    file_type TEXT NOT NULL DEFAULT 'chunk'
        CHECK (file_type IN ('chunk', 'chapter', 'final')),
    chapter_number INTEGER,  -- Chapter number (nullable for non-chapter files)
    part_number INTEGER,     -- Part/chunk number within chapter (nullable)

    -- Audio File Metadata
    audio_path TEXT NOT NULL,  -- Path in Supabase Storage (e.g., audiobooks/job123/ch1_part3.mp3)
    duration_seconds NUMERIC(10,2),  -- Audio duration in seconds (e.g., 45.67)
    file_size_bytes BIGINT,          -- File size in bytes

    -- Processing Metadata
    text_content TEXT,  -- The text that was converted to audio (useful for regeneration)
    word_count INTEGER, -- Word count of text_content

    -- Voice Used (for tracking in dual-voice mode)
    voice_id TEXT,  -- Which voice was used for this file
    speaker_type TEXT CHECK (speaker_type IN ('narrator', 'character', 'single')),

    -- Status
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Indexes for performance
CREATE INDEX idx_job_files_job_id ON job_files(job_id);
CREATE INDEX idx_job_files_chapter ON job_files(job_id, chapter_number, part_number);
CREATE INDEX idx_job_files_status ON job_files(status);
CREATE INDEX idx_job_files_type ON job_files(file_type);

-- Comments for documentation
COMMENT ON TABLE job_files IS 'Individual audio files generated during audiobook creation (chapters, chunks, final output)';
COMMENT ON COLUMN job_files.file_type IS 'File category: chunk (individual TTS output), chapter (merged chapter), final (complete audiobook)';
COMMENT ON COLUMN job_files.text_content IS 'Original text converted to audio (enables regeneration of specific parts)';


-- ============================================================================
-- FUNCTION: update_job_updated_at()
-- Purpose: Automatically update jobs.updated_at on every row update
-- ============================================================================

CREATE OR REPLACE FUNCTION update_job_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
CREATE TRIGGER trigger_update_job_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_job_updated_at();

COMMENT ON FUNCTION update_job_updated_at() IS 'Auto-update jobs.updated_at timestamp on every UPDATE';


-- ============================================================================
-- FUNCTION: update_job_progress()
-- Purpose: Calculate and update progress_percent based on chunks_completed
-- ============================================================================

CREATE OR REPLACE FUNCTION update_job_progress()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.total_chunks > 0 THEN
        NEW.progress_percent = (NEW.chunks_completed::NUMERIC / NEW.total_chunks::NUMERIC) * 100;
    ELSE
        NEW.progress_percent = 0;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically calculate progress
CREATE TRIGGER trigger_update_job_progress
    BEFORE UPDATE OF chunks_completed, total_chunks ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_job_progress();

COMMENT ON FUNCTION update_job_progress() IS 'Auto-calculate progress_percent based on chunks_completed / total_chunks';


-- ============================================================================
-- SAMPLE DATA (Optional - for development only)
-- Uncomment to insert test data
-- ============================================================================

-- INSERT INTO jobs (
--     user_id,
--     status,
--     mode,
--     title,
--     source_type,
--     source_path,
--     tts_provider,
--     narrator_voice_id
-- ) VALUES (
--     '00000000-0000-0000-0000-000000000000',  -- Replace with real user_id
--     'pending',
--     'single_voice',
--     'The Great Adventure',
--     'upload',
--     'manuscripts/user123/great_adventure.txt',
--     'openai',
--     'alloy'
-- );


-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
