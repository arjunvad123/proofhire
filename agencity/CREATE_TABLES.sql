-- ============================================================================
-- UNIFY DATABASE: Add Profile System Tables to Supabase
-- ============================================================================
-- Instructions:
-- 1. Go to https://supabase.com/dashboard/project/npqjuljzpjvcqmrgpyqj/editor
-- 2. Click "New query"
-- 3. Copy and paste this ENTIRE file
-- 4. Click "Run" or press Cmd+Enter
-- ============================================================================

-- Table 1: Organization Profiles
-- Stores company context from Slack conversations or manual imports
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS org_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Slack workspace identification (for Slack bot integration)
    slack_workspace_id VARCHAR(255) UNIQUE,
    slack_workspace_name VARCHAR(255),

    -- Supabase user identification (link to companies table)
    supabase_user_id VARCHAR(255),
    company_id UUID,  -- Reference to companies table

    -- Company context
    company_name VARCHAR(255),
    company_hq_location VARCHAR(255),
    company_size INTEGER,
    company_stage VARCHAR(100),  -- "seed", "series-a", etc.
    industry VARCHAR(255),
    product_description TEXT,

    -- Operating style (aligned with ProofHire COM)
    pace VARCHAR(50),
    quality_bar VARCHAR(50),
    ambiguity VARCHAR(50),
    tech_stack JSONB DEFAULT '[]'::jsonb,

    -- Hiring preferences
    hiring_priorities JSONB DEFAULT '[]'::jsonb,
    preferred_schools JSONB DEFAULT '[]'::jsonb,
    preferred_companies JSONB DEFAULT '[]'::jsonb,
    avoid_patterns JSONB DEFAULT '[]'::jsonb,

    -- Additional context (flexible storage)
    extra_context JSONB DEFAULT '{}'::jsonb,

    -- Metadata
    onboarding_complete BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_org_profiles_slack_workspace_id
    ON org_profiles(slack_workspace_id);

CREATE INDEX IF NOT EXISTS idx_org_profiles_supabase_user_id
    ON org_profiles(supabase_user_id);

CREATE INDEX IF NOT EXISTS idx_org_profiles_company_id
    ON org_profiles(company_id);


-- Table 2: Organization Knowledge
-- Learned facts about companies from conversations
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS org_knowledge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_profile_id UUID NOT NULL REFERENCES org_profiles(id) ON DELETE CASCADE,

    -- Knowledge content
    category VARCHAR(100) NOT NULL,  -- "technical_challenge", "cultural_fit", etc.
    content TEXT NOT NULL,
    source VARCHAR(100) NOT NULL,  -- "slack", "manual", "api", etc.
    confidence FLOAT DEFAULT 1.0,
    context_json JSONB DEFAULT '{}'::jsonb,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by_slack_user VARCHAR(255)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_org_knowledge_org_profile_id
    ON org_knowledge(org_profile_id);

CREATE INDEX IF NOT EXISTS idx_org_knowledge_category
    ON org_knowledge(category);


-- Table 3: Hiring Priorities (Optional - can use org_profiles.hiring_priorities JSONB instead)
-- Role-specific hiring criteria
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hiring_priorities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_profile_id UUID NOT NULL REFERENCES org_profiles(id) ON DELETE CASCADE,

    -- Priority details
    role_title VARCHAR(255) NOT NULL,
    must_haves TEXT[] DEFAULT '{}',
    nice_to_haves TEXT[] DEFAULT '{}',
    dealbreakers TEXT[] DEFAULT '{}',

    -- Context
    specific_work TEXT,
    success_criteria TEXT,
    context_json JSONB DEFAULT '{}'::jsonb,

    -- Metadata
    priority_level INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index
CREATE INDEX IF NOT EXISTS idx_hiring_priorities_org_profile_id
    ON hiring_priorities(org_profile_id);


-- ============================================================================
-- ENABLE ROW LEVEL SECURITY (RLS) - Optional but Recommended
-- ============================================================================
-- This ensures users can only access their own data

ALTER TABLE org_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE org_knowledge ENABLE ROW LEVEL SECURITY;
ALTER TABLE hiring_priorities ENABLE ROW LEVEL SECURITY;

-- RLS Policies (adjust based on your auth setup)
-- For now, allow service role to access everything
CREATE POLICY "Enable all for service role" ON org_profiles
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Enable all for service role" ON org_knowledge
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Enable all for service role" ON hiring_priorities
    FOR ALL USING (auth.role() = 'service_role');


-- ============================================================================
-- VERIFICATION
-- ============================================================================
-- Check that tables were created successfully

DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_name IN ('org_profiles', 'org_knowledge', 'hiring_priorities');

    IF table_count = 3 THEN
        RAISE NOTICE '✅ SUCCESS! All 3 tables created.';
    ELSE
        RAISE NOTICE '⚠️  Only % tables found. Expected 3.', table_count;
    END IF;
END $$;

-- Show table details
SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as columns
FROM information_schema.tables t
WHERE table_schema = 'public'
  AND table_name IN ('org_profiles', 'org_knowledge', 'hiring_priorities')
ORDER BY table_name;
