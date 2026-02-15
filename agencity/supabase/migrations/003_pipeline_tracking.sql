-- Add pipeline tracking to people table
-- Migration: 003_pipeline_tracking.sql
-- Created: 2026-02-14

-- Add pipeline status field with constraint
ALTER TABLE people ADD COLUMN IF NOT EXISTS pipeline_status VARCHAR(20)
  CHECK (pipeline_status IN ('sourced', 'contacted', 'scheduled'));

-- Add timestamp fields for pipeline tracking
ALTER TABLE people ADD COLUMN IF NOT EXISTS contacted_at TIMESTAMPTZ;
ALTER TABLE people ADD COLUMN IF NOT EXISTS scheduled_at TIMESTAMPTZ;

-- Index for efficient pipeline queries
CREATE INDEX IF NOT EXISTS idx_people_pipeline_status ON people(company_id, pipeline_status)
  WHERE pipeline_status IS NOT NULL;

-- Set default pipeline_status for existing records that came from network
UPDATE people
SET pipeline_status = 'sourced'
WHERE pipeline_status IS NULL
  AND (is_from_network = TRUE OR is_from_existing_db = TRUE);

-- Add comment for documentation
COMMENT ON COLUMN people.pipeline_status IS 'Pipeline stage: sourced, contacted, or scheduled';
COMMENT ON COLUMN people.contacted_at IS 'Timestamp when candidate was marked as contacted';
COMMENT ON COLUMN people.scheduled_at IS 'Timestamp when candidate was marked as scheduled';
