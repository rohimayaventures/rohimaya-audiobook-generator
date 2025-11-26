-- ============================================================================
-- Rohimaya Audiobook Generator - Storage Buckets
-- Migration: 0002_create_storage_buckets
-- Created: 2025-11-22
-- ============================================================================

-- ============================================================================
-- STORAGE BUCKET: manuscripts
-- Purpose: Store uploaded manuscript files (TXT, DOCX, PDF)
-- ============================================================================

INSERT INTO storage.buckets (id, name, public)
VALUES ('manuscripts', 'manuscripts', false)
ON CONFLICT (id) DO NOTHING;

-- Storage policy: Users can only upload to their own folder
CREATE POLICY "Users can upload their own manuscripts"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
    bucket_id = 'manuscripts' AND
    (storage.foldername(name))[1] = auth.uid()::text
);

-- Storage policy: Users can read their own manuscripts
CREATE POLICY "Users can read their own manuscripts"
ON storage.objects FOR SELECT
TO authenticated
USING (
    bucket_id = 'manuscripts' AND
    (storage.foldername(name))[1] = auth.uid()::text
);

-- Storage policy: Users can delete their own manuscripts
CREATE POLICY "Users can delete their own manuscripts"
ON storage.objects FOR DELETE
TO authenticated
USING (
    bucket_id = 'manuscripts' AND
    (storage.foldername(name))[1] = auth.uid()::text
);

COMMENT ON TABLE storage.buckets IS 'manuscripts: Private bucket for uploaded book manuscripts';


-- ============================================================================
-- STORAGE BUCKET: audiobooks
-- Purpose: Store generated audiobook files (MP3, WAV, FLAC, M4B)
-- ============================================================================

INSERT INTO storage.buckets (id, name, public)
VALUES ('audiobooks', 'audiobooks', false)
ON CONFLICT (id) DO NOTHING;

-- Storage policy: Users can read their own audiobooks
CREATE POLICY "Users can read their own audiobooks"
ON storage.objects FOR SELECT
TO authenticated
USING (
    bucket_id = 'audiobooks' AND
    (storage.foldername(name))[1] = auth.uid()::text
);

-- Storage policy: Backend service can write to any user's audiobook folder
-- (using service role key, not user auth)
CREATE POLICY "Service can write to audiobooks bucket"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'audiobooks');

-- Storage policy: Service can update audiobook files
CREATE POLICY "Service can update audiobooks bucket"
ON storage.objects FOR UPDATE
TO authenticated
USING (bucket_id = 'audiobooks');

-- Storage policy: Users can delete their own audiobooks
CREATE POLICY "Users can delete their own audiobooks"
ON storage.objects FOR DELETE
TO authenticated
USING (
    bucket_id = 'audiobooks' AND
    (storage.foldername(name))[1] = auth.uid()::text
);

COMMENT ON TABLE storage.buckets IS 'audiobooks: Private bucket for generated audiobook files';


-- ============================================================================
-- STORAGE BUCKET CONFIGURATION
-- ============================================================================

-- Set file size limits (adjust as needed)
-- manuscripts: 50 MB per file (generous for text files)
-- audiobooks: 500 MB per file (full-length audiobooks can be large)

-- Note: File size limits are typically configured in Supabase Dashboard
-- under Storage > [bucket] > Settings, not via SQL.

-- Recommended limits:
-- - manuscripts: 50 MB (text files are small)
-- - audiobooks: 500 MB (hours of audio)


-- ============================================================================
-- FOLDER STRUCTURE (Documented, not enforced)
-- ============================================================================

-- manuscripts/
-- ├── {user_id}/
-- │   ├── {manuscript_filename}.txt
-- │   ├── {manuscript_filename}.docx
-- │   └── {manuscript_filename}.pdf
--
-- audiobooks/
-- ├── {user_id}/
-- │   ├── {job_id}/
-- │   │   ├── chunks/
-- │   │   │   ├── ch1_part1.mp3
-- │   │   │   ├── ch1_part2.mp3
-- │   │   │   └── ...
-- │   │   ├── chapters/
-- │   │   │   ├── CHAPTER_01.mp3
-- │   │   │   ├── CHAPTER_02.mp3
-- │   │   │   └── ...
-- │   │   └── final/
-- │   │       └── {title}_COMPLETE.mp3


-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
