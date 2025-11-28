-- ============================================================================
-- Migration: 0005_cover_art_columns
-- Purpose: Add cover art generation fields to jobs table
-- Created: 2025-11-28
-- ============================================================================

-- Add cover art generation columns to jobs table
ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS generate_cover BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS cover_vibe TEXT,
ADD COLUMN IF NOT EXISTS cover_description TEXT,
ADD COLUMN IF NOT EXISTS cover_image_provider TEXT DEFAULT 'openai',
ADD COLUMN IF NOT EXISTS cover_image_path TEXT,
ADD COLUMN IF NOT EXISTS has_cover BOOLEAN DEFAULT FALSE;

-- Add findaway-specific columns if not present
ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS package_type TEXT,
ADD COLUMN IF NOT EXISTS section_count INTEGER,
ADD COLUMN IF NOT EXISTS manifest_json TEXT,
ADD COLUMN IF NOT EXISTS current_step TEXT;

-- Add mode constraint update for findaway mode
ALTER TABLE jobs
DROP CONSTRAINT IF EXISTS jobs_mode_check;

ALTER TABLE jobs
ADD CONSTRAINT jobs_mode_check
CHECK (mode IN ('single_voice', 'dual_voice', 'findaway'));

-- Comments for documentation
COMMENT ON COLUMN jobs.generate_cover IS 'Whether to generate AI cover art for this audiobook';
COMMENT ON COLUMN jobs.cover_vibe IS 'Visual style/mood for cover (dramatic, minimalist, vintage, etc.)';
COMMENT ON COLUMN jobs.cover_description IS 'Custom user description for cover art';
COMMENT ON COLUMN jobs.cover_image_provider IS 'Provider for cover generation (openai, banana, etc.)';
COMMENT ON COLUMN jobs.cover_image_path IS 'R2 path to generated cover image';
COMMENT ON COLUMN jobs.has_cover IS 'Whether cover has been generated successfully';
COMMENT ON COLUMN jobs.package_type IS 'Package type for Findaway mode (findaway)';
COMMENT ON COLUMN jobs.section_count IS 'Number of sections in Findaway package';
COMMENT ON COLUMN jobs.manifest_json IS 'JSON manifest for Findaway package';
COMMENT ON COLUMN jobs.current_step IS 'Current processing step description';

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
