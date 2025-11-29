-- ============================================================================
-- Migration: 0006_multilingual_tts_columns
-- Purpose: Add multilingual TTS fields to jobs table for Gemini TTS support
-- Created: 2025-11-28
-- ============================================================================

-- Add multilingual TTS columns to jobs table
ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS input_language_code TEXT DEFAULT 'en-US',
ADD COLUMN IF NOT EXISTS output_language_code TEXT,
ADD COLUMN IF NOT EXISTS voice_preset_id TEXT,
ADD COLUMN IF NOT EXISTS emotion_style_prompt TEXT;

-- Update tts_provider constraint to include 'google' and 'gemini'
ALTER TABLE jobs
DROP CONSTRAINT IF EXISTS jobs_tts_provider_check;

ALTER TABLE jobs
ADD CONSTRAINT jobs_tts_provider_check
CHECK (tts_provider IN ('openai', 'elevenlabs', 'inworld', 'google', 'gemini'));

-- Comments for documentation
COMMENT ON COLUMN jobs.input_language_code IS 'Language code of the input manuscript (e.g., en-US, es-ES, auto for auto-detect)';
COMMENT ON COLUMN jobs.output_language_code IS 'Target language for TTS output (if different from input, text will be translated)';
COMMENT ON COLUMN jobs.voice_preset_id IS 'Gemini TTS voice preset ID (e.g., narrator_female_warm, romantic_male)';
COMMENT ON COLUMN jobs.emotion_style_prompt IS 'Natural language style/emotion instructions for TTS (e.g., soft, romantic, intimate)';

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
