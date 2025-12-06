-- ============================================================================
-- Rohimaya Audiobook Generator - Bonus & Teaser Segment Types
-- Migration: 0009_bonus_teaser_segments
-- Created: 2025-12-04
-- Purpose: Add bonus_chapter (90-94) and teaser_chapter (95-97) segment types
-- ============================================================================

-- ============================================================================
-- UPDATED FINDAWAY SEGMENT ORDERING RULES
-- ============================================================================
--
-- Segment Types and their reserved segment_order ranges:
--   OPENING_CREDITS  = 0          (exactly one)
--   FRONT_MATTER     = 1-9        (0-9 items: preface, foreword, etc.)
--   BODY_CHAPTER     = 10-79      (1-70 chapters)
--   BACK_MATTER      = 80-89      (0-10 items: afterword, appendix, etc.)
--   BONUS_CHAPTER    = 90-94      (0-5 bonus chapters: deleted scenes, etc.)
--   TEASER_CHAPTER   = 95-97      (0-3 teaser chapters: sneak peeks, etc.)
--   CLOSING_CREDITS  = 98         (exactly one)
--   RETAIL_SAMPLE    = 99         (exactly one)
--
-- Output filenames:
--   90_bonus_01.mp3
--   91_bonus_02.mp3
--   95_teaser_01.mp3
--   96_teaser_02.mp3
-- ============================================================================


-- ============================================================================
-- UPDATE: get_next_segment_order()
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
        WHEN 'bonus_chapter' THEN
            v_base_order := 90;
            v_limit := 94;  -- Up to 5 bonus chapters
        WHEN 'teaser_chapter' THEN
            v_base_order := 95;
            v_limit := 97;  -- Up to 3 teaser chapters
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

COMMENT ON FUNCTION get_next_segment_order IS 'Returns the next available segment_order for a given segment type in a job (updated with bonus/teaser support)';


-- ============================================================================
-- UPDATE: validate_segment_order()
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
        WHEN 'bonus_chapter' THEN
            IF NEW.segment_order < 90 OR NEW.segment_order > 94 THEN
                RAISE EXCEPTION 'bonus_chapter must have segment_order between 90 and 94';
            END IF;
        WHEN 'teaser_chapter' THEN
            IF NEW.segment_order < 95 OR NEW.segment_order > 97 THEN
                RAISE EXCEPTION 'teaser_chapter must have segment_order between 95 and 97';
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


-- ============================================================================
-- UPDATE VIEW: job_segments_ordered
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
        WHEN c.segment_type = 'bonus_chapter' THEN
            LPAD(c.segment_order::TEXT, 2, '0') || '_bonus_' ||
            LPAD((c.segment_order - 89)::TEXT, 2, '0') || '.mp3'
        WHEN c.segment_type = 'teaser_chapter' THEN
            LPAD(c.segment_order::TEXT, 2, '0') || '_teaser_' ||
            LPAD((c.segment_order - 94)::TEXT, 2, '0') || '.mp3'
        WHEN c.segment_type = 'closing_credits' THEN '98_closing_credits.mp3'
        WHEN c.segment_type = 'retail_sample' THEN '99_retail_sample.mp3'
        ELSE LPAD(c.segment_order::TEXT, 2, '0') || '_unknown.mp3'
    END AS export_filename
FROM chapters c
WHERE c.segment_order IS NOT NULL
ORDER BY c.job_id, c.segment_order;

COMMENT ON VIEW job_segments_ordered IS 'All job segments in Findaway export order with generated filenames (includes bonus/teaser support)';


-- ============================================================================
-- UPDATE COLUMN COMMENTS
-- ============================================================================

COMMENT ON COLUMN chapters.segment_order IS 'Findaway segment order: 0=opening, 1-9=front matter, 10-79=body chapters, 80-89=back matter, 90-94=bonus chapters, 95-97=teaser chapters, 98=closing, 99=retail sample';


-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
