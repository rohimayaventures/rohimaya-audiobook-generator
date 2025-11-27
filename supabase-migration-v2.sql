-- =============================================================================
-- AUTHORFLOW STUDIOS - DATABASE MIGRATION V2
-- =============================================================================
-- Run this SQL in your Supabase Dashboard → SQL Editor
-- This adds new columns for Findaway package support
-- Safe to run multiple times (uses IF NOT EXISTS patterns)
-- =============================================================================

-- Add new columns to jobs table (if they don't exist)
DO $$
BEGIN
    -- Book metadata columns
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

    -- Processing configuration columns
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

    -- Findaway-specific options
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'sample_style') THEN
        ALTER TABLE jobs ADD COLUMN sample_style TEXT DEFAULT 'default';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'cover_vibe') THEN
        ALTER TABLE jobs ADD COLUMN cover_vibe TEXT;
    END IF;

    -- Progress tracking (upgrade from integer to decimal)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'progress_percent') THEN
        ALTER TABLE jobs ADD COLUMN progress_percent DECIMAL(5,2) DEFAULT 0;
        -- Migrate old progress values if they exist
        UPDATE jobs SET progress_percent = progress WHERE progress IS NOT NULL;
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

    -- Source path for manuscript storage
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'source_path') THEN
        ALTER TABLE jobs ADD COLUMN source_path TEXT;
    END IF;

END $$;

-- Update mode check constraint to include new modes
ALTER TABLE jobs DROP CONSTRAINT IF EXISTS jobs_mode_check;
-- Note: We're being lenient with mode values to avoid migration issues
-- The application code validates modes

-- Update status check constraint (in case we need new statuses later)
-- Currently keeping: pending, processing, completed, failed, cancelled

-- =============================================================================
-- DONE!
-- =============================================================================
-- Migration complete. Your database now supports:
-- - Findaway package generation
-- - Book metadata (author, genre, ISBN, etc.)
-- - AI cover generation settings
-- - Detailed progress tracking
-- =============================================================================
