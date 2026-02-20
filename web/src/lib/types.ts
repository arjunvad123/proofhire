/**
 * Shared TypeScript types for ProofHire
 */

// Company Operating Model
export interface CompanyOperatingModel {
  pace: 'high' | 'medium' | 'low';
  quality_bar: 'high' | 'medium' | 'low';
  ambiguity_tolerance: 'high' | 'medium' | 'low';
  collaboration_style: 'async' | 'sync' | 'hybrid';
  priorities: string[];
}

// Role Rubric
export interface RoleRubric {
  dimensions: RubricDimension[];
}

export interface RubricDimension {
  name: string;
  weight: number;
  description: string;
  signals: string[];
}

// Role Spec Interview
export interface InterviewQuestion {
  id: string;
  question: string;
  type: 'choice' | 'multiselect' | 'text';
  options?: string[];
  required: boolean;
}

export interface InterviewAnswer {
  question_id: string;
  answer: string | string[];
}

// Simulation
export interface SimulationDefinition {
  id: string;
  name: string;
  description: string;
  type: 'bugfix' | 'feature' | 'refactor';
  difficulty: 'easy' | 'medium' | 'hard';
  time_limit_minutes: number;
  languages: string[];
  dimensions: string[];
  candidate_instructions: string;
  writeup_prompts: string[];
}

// Evidence
export interface EvidenceRef {
  type: 'metric' | 'artifact' | 'llm_tag';
  id: string;
  field: string;
  value: unknown;
}

// Brief
export interface CandidateBrief {
  brief_id: string;
  application_id: string;
  candidate_id: string;
  candidate_name: string;
  role_id: string;
  simulation_id: string;
  simulation_name: string;
  created_at: string;
  simulation_completed_at: string;
  time_to_complete_seconds: number;
  proven_claims: ProvenClaim[];
  unproven_claims: UnprovenClaim[];
  risk_flags: RiskFlag[];
  total_claims: number;
  proven_count: number;
  unproven_count: number;
  proof_rate: number;
  dimensions_covered: Record<string, 'proven' | 'unproven' | 'not_evaluated'>;
  suggested_interview_questions: string[];
}

export interface ProvenClaim {
  claim_type: string;
  statement: string;
  dimensions: string[];
  evidence_refs: EvidenceRef[];
  rule_id: string;
  confidence: number;
}

export interface UnprovenClaim {
  claim_type: string;
  statement: string;
  dimension: string;
  reason: string;
  next_step: string;
  suggested_questions: string[];
}

export interface RiskFlag {
  flag_type: string;
  severity: 'low' | 'medium' | 'high';
  description: string;
}

// Claim types for display
export const CLAIM_DISPLAY_NAMES: Record<string, string> = {
  debugging_effective: 'Effective Debugging',
  added_regression_test: 'Added Regression Test',
  testing_discipline: 'Testing Discipline',
  handles_edge_cases: 'Handles Edge Cases',
  communication_clear: 'Clear Communication',
  time_efficient: 'Time Efficient',
};

// Dimension types for display
export const DIMENSION_DISPLAY_NAMES: Record<string, string> = {
  debugging_method: 'Debugging Method',
  testing_discipline: 'Testing Discipline',
  correctness: 'Correctness',
  shipping_speed: 'Shipping Speed',
  communication: 'Communication',
};
