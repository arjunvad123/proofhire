-- Migration: LinkedIn Automation System
-- Version: 006
-- Description: Tables for LinkedIn session management, connection extraction, and DM automation

-- LinkedIn Sessions
-- Stores encrypted session cookies for authenticated LinkedIn access
CREATE TABLE IF NOT EXISTS linkedin_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    user_id UUID,  -- Can reference users table if exists

    -- Encrypted session data (Fernet/AES-128)
    cookies_encrypted TEXT NOT NULL,

    -- Session metadata
    linkedin_user_id TEXT,
    linkedin_name TEXT,
    user_location TEXT,
    user_timezone TEXT DEFAULT 'UTC',

    -- Health tracking
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'expired', 'disconnected')),
    health TEXT DEFAULT 'healthy' CHECK (health IN ('healthy', 'warning', 'restricted')),

    -- Usage stats
    connections_extracted INTEGER DEFAULT 0,
    profiles_enriched INTEGER DEFAULT 0,
    messages_sent INTEGER DEFAULT 0,

    -- Rate limiting (reset daily)
    daily_message_count INTEGER DEFAULT 0,
    daily_enrichment_count INTEGER DEFAULT 0,
    last_activity_at TIMESTAMPTZ,

    -- Timestamps
    connected_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    paused_until TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_linkedin_sessions_company ON linkedin_sessions(company_id);
CREATE INDEX IF NOT EXISTS idx_linkedin_sessions_status ON linkedin_sessions(status);
CREATE INDEX IF NOT EXISTS idx_linkedin_sessions_user ON linkedin_sessions(company_id, user_id);


-- Connection extraction jobs
-- Tracks background jobs that extract connections from LinkedIn
CREATE TABLE IF NOT EXISTS connection_extraction_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES linkedin_sessions(id) ON DELETE CASCADE,

    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),

    -- Progress tracking
    connections_found INTEGER DEFAULT 0,
    last_scroll_position INTEGER DEFAULT 0,

    -- Results
    completed_at TIMESTAMPTZ,
    error_message TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_extraction_jobs_session ON connection_extraction_jobs(session_id);
CREATE INDEX IF NOT EXISTS idx_extraction_jobs_status ON connection_extraction_jobs(status);


-- LinkedIn connections
-- Stores extracted connections before full enrichment
CREATE TABLE IF NOT EXISTS linkedin_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    session_id UUID REFERENCES linkedin_sessions(id),

    -- Basic data from connections list (before enrichment)
    linkedin_url TEXT NOT NULL,
    full_name TEXT,
    current_title TEXT,
    current_company TEXT,
    headline TEXT,
    location TEXT,
    profile_image_url TEXT,
    connected_at_text TEXT,  -- "Connected 3 months ago"

    -- Priority scoring (Phase 3)
    priority_score INTEGER DEFAULT 0,
    priority_tier TEXT CHECK (priority_tier IN ('tier_1', 'tier_2', 'tier_3')),

    -- Enrichment status
    enrichment_status TEXT DEFAULT 'pending' CHECK (
        enrichment_status IN ('pending', 'queued', 'processing', 'completed', 'failed', 'skipped')
    ),
    enriched_at TIMESTAMPTZ,

    -- Link to people table after enrichment
    person_id UUID REFERENCES people(id),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Ensure unique LinkedIn URL per company
    UNIQUE(company_id, linkedin_url)
);

CREATE INDEX IF NOT EXISTS idx_linkedin_connections_company ON linkedin_connections(company_id);
CREATE INDEX IF NOT EXISTS idx_linkedin_connections_priority ON linkedin_connections(priority_tier, priority_score DESC);
CREATE INDEX IF NOT EXISTS idx_linkedin_connections_enrichment ON linkedin_connections(enrichment_status);
CREATE INDEX IF NOT EXISTS idx_linkedin_connections_url ON linkedin_connections(linkedin_url);


-- Enrichment queue
-- Queue for profile enrichment (uses scraper pool, not user session)
CREATE TABLE IF NOT EXISTS enrichment_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID REFERENCES linkedin_connections(id) ON DELETE CASCADE,
    linkedin_url TEXT NOT NULL,

    -- Assignment (which scraper account is processing this)
    scraper_account_id UUID,  -- REFERENCES scraper_accounts(id) - created below

    -- Status
    status TEXT DEFAULT 'pending' CHECK (
        status IN ('pending', 'processing', 'completed', 'failed', 'retry')
    ),
    priority INTEGER DEFAULT 0,  -- Higher = process first
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,

    -- Results
    enrichment_data JSONB,
    error_message TEXT,

    -- Timing
    scheduled_for TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_enrichment_queue_status ON enrichment_queue(status, priority DESC, scheduled_for);
CREATE INDEX IF NOT EXISTS idx_enrichment_queue_scraper ON enrichment_queue(scraper_account_id, status);


-- Scraper account pool
-- Disposable LinkedIn accounts for profile enrichment (NOT user accounts)
CREATE TABLE IF NOT EXISTS scraper_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Credentials (encrypted)
    email_encrypted TEXT NOT NULL,
    password_encrypted TEXT NOT NULL,
    cookies_encrypted TEXT,

    -- Proxy assignment
    proxy_location TEXT,  -- us-ca, us-ny, gb-london, etc.
    proxy_url_encrypted TEXT,

    -- Status
    status TEXT DEFAULT 'aging' CHECK (
        status IN ('aging', 'active', 'warned', 'banned', 'retired')
    ),

    -- Usage tracking
    profiles_scraped_today INTEGER DEFAULT 0,
    profiles_scraped_total INTEGER DEFAULT 0,
    last_used_at TIMESTAMPTZ,

    -- Health monitoring
    consecutive_failures INTEGER DEFAULT 0,
    last_warning_at TIMESTAMPTZ,
    banned_at TIMESTAMPTZ,

    -- Lifecycle
    created_at TIMESTAMPTZ DEFAULT NOW(),
    activated_at TIMESTAMPTZ,  -- When it becomes ready (after aging period)

    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scraper_accounts_status ON scraper_accounts(status);


-- Add foreign key for enrichment_queue -> scraper_accounts
ALTER TABLE enrichment_queue
    ADD CONSTRAINT fk_enrichment_scraper
    FOREIGN KEY (scraper_account_id)
    REFERENCES scraper_accounts(id)
    ON DELETE SET NULL;


-- DM automation queue
-- Queue for sending LinkedIn DMs (uses user session with safe limits)
CREATE TABLE IF NOT EXISTS dm_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES linkedin_sessions(id) ON DELETE CASCADE,
    connection_id UUID REFERENCES linkedin_connections(id),
    role_id UUID,  -- REFERENCES roles(id) if exists

    -- Target
    linkedin_url TEXT NOT NULL,
    recipient_name TEXT,

    -- Message
    message_template TEXT,
    personalized_message TEXT NOT NULL,

    -- Status
    status TEXT DEFAULT 'pending' CHECK (
        status IN ('pending', 'approved', 'scheduled', 'sending', 'sent', 'failed', 'cancelled')
    ),

    -- User approval (required before sending)
    approved_by UUID,
    approved_at TIMESTAMPTZ,

    -- Sending
    scheduled_for TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    error_message TEXT,

    -- Response tracking
    response_received BOOLEAN DEFAULT FALSE,
    response_at TIMESTAMPTZ,
    response_snippet TEXT,  -- First 200 chars of response

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dm_queue_session ON dm_queue(session_id, status);
CREATE INDEX IF NOT EXISTS idx_dm_queue_status ON dm_queue(status, scheduled_for);


-- RLS Policies (Row Level Security)
-- Enable RLS on all tables
ALTER TABLE linkedin_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE connection_extraction_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE linkedin_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE enrichment_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE dm_queue ENABLE ROW LEVEL SECURITY;

-- Service role can access all (for backend)
-- These policies allow the service key to access everything
CREATE POLICY "Service role access for linkedin_sessions"
    ON linkedin_sessions FOR ALL
    USING (true);

CREATE POLICY "Service role access for connection_extraction_jobs"
    ON connection_extraction_jobs FOR ALL
    USING (true);

CREATE POLICY "Service role access for linkedin_connections"
    ON linkedin_connections FOR ALL
    USING (true);

CREATE POLICY "Service role access for enrichment_queue"
    ON enrichment_queue FOR ALL
    USING (true);

CREATE POLICY "Service role access for dm_queue"
    ON dm_queue FOR ALL
    USING (true);

CREATE POLICY "Service role access for scraper_accounts"
    ON scraper_accounts FOR ALL
    USING (true);


-- Comments for documentation
COMMENT ON TABLE linkedin_sessions IS 'Stores encrypted LinkedIn session cookies for authenticated access';
COMMENT ON TABLE linkedin_connections IS 'Extracted LinkedIn connections before full profile enrichment';
COMMENT ON TABLE enrichment_queue IS 'Queue for profile enrichment jobs using scraper pool';
COMMENT ON TABLE scraper_accounts IS 'Pool of disposable LinkedIn accounts for safe enrichment';
COMMENT ON TABLE dm_queue IS 'Queue for LinkedIn DM automation with user approval workflow';
