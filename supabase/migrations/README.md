# Supabase Migrations

## Status: 🚧 Placeholder

This directory will contain SQL migration files for the Supabase database schema.

### Planned Tables:

**users** (managed by Supabase Auth)
- Standard Supabase auth.users table

**jobs**
- `id` (uuid, primary key)
- `user_id` (uuid, foreign key to auth.users)
- `status` (enum: pending, processing, completed, failed)
- `manuscript_path` (text)
- `audiobook_path` (text)
- `voice_config` (jsonb)
- `created_at` (timestamp)
- `updated_at` (timestamp)

**job_files**
- `id` (uuid, primary key)
- `job_id` (uuid, foreign key to jobs)
- `file_type` (enum: manuscript, audio_chunk, final_audiobook)
- `storage_path` (text)
- `size_bytes` (bigint)
- `created_at` (timestamp)

### Storage Buckets:
- `manuscripts` - Uploaded manuscript files
- `audiobooks` - Generated audiobook files

### Row Level Security (RLS):
- Users can only access their own jobs
- Service role can access all jobs

---
**Last Updated:** 2025-11-22
