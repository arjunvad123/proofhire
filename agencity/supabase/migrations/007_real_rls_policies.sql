-- ============================================================================
-- REAL RLS POLICIES
-- Replace permissive USING (true) with company-scoped policies.
--
-- NOTE: Agencity backend uses the Supabase service role key, which bypasses
-- RLS entirely. These policies serve as defense-in-depth documentation and
-- protect against accidental use of the anon key.
-- ============================================================================

-- Drop all existing permissive policies
DROP POLICY IF EXISTS "Allow all for service role" ON companies;
DROP POLICY IF EXISTS "Allow all for service role" ON company_umos;
DROP POLICY IF EXISTS "Allow all for service role" ON roles;
DROP POLICY IF EXISTS "Allow all for service role" ON people;
DROP POLICY IF EXISTS "Allow all for service role" ON person_enrichments;
DROP POLICY IF EXISTS "Allow all for service role" ON data_sources;
DROP POLICY IF EXISTS "Allow all for service role" ON person_sources;
DROP POLICY IF EXISTS "Allow all for service role" ON enrichment_queue;
DROP POLICY IF EXISTS "Allow all for service role" ON activation_requests;
DROP POLICY IF EXISTS "Allow all for service role" ON recommendations;
DROP POLICY IF EXISTS "Allow all for service role" ON employment_history;
DROP POLICY IF EXISTS "Allow all for service role" ON timing_signals;
DROP POLICY IF EXISTS "Allow all for service role" ON company_events;
DROP POLICY IF EXISTS "Allow all for service role" ON warm_paths;
DROP POLICY IF EXISTS "Allow all for service role" ON api_keys;

-- Companies: can only see own company
CREATE POLICY "companies_self_access" ON companies FOR ALL
    USING (id = current_setting('app.current_company_id', true)::uuid);

-- Company UMOs: scoped to company
CREATE POLICY "umos_company_scoped" ON company_umos FOR ALL
    USING (company_id = current_setting('app.current_company_id', true)::uuid);

-- Roles: scoped to company
CREATE POLICY "roles_company_scoped" ON roles FOR ALL
    USING (company_id = current_setting('app.current_company_id', true)::uuid);

-- People: scoped to company
CREATE POLICY "people_company_scoped" ON people FOR ALL
    USING (company_id = current_setting('app.current_company_id', true)::uuid);

-- Person enrichments: via people join
CREATE POLICY "enrichments_company_scoped" ON person_enrichments FOR ALL
    USING (person_id IN (
        SELECT id FROM people
        WHERE company_id = current_setting('app.current_company_id', true)::uuid
    ));

-- Data sources: scoped to company
CREATE POLICY "data_sources_company_scoped" ON data_sources FOR ALL
    USING (company_id = current_setting('app.current_company_id', true)::uuid);

-- Person sources: via people join
CREATE POLICY "person_sources_company_scoped" ON person_sources FOR ALL
    USING (person_id IN (
        SELECT id FROM people
        WHERE company_id = current_setting('app.current_company_id', true)::uuid
    ));

-- Enrichment queue: via people join
CREATE POLICY "enrichment_queue_company_scoped" ON enrichment_queue FOR ALL
    USING (person_id IN (
        SELECT id FROM people
        WHERE company_id = current_setting('app.current_company_id', true)::uuid
    ));

-- Activation requests: scoped to company
CREATE POLICY "activation_requests_company_scoped" ON activation_requests FOR ALL
    USING (company_id = current_setting('app.current_company_id', true)::uuid);

-- Recommendations: scoped to company
CREATE POLICY "recommendations_company_scoped" ON recommendations FOR ALL
    USING (company_id = current_setting('app.current_company_id', true)::uuid);

-- Employment history: via people join
CREATE POLICY "employment_history_company_scoped" ON employment_history FOR ALL
    USING (person_id IN (
        SELECT id FROM people
        WHERE company_id = current_setting('app.current_company_id', true)::uuid
    ));

-- Timing signals: via people join
CREATE POLICY "timing_signals_company_scoped" ON timing_signals FOR ALL
    USING (person_id IN (
        SELECT id FROM people
        WHERE company_id = current_setting('app.current_company_id', true)::uuid
    ));

-- Company events: public read (not company-scoped, shared intelligence)
CREATE POLICY "company_events_public_read" ON company_events FOR SELECT
    USING (true);

-- Warm paths: scoped to company
CREATE POLICY "warm_paths_company_scoped" ON warm_paths FOR ALL
    USING (company_id = current_setting('app.current_company_id', true)::uuid);

-- API keys: scoped to company
CREATE POLICY "api_keys_company_scoped" ON api_keys FOR ALL
    USING (company_id = current_setting('app.current_company_id', true)::uuid);
