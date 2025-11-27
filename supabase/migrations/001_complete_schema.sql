-- =============================================================================
-- AUTHORFLOW STUDIOS - COMPLETE DATABASE MIGRATION
-- =============================================================================
-- This is a comprehensive migration that creates all tables and columns needed
-- for the AuthorFlow Studios platform.
--
-- SAFE TO RUN MULTIPLE TIMES - Uses IF NOT EXISTS and conditional logic.
--
-- Run this SQL in your Supabase Dashboard → SQL Editor
--
-- Tables created/updated:
--   - jobs (audiobook conversion jobs)
--   - job_files (audio chunks/chapters)
--   - user_billing (Stripe subscription tracking)
--   - user_usage (monthly usage limits)
--
-- Created: 2025-11-27
-- =============================================================================

-- Enable UUID extension (usually already enabled in Supabase)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- UTILITY FUNCTION: update_updated_at_column
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';


-- =============================================================================
-- 1. JOBS TABLE
-- =============================================================================
-- Stores audiobook conversion jobs

CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Job metadata
    title TEXT,
    filename TEXT,
    manuscript_path TEXT,           -- R2 path to uploaded manuscript (legacy)
    source_path TEXT,               -- R2 path to uploaded manuscript
    source_type TEXT,               -- 'upload', 'paste', 'url'
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
    audio_format TEXT DEFAULT 'mp3',
    audio_bitrate TEXT DEFAULT '128k',
    mode TEXT DEFAULT 'single_voice',  -- single_voice, dual_voice, findaway

    -- Findaway-specific options
    sample_style TEXT DEFAULT 'default',  -- 'default' or 'spicy' for romance
    cover_vibe TEXT,                -- Visual vibe for AI cover generation

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'pending',
    progress_percent DECIMAL(5,2) DEFAULT 0 CHECK (progress_percent >= 0 AND progress_percent <= 100),
    current_step TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

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

-- Add missing columns if table already exists (safe migration)
DO $$
BEGIN
    -- Source columns
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'source_path') THEN
        ALTER TABLE jobs ADD COLUMN source_path TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'source_type') THEN
        ALTER TABLE jobs ADD COLUMN source_type TEXT;
    END IF;

    -- Book metadata
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'author') THEN
        ALTER TABLE jobs ADD COLUMN author TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'narrator_name') THEN
        ALTER TABLE jobs ADD COLUMN narrator_name TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'genre') THEN
        ALTER TABLE jobs ADD COLUMN genre TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'language') THEN
        ALTER TABLE jobs ADD COLUMN language TEXT DEFAULT 'en';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'isbn') THEN
        ALTER TABLE jobs ADD COLUMN isbn TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'publisher') THEN
        ALTER TABLE jobs ADD COLUMN publisher TEXT;
    END IF;

    -- Voice configuration
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'narrator_voice_id') THEN
        ALTER TABLE jobs ADD COLUMN narrator_voice_id TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'character_voice_id') THEN
        ALTER TABLE jobs ADD COLUMN character_voice_id TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'character_name') THEN
        ALTER TABLE jobs ADD COLUMN character_name TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'tts_provider') THEN
        ALTER TABLE jobs ADD COLUMN tts_provider TEXT DEFAULT 'openai';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'audio_format') THEN
        ALTER TABLE jobs ADD COLUMN audio_format TEXT DEFAULT 'mp3';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'audio_bitrate') THEN
        ALTER TABLE jobs ADD COLUMN audio_bitrate TEXT DEFAULT '128k';
    END IF;

    -- Findaway options
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'sample_style') THEN
        ALTER TABLE jobs ADD COLUMN sample_style TEXT DEFAULT 'default';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'cover_vibe') THEN
        ALTER TABLE jobs ADD COLUMN cover_vibe TEXT;
    END IF;

    -- Progress tracking
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'progress_percent') THEN
        ALTER TABLE jobs ADD COLUMN progress_percent DECIMAL(5,2) DEFAULT 0;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'retry_count') THEN
        ALTER TABLE jobs ADD COLUMN retry_count INTEGER DEFAULT 0;
    END IF;

    -- Findaway package output
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'package_type') THEN
        ALTER TABLE jobs ADD COLUMN package_type TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'section_count') THEN
        ALTER TABLE jobs ADD COLUMN section_count INTEGER;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'has_cover') THEN
        ALTER TABLE jobs ADD COLUMN has_cover BOOLEAN DEFAULT FALSE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'manifest_json') THEN
        ALTER TABLE jobs ADD COLUMN manifest_json TEXT;
    END IF;
END $$;

-- Indexes for jobs table
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);

-- Update trigger for jobs
DROP TRIGGER IF EXISTS update_jobs_updated_at ON jobs;
CREATE TRIGGER update_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- 2. JOB_FILES TABLE
-- =============================================================================
-- Stores individual audio chunks/chapters for a job

CREATE TABLE IF NOT EXISTS job_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,

    -- File info
    file_type TEXT NOT NULL,
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

CREATE INDEX IF NOT EXISTS idx_job_files_job_id ON job_files(job_id);


-- =============================================================================
-- 3. USER_BILLING TABLE
-- =============================================================================
-- Stores Stripe subscription info linked to Supabase users

CREATE TABLE IF NOT EXISTS user_billing (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Stripe identifiers
    stripe_customer_id TEXT UNIQUE,
    stripe_subscription_id TEXT,

    -- Plan information
    -- "free", "creator", "author_pro", "publisher", or "admin"
    plan_id TEXT NOT NULL DEFAULT 'free',

    -- Subscription status
    -- "inactive", "active", "trialing", "past_due", "canceled", "unpaid"
    status TEXT NOT NULL DEFAULT 'inactive',

    -- Billing period
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,

    -- Cancellation tracking
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    canceled_at TIMESTAMP WITH TIME ZONE,

    -- Trial tracking (optional)
    trial_start TIMESTAMP WITH TIME ZONE,
    trial_end TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for user_billing
CREATE INDEX IF NOT EXISTS idx_user_billing_user_id ON user_billing(user_id);
CREATE INDEX IF NOT EXISTS idx_user_billing_stripe_customer_id ON user_billing(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_user_billing_status ON user_billing(status);

-- Update trigger for user_billing
DROP TRIGGER IF EXISTS update_user_billing_updated_at ON user_billing;
CREATE TRIGGER update_user_billing_updated_at
    BEFORE UPDATE ON user_billing
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- 4. USER_USAGE TABLE
-- =============================================================================
-- Tracks monthly usage for limit enforcement

CREATE TABLE IF NOT EXISTS user_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Usage period (monthly)
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Usage counters
    projects_created INTEGER DEFAULT 0,
    total_minutes_generated INTEGER DEFAULT 0,
    total_characters_processed BIGINT DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Unique constraint per user per period
    UNIQUE(user_id, period_start)
);

-- Indexes for user_usage
CREATE INDEX IF NOT EXISTS idx_user_usage_user_id ON user_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_user_usage_period ON user_usage(period_start, period_end);

-- Update trigger for user_usage
DROP TRIGGER IF EXISTS update_user_usage_updated_at ON user_usage;
CREATE TRIGGER update_user_usage_updated_at
    BEFORE UPDATE ON user_usage
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- 5. ROW LEVEL SECURITY (RLS)
-- =============================================================================

-- Enable RLS on all tables
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_billing ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_usage ENABLE ROW LEVEL SECURITY;

-- Jobs RLS Policies
DROP POLICY IF EXISTS "Users can view their own jobs" ON jobs;
CREATE POLICY "Users can view their own jobs"
    ON jobs FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own jobs" ON jobs;
CREATE POLICY "Users can insert their own jobs"
    ON jobs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own jobs" ON jobs;
CREATE POLICY "Users can update their own jobs"
    ON jobs FOR UPDATE
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own jobs" ON jobs;
CREATE POLICY "Users can delete their own jobs"
    ON jobs FOR DELETE
    USING (auth.uid() = user_id);

-- Job Files RLS Policies
DROP POLICY IF EXISTS "Users can view their job files" ON job_files;
CREATE POLICY "Users can view their job files"
    ON job_files FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM jobs
            WHERE jobs.id = job_files.job_id
            AND jobs.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can insert their job files" ON job_files;
CREATE POLICY "Users can insert their job files"
    ON job_files FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM jobs
            WHERE jobs.id = job_files.job_id
            AND jobs.user_id = auth.uid()
        )
    );

-- User Billing RLS Policies
DROP POLICY IF EXISTS "Users can view their own billing" ON user_billing;
CREATE POLICY "Users can view their own billing"
    ON user_billing FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own billing" ON user_billing;
CREATE POLICY "Users can insert their own billing"
    ON user_billing FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- User Usage RLS Policies
DROP POLICY IF EXISTS "Users can view their own usage" ON user_usage;
CREATE POLICY "Users can view their own usage"
    ON user_usage FOR SELECT
    USING (auth.uid() = user_id);


-- =============================================================================
-- 6. GRANT PERMISSIONS
-- =============================================================================
-- Service role bypasses RLS automatically, but we grant permissions anyway

GRANT ALL ON jobs TO authenticated;
GRANT ALL ON jobs TO service_role;
GRANT ALL ON job_files TO authenticated;
GRANT ALL ON job_files TO service_role;
GRANT ALL ON user_billing TO authenticated;
GRANT ALL ON user_billing TO service_role;
GRANT ALL ON user_usage TO authenticated;
GRANT ALL ON user_usage TO service_role;


-- =============================================================================
-- MIGRATION COMPLETE
-- =============================================================================
-- Your database now has all tables needed for AuthorFlow Studios:
--
-- Tables:
--   - jobs: Audiobook conversion jobs with Findaway support
--   - job_files: Audio chunks and chapters
--   - user_billing: Stripe subscription tracking
--   - user_usage: Monthly usage for limit enforcement
--
-- Next Steps:
--   1. Add Stripe env vars to Railway (backend)
--   2. Create products/prices in Stripe Dashboard with plan_id metadata
--   3. Configure Stripe webhook to point to /billing/webhook
--   4. Make yourself admin: Set {"role": "admin"} in Supabase user metadata
--
-- =============================================================================
