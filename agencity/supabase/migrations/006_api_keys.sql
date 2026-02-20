-- ============================================================================
-- API KEYS TABLE
-- Stripe-style API key authentication for multi-tenant access
-- ============================================================================

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    -- Key storage (only hash stored, never raw key)
    key_hash TEXT NOT NULL,
    key_prefix TEXT NOT NULL,       -- "ag_live_abc1..." for display/lookup

    -- Metadata
    name TEXT DEFAULT 'default',
    scopes TEXT[] DEFAULT '{read,write}',

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Lookup by prefix (used during auth verification)
CREATE INDEX idx_api_keys_prefix ON api_keys(key_prefix);

-- List keys for a company
CREATE INDEX idx_api_keys_company ON api_keys(company_id);

-- Active keys only
CREATE INDEX idx_api_keys_active ON api_keys(company_id, is_active) WHERE is_active = TRUE;

-- RLS
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all for service role" ON api_keys FOR ALL USING (true);
