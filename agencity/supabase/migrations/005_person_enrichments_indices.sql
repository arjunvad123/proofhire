-- Migration: Add indices and triggers for person_enrichments table
-- Purpose: Optimize enrichment queries and automatic timestamp updates
-- Date: 2026-02-14

-- Add indices for efficient enrichment queries
CREATE INDEX IF NOT EXISTS idx_person_enrichments_person_id
  ON person_enrichments(person_id);

CREATE INDEX IF NOT EXISTS idx_person_enrichments_source
  ON person_enrichments(enrichment_source);

-- Add index for checking freshness of enrichments
CREATE INDEX IF NOT EXISTS idx_person_enrichments_updated_at
  ON person_enrichments(updated_at);

-- Add updated_at trigger function (if not already exists)
CREATE OR REPLACE FUNCTION update_person_enrichments_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update updated_at timestamp
DROP TRIGGER IF EXISTS trigger_person_enrichments_updated_at ON person_enrichments;

CREATE TRIGGER trigger_person_enrichments_updated_at
  BEFORE UPDATE ON person_enrichments
  FOR EACH ROW
  EXECUTE FUNCTION update_person_enrichments_updated_at();

-- Add comments for documentation
COMMENT ON INDEX idx_person_enrichments_person_id IS 'Fast lookups for person enrichment data';
COMMENT ON INDEX idx_person_enrichments_source IS 'Filter by enrichment source (pdl, manual)';
COMMENT ON INDEX idx_person_enrichments_updated_at IS 'Check enrichment freshness (avoid re-enriching within 30 days)';
