-- Add warming status tracking to linkedin_sessions
-- This tracks whether a session has been "warmed" (completed initial CAPTCHA/verification)

ALTER TABLE linkedin_sessions
ADD COLUMN IF NOT EXISTS profile_id TEXT,
ADD COLUMN IF NOT EXISTS warming_status TEXT DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS warmed_at TIMESTAMPTZ;

-- Index for querying by warming status
CREATE INDEX IF NOT EXISTS idx_linkedin_sessions_warming_status
ON linkedin_sessions(warming_status);

-- Comment for documentation
COMMENT ON COLUMN linkedin_sessions.profile_id IS 'Browser profile ID (hash of email) for persistent session isolation';
COMMENT ON COLUMN linkedin_sessions.warming_status IS 'Warming status: pending, warming, warmed, failed';
COMMENT ON COLUMN linkedin_sessions.warmed_at IS 'Timestamp when session was successfully warmed';
