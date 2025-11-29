-- ============================================================================
-- Rohimaya Audiobook Generator - Chapters Table
-- Migration: 0007_chapters_table
-- Created: 2025-11-29
-- Purpose: Add explicit chapter tracking for review/ordering before TTS
-- ============================================================================

-- ============================================================================
-- TABLE: chapters
-- Purpose: Track individual chapters extracted from manuscripts
-- Allows users to review, reorder, and approve chapters before TTS generation
-- ============================================================================

CREATE TABLE IF NOT EXISTS chapters (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Foreign Key to jobs table
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,

    -- Chapter Ordering (the key differentiator!)
    chapter_index INTEGER NOT NULL,  -- 0-based index for final audio order
    source_order INTEGER NOT NULL,   -- Original position in manuscript (for reference)

    -- Chapter Metadata
    title TEXT NOT NULL DEFAULT 'Untitled',

    -- Content Statistics
    text_content TEXT,          -- Full chapter text (stored for processing)
    character_count INTEGER DEFAULT 0,
    word_count INTEGER DEFAULT 0,
    estimated_duration_seconds INTEGER DEFAULT 0,  -- Estimated based on word count

    -- Review Status
    status TEXT NOT NULL DEFAULT 'pending_review'
        CHECK (status IN (
            'pending_review',   -- Awaiting user review
            'approved',         -- User approved for TTS
            'excluded',         -- User excluded from audio
            'processing',       -- Currently generating audio
            'completed',        -- Audio generation complete
            'failed'            -- Audio generation failed
        )),

    -- Segment Type (for Findaway compatibility)
    segment_type TEXT NOT NULL DEFAULT 'body_chapter'
        CHECK (segment_type IN (
            'opening_credits',   -- Standard audiobook opening
            'front_matter',      -- Dedication, foreword, etc.
            'body_chapter',      -- Main content chapters
            'back_matter',       -- Epilogue, afterword, etc.
            'closing_credits',   -- Standard audiobook closing
            'retail_sample'      -- Retail audio sample
        )),

    -- Audio Output (once generated)
    audio_path TEXT,            -- R2 path to chapter audio
    audio_duration_seconds INTEGER,
    audio_file_size_bytes BIGINT,

    -- Error Tracking
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    approved_at TIMESTAMPTZ,    -- When user approved this chapter
    completed_at TIMESTAMPTZ    -- When audio generation finished
);

-- Ensure unique chapter indices per job (no duplicates!)
CREATE UNIQUE INDEX idx_chapters_job_index ON chapters(job_id, chapter_index);

-- Indexes for common queries
CREATE INDEX idx_chapters_job_id ON chapters(job_id);
CREATE INDEX idx_chapters_status ON chapters(status);
CREATE INDEX idx_chapters_segment_type ON chapters(segment_type);
CREATE INDEX idx_chapters_job_status ON chapters(job_id, status);

-- Comments for documentation
COMMENT ON TABLE chapters IS 'Individual chapters extracted from manuscripts, supporting review and reordering before TTS';
COMMENT ON COLUMN chapters.chapter_index IS 'Final playback order (0-based). Users can reorder via the review UI.';
COMMENT ON COLUMN chapters.source_order IS 'Original position in manuscript. Preserved for reference even after reordering.';
COMMENT ON COLUMN chapters.segment_type IS 'Findaway-compatible segment classification';
COMMENT ON COLUMN chapters.status IS 'Chapter lifecycle: pending_review -> approved -> processing -> completed';


-- ============================================================================
-- TABLE: tracks
-- Purpose: Track final audio files in playback order (for downloads UI)
-- ============================================================================

CREATE TABLE IF NOT EXISTS tracks (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Foreign Keys
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    chapter_id UUID REFERENCES chapters(id) ON DELETE SET NULL,  -- Nullable for credits/samples

    -- Track Ordering
    track_index INTEGER NOT NULL,  -- 0-based playback order

    -- Track Metadata
    title TEXT NOT NULL,
    segment_type TEXT NOT NULL DEFAULT 'body_chapter'
        CHECK (segment_type IN (
            'opening_credits',
            'front_matter',
            'body_chapter',
            'back_matter',
            'closing_credits',
            'retail_sample'
        )),

    -- Audio File Info
    audio_path TEXT,             -- R2 path
    duration_seconds INTEGER,
    file_size_bytes BIGINT,

    -- Status
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Ensure unique track indices per job
CREATE UNIQUE INDEX idx_tracks_job_index ON tracks(job_id, track_index);

-- Indexes
CREATE INDEX idx_tracks_job_id ON tracks(job_id);
CREATE INDEX idx_tracks_status ON tracks(status);
CREATE INDEX idx_tracks_chapter_id ON tracks(chapter_id);

COMMENT ON TABLE tracks IS 'Final audio tracks in playback order (maps to downloadable files)';
COMMENT ON COLUMN tracks.track_index IS 'Playback order: 0=opening credits, 1-N=chapters, N+1=closing credits, etc.';


-- ============================================================================
-- UPDATE jobs TABLE: Add chapter review status
-- ============================================================================

-- Add new status values for chapter review workflow
ALTER TABLE jobs DROP CONSTRAINT IF EXISTS jobs_status_check;
ALTER TABLE jobs ADD CONSTRAINT jobs_status_check
    CHECK (status IN (
        'pending',              -- Job created, not yet parsed
        'parsing',              -- Manuscript being parsed into chapters
        'chapters_pending',     -- Chapters extracted, awaiting user review
        'chapters_approved',    -- User approved chapter order, ready for TTS
        'processing',           -- TTS generation in progress
        'completed',            -- All done
        'failed',               -- Something went wrong
        'cancelled'             -- User cancelled
    ));

-- Add new columns for chapter workflow
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS chapters_parsed_at TIMESTAMPTZ;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS chapters_approved_at TIMESTAMPTZ;

COMMENT ON COLUMN jobs.chapters_parsed_at IS 'When manuscript parsing completed and chapters are ready for review';
COMMENT ON COLUMN jobs.chapters_approved_at IS 'When user approved chapter order for TTS processing';


-- ============================================================================
-- FUNCTION: update_chapter_updated_at()
-- ============================================================================

CREATE OR REPLACE FUNCTION update_chapter_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_chapter_updated_at
    BEFORE UPDATE ON chapters
    FOR EACH ROW
    EXECUTE FUNCTION update_chapter_updated_at();


-- ============================================================================
-- FUNCTION: estimate_chapter_duration()
-- Purpose: Estimate audio duration based on word count (avg 150 words/minute)
-- ============================================================================

CREATE OR REPLACE FUNCTION estimate_chapter_duration()
RETURNS TRIGGER AS $$
BEGIN
    -- Estimate ~150 words per minute for audiobook narration
    IF NEW.word_count > 0 THEN
        NEW.estimated_duration_seconds = (NEW.word_count / 150.0) * 60;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_estimate_chapter_duration
    BEFORE INSERT OR UPDATE OF word_count ON chapters
    FOR EACH ROW
    EXECUTE FUNCTION estimate_chapter_duration();


-- ============================================================================
-- TABLE: retail_samples
-- Purpose: Track auto-suggested and user-confirmed retail sample selections
-- ============================================================================

CREATE TABLE IF NOT EXISTS retail_samples (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Foreign Key to jobs table
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,

    -- Source Information
    source_chapter_id UUID REFERENCES chapters(id) ON DELETE SET NULL,
    source_chapter_title TEXT,
    source_start_char INTEGER,  -- Character position in source chapter text
    source_end_char INTEGER,

    -- Sample Content
    sample_text TEXT NOT NULL,
    word_count INTEGER DEFAULT 0,
    character_count INTEGER DEFAULT 0,
    estimated_duration_seconds INTEGER DEFAULT 0,

    -- AI Scoring (from Gemini analysis)
    engagement_score NUMERIC(3,2),      -- 0.00 to 1.00
    emotional_intensity_score NUMERIC(3,2),
    spoiler_risk_score NUMERIC(3,2),    -- 0.00 = no spoilers, 1.00 = major spoilers
    overall_score NUMERIC(3,2),

    -- Selection Status
    is_auto_suggested BOOLEAN DEFAULT TRUE,
    is_user_confirmed BOOLEAN DEFAULT FALSE,
    is_final BOOLEAN DEFAULT FALSE,     -- True when audio has been generated

    -- Audio Output (once generated)
    audio_path TEXT,
    audio_duration_seconds INTEGER,
    audio_file_size_bytes BIGINT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    confirmed_at TIMESTAMPTZ,
    generated_at TIMESTAMPTZ
);

-- Only one final retail sample per job
CREATE UNIQUE INDEX idx_retail_samples_job_final ON retail_samples(job_id) WHERE is_final = TRUE;

-- Indexes
CREATE INDEX idx_retail_samples_job_id ON retail_samples(job_id);
CREATE INDEX idx_retail_samples_confirmed ON retail_samples(job_id, is_user_confirmed);

COMMENT ON TABLE retail_samples IS 'Retail sample candidates and selections for audiobook distribution';
COMMENT ON COLUMN retail_samples.engagement_score IS 'AI-rated engagement level (0-1)';
COMMENT ON COLUMN retail_samples.spoiler_risk_score IS 'AI-rated spoiler risk (0=safe, 1=major spoilers)';


-- ============================================================================
-- Add Findaway export filename column to tracks
-- ============================================================================

ALTER TABLE tracks ADD COLUMN IF NOT EXISTS export_filename TEXT;

COMMENT ON COLUMN tracks.export_filename IS 'Findaway-style filename (e.g., 10_chapter_01.mp3)';


-- ============================================================================
-- Add retail sample and credits configuration to jobs
-- ============================================================================

ALTER TABLE jobs ADD COLUMN IF NOT EXISTS opening_credits_text TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS closing_credits_text TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS retail_sample_confirmed BOOLEAN DEFAULT FALSE;

COMMENT ON COLUMN jobs.opening_credits_text IS 'Text for opening credits (e.g., "Book title by Author, narrated by...")';
COMMENT ON COLUMN jobs.closing_credits_text IS 'Text for closing credits (e.g., "The end. Thank you for listening...")';
COMMENT ON COLUMN jobs.retail_sample_confirmed IS 'Whether user has confirmed the retail sample selection';


-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE chapters ENABLE ROW LEVEL SECURITY;
ALTER TABLE tracks ENABLE ROW LEVEL SECURITY;
ALTER TABLE retail_samples ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see chapters/tracks for their own jobs
CREATE POLICY chapters_user_policy ON chapters
    FOR ALL
    USING (
        job_id IN (SELECT id FROM jobs WHERE user_id = auth.uid())
    );

CREATE POLICY tracks_user_policy ON tracks
    FOR ALL
    USING (
        job_id IN (SELECT id FROM jobs WHERE user_id = auth.uid())
    );

CREATE POLICY retail_samples_user_policy ON retail_samples
    FOR ALL
    USING (
        job_id IN (SELECT id FROM jobs WHERE user_id = auth.uid())
    );


-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
