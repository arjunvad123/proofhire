-- ============================================================================
-- AGENCITY ↔ PROOFHIRE INTEGRATION TABLES
-- Migration: 002_integration_tables
-- ============================================================================

-- ----------------------------------------------------------------------------
-- CANDIDATE LINKAGES (Track Agencity → ProofHire connections)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS candidate_linkages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    agencity_candidate_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    agencity_search_id UUID,  -- Optional: reference to search that found this candidate

    -- ProofHire references (stored as strings since ProofHire uses different ID format)
    proofhire_application_id TEXT NOT NULL,
    proofhire_role_id TEXT NOT NULL,

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'linked',
    -- Possible statuses:
    --   'linked' - Just created the connection
    --   'simulation_pending' - Candidate invited, waiting for them to start
    --   'simulation_in_progress' - Candidate is taking the simulation
    --   'simulation_complete' - Simulation finished, brief being generated
    --   'evaluated' - Brief generated and ready for founder review

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_agencity_candidate UNIQUE(agencity_candidate_id),
    CONSTRAINT unique_proofhire_application UNIQUE(proofhire_application_id)
);

-- Indexes for quick lookups
CREATE INDEX IF NOT EXISTS idx_linkages_company ON candidate_linkages(company_id);
CREATE INDEX IF NOT EXISTS idx_linkages_status ON candidate_linkages(status);
CREATE INDEX IF NOT EXISTS idx_linkages_proofhire_app ON candidate_linkages(proofhire_application_id);
CREATE INDEX IF NOT EXISTS idx_linkages_created_at ON candidate_linkages(created_at DESC);

-- ----------------------------------------------------------------------------
-- FEEDBACK ACTIONS (Track hiring decisions for RL training)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS feedback_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    candidate_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    search_id UUID,  -- Optional: reference to search that found this candidate

    -- Action details
    action TEXT NOT NULL,
    -- Possible actions:
    --   'hired' - Candidate was hired
    --   'interviewed' - Progressed to interview stage
    --   'contacted' - Founder reached out
    --   'saved' - Founder saved for later
    --   'rejected' - Candidate rejected
    --   'ignored' - No action taken

    -- ProofHire integration data
    proofhire_application_id TEXT,
    proofhire_score INTEGER,  -- 0-100 score from ProofHire brief

    -- Additional context
    notes TEXT,
    metadata JSONB DEFAULT '{}',

    -- Timestamp
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for analytics queries
CREATE INDEX IF NOT EXISTS idx_feedback_company ON feedback_actions(company_id);
CREATE INDEX IF NOT EXISTS idx_feedback_candidate ON feedback_actions(candidate_id);
CREATE INDEX IF NOT EXISTS idx_feedback_search ON feedback_actions(search_id);
CREATE INDEX IF NOT EXISTS idx_feedback_action ON feedback_actions(action);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback_actions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_proofhire_app ON feedback_actions(proofhire_application_id);

-- ----------------------------------------------------------------------------
-- ROW LEVEL SECURITY
-- ----------------------------------------------------------------------------
ALTER TABLE candidate_linkages ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback_actions ENABLE ROW LEVEL SECURITY;

-- For now, allow all access (service role key)
-- In production, add proper policies based on user authentication
CREATE POLICY "Allow all for service role" ON candidate_linkages FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON feedback_actions FOR ALL USING (true);

-- ----------------------------------------------------------------------------
-- TRIGGER FOR AUTO-UPDATING TIMESTAMPS
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_linkages_updated_at
    BEFORE UPDATE ON candidate_linkages
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
