/**
 * API client for Agencity integration
 */

const AGENCITY_BASE = process.env.NEXT_PUBLIC_AGENCITY_URL || 'http://107.20.131.235';

interface ApiResponse<T> {
  data?: T;
  error?: string;
}

async function fetchAgencity<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('agencity_token') : null;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
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
  } catch (error) {
    return { error: 'Network error' };
  }
}

// Types
export interface AgencityCandidate {
  id: string;
  name: string;
  email: string;
  title: string;
  company: string;
  location?: string;
  linkedin_url?: string;
  score: number;
  fit_score: number;
  warmth_score: number;
  timing_score?: number;
  warmth_level: 'network' | 'warm' | 'cold';
  warm_path?: {
    type: 'direct' | 'school' | 'company' | '2nd_degree';
    description: string;
    connector?: string;
  };
  skills: string[];
  experience_years?: number;
  timing_signals?: string[];
  why_consider?: string;
  unknowns?: string[];
  github_url?: string;
  status?: 'sourced' | 'contacted' | 'interviewing' | 'invited' | 'in_simulation' | 'reviewed';
}

export interface SearchRequest {
  company_id: string;
  role_title: string;
  required_skills: string[];
  preferred_skills?: string[];
  experience_level?: string;
  include_external?: boolean;
  include_timing?: boolean;
  deep_research?: boolean;
  limit?: number;
  mode?: 'full' | 'quick' | 'network_only';
}

export interface SearchResponse {
  candidates: AgencityCandidate[];
  search_id: string;
  mode: string;
  total_count: number;
  tier1_count: number;
  tier2_count: number;
  tier3_count: number;
  search_time_ms: number;
}

export interface NetworkStats {
  total_contacts: number;
  companies: number;
  schools: number;
  engineers: number;
  by_company: Record<string, number>;
  by_school: Record<string, number>;
  by_skill: Record<string, number>;
}

export interface SearchHistory {
  id: string;
  query: string;
  role_title: string;
  required_skills: string[];
  results_count: number;
  timestamp: string;
  mode: string;
}

export interface SavedCandidate extends AgencityCandidate {
  saved_at: string;
  notes?: string;
  tags?: string[];
}

// Network & Company Management
export async function getNetworkStats(companyId: string) {
  return fetchAgencity<NetworkStats>(`/api/v3/network/${companyId}/stats`);
}

export async function importNetwork(companyId: string, source: 'linkedin' | 'csv', data: any) {
  return fetchAgencity<{ imported: number }>(`/api/v3/network/${companyId}/import`, {
    method: 'POST',
    body: JSON.stringify({ source, data }),
  });
}

// Search
export async function searchCandidates(request: SearchRequest) {
  return fetchAgencity<SearchResponse>('/api/search', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function getSearchHistory(companyId: string, limit = 10) {
  return fetchAgencity<SearchHistory[]>(
    `/api/search/history?company_id=${companyId}&limit=${limit}`
  );
}

export async function getSearchResults(searchId: string) {
  return fetchAgencity<SearchResponse>(`/api/search/${searchId}/results`);
}

// Warm Paths
export async function findWarmPaths(companyId: string, linkedinUrls: string[]) {
  return fetchAgencity<{ paths: any[] }>(`/api/v3/warm-paths/${companyId}`, {
    method: 'POST',
    body: JSON.stringify({ linkedin_urls: linkedinUrls }),
  });
}

export async function getWarmPath(companyId: string, candidateId: string) {
  return fetchAgencity<any>(`/api/v3/warm-paths/${companyId}/${candidateId}`);
}

// Saved Candidates
export async function saveCandidate(
  companyId: string,
  candidate: AgencityCandidate,
  notes?: string,
  tags?: string[]
) {
  return fetchAgencity<SavedCandidate>(`/api/candidates/${companyId}/save`, {
    method: 'POST',
    body: JSON.stringify({ candidate, notes, tags }),
  });
}

export async function getSavedCandidates(companyId: string) {
  return fetchAgencity<SavedCandidate[]>(`/api/candidates/${companyId}/saved`);
}

export async function unsaveCandidate(companyId: string, candidateId: string) {
  return fetchAgencity<{ success: boolean }>(
    `/api/candidates/${companyId}/saved/${candidateId}`,
    {
      method: 'DELETE',
    }
  );
}

export async function updateCandidateStatus(
  companyId: string,
  candidateId: string,
  status: AgencityCandidate['status']
) {
  return fetchAgencity<SavedCandidate>(
    `/api/candidates/${companyId}/saved/${candidateId}/status`,
    {
      method: 'PUT',
      body: JSON.stringify({ status }),
    }
  );
}

// Feedback
export async function recordFeedback(
  companyId: string,
  candidateId: string,
  action: 'viewed' | 'saved' | 'contacted' | 'interviewed' | 'hired' | 'rejected' | 'ignored',
  searchId?: string
) {
  return fetchAgencity<{ success: boolean }>('/api/feedback/action', {
    method: 'POST',
    body: JSON.stringify({
      company_id: companyId,
      candidate_id: candidateId,
      action,
      search_id: searchId,
      timestamp: new Date().toISOString(),
    }),
  });
}

// Intelligence
export async function getTimingAlerts(companyId: string) {
  return fetchAgencity<any[]>(`/api/v3/timing/alerts?company_id=${companyId}`);
}

export async function getCompanyEvents(companyId: string) {
  return fetchAgencity<any[]>(`/api/v3/company/events?company_id=${companyId}`);
}

// Integration with ProofHire
export async function inviteToProofHire(
  candidateId: string,
  proofhireRoleId: string,
  agencitySearchId?: string
) {
  /**
   * This will:
   * 1. Get candidate details from Agencity
   * 2. Create an application in ProofHire
   * 3. Send invitation email
   * 4. Track the linkage between Agencity candidate and ProofHire application
   */
  return fetchAgencity<{ application_id: string; invitation_sent: boolean }>(
    '/api/integration/proofhire/invite',
    {
      method: 'POST',
      body: JSON.stringify({
        candidate_id: candidateId,
        proofhire_role_id: proofhireRoleId,
        agencity_search_id: agencitySearchId,
      }),
    }
  );
}

export async function syncWithProofHire(candidateId: string, applicationId: string) {
  /**
   * Link an Agencity candidate with a ProofHire application
   * This enables tracking the full journey from sourcing to evaluation
   */
  return fetchAgencity<{ success: boolean }>('/api/integration/proofhire/sync', {
    method: 'POST',
    body: JSON.stringify({
      candidate_id: candidateId,
      application_id: applicationId,
    }),
  });
}

export async function getCandidateJourney(candidateId: string) {
  /**
   * Get the full candidate journey across both systems:
   * - Agencity: How they were found, warm paths, timing signals
   * - ProofHire: Simulation results, brief, evaluation
   */
  return fetchAgencity<any>(`/api/integration/proofhire/journey/${candidateId}`);
}
