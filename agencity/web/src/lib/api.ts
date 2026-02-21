/**
 * API client for Agencity backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api';

// =============================================================================
// TYPES
// =============================================================================

export interface Company {
  id: string;
  name: string;
  domain?: string;
  stage?: string;
  industry?: string;
  tech_stack: string[];
  team_size?: number;
  founder_email: string;
  founder_name: string;
  founder_linkedin_url?: string;
  linkedin_imported: boolean;
  existing_db_imported: boolean;
  onboarding_complete: boolean;
  pinecone_namespace?: string;
  people_count: number;
  roles_count: number;
  created_at: string;
  updated_at: string;
}

export interface CompanyUMO {
  id: string;
  company_id: string;
  preferred_backgrounds: string[];
  must_have_traits: string[];
  anti_patterns: string[];
  culture_values: string[];
  work_style?: string;
  ideal_candidate_description?: string;
  umo_text?: string;
  created_at: string;
  updated_at: string;
}

export interface Role {
  id: string;
  company_id: string;
  title: string;
  level?: string;
  department?: string;
  required_skills: string[];
  preferred_skills: string[];
  years_experience_min?: number;
  years_experience_max?: number;
  description?: string;
  location?: string;
  salary_min?: number;
  salary_max?: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Person {
  id: string;
  company_id: string;
  email?: string;
  linkedin_url?: string;
  github_url?: string;
  full_name: string;
  first_name?: string;
  last_name?: string;
  headline?: string;
  location?: string;
  current_company?: string;
  current_title?: string;
  status: string;
  trust_score: number;
  is_from_network: boolean;
  is_from_existing_db: boolean;
  is_from_people_search: boolean;
  created_at: string;
}

export interface ImportResult {
  source_id: string;
  status: string;
  total_records: number;
  records_created: number;
  records_matched: number;
  records_failed: number;
  errors: string[];
}

export interface CompanyWithStats extends Company {
  umo?: CompanyUMO;
  roles: Role[];
  recent_imports: DataSource[];
}

export interface DataSource {
  id: string;
  company_id: string;
  type: string;
  name?: string;
  status: string;
  total_records: number;
  records_created: number;
  records_matched: number;
  records_failed: number;
  imported_at?: string;
  created_at: string;
}

// =============================================================================
// API FUNCTIONS
// =============================================================================

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  console.log(`[API] ${options.method || 'GET'} ${url}`);

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  console.log(`[API] Response: ${response.status} ${response.statusText}`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    console.error(`[API] Error response:`, error);
    throw new Error(error.detail || `Request failed: ${response.status}`);
  }

  const data = await response.json();
  console.log(`[API] Success:`, typeof data === 'object' ? Object.keys(data) : data);
  return data;
}

// Companies

export async function createCompany(data: {
  name: string;
  founder_email: string;
  founder_name: string;
  domain?: string;
  stage?: string;
  industry?: string;
  tech_stack?: string[];
  team_size?: number;
}): Promise<Company> {
  return request('/companies', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getCompany(companyId: string): Promise<CompanyWithStats> {
  return request(`/companies/${companyId}`);
}

export async function updateCompany(
  companyId: string,
  data: Partial<Company>
): Promise<Company> {
  return request(`/companies/${companyId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

// UMO

export async function updateUMO(
  companyId: string,
  data: {
    preferred_backgrounds?: string[];
    must_have_traits?: string[];
    anti_patterns?: string[];
    culture_values?: string[];
    work_style?: string;
    ideal_candidate_description?: string;
  }
): Promise<CompanyUMO> {
  return request(`/companies/${companyId}/umo`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function getUMO(companyId: string): Promise<CompanyUMO | null> {
  return request(`/companies/${companyId}/umo`);
}

// Roles

export async function createRole(
  companyId: string,
  data: {
    title: string;
    level?: string;
    department?: string;
    required_skills?: string[];
    preferred_skills?: string[];
    years_experience_min?: number;
    years_experience_max?: number;
    description?: string;
    location?: string;
  }
): Promise<Role> {
  return request(`/companies/${companyId}/roles`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getRoles(companyId: string): Promise<Role[]> {
  return request(`/companies/${companyId}/roles`);
}

// Imports

export async function importLinkedIn(
  companyId: string,
  file: File
): Promise<ImportResult> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(
    `${API_BASE}/companies/${companyId}/import/linkedin`,
    {
      method: 'POST',
      body: formData,
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Import failed');
  }

  return response.json();
}

export async function importDatabase(
  companyId: string,
  file: File
): Promise<ImportResult> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(
    `${API_BASE}/companies/${companyId}/import/database`,
    {
      method: 'POST',
      body: formData,
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Import failed');
  }

  return response.json();
}

// People

export async function getPeople(
  companyId: string,
  limit = 50,
  offset = 0
): Promise<{ people: Person[]; total: number }> {
  return request(
    `/companies/${companyId}/people?limit=${limit}&offset=${offset}`
  );
}

// Complete onboarding

export async function completeOnboarding(
  companyId: string
): Promise<{ status: string; message: string }> {
  return request(`/companies/${companyId}/complete-onboarding`, {
    method: 'POST',
  });
}

// =============================================================================
// SEARCH TYPES
// =============================================================================

export interface SearchCandidate {
  id: string;
  full_name: string;
  first_name?: string;
  last_name?: string;
  current_title?: string;
  current_company?: string;
  headline?: string;
  location?: string;
  linkedin_url?: string;
  github_url?: string;
  email?: string;
  // Scores
  warmth_score?: number;
  readiness_score?: number;
  relevance_score?: number;
  match_score?: number;
  combined_score?: number;
  // Tier info
  tier: number;
  tier_label?: string;
  // Reasons and actions
  match_reasons?: string[];
  readiness_signals?: string[];
  action?: string;
  // Network path info
  warm_path?: {
    type: string;
    via?: string;
    company?: string;
  } | null;
  warm_paths?: WarmPath[];
  // Recruiter specific
  is_from_network?: boolean;
  is_recruiter?: boolean;
  recruiter_score?: number;
  specialty?: string;
  recruiter_signals?: string[];
}

export interface WarmPath {
  type: 'direct' | 'colleague' | 'school' | 'recommendation';
  warmth: number;
  connector?: {
    name: string;
    linkedin_url?: string;
  };
  overlap_company?: string;
  overlap_dates?: string;
}

export interface SearchResults {
  // Actual API response format
  tier_1_network: SearchCandidate[];
  tier_2_one_intro: SearchCandidate[];
  tier_3_recruiters: SearchCandidate[];
  tier_4_cold: SearchCandidate[];
  search_target: string | {
    role_title: string;
    required_skills: string[];
    preferred_backgrounds: string[];
    locations: string[];
  };
  search_duration_seconds: number;
  network_size: number;
  total_candidates: number;
  tier_1_count: number;
  tier_2_count: number;
  tier_3_count: number;
  tier_4_count: number;
  primary_recommendation?: string;
  recruiter_recommendation?: string;

  // Computed/legacy fields for backward compatibility
  query?: string;
  total_found?: number;
  network_matches?: number;
  warm_matches?: number;
  cold_matches?: number;
}

export interface TimingAlert {
  person_id: string;
  person_name: string;
  signal_type: string;
  urgency: 'high' | 'medium' | 'low';
  message: string;
  recommended_action: string;
}

export interface ActivationSuggestion {
  message: string;
  targets: {
    name: string;
    reason: string;
  }[];
}

// Intelligence Types

export interface NetworkStats {
  company_id: string;
  network: {
    total_nodes: number;
    by_type: Record<string, number>;
    by_access_pattern: Record<string, number>;
    total_estimated_reach: number;
    top_companies: Record<string, number>;
    avg_seniority: number;
  };
  // Computed helpers for backward compatibility
  total_connections?: number;
  role_breakdown?: Record<string, number>;
  unique_companies?: number;
}

export interface LayoffExposure {
  total_network_members: number;
  affected_members: number;
  affected_percentage: number;
  companies_with_layoffs: number;
  by_company: Record<string, {
    count: number;
    urgency: string;
    layoff_date: string;
    scale: string;
    members: {
      id: string;
      name: string;
      title: string;
      company: string;
      linkedin_url: string;
    }[];
  }>;
}

export interface ActivationRequest {
  id: string;
  target_name: string;
  target_title: string;
  target_company: string;
  target_linkedin_url: string;
  role_title: string;
  message: string;
  priority_score: number;
  reason: string;
}

export interface TimingAnalysis {
  person_id: string;
  person_name: string;
  current_title: string;
  current_company: string;
  linkedin_url: string;
  readiness_score: number;
  signals: {
    type: string;
    description: string;
    score_impact: number;
  }[];
  recommended_action: string;
}

// =============================================================================
// SEARCH API FUNCTIONS
// =============================================================================

export async function searchCandidates(
  companyId: string,
  params: {
    role_id?: string;
    query?: string;
    limit?: number;
  }
): Promise<SearchResults> {
  return request('/v2/search', {
    method: 'POST',
    body: JSON.stringify({
      company_id: companyId,
      role_title: params.query || 'Software Engineer',
      limit: params.limit || 20,
    }),
  });
}

export async function getNetworkStats(companyId: string): Promise<NetworkStats> {
  return request(`/companies/${companyId}/network/stats`);
}

export async function getLayoffExposure(companyId: string): Promise<LayoffExposure> {
  return request(`/v3/company/layoffs/${companyId}`);
}

export async function getTimingAlerts(companyId: string): Promise<TimingAnalysis[]> {
  return request(`/v3/timing/network-analysis/${companyId}?limit=20`);
}

export async function getActivationRequests(
  companyId: string,
  roleTitle: string
): Promise<ActivationRequest[]> {
  const response = await request<{
    requests: ActivationRequest[];
  }>('/v3/activate/reverse-reference', {
    method: 'POST',
    body: JSON.stringify({
      company_id: companyId,
      role_title: roleTitle,
      required_skills: [],
      limit: 20,
      save_to_db: false,
    }),
  });

  return response.requests || [];
}

export async function getDailyDigest(companyId: string): Promise<{
  date: string;
  summary: string;
  top_actions: {
    priority?: string;
    category?: string;
    action?: string;
    targets?: string[];
  }[];
  alert_counts: Record<string, number>;
}> {
  return request(`/v3/company/digest/${companyId}`);
}

// =============================================================================
// UNIFIED SEARCH API
// =============================================================================

export interface UnifiedCandidate {
  id: string;
  full_name: string;
  current_title?: string;
  current_company?: string;
  location?: string;
  linkedin_url?: string;
  github_url?: string;

  // Scores
  fit_score: number;
  warmth_score: number;
  timing_score: number;
  combined_score: number;

  // Classification
  tier: number;
  tier_label: string;
  source: string;
  timing_urgency: string;

  // Warm path
  has_warm_path: boolean;
  warm_path_type?: string;
  warm_path_connector?: string;
  warm_path_relationship?: string;
  intro_message?: string;

  // Context
  why_consider: string[];
  unknowns: string[];
  research_highlights: string[];
}

export interface UnifiedSearchResponse {
  role_title: string;
  query_used: string;
  search_duration_seconds: number;

  network_size: number;
  network_companies: number;

  total_found: number;
  tier_1_network: number;
  tier_2_warm: number;
  tier_3_cold: number;
  high_urgency: number;

  external_enabled: boolean;
  timing_enabled: boolean;
  research_enabled: boolean;
  deep_researched: number;
  external_yield_ok: boolean;
  external_provider_stats: Record<string, number>;
  external_provider_health: Record<string, {
    provider: string;
    ok: boolean;
    status_code?: number;
    reason?: string;
  }>;
  external_diagnostics: string[];
  warnings: string[];
  degraded: boolean;
  decision_confidence: 'high' | 'medium' | 'low';
  recommended_actions: string[];

  candidates: UnifiedCandidate[];
}

export async function unifiedSearch(params: {
  companyId: string;
  roleTitle: string;
  requiredSkills?: string[];
  preferredSkills?: string[];
  location?: string;
  yearsExperience?: number;
  includeExternal?: boolean;
  includeTiming?: boolean;
  deepResearch?: boolean;
  limit?: number;
}): Promise<UnifiedSearchResponse> {
  return request('/search', {
    method: 'POST',
    body: JSON.stringify({
      company_id: params.companyId,
      role_title: params.roleTitle,
      required_skills: params.requiredSkills || [],
      preferred_skills: params.preferredSkills || [],
      location: params.location,
      years_experience: params.yearsExperience,
      include_external: params.includeExternal ?? true,
      include_timing: params.includeTiming ?? true,
      deep_research: params.deepResearch ?? true,
      limit: params.limit || 20,
    }),
  });
}


// =============================================================================
// CURATION TYPES
// =============================================================================

export type MatchStrength = 'high' | 'medium' | 'low' | 'unknown';

export interface WhyConsiderPoint {
  category: string;
  strength: MatchStrength;
  points: string[];
}

export interface DeepResearchInsight {
  category: string;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  insights: string[];
}

export interface AgentScore {
  score: number;
  reasoning: string;
}

export interface ResearchHighlight {
  type: 'github' | 'publication' | 'achievement' | 'skill';
  title: string;
  description: string;
  url?: string;
}

export interface EnrichmentDetails {
  sources: string[];  // ["pdl", "perplexity", "manual"]
  pdl_fields: string[];  // Fields enriched by PDL
  research_highlights: ResearchHighlight[];
  data_quality_score: number;
}

export interface ClaudeReasoning {
  overall_score: number;
  confidence: number;
  agent_scores: {
    skills_agent?: AgentScore;
    skill_agent?: AgentScore;
    trajectory_agent?: AgentScore;
    fit_agent?: AgentScore;
    timing_agent?: AgentScore;
  };
  weighted_calculation: string;
}

export interface CandidateContext {
  why_consider: (string | WhyConsiderPoint)[];
  unknowns: string[];
  standout_signal?: string;
  warm_path?: string;
  detailed_analysis: {
    skills_match: {
      matched: string[];
      missing: string[];
    };
  };
  suggested_interview_questions: string[];

  // NEW: Enrichment details
  enrichment_details?: EnrichmentDetails;

  // NEW: Claude reasoning breakdown
  claude_reasoning?: ClaudeReasoning;
}

export interface CuratedCandidate {
  person_id: string;
  full_name: string;
  headline?: string;
  location?: string;
  current_company?: string;
  current_title?: string;
  linkedin_url?: string;
  github_url?: string;

  // Skills & Experience (from PDL enrichment)
  skills?: string[];
  experience?: any[];
  education?: any[];

  // Scores
  match_score: number;
  fit_confidence: number;
  data_completeness: number;

  // Metadata
  was_enriched: boolean;

  // Context
  context: CandidateContext;
}

export interface CurationResults {
  role_id: string;
  role_title: string;
  candidates: CuratedCandidate[];

  // Stats
  total_searched: number;
  total_enriched: number;
  enrichment_rate: number;
  total_researched: number;
  research_rate: number;
  average_fit_score: number;
  average_confidence: number;
  processing_time_seconds: number;
}

// =============================================================================
// CURATION API FUNCTIONS
// =============================================================================

export async function curateCandidates(
  companyId: string,
  roleId: string,
  options: { limit?: number; forceRefresh?: boolean } = {}
): Promise<CurationResults> {
  const start = Date.now();

  // 1. Try to get from cache first
  try {
    console.log('📦 Attempting to load from cache...', { companyId, roleId });
    const cacheResponse = await request<{
      role_id: string;
      role_title: string;
      status: string;
      shortlist: any[];
      total_searched: number;
      enriched_count: number;
      avg_match_score: number;
      generated_at: string;
      expires_at: string;
      from_cache: boolean;
    }>(`/curation/cache/${companyId}/${roleId}?force_refresh=${options.forceRefresh || false}`);

    console.log('📦 Cache response received:', {
      from_cache: cacheResponse.from_cache,
      shortlist_length: cacheResponse.shortlist?.length || 0,
      total_searched: cacheResponse.total_searched,
      status: cacheResponse.status
    });

    if (cacheResponse.from_cache) {
      console.log('✓ Loaded from cache (instant)', { roleId });

      // Validate shortlist is an array
      if (!Array.isArray(cacheResponse.shortlist)) {
        console.error('❌ Cache shortlist is not an array:', typeof cacheResponse.shortlist);
        throw new Error('Invalid cache format: shortlist is not an array');
      }

      if (cacheResponse.shortlist.length === 0) {
        console.warn('⚠️ Cache exists but shortlist is empty');
      }

      // Map cached data to CurationResults
      const candidates: CuratedCandidate[] = cacheResponse.shortlist.map((c: any) => ({
        person_id: c.person_id,
        full_name: c.full_name,
        headline: c.headline,
        location: c.location,
        current_company: c.current_company,
        current_title: c.current_title,
        linkedin_url: c.linkedin_url,
        github_url: c.github_url,
        skills: c.skills || [],
        experience: c.experience || [],
        education: c.education || [],
        match_score: c.match_score,
        fit_confidence: c.fit_confidence,
        data_completeness: c.data_completeness,
        was_enriched: c.was_enriched,
        context: c.context
      }));

      console.log('✓ Mapped candidates:', candidates.length);

      return {
        role_id: roleId,
        role_title: cacheResponse.role_title,
        candidates,
        total_searched: cacheResponse.total_searched,
        total_enriched: cacheResponse.enriched_count,
        enrichment_rate: candidates.length > 0 ? (cacheResponse.enriched_count / candidates.length) * 100 : 0,
        total_researched: cacheResponse.enriched_count,
        research_rate: candidates.length > 0 ? (cacheResponse.enriched_count / candidates.length) * 100 : 0,
        average_fit_score: cacheResponse.avg_match_score || 0,
        average_confidence: 0.8,
        processing_time_seconds: (Date.now() - start) / 1000 // Should be < 1 second
      };
    } else {
      console.warn('⚠️ Cache response has from_cache=false, falling through to live curation');
    }
  } catch (error: any) {
    // Cache miss (404) - fall through to generate new curation
    if (error.message?.includes('404') || error.message?.includes('Cache not found')) {
      console.log('⚠ Cache miss, generating new curation...', { roleId });
    } else {
      console.warn('Cache fetch error, falling back to live curation:', error);
    }
  }

  // 2. Cache miss - call backend curation endpoint (slow path)
  console.log('⏳ Cache miss, calling live curation endpoint...');
  let roleTitle = 'Unknown Role';
  try {
    const roles = await getRoles(companyId);
    const role = roles.find(r => r.id === roleId);
    if (role) roleTitle = role.title;
  } catch (e) {
    console.warn('Failed to fetch role title', e);
  }

  console.log('Calling /v1/curation/curate with:', { company_id: companyId, role_id: roleId, limit: options.limit || 15 });

  const response = await request<{
    shortlist: any[];
    total_searched: number;
    metadata: any;
  }>('/v1/curation/curate', {
    method: 'POST',
    body: JSON.stringify({
      company_id: companyId,
      role_id: roleId,
      limit: options.limit || 15
    }),
  });

  console.log('Curation API response:', response);

  const processingTime = (Date.now() - start) / 1000;

  const candidates: CuratedCandidate[] = response.shortlist.map((c: any) => ({
    person_id: c.person_id,
    full_name: c.full_name,
    headline: c.headline,
    location: c.location,
    current_company: c.current_company,
    current_title: c.current_title,
    linkedin_url: c.linkedin_url,
    github_url: c.github_url,
    skills: c.skills || [],
    experience: c.experience || [],
    education: c.education || [],
    match_score: c.match_score,
    fit_confidence: c.fit_confidence,
    data_completeness: c.data_completeness,
    was_enriched: c.was_enriched,
    context: c.context
  }));

  const totalEnriched = response.metadata.enriched_count || 0;

  return {
    role_id: roleId,
    role_title: roleTitle,
    candidates,
    total_searched: response.total_searched,
    total_enriched: totalEnriched,
    enrichment_rate: candidates.length > 0 ? (totalEnriched / candidates.length) * 100 : 0,
    total_researched: totalEnriched,
    research_rate: candidates.length > 0 ? (totalEnriched / candidates.length) * 100 : 0,
    average_fit_score: response.metadata.avg_match_score || 0,
    average_confidence: response.metadata.avg_confidence || 0,
    processing_time_seconds: processingTime
  };
}

// Generate cache for a specific role
export async function generateCurationCache(
  companyId: string,
  roleId: string,
  forceRefresh: boolean = false
): Promise<{ status: string; role_id: string; message: string }> {
  return request(`/curation/cache/generate/${companyId}`, {
    method: 'POST',
    body: JSON.stringify({
      role_id: roleId,
      force_refresh: forceRefresh
    })
  });
}

// Generate cache for all company roles
export async function generateAllCurationCaches(
  companyId: string,
  forceRefresh: boolean = false
): Promise<{ status: string; queued_count: number; role_ids: string[]; message: string }> {
  return request(`/curation/cache/generate-all/${companyId}`, {
    method: 'POST',
    body: JSON.stringify({
      force_refresh: forceRefresh
    })
  });
}

// Get cache status for all roles
export async function getCurationCacheStatus(
  companyId: string
): Promise<{
  total_roles: number;
  cached: number;
  processing: number;
  pending: number;
  failed: number;
  roles: Array<{
    id: string;
    title: string;
    status: string;
    curation_status: string;
    last_curated_at?: string;
  }>;
}> {
  return request(`/curation/cache-status/${companyId}`);
}

export async function getCandidateContext(
  personId: string,
  roleId: string
): Promise<CandidateContext> {
  const result = await request<any>(`/v1/curation/candidate/${personId}/context?role_id=${roleId}`);

  // Adapt to CandidateContext interface
  return {
    why_consider: result.context.why_consider.map((w: any) =>
      typeof w === 'string' ? w : `${w.points[0]}`
    ),
    unknowns: result.context.unknowns,
    standout_signal: result.context.standout_signal,
    warm_path: result.context.warm_path,
    detailed_analysis: {
      skills_match: {
        matched: [], // Backend doesn't seem to return this in context structure yet, verifying
        missing: []
      }
    },
    suggested_interview_questions: [] // Backend logic for this might be pending or in different field
  };
}

export async function recordCandidateFeedback(
  personId: string,
  roleId: string,
  decision: string, // "interview", "pass", "need_more_info"
  notes?: string
): Promise<{ status: string }> {
  return request(`/v1/curation/candidate/${personId}/feedback`, {
    method: 'POST',
    body: JSON.stringify({
      role_id: roleId,
      decision,
      notes
    })
  });
}

// =============================================================================
// PIPELINE API FUNCTIONS
// =============================================================================

export interface PipelineCandidate {
  id: string;
  agencity_candidate_id: string;
  name: string;
  email?: string;
  linkedin_url?: string;
  title?: string;
  company?: string;
  warmth_score: number;
  warmth_level: string;
  warm_path?: {
    type: string;
    description: string;
  };
  status: 'sourced' | 'contacted' | 'scheduled';
  sourced_at: string;
  contacted_at?: string;
  scheduled_at?: string;
}

export interface PipelineResponse {
  candidates: PipelineCandidate[];
  total: number;
  by_status: {
    sourced: number;
    contacted: number;
    scheduled: number;
  };
}

export async function getPipeline(
  companyId: string,
  params?: {
    status?: 'all' | 'sourced' | 'contacted' | 'scheduled';
    sort?: 'date' | 'score' | 'status';
    limit?: number;
  }
): Promise<PipelineResponse> {
  const queryParams = new URLSearchParams({
    status: params?.status || 'all',
    sort: params?.sort || 'date',
    limit: String(params?.limit || 50),
  });

  return request(`/pipeline/${companyId}?${queryParams}`);
}

export async function updateCandidateStatus(
  candidateId: string,
  update: {
    status: 'sourced' | 'contacted' | 'scheduled';
    notes?: string;
  }
): Promise<{
  id: string;
  status: string;
  contacted_at?: string;
  scheduled_at?: string;
  updated_at: string;
}> {
  return request(`/candidates/${candidateId}/status`, {
    method: 'PATCH',
    body: JSON.stringify(update),
  });
}

export async function enrichCandidateEmail(
  personId: string
): Promise<{ email: string | null; source: string; message?: string }> {
  return request(`/v1/curation/candidate/${personId}/enrich-email`, { method: 'POST' });
}

export async function recordFeedback(feedback: {
  company_id: string;
  candidate_id: string;
  action: 'hired' | 'interviewed' | 'contacted' | 'saved' | 'viewed' | 'rejected' | 'ignored';
  search_id?: string;
  notes?: string;
  metadata?: any;
}): Promise<{
  id: string;
  action: string;
  recorded_at: string;
}> {
  return request('/feedback/action', {
    method: 'POST',
    body: JSON.stringify(feedback),
  });
}

export interface ProofHireInviteResponse {
  linkage_id: string;
  candidate_id: string;
  proofhire_application_id: string;
  proofhire_role_id: string;
  status: string;
}

export async function inviteCandidateToProofHire(payload: {
  company_id: string;
  candidate_id: string;
  proofhire_role_id: string;
  search_id?: string;
}): Promise<ProofHireInviteResponse> {
  return request('/proofhire/invite', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export interface ProviderHealth {
  provider: string;
  ok: boolean;
  status_code?: number;
  reason?: string;
}

export async function getExternalProvidersHealth(): Promise<{
  ok: boolean;
  providers: ProviderHealth[];
}> {
  return request('/providers/health');
}

export async function getProofHireDecisionPacket(
  proofhireApplicationId: string
): Promise<{
  linkage: {
    id: string;
    company_id: string;
    agencity_candidate_id: string;
    proofhire_application_id: string;
    proofhire_role_id: string;
    status: string;
    created_at: string;
    updated_at: string;
  };
  candidate: Record<string, unknown>;
  feedback: Array<Record<string, unknown>>;
}> {
  return request(`/proofhire/decision-packet/${proofhireApplicationId}`);
}

