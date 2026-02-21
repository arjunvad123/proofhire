/**
 * TypeScript types mirroring Agencity backend Pydantic models
 */

// ─── Company & Onboarding ───────────────────────────────────────────────────

export interface CompanyCreate {
  name: string;
  founder_email: string;
  founder_name: string;
  domain?: string;
  stage?: string;
  industry?: string;
  tech_stack: string[];
  team_size?: number;
}

export interface Company {
  id: string;
  name: string;
  founder_email: string;
  founder_name: string;
  domain?: string;
  stage?: string;
  industry?: string;
  tech_stack: string[];
  team_size?: number;
  linkedin_imported: boolean;
  existing_db_imported: boolean;
  onboarding_complete: boolean;
  created_at: string;
  updated_at: string;
}

export interface CompanyWithDetails extends Company {
  umo?: CompanyUMO;
  roles: Role[];
  recent_imports: DataSource[];
}

export interface CompanyCreateResponse {
  company: Company;
  api_key: string;
  api_key_prefix: string;
  next_steps: string[];
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

// ─── Roles ──────────────────────────────────────────────────────────────────

export type RoleLevel =
  | 'intern'
  | 'junior'
  | 'mid'
  | 'senior'
  | 'staff'
  | 'principal'
  | 'director'
  | 'vp'
  | 'c_level';

export type RoleStatus = 'active' | 'paused' | 'filled' | 'closed';

export interface RoleCreate {
  title: string;
  level?: RoleLevel;
  department?: string;
  required_skills: string[];
  preferred_skills?: string[];
  years_experience_min?: number;
  years_experience_max?: number;
  description?: string;
  location?: string;
  salary_min?: number;
  salary_max?: number;
}

export interface Role {
  id: string;
  company_id: string;
  title: string;
  level?: RoleLevel;
  department?: string;
  required_skills: string[];
  preferred_skills: string[];
  years_experience_min?: number;
  years_experience_max?: number;
  description?: string;
  location?: string;
  salary_min?: number;
  salary_max?: number;
  status: RoleStatus;
  created_at: string;
  updated_at: string;
}

// ─── Data Import ────────────────────────────────────────────────────────────

export type ImportStatus = 'completed' | 'processing' | 'pending' | 'failed';

export interface DataSource {
  source_id: string;
  status: ImportStatus;
  total_records: number;
  records_created: number;
  records_matched: number;
  records_failed: number;
  errors: string[];
}

// ─── Search ─────────────────────────────────────────────────────────────────

export interface SearchRequest {
  company_id?: string;
  role_title: string;
  required_skills: string[];
  preferred_skills?: string[];
  location?: string;
  years_experience?: number;
  include_external?: boolean;
  include_timing?: boolean;
  deep_research?: boolean;
  limit?: number;
}

export interface SearchResponse {
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
  warnings: string[];
  degraded: boolean;
  decision_confidence: string;
  recommended_actions: string[];
  candidates: CandidateResponse[];
}

export interface CandidateResponse {
  id: string;
  full_name: string;
  current_title?: string;
  current_company?: string;
  location?: string;
  linkedin_url?: string;
  github_url?: string;
  fit_score: number;
  warmth_score: number;
  timing_score: number;
  combined_score: number;
  tier: 1 | 2 | 3;
  tier_label: string;
  source: 'network' | 'external';
  timing_urgency: 'high' | 'medium' | 'low';
  has_warm_path: boolean;
  warm_path_type?: string;
  warm_path_connector?: string;
  warm_path_relationship?: string;
  intro_message?: string;
  why_consider: string[];
  unknowns: string[];
  research_highlights: string[];
}

// ─── Curation ───────────────────────────────────────────────────────────────

export interface CurationRequest {
  company_id?: string;
  role_id: string;
  limit?: number;
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
  skills: string[];
  experience: Record<string, unknown>[];
  education: Record<string, unknown>[];
  match_score: number;
  fit_confidence: number;
  context: CandidateContext;
  was_enriched: boolean;
  data_completeness: number;
}

export interface CandidateContext {
  why_consider: Array<{ reason: string; evidence?: string }>;
  unknowns: string[];
  standout_signal?: string;
  warm_path: string;
  enrichment_details?: Record<string, unknown>;
  claude_reasoning?: {
    overall_assessment?: string;
    skill_reasoning?: string;
    trajectory_reasoning?: string;
    fit_reasoning?: string;
    timing_reasoning?: string;
    concerns?: string[];
  };
}

export interface CurationResponse {
  shortlist: CuratedCandidate[];
  total_searched: number;
  processing_time_seconds: number;
  metadata: {
    avg_match_score: number;
    enriched_count: number;
    avg_confidence: number;
    completeness: {
      high: number;
      medium: number;
      low: number;
    };
  };
}

export interface CandidateContextResponse {
  person_id: string;
  full_name: string;
  match_score: number;
  fit_confidence: number;
  context: CandidateContext;
  candidate_data: {
    headline: string;
    location: string;
    current_company: string;
    current_title: string;
    linkedin_url: string;
    github_url: string;
    data_completeness: number;
  };
}

export interface AISummary {
  overall_assessment: string;
  why_consider: string[];
  concerns: string[];
  unknowns: string[];
  skill_reasoning: string;
  trajectory_reasoning: string;
  fit_reasoning: string;
  timing_reasoning: string;
}

// ─── Pipeline ───────────────────────────────────────────────────────────────

export type PipelineStatus = 'sourced' | 'contacted' | 'scheduled';

export interface PipelineCandidate {
  id: string;
  agencity_candidate_id: string;
  name: string;
  email?: string;
  title?: string;
  company?: string;
  warmth_score: number;
  warmth_level: string;
  warm_path?: {
    type: string;
    description: string;
    connector?: string;
  };
  status: PipelineStatus;
  sourced_at: string;
  contacted_at?: string;
  scheduled_at?: string;
}

export interface PipelineResponse {
  candidates: PipelineCandidate[];
  total: number;
  by_status: Record<PipelineStatus, number>;
}

export interface StatusUpdateResponse {
  id: string;
  status: PipelineStatus;
  contacted_at?: string;
  scheduled_at?: string;
  updated_at: string;
}

// ─── Feedback ───────────────────────────────────────────────────────────────

export type FeedbackAction =
  | 'hired'
  | 'interviewed'
  | 'contacted'
  | 'saved'
  | 'viewed'
  | 'rejected'
  | 'ignored';

export interface FeedbackRequest {
  company_id?: string;
  candidate_id: string;
  search_id?: string;
  action: FeedbackAction;
  proofhire_score?: number;
  proofhire_application_id?: string;
  notes?: string;
  metadata?: Record<string, unknown>;
}

export interface FeedbackStats {
  total_feedback: number;
  by_action: Record<FeedbackAction, number>;
  proofhire_integration: {
    total_invited: number;
    total_completed: number;
    completion_rate: number;
    avg_score?: number;
  };
}

// ─── ProofHire Integration ──────────────────────────────────────────────────

export interface ProofHireInviteRequest {
  company_id?: string;
  candidate_id: string;
  proofhire_role_id: string;
  search_id?: string;
}

export interface ProofHireInviteResponse {
  linkage_id: string;
  candidate_id: string;
  proofhire_application_id: string;
  proofhire_role_id: string;
  status: string;
}

// ─── Curation Cache ─────────────────────────────────────────────────────────

export interface CurationCacheResponse {
  role_id: string;
  role_title: string;
  status: 'pending' | 'processing' | 'cached' | 'failed';
  shortlist: CuratedCandidate[];
  total_searched: number;
  enriched_count: number;
  avg_match_score: number;
  generated_at: string;
  expires_at: string;
  from_cache: boolean;
}

// ─── Provider Health ────────────────────────────────────────────────────────

export interface ProviderHealth {
  status: 'healthy' | 'degraded';
  unified_search: boolean;
  features: {
    network_search: boolean;
    external_search: boolean;
    warm_path_finding: boolean;
    timing_intelligence: boolean;
    deep_research: boolean;
  };
}

// ─── Network ────────────────────────────────────────────────────────────────

export interface NetworkIndex {
  company_id: string;
  total_contacts: number;
  unique_companies: number;
  unique_schools: number;
  unique_skills: number;
  top_companies: Array<{ name: string; count: number }>;
  top_schools: Array<{ name: string; count: number }>;
  indexed: boolean;
}

// ─── Timing & Intelligence ──────────────────────────────────────────────────

export interface TimingAlert {
  id: string;
  candidate_name: string;
  candidate_id: string;
  urgency: 'high' | 'medium' | 'low';
  signal_type: string;
  description: string;
  detected_at: string;
}

export interface CompanyEvent {
  id: string;
  company_name: string;
  event_type: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  detected_at: string;
}

// ─── Activation / Intro Messages ────────────────────────────────────────────

export interface IntroRequest {
  company_id?: string;
  role_title: string;
  required_skills?: string[];
  target_person_ids?: string[];
  limit?: number;
  save_to_db?: boolean;
}

export interface IntroRequestResponse {
  requests_count: number;
  requests: Array<{
    person_id: string;
    connector_name: string;
    message: string;
    warm_path: string;
  }>;
  summary: Record<string, unknown>;
}

// ─── API Key Management ─────────────────────────────────────────────────────

export interface ApiKeyInfo {
  id: string;
  key_prefix: string;
  name: string;
  scopes: string[];
  is_active: boolean;
  last_used_at?: string;
  created_at: string;
}

// ─── Generic API Response ───────────────────────────────────────────────────

export interface ApiResponse<T> {
  data?: T;
  error?: string;
}
