-- ============================================================================
-- AGENCITY DATA SCHEMA
-- Run this in your Supabase SQL Editor to create the required tables
-- ============================================================================

-- ----------------------------------------------------------------------------
-- COMPANIES (Our clients)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    domain TEXT,

    -- Company context
    stage TEXT,  -- "pre_seed", "seed", "series_a", etc.
    industry TEXT,
    tech_stack TEXT[] DEFAULT '{}',
    team_size INTEGER,

    -- Founder info
    founder_email TEXT NOT NULL,
    founder_name TEXT NOT NULL,
    founder_linkedin_url TEXT,

    -- Onboarding status
    linkedin_imported BOOLEAN DEFAULT FALSE,
    existing_db_imported BOOLEAN DEFAULT FALSE,
    onboarding_complete BOOLEAN DEFAULT FALSE,

    -- Pinecone
    pinecone_namespace TEXT UNIQUE,

    -- Stats
    people_count INTEGER DEFAULT 0,
    roles_count INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_companies_founder_email ON companies(founder_email);

-- ----------------------------------------------------------------------------
-- COMPANY UMOs (What they're looking for)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS company_umos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    -- Ideal candidate profile
    preferred_backgrounds TEXT[] DEFAULT '{}',
    must_have_traits TEXT[] DEFAULT '{}',
    anti_patterns TEXT[] DEFAULT '{}',

    -- Culture
    culture_values TEXT[] DEFAULT '{}',
    work_style TEXT,

    -- Description
    ideal_candidate_description TEXT,

    -- For embedding
    umo_text TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(company_id)
);

-- ----------------------------------------------------------------------------
-- ROLES (Active hiring positions)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    title TEXT NOT NULL,
    level TEXT,  -- "intern", "junior", "mid", "senior", "staff", etc.
    department TEXT,

    -- Requirements
    required_skills TEXT[] DEFAULT '{}',
    preferred_skills TEXT[] DEFAULT '{}',
    years_experience_min INTEGER,
    years_experience_max INTEGER,

    -- Details
    description TEXT,
    location TEXT,
    salary_min INTEGER,
    salary_max INTEGER,

    status TEXT DEFAULT 'active',  -- "active", "paused", "filled", "closed"

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_roles_company ON roles(company_id);

-- ----------------------------------------------------------------------------
-- PEOPLE (The core entity)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS people (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    -- Identity (dedupe keys)
    email TEXT,
    linkedin_url TEXT,
    github_url TEXT,

    -- Basic info
    full_name TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    headline TEXT,
    location TEXT,

    -- Current position
    current_company TEXT,
    current_title TEXT,

    -- Status
    status TEXT DEFAULT 'unknown',  -- "active_seeker", "passive", "not_looking", "unknown"

    -- Scores
    trust_score FLOAT DEFAULT 0.5,
    relevance_score FLOAT,

    -- Flags
    is_from_network BOOLEAN DEFAULT FALSE,
    is_from_existing_db BOOLEAN DEFAULT FALSE,
    is_from_people_search BOOLEAN DEFAULT FALSE,

    -- Pinecone reference
    pinecone_id TEXT,

    -- Timestamps
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_enriched TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_people_company ON people(company_id);
CREATE INDEX IF NOT EXISTS idx_people_email ON people(company_id, email);
CREATE INDEX IF NOT EXISTS idx_people_linkedin ON people(company_id, linkedin_url);

-- Unique constraints for dedupe within a company
CREATE UNIQUE INDEX IF NOT EXISTS idx_people_unique_email
    ON people(company_id, email)
    WHERE email IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_people_unique_linkedin
    ON people(company_id, linkedin_url)
    WHERE linkedin_url IS NOT NULL;

-- ----------------------------------------------------------------------------
-- PERSON ENRICHMENTS (Detailed profile data)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS person_enrichments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,

    -- Skills (normalized)
    skills JSONB DEFAULT '[]',

    -- Work history
    experience JSONB DEFAULT '[]',

    -- Education
    education JSONB DEFAULT '[]',

    -- Projects & signals
    projects JSONB DEFAULT '[]',
    signals JSONB DEFAULT '[]',

    -- Raw enrichment data
    raw_enrichment JSONB,
    enrichment_source TEXT,

    -- Embedding text
    embedding_text TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(person_id)
);

-- ----------------------------------------------------------------------------
-- DATA SOURCES (Track where data came from)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    type TEXT NOT NULL,  -- "linkedin_export", "company_database", "people_search", "manual"
    name TEXT,

    -- File info
    file_url TEXT,
    file_name TEXT,

    -- Stats
    total_records INTEGER DEFAULT 0,
    records_matched INTEGER DEFAULT 0,
    records_created INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,

    -- Status
    status TEXT DEFAULT 'pending',  -- "pending", "processing", "completed", "failed"
    error_message TEXT,

    imported_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_data_sources_company ON data_sources(company_id);

-- ----------------------------------------------------------------------------
-- PERSON SOURCES (Junction: which sources contributed to each person)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS person_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    source_id UUID NOT NULL REFERENCES data_sources(id) ON DELETE CASCADE,

    -- Original data from this source
    original_data JSONB,

    -- For network connections
    connected_on TIMESTAMPTZ,
    connection_strength FLOAT,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(person_id, source_id)
);

CREATE INDEX IF NOT EXISTS idx_person_sources_person ON person_sources(person_id);
CREATE INDEX IF NOT EXISTS idx_person_sources_source ON person_sources(source_id);

-- ----------------------------------------------------------------------------
-- ENRICHMENT QUEUE (Background processing)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS enrichment_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,

    priority INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',  -- "pending", "processing", "completed", "failed"

    attempts INTEGER DEFAULT 0,
    last_error TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_enrichment_queue_status
    ON enrichment_queue(status, priority DESC);

-- ----------------------------------------------------------------------------
-- ROW LEVEL SECURITY (Optional but recommended)
-- ----------------------------------------------------------------------------

-- Enable RLS on all tables
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE company_umos ENABLE ROW LEVEL SECURITY;
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE people ENABLE ROW LEVEL SECURITY;
ALTER TABLE person_enrichments ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE person_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE enrichment_queue ENABLE ROW LEVEL SECURITY;

-- For now, allow all access (service role key)
-- In production, add proper policies based on user authentication

CREATE POLICY "Allow all for service role" ON companies FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON company_umos FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON roles FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON people FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON person_enrichments FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON data_sources FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON person_sources FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON enrichment_queue FOR ALL USING (true);

-- ============================================================================
-- INTELLIGENCE SYSTEM TABLES (V3)
-- Network-driven discovery through activation and recommendations
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
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS employment_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,

    company_name TEXT NOT NULL,
    title TEXT,
    start_date DATE,
    end_date DATE,
    is_current BOOLEAN DEFAULT FALSE,
    normalized_company TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_employment_history_person ON employment_history(person_id);
CREATE INDEX IF NOT EXISTS idx_employment_history_company ON employment_history(normalized_company);

-- ----------------------------------------------------------------------------
-- TIMING SIGNALS (Predict who's ready to move)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS timing_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,

    current_company TEXT,
    tenure_start DATE,
    tenure_months INTEGER,
    vesting_cliff_date DATE,
    months_to_cliff INTEGER,

    company_had_layoffs BOOLEAN DEFAULT FALSE,
    layoff_date DATE,
    manager_departed BOOLEAN DEFAULT FALSE,
    title_signals TEXT[] DEFAULT '{}',
    profile_updated_recently BOOLEAN DEFAULT FALSE,

    readiness_score FLOAT,
    recommended_action TEXT,
    action_urgency TEXT,

    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(person_id)
);

CREATE INDEX IF NOT EXISTS idx_timing_signals_readiness ON timing_signals(readiness_score DESC);

-- ----------------------------------------------------------------------------
-- COMPANY EVENTS (Monitor layoffs, funding, etc.)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS company_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    company_name TEXT NOT NULL,
    normalized_name TEXT,
    event_type TEXT NOT NULL,
    event_date DATE,
    event_details JSONB DEFAULT '{}',
    source_url TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_company_events_company ON company_events(normalized_name);
CREATE INDEX IF NOT EXISTS idx_company_events_type ON company_events(event_type);

-- ----------------------------------------------------------------------------
-- WARM PATHS (Pre-computed paths to candidates)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS warm_paths (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    candidate_id UUID REFERENCES people(id) ON DELETE CASCADE,
    candidate_name TEXT,
    candidate_linkedin TEXT,

    via_person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    path_type TEXT NOT NULL,
    relationship_description TEXT,
    overlap_details JSONB DEFAULT '{}',

    warmth_score FLOAT NOT NULL,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_warm_paths_company ON warm_paths(company_id);
CREATE INDEX IF NOT EXISTS idx_warm_paths_warmth ON warm_paths(company_id, warmth_score DESC);

-- Enable RLS on intelligence tables
ALTER TABLE activation_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE employment_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE timing_signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE company_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE warm_paths ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all for service role" ON activation_requests FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON recommendations FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON employment_history FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON timing_signals FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON company_events FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON warm_paths FOR ALL USING (true);

