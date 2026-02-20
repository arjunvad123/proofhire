/**
 * API client for ProofHire backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

interface ApiResponse<T> {
  data?: T;
  error?: string;
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
    ...options.headers,
  };

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
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

// Auth
export async function login(email: string, password: string) {
  return fetchApi<{ access_token: string; user: User }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function register(email: string, password: string, name: string) {
  return fetchApi<{ access_token: string; user: User }>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, name }),
  });
}

export async function getCurrentUser() {
  return fetchApi<User>('/auth/me');
}

export async function getCurrentOrg() {
  return fetchApi<Org>('/auth/me/org');
}

// Organizations
export async function createOrg(name: string) {
  return fetchApi<Org>('/orgs', {
    method: 'POST',
    body: JSON.stringify({ name }),
  });
}

export async function getOrg(orgId: string) {
  return fetchApi<Org>(`/orgs/${orgId}`);
}

// Roles
export async function createRole(orgId: string, data: CreateRoleData) {
  return fetchApi<Role>(`/orgs/${orgId}/roles`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getRoles(orgId: string) {
  return fetchApi<Role[]>(`/orgs/${orgId}/roles`);
}

export async function getRole(roleId: string) {
  return fetchApi<Role>(`/roles/${roleId}`);
}

// Applications
export async function createApplication(roleId: string, data: ApplyData) {
  return fetchApi<Application>(`/applications/roles/${roleId}/apply`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getApplications(roleId: string) {
  return fetchApi<Application[]>(`/roles/${roleId}/applications`);
}

export async function getApplication(applicationId: string) {
  return fetchApi<Application>(`/applications/${applicationId}`);
}

// Simulations
export async function startSimulation(applicationId: string, simulationId: string = 'bugfix_v1') {
  return fetchApi<SimulationRun>(`/runs/applications/${applicationId}/runs`, {
    method: 'POST',
    body: JSON.stringify({ simulation_id: simulationId }),
  });
}

export async function submitSimulation(runId: string, data: SubmitData) {
  // Backend expects multipart form data with 'code' file and 'writeup' form field
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;

  const formData = new FormData();
  // Create a file blob from the code string
  const codeBlob = new Blob([data.code], { type: 'text/plain' });
  formData.append('code', codeBlob, 'submission.py');
  // Writeup as JSON string
  formData.append('writeup', JSON.stringify({ content: data.writeup }));

  try {
    const response = await fetch(`${API_BASE}/runs/${runId}/submit`, {
      method: 'POST',
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
        // Don't set Content-Type - browser will set it with boundary for FormData
      },
      body: formData,
    });

    const responseData = await response.json();

    if (!response.ok) {
      return { error: responseData.detail || 'An error occurred' };
    }

    return { data: responseData as SimulationRun };
  } catch (error) {
    return { error: 'Network error' };
  }
}

export async function getSimulationRun(runId: string) {
  return fetchApi<SimulationRun>(`/runs/${runId}`);
}

// Briefs
export async function getBrief(applicationId: string) {
  return fetchApi<Brief>(`/applications/${applicationId}/brief`);
}

export async function getBriefs(roleId: string) {
  return fetchApi<BriefSummary[]>(`/roles/${roleId}/briefs`);
}

// Types
export interface User {
  id: string;
  email: string;
  name: string;
  role?: 'founder' | 'candidate';
  org_id?: string;
}

export interface Org {
  id: string;
  name: string;
  created_at: string;
}

export interface Role {
  id: string;
  org_id: string;
  title: string;
  status: 'draft' | 'active' | 'closed';
  com: Record<string, unknown>;
  rubric: Record<string, unknown>;
  simulation_ids: string[];
  created_at: string;
}

export interface CreateRoleData {
  title: string;
  interview_answers: Record<string, string>;
}

export interface Application {
  id: string;
  role_id: string;
  candidate_id: string;
  status: 'applied' | 'simulation_started' | 'simulation_completed' | 'evaluated';
  consent_given: boolean;
  applied_at: string;
}

export interface ApplyData {
  name: string;
  email: string;
  consent: boolean;
}

export interface SimulationRun {
  id: string;
  application_id: string;
  simulation_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at?: string;
  completed_at?: string;
}

export interface SubmitData {
  code: string;
  writeup: string;
}

export interface Brief {
  brief_id: string;
  application_id: string;
  candidate_name: string;
  simulation_name: string;
  created_at: string;
  proven_claims: ProvenClaim[];
  unproven_claims: UnprovenClaim[];
  proof_rate: number;
  suggested_interview_questions: string[];
}

export interface BriefSummary {
  brief_id: string;
  application_id: string;
  candidate_name: string;
  proof_rate: number;
  proven_count: number;
  unproven_count: number;
}

export interface ProvenClaim {
  claim_type: string;
  statement: string;
  dimensions: string[];
  evidence_refs: Record<string, unknown>[];
}

export interface UnprovenClaim {
  claim_type: string;
  statement: string;
  dimension: string;
  reason: string;
  suggested_questions: string[];
}
