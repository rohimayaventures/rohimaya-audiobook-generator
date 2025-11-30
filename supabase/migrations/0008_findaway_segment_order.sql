-- ============================================================================
-- Rohimaya Audiobook Generator - Findaway Segment Order Enhancement
-- Migration: 0008_findaway_segment_order
-- Created: 2025-11-29
-- Purpose: Add strict Findaway ordering with segment_order column
-- ============================================================================

-- ============================================================================
-- FINDAWAY SEGMENT ORDERING RULES
-- ============================================================================
--
-- Segment Types and their reserved segment_order ranges:
--   OPENING_CREDITS  = 0          (exactly one)
--   FRONT_MATTER     = 1-9        (0-9 items: preface, foreword, etc.)
--   BODY_CHAPTER     = 10-79      (1-70 chapters)
--   BACK_MATTER      = 80-89      (0-10 items: afterword, appendix, etc.)
--   CLOSING_CREDITS  = 98         (exactly one)
--   RETAIL_SAMPLE    = 99         (exactly one)
--
-- Output filenames MUST sort alphabetically:
--   00_opening_credits.mp3
--   01_front_matter_01.mp3
--   02_front_matter_02.mp3
--   10_chapter_01.mp3
--   11_chapter_02.mp3
--   ...
--   80_back_matter_01.mp3
--   98_closing_credits.mp3
--   99_retail_sample.mp3
-- ============================================================================


-- ============================================================================
-- ADD segment_order TO chapters TABLE
-- ============================================================================

-- Add segment_order column - this is the AUTHORITATIVE order for audio generation
ALTER TABLE chapters ADD COLUMN IF NOT EXISTS segment_order INTEGER;

-- Add display_title for cleaner UI display (separate from internal title)
ALTER TABLE chapters ADD COLUMN IF NOT EXISTS display_title TEXT;

COMMENT ON COLUMN chapters.segment_order IS 'Findaway segment order: 0=opening, 1-9=front matter, 10-79=body chapters, 80-89=back matter, 98=closing, 99=retail sample';
COMMENT ON COLUMN chapters.display_title IS 'Clean title for UI display (e.g., "Chapter 1: The Beginning")';

-- Create index for segment_order queries
CREATE INDEX IF NOT EXISTS idx_chapters_segment_order ON chapters(job_id, segment_order);

-- Unique constraint: no duplicate segment_orders per job
CREATE UNIQUE INDEX IF NOT EXISTS idx_chapters_job_segment_order ON chapters(job_id, segment_order);


-- ============================================================================
-- ADD segment_order TO tracks TABLE
-- ============================================================================

-- Add segment_order column for strict ordering
ALTER TABLE tracks ADD COLUMN IF NOT EXISTS segment_order INTEGER;

COMMENT ON COLUMN tracks.segment_order IS 'Findaway segment order matching chapters table';

-- Create index for segment_order queries
CREATE INDEX IF NOT EXISTS idx_tracks_segment_order ON tracks(job_id, segment_order);


-- ============================================================================
-- ADD opening/closing credits generation flag
-- ============================================================================

-- Jobs table additions for credits configuration
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS narrator_name TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS has_opening_credits BOOLEAN DEFAULT TRUE;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS has_closing_credits BOOLEAN DEFAULT TRUE;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS author_name TEXT;

COMMENT ON COLUMN jobs.narrator_name IS 'Narrator name for credits (e.g., "Read by John Smith")';
COMMENT ON COLUMN jobs.has_opening_credits IS 'Whether to generate opening credits audio';
COMMENT ON COLUMN jobs.has_closing_credits IS 'Whether to generate closing credits audio';
COMMENT ON COLUMN jobs.author_name IS 'Author name for credits (if different from title parsing)';


-- ============================================================================
-- ADD retail sample edit boundaries
-- ============================================================================

-- Allow user to manually edit sample boundaries
ALTER TABLE retail_samples ADD COLUMN IF NOT EXISTS user_edited_text TEXT;
ALTER TABLE retail_samples ADD COLUMN IF NOT EXISTS is_user_edited BOOLEAN DEFAULT FALSE;
ALTER TABLE retail_samples ADD COLUMN IF NOT EXISTS candidate_rank INTEGER DEFAULT 1;
ALTER TABLE retail_samples ADD COLUMN IF NOT EXISTS rejection_reason TEXT;

COMMENT ON COLUMN retail_samples.user_edited_text IS 'User-edited version of the sample text (if they modified boundaries)';
COMMENT ON COLUMN retail_samples.is_user_edited IS 'True if user manually edited the sample boundaries';
COMMENT ON COLUMN retail_samples.candidate_rank IS 'Rank among AI-suggested candidates (1=best, 2=second, etc.)';
COMMENT ON COLUMN retail_samples.rejection_reason IS 'If user rejected this candidate, why (for logging)';


-- ============================================================================
-- HELPER FUNCTION: get_next_segment_order()
-- Purpose: Get the next available segment_order for a given segment type
-- ============================================================================

CREATE OR REPLACE FUNCTION get_next_segment_order(
    p_job_id UUID,
    p_segment_type TEXT
) RETURNS INTEGER AS $$
DECLARE
    v_base_order INTEGER;
    v_max_order INTEGER;
    v_limit INTEGER;
    v_next_order INTEGER;
BEGIN
    -- Determine base order and limits based on segment type
    CASE p_segment_type
        WHEN 'opening_credits' THEN
            v_base_order := 0;
            v_limit := 0;  -- Only one allowed
        WHEN 'front_matter' THEN
            v_base_order := 1;
            v_limit := 9;  -- Up to 9 front matter items
        WHEN 'body_chapter' THEN
            v_base_order := 10;
            v_limit := 79;  -- Up to 70 chapters
        WHEN 'back_matter' THEN
            v_base_order := 80;
            v_limit := 89;  -- Up to 10 back matter items
        WHEN 'closing_credits' THEN
            v_base_order := 98;
            v_limit := 98;  -- Only one allowed
        WHEN 'retail_sample' THEN
            v_base_order := 99;
            v_limit := 99;  -- Only one allowed
        ELSE
            v_base_order := 10;  -- Default to body chapter range
            v_limit := 79;
    END CASE;

    -- Find current max segment_order for this type in this job
    SELECT COALESCE(MAX(segment_order), v_base_order - 1)
    INTO v_max_order
    FROM chapters
    WHERE job_id = p_job_id
      AND segment_type = p_segment_type;

    -- Calculate next order
    v_next_order := GREATEST(v_max_order + 1, v_base_order);

    -- Check if we've exceeded the limit
    IF v_next_order > v_limit THEN
        RAISE EXCEPTION 'Maximum % segments reached for job %', p_segment_type, p_job_id;
    END IF;

    RETURN v_next_order;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_next_segment_order IS 'Returns the next available segment_order for a given segment type in a job';


-- ============================================================================
-- HELPER FUNCTION: validate_segment_order()
-- Purpose: Validate that segment_order matches segment_type range
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_segment_order()
RETURNS TRIGGER AS $$
BEGIN
    -- Validate segment_order is in correct range for segment_type
    CASE NEW.segment_type
        WHEN 'opening_credits' THEN
            IF NEW.segment_order != 0 THEN
                RAISE EXCEPTION 'opening_credits must have segment_order = 0';
            END IF;
        WHEN 'front_matter' THEN
            IF NEW.segment_order < 1 OR NEW.segment_order > 9 THEN
                RAISE EXCEPTION 'front_matter must have segment_order between 1 and 9';
            END IF;
        WHEN 'body_chapter' THEN
            IF NEW.segment_order < 10 OR NEW.segment_order > 79 THEN
                RAISE EXCEPTION 'body_chapter must have segment_order between 10 and 79';
            END IF;
        WHEN 'back_matter' THEN
            IF NEW.segment_order < 80 OR NEW.segment_order > 89 THEN
                RAISE EXCEPTION 'back_matter must have segment_order between 80 and 89';
            END IF;
        WHEN 'closing_credits' THEN
            IF NEW.segment_order != 98 THEN
                RAISE EXCEPTION 'closing_credits must have segment_order = 98';
            END IF;
        WHEN 'retail_sample' THEN
            IF NEW.segment_order != 99 THEN
                RAISE EXCEPTION 'retail_sample must have segment_order = 99';
            END IF;
    END CASE;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for validation
DROP TRIGGER IF EXISTS trigger_validate_chapter_segment_order ON chapters;
CREATE TRIGGER trigger_validate_chapter_segment_order
    BEFORE INSERT OR UPDATE OF segment_order, segment_type ON chapters
    FOR EACH ROW
    WHEN (NEW.segment_order IS NOT NULL)
    EXECUTE FUNCTION validate_segment_order();


-- ============================================================================
-- VIEW: job_segments_ordered
-- Purpose: Get all segments for a job in correct Findaway order
-- ============================================================================

CREATE OR REPLACE VIEW job_segments_ordered AS
SELECT
    c.id,
    c.job_id,
    c.segment_order,
    c.segment_type,
    c.title,
    c.display_title,
    c.word_count,
    c.estimated_duration_seconds,
    c.status,
    c.audio_path,
    -- Generate export filename from segment_order
    CASE
        WHEN c.segment_type = 'opening_credits' THEN '00_opening_credits.mp3'
        WHEN c.segment_type = 'front_matter' THEN
            LPAD(c.segment_order::TEXT, 2, '0') || '_front_matter_' ||
            LPAD((c.segment_order)::TEXT, 2, '0') || '.mp3'
        WHEN c.segment_type = 'body_chapter' THEN
            LPAD(c.segment_order::TEXT, 2, '0') || '_chapter_' ||
            LPAD((c.segment_order - 9)::TEXT, 2, '0') || '.mp3'
        WHEN c.segment_type = 'back_matter' THEN
            LPAD(c.segment_order::TEXT, 2, '0') || '_back_matter_' ||
            LPAD((c.segment_order - 79)::TEXT, 2, '0') || '.mp3'
        WHEN c.segment_type = 'closing_credits' THEN '98_closing_credits.mp3'
        WHEN c.segment_type = 'retail_sample' THEN '99_retail_sample.mp3'
        ELSE LPAD(c.segment_order::TEXT, 2, '0') || '_unknown.mp3'
    END AS export_filename
FROM chapters c
WHERE c.segment_order IS NOT NULL
ORDER BY c.job_id, c.segment_order;

COMMENT ON VIEW job_segments_ordered IS 'All job segments in Findaway export order with generated filenames';


-- ============================================================================
-- FUNCTION: generate_default_credits_text()
-- Purpose: Generate default opening/closing credits text
-- ============================================================================

CREATE OR REPLACE FUNCTION generate_default_credits_text(
    p_job_id UUID,
    p_credit_type TEXT  -- 'opening' or 'closing'
) RETURNS TEXT AS $$
DECLARE
    v_job RECORD;
    v_text TEXT;
BEGIN
    -- Get job details
    SELECT title, author_name, narrator_name
    INTO v_job
    FROM jobs
    WHERE id = p_job_id;

    IF NOT FOUND THEN
        RETURN NULL;
    END IF;

    IF p_credit_type = 'opening' THEN
        -- Opening credits format
        v_text := COALESCE(v_job.title, 'Untitled');
        IF v_job.author_name IS NOT NULL THEN
            v_text := v_text || '. By ' || v_job.author_name;
        END IF;
        IF v_job.narrator_name IS NOT NULL THEN
            v_text := v_text || '. Read by ' || v_job.narrator_name;
        END IF;
        v_text := v_text || '.';
    ELSIF p_credit_type = 'closing' THEN
        -- Closing credits format
        v_text := 'The end. ';
        v_text := v_text || COALESCE(v_job.title, 'This audiobook');
        IF v_job.author_name IS NOT NULL THEN
            v_text := v_text || ' by ' || v_job.author_name;
        END IF;
        IF v_job.narrator_name IS NOT NULL THEN
            v_text := v_text || ', narrated by ' || v_job.narrator_name;
        END IF;
        v_text := v_text || '. Thank you for listening.';
    ELSE
        RETURN NULL;
    END IF;

    RETURN v_text;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION generate_default_credits_text IS 'Generate default opening or closing credits text for a job';


-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
