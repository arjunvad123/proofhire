-- ============================================================================
-- INTELLIGENCE SYSTEM TABLES
-- V3: Network-driven discovery through activation and recommendations
-- ============================================================================

-- ----------------------------------------------------------------------------
-- ACTIVATION REQUESTS (Track asks to network)
-- "Who's the best ML engineer you've ever worked with?"
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS activation_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    target_person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,

    -- Request details
    template_type TEXT NOT NULL,  -- 'reverse_reference', 'referral_request', 'community_access'
    message_content TEXT NOT NULL,

    -- Metadata (role asked about, skills, priority, etc.)
    metadata JSONB DEFAULT '{}',

    -- Status tracking
    status TEXT DEFAULT 'pending',  -- 'pending', 'sent', 'responded_with_rec', 'responded_no_rec', 'no_response'
    sent_at TIMESTAMPTZ,
    responded_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_activation_requests_company ON activation_requests(company_id);
CREATE INDEX IF NOT EXISTS idx_activation_requests_target ON activation_requests(target_person_id);
CREATE INDEX IF NOT EXISTS idx_activation_requests_status ON activation_requests(company_id, status);

-- ----------------------------------------------------------------------------
-- RECOMMENDATIONS (Track recommendations from network)
-- When someone says "You should talk to Sarah Chen"
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    -- Who recommended (must be in our network)
    recommender_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    activation_request_id UUID REFERENCES activation_requests(id) ON DELETE SET NULL,

    -- Who was recommended (may not be in our DB yet)
    recommended_name TEXT NOT NULL,
    recommended_linkedin TEXT,
    recommended_email TEXT,
    recommended_context TEXT,  -- "Best ML engineer I worked with at Google"
    recommended_current_company TEXT,
    recommended_current_title TEXT,

    -- Status pipeline
    status TEXT DEFAULT 'new',  -- 'new', 'intro_requested', 'intro_made', 'contacted', 'responded', 'converted', 'declined'

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_recommendations_company ON recommendations(company_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_recommender ON recommendations(recommender_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_status ON recommendations(company_id, status);

-- ----------------------------------------------------------------------------
-- EMPLOYMENT HISTORY (For warm path calculation)
-- Same company + Same time = They know each other
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS employment_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,

    company_name TEXT NOT NULL,
    title TEXT,
    start_date DATE,
    end_date DATE,  -- NULL if current
    is_current BOOLEAN DEFAULT FALSE,

    -- For colleague matching
    normalized_company TEXT,  -- Lowercase, cleaned

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_employment_history_person ON employment_history(person_id);
CREATE INDEX IF NOT EXISTS idx_employment_history_company ON employment_history(normalized_company);
CREATE INDEX IF NOT EXISTS idx_employment_history_dates ON employment_history(normalized_company, start_date, end_date);

-- ----------------------------------------------------------------------------
-- TIMING SIGNALS (Predict who's ready to move)
-- Vesting cliffs, layoffs, manager departures
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS timing_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,

    -- Tenure info
    current_company TEXT,
    tenure_start DATE,
    tenure_months INTEGER,
    vesting_cliff_date DATE,
    months_to_cliff INTEGER,

    -- Signals
    company_had_layoffs BOOLEAN DEFAULT FALSE,
    layoff_date DATE,
    manager_departed BOOLEAN DEFAULT FALSE,
    title_signals TEXT[] DEFAULT '{}',  -- ['consultant', 'advisor', etc.]
    profile_updated_recently BOOLEAN DEFAULT FALSE,

    -- Computed score
    readiness_score FLOAT,
    recommended_action TEXT,
    action_urgency TEXT,  -- 'high', 'medium', 'low', 'wait'

    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(person_id)
);

CREATE INDEX IF NOT EXISTS idx_timing_signals_readiness ON timing_signals(readiness_score DESC);
CREATE INDEX IF NOT EXISTS idx_timing_signals_urgency ON timing_signals(action_urgency);

-- ----------------------------------------------------------------------------
-- COMPANY EVENTS (Monitor layoffs, funding, etc.)
-- Track events affecting companies where network members work
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS company_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    company_name TEXT NOT NULL,
    normalized_name TEXT,

    event_type TEXT NOT NULL,  -- 'layoff', 'funding', 'acquisition', 'exec_departure', 'bad_earnings'
    event_date DATE,
    event_details JSONB DEFAULT '{}',  -- Flexible storage for event-specific data

    source_url TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_company_events_company ON company_events(normalized_name);
CREATE INDEX IF NOT EXISTS idx_company_events_type ON company_events(event_type);
CREATE INDEX IF NOT EXISTS idx_company_events_date ON company_events(event_date DESC);

-- ----------------------------------------------------------------------------
-- WARM PATHS (Pre-computed paths to candidates)
-- Via: employment overlap, school overlap, recommendations
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS warm_paths (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    -- The candidate (may not be in our DB yet)
    candidate_id UUID REFERENCES people(id) ON DELETE CASCADE,  -- NULL if not in DB
    candidate_name TEXT,
    candidate_linkedin TEXT,

    -- The connection path
    via_person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    path_type TEXT NOT NULL,  -- 'colleague', 'school', 'github', 'recommendation'
    relationship_description TEXT,
    overlap_details JSONB DEFAULT '{}',  -- Company, dates, etc.

    warmth_score FLOAT NOT NULL,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_warm_paths_company ON warm_paths(company_id);
CREATE INDEX IF NOT EXISTS idx_warm_paths_via ON warm_paths(via_person_id);
CREATE INDEX IF NOT EXISTS idx_warm_paths_warmth ON warm_paths(company_id, warmth_score DESC);

-- ----------------------------------------------------------------------------
-- ENABLE RLS
-- ----------------------------------------------------------------------------
ALTER TABLE activation_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE employment_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE timing_signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE company_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE warm_paths ENABLE ROW LEVEL SECURITY;

-- Service role policies
CREATE POLICY "Allow all for service role" ON activation_requests FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON recommendations FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON employment_history FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON timing_signals FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON company_events FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON warm_paths FOR ALL USING (true);
