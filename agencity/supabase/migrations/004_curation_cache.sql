-- Add curation cache table
-- Migration: 004_curation_cache.sql
-- Created: 2026-02-14

-- Table to cache curated candidate shortlists per role
CREATE TABLE IF NOT EXISTS curation_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,

  -- Cached results
  shortlist JSONB NOT NULL,
  metadata JSONB NOT NULL,

  -- Cache metadata
  total_searched INTEGER NOT NULL DEFAULT 0,
  enriched_count INTEGER NOT NULL DEFAULT 0,
  avg_match_score FLOAT NOT NULL DEFAULT 0,

  -- Timestamps
  generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL DEFAULT NOW() + INTERVAL '24 hours',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- Ensure one cache per role
  UNIQUE(company_id, role_id)
);

-- Index for efficient lookups
CREATE INDEX IF NOT EXISTS idx_curation_cache_lookup ON curation_cache(company_id, role_id);
CREATE INDEX IF NOT EXISTS idx_curation_cache_expiry ON curation_cache(expires_at);

-- Add status field to roles table to track curation status
ALTER TABLE roles ADD COLUMN IF NOT EXISTS curation_status VARCHAR(20) DEFAULT 'pending'
  CHECK (curation_status IN ('pending', 'processing', 'cached', 'failed'));

ALTER TABLE roles ADD COLUMN IF NOT EXISTS last_curated_at TIMESTAMPTZ;

-- Index for finding roles that need curation
CREATE INDEX IF NOT EXISTS idx_roles_curation_status ON roles(company_id, curation_status);

-- Add trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_curation_cache_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger if exists, then recreate
DROP TRIGGER IF EXISTS trigger_update_curation_cache_updated_at ON curation_cache;

CREATE TRIGGER trigger_update_curation_cache_updated_at
  BEFORE UPDATE ON curation_cache
  FOR EACH ROW
  EXECUTE FUNCTION update_curation_cache_updated_at();

-- Comment for documentation
COMMENT ON TABLE curation_cache IS 'Cached curated candidate shortlists per role to avoid re-enrichment';
COMMENT ON COLUMN curation_cache.shortlist IS 'JSON array of curated candidates with full context';
COMMENT ON COLUMN curation_cache.metadata IS 'Curation metadata including processing stats';
COMMENT ON COLUMN curation_cache.expires_at IS 'Cache expiry time (default: 24 hours)';
COMMENT ON COLUMN roles.curation_status IS 'Status of curation: pending, processing, cached, or failed';
