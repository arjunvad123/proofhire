-- External Candidates Cache
-- Caches search results from Firecrawl/Clado/Apollo to avoid re-hitting APIs

CREATE TABLE external_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    linkedin_url TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    current_title TEXT,
    current_company TEXT,
    headline TEXT,
    location TEXT,
    skills JSONB DEFAULT '[]',
    experience JSONB DEFAULT '[]',
    education JSONB DEFAULT '[]',
    github_url TEXT,
    twitter_url TEXT,
    personal_website TEXT,
    -- Source tracking
    discovery_source TEXT NOT NULL,       -- 'firecrawl', 'clado', 'apollo'
    enrichment_source TEXT,               -- 'clado_profile', 'clado_scrape', null
    enrichment_data JSONB,                -- raw enrichment payload
    -- Research
    research_data JSONB,                  -- structured research results
    research_confidence REAL DEFAULT 0,   -- 0-1
    last_researched_at TIMESTAMPTZ,
    -- Timestamps
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ext_candidates_linkedin ON external_candidates(linkedin_url);
CREATE INDEX idx_ext_candidates_name ON external_candidates(full_name);
CREATE INDEX idx_ext_candidates_company ON external_candidates(current_company);
CREATE INDEX idx_ext_candidates_updated ON external_candidates(updated_at);

-- Enable RLS
ALTER TABLE external_candidates ENABLE ROW LEVEL SECURITY;

-- Allow service role full access (this table is accessed server-side only)
CREATE POLICY "Service role full access on external_candidates"
    ON external_candidates
    FOR ALL
    USING (true)
    WITH CHECK (true);
