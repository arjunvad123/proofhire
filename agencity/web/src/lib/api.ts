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

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Request failed: ${response.status}`);
  }

  return response.json();
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
  search_target: string;
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
  return request(`/v3/activate/reverse-reference?company_id=${companyId}&role_title=${encodeURIComponent(roleTitle)}&limit=20`);
}

export async function getDailyDigest(companyId: string): Promise<{
  date: string;
  summary: string;
  priority_actions: {
    priority: string;
    category: string;
    action: string;
    targets: string[];
  }[];
  stats: Record<string, number>;
}> {
  return request(`/v3/company/digest/${companyId}`);
}
