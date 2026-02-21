/**
 * API client for Agencity backend
 * Aligned with real backend endpoints
 */

import type {
  ApiResponse,
  Company,
  CompanyCreate,
  CompanyCreateResponse,
  CompanyWithDetails,
  CompanyUMO,
  Role,
  RoleCreate,
  DataSource,
  SearchRequest,
  SearchResponse,
  CurationRequest,
  CurationResponse,
  CandidateContextResponse,
  AISummary,
  PipelineResponse,
  PipelineStatus,
  StatusUpdateResponse,
  FeedbackRequest,
  FeedbackStats,
  ProofHireInviteRequest,
  ProofHireInviteResponse,
  CurationCacheResponse,
  ProviderHealth,
  NetworkIndex,
  TimingAlert,
  CompanyEvent,
  IntroRequest,
  IntroRequestResponse,
  ApiKeyInfo,
  CandidateResponse,
} from './agencity-types';

const AGENCITY_BASE =
  process.env.NEXT_PUBLIC_AGENCITY_URL || 'http://107.20.131.235';

function getApiKey(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('agencity_api_key');
}

async function fetchAgencity<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const apiKey = getApiKey();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(apiKey && { Authorization: `Bearer ${apiKey}` }),
    ...options.headers,
  };

  try {
    const response = await fetch(`${AGENCITY_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    const data = await response.json();

    if (!response.ok) {
      return { error: data.detail || 'An error occurred' };
    }

    return { data };
  } catch {
    return { error: 'Network error — is the backend running?' };
  }
}

async function fetchAgencityFormData<T>(
  endpoint: string,
  formData: FormData
): Promise<ApiResponse<T>> {
  const apiKey = getApiKey();

  const headers: HeadersInit = {
    ...(apiKey && { Authorization: `Bearer ${apiKey}` }),
  };

  try {
    const response = await fetch(`${AGENCITY_BASE}${endpoint}`, {
      method: 'POST',
      headers,
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      return { error: data.detail || 'An error occurred' };
    }

    return { data };
  } catch {
    return { error: 'Network error — is the backend running?' };
  }
}

// ─── Company & Onboarding ───────────────────────────────────────────────────

export async function createCompany(company: CompanyCreate) {
  return fetchAgencity<CompanyCreateResponse>('/api/companies', {
    method: 'POST',
    body: JSON.stringify(company),
  });
}

export async function getCompany(companyId: string) {
  return fetchAgencity<CompanyWithDetails>(`/api/companies/${companyId}`);
}

export async function updateCompany(
  companyId: string,
  updates: Partial<CompanyCreate>
) {
  return fetchAgencity<Company>(`/api/companies/${companyId}`, {
    method: 'PATCH',
    body: JSON.stringify(updates),
  });
}

export async function completeOnboarding(companyId: string) {
  return fetchAgencity<{ status: string; message: string }>(
    `/api/companies/${companyId}/complete-onboarding`,
    { method: 'POST' }
  );
}

// ─── UMO (Company Operating Model) ─────────────────────────────────────────

export async function getCompanyUMO(companyId: string) {
  return fetchAgencity<CompanyUMO>(`/api/companies/${companyId}/umo`);
}

export async function updateCompanyUMO(
  companyId: string,
  umo: Partial<CompanyUMO>
) {
  return fetchAgencity<CompanyUMO>(`/api/companies/${companyId}/umo`, {
    method: 'PUT',
    body: JSON.stringify(umo),
  });
}

// ─── Roles ──────────────────────────────────────────────────────────────────

export async function createRole(companyId: string, role: RoleCreate) {
  return fetchAgencity<Role>(`/api/companies/${companyId}/roles`, {
    method: 'POST',
    body: JSON.stringify(role),
  });
}

export async function getCompanyRoles(companyId: string) {
  return fetchAgencity<Role[]>(`/api/companies/${companyId}/roles`);
}

// ─── Data Import ────────────────────────────────────────────────────────────

export async function importLinkedIn(companyId: string, file: File) {
  const formData = new FormData();
  formData.append('file', file);
  return fetchAgencityFormData<DataSource>(
    `/api/companies/${companyId}/import/linkedin`,
    formData
  );
}

export async function importDatabase(companyId: string, file: File) {
  const formData = new FormData();
  formData.append('file', file);
  return fetchAgencityFormData<DataSource>(
    `/api/companies/${companyId}/import/database`,
    formData
  );
}

export async function getImportHistory(companyId: string) {
  return fetchAgencity<DataSource[]>(`/api/companies/${companyId}/imports`);
}

export async function getPeople(
  companyId: string,
  limit = 50,
  offset = 0
) {
  return fetchAgencity<{ people: Record<string, unknown>[]; total: number }>(
    `/api/companies/${companyId}/people?limit=${limit}&offset=${offset}`
  );
}

// ─── Unified Search ─────────────────────────────────────────────────────────

export async function searchCandidates(request: SearchRequest) {
  return fetchAgencity<SearchResponse>('/api/search', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function searchNetworkOnly(request: SearchRequest) {
  return fetchAgencity<SearchResponse>('/api/search/network-only', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function quickSearch(request: SearchRequest) {
  return fetchAgencity<SearchResponse>('/api/search/quick', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function getSearchHealth() {
  return fetchAgencity<ProviderHealth>('/api/search/health');
}

// ─── Curation ───────────────────────────────────────────────────────────────

export async function curateCandidates(request: CurationRequest) {
  return fetchAgencity<CurationResponse>('/api/v1/curation/curate', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function getCandidateContext(personId: string, roleId: string) {
  return fetchAgencity<CandidateContextResponse>(
    `/api/v1/curation/candidate/${personId}/context?role_id=${roleId}`
  );
}

export async function recordCurationFeedback(
  personId: string,
  roleId: string,
  decision: 'interview' | 'pass' | 'need_more_info',
  notes?: string
) {
  const params = new URLSearchParams({
    role_id: roleId,
    decision,
    ...(notes && { notes }),
  });
  return fetchAgencity<{ status: string }>(
    `/api/v1/curation/candidate/${personId}/feedback?${params}`,
    { method: 'POST' }
  );
}

export async function regenerateSummary(personId: string, roleId: string) {
  return fetchAgencity<{ status: string; ai_summary: AISummary }>(
    `/api/v1/curation/candidate/${personId}/regenerate-summary?role_id=${roleId}`,
    { method: 'POST' }
  );
}

// ─── Curation Cache ─────────────────────────────────────────────────────────

export async function generateCurationCache(
  roleId: string,
  forceRefresh = false
) {
  return fetchAgencity<CurationCacheResponse>(
    '/api/curation-cache/generate',
    {
      method: 'POST',
      body: JSON.stringify({ role_id: roleId, force_refresh: forceRefresh }),
    }
  );
}

export async function generateAllCaches(forceRefresh = false) {
  return fetchAgencity<{
    total_roles: number;
    cached: number;
    processing: number;
    pending: number;
    failed: number;
  }>('/api/curation-cache/generate-all', {
    method: 'POST',
    body: JSON.stringify({ force_refresh: forceRefresh }),
  });
}

export async function getCacheStatus() {
  return fetchAgencity<{
    total_roles: number;
    cached: number;
    processing: number;
    pending: number;
    failed: number;
  }>('/api/curation-cache/status');
}

// ─── Pipeline ───────────────────────────────────────────────────────────────

export async function getPipeline(status?: PipelineStatus, limit = 50) {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  params.set('limit', String(limit));
  return fetchAgencity<PipelineResponse>(`/api/pipeline?${params}`);
}

export async function updateCandidateStatus(
  candidateId: string,
  status: PipelineStatus,
  notes?: string
) {
  return fetchAgencity<StatusUpdateResponse>(
    `/api/candidates/${candidateId}/status`,
    {
      method: 'PATCH',
      body: JSON.stringify({ status, ...(notes && { notes }) }),
    }
  );
}

// ─── Feedback ───────────────────────────────────────────────────────────────

export async function recordFeedback(feedback: FeedbackRequest) {
  return fetchAgencity<{ id: string; action: string; recorded_at: string }>(
    '/api/feedback',
    {
      method: 'POST',
      body: JSON.stringify(feedback),
    }
  );
}

export async function getFeedbackStats() {
  return fetchAgencity<FeedbackStats>('/api/feedback/stats');
}

// ─── ProofHire Integration ──────────────────────────────────────────────────

export async function inviteToProofHire(request: ProofHireInviteRequest) {
  return fetchAgencity<ProofHireInviteResponse>('/api/proofhire/invite', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// ─── Intelligence: Timing & Events ──────────────────────────────────────────

export async function getTimingAlerts(companyId: string) {
  return fetchAgencity<TimingAlert[]>(
    `/api/v3/timing/alerts?company_id=${companyId}`
  );
}

export async function getCompanyEvents(companyId: string) {
  return fetchAgencity<CompanyEvent[]>(
    `/api/v3/company/events?company_id=${companyId}`
  );
}

// ─── Activation: Intro Messages ─────────────────────────────────────────────

export async function generateIntroRequests(request: IntroRequest) {
  return fetchAgencity<IntroRequestResponse>(
    '/api/v3/activate/reverse-reference',
    {
      method: 'POST',
      body: JSON.stringify(request),
    }
  );
}

// ─── Warm Paths (V3) ───────────────────────────────────────────────────────

export async function findWarmPaths(
  companyId: string,
  linkedinUrls: string[]
) {
  return fetchAgencity<{ results: CandidateResponse[] }>(
    `/api/v3/search/warm-paths/${companyId}`,
    {
      method: 'POST',
      body: JSON.stringify({ linkedin_urls: linkedinUrls }),
    }
  );
}

export async function getNetworkIndex(companyId: string) {
  return fetchAgencity<NetworkIndex>(
    `/api/v3/search/network-index/${companyId}`
  );
}

// ─── API Key Management ─────────────────────────────────────────────────────

export async function createApiKey(companyId: string, name = 'default') {
  return fetchAgencity<{ api_key: string; api_key_prefix: string }>(
    `/api/companies/${companyId}/api-keys`,
    {
      method: 'POST',
      body: JSON.stringify({ name }),
    }
  );
}

export async function listApiKeys(companyId: string) {
  return fetchAgencity<{ api_keys: ApiKeyInfo[] }>(
    `/api/companies/${companyId}/api-keys`
  );
}

// ─── Health ─────────────────────────────────────────────────────────────────

export async function getProviderHealth() {
  return fetchAgencity<ProviderHealth>('/api/search/health');
}

// Re-export types for convenience
export type {
  Company,
  CompanyCreate,
  CompanyCreateResponse,
  CompanyWithDetails,
  Role,
  RoleCreate,
  SearchRequest,
  SearchResponse,
  CandidateResponse,
  CuratedCandidate,
  CurationResponse,
  PipelineCandidate,
  PipelineResponse,
  PipelineStatus,
  TimingAlert,
  CompanyEvent,
  ProviderHealth,
  FeedbackStats,
  DataSource,
  NetworkIndex,
  ProofHireInviteRequest,
  CandidateContextResponse,
  AISummary,
} from './agencity-types';
