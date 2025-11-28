-- Google Drive OAuth Tokens Table
-- Stores encrypted OAuth tokens for Google Drive integration per user

CREATE TABLE IF NOT EXISTS google_drive_tokens (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    access_token TEXT,
    refresh_token TEXT,
    token_type TEXT DEFAULT 'Bearer',
    expires_in INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Enable RLS
ALTER TABLE google_drive_tokens ENABLE ROW LEVEL SECURITY;

-- Users can only see their own tokens
CREATE POLICY "Users can view own Google Drive tokens"
ON google_drive_tokens FOR SELECT
USING (auth.uid() = user_id);

-- Users can insert their own tokens
CREATE POLICY "Users can insert own Google Drive tokens"
ON google_drive_tokens FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Users can update their own tokens
CREATE POLICY "Users can update own Google Drive tokens"
ON google_drive_tokens FOR UPDATE
USING (auth.uid() = user_id);

-- Users can delete their own tokens
CREATE POLICY "Users can delete own Google Drive tokens"
ON google_drive_tokens FOR DELETE
USING (auth.uid() = user_id);

-- Service role can manage all tokens (for backend operations)
CREATE POLICY "Service role can manage all tokens"
ON google_drive_tokens FOR ALL
USING (auth.jwt() ->> 'role' = 'service_role');

-- Index for quick lookups
CREATE INDEX IF NOT EXISTS idx_google_drive_tokens_user_id ON google_drive_tokens(user_id);

-- Add trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_google_drive_tokens_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER google_drive_tokens_updated_at
    BEFORE UPDATE ON google_drive_tokens
    FOR EACH ROW
    EXECUTE FUNCTION update_google_drive_tokens_updated_at();
