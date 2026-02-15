'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  curateCandidates,
  getCandidateContext,
  getRoles,
  recordCandidateFeedback,
  type CurationResults,
  type CuratedCandidate,
  type CandidateContext,
  type Role,
} from '@/lib/api';
import { Button } from '@/components/ui/button';
import CurationSummary from '@/components/CurationSummary';

export default function CurationPage() {
  const [companyId, setCompanyId] = useState<string | null>(null);
  const [roles, setRoles] = useState<Role[]>([]);
  const [selectedRoleId, setSelectedRoleId] = useState<string>('');
  const [results, setResults] = useState<CurationResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Get company ID from localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('onboarding-state');
      if (saved) {
        try {
          const state = JSON.parse(saved);
          if (state.company?.id) {
            setCompanyId(state.company.id);
            return;
          }
        } catch (error) {
          console.error('Failed to parse onboarding state:', error);
        }
      }
      // Fallback to Confido for demo
      setCompanyId("100b5ac1-1912-4970-a378-04d0169fd597");
    }
  }, []);

  // Load roles
  useEffect(() => {
    if (!companyId) return;

    async function loadRoles() {
      try {
        const rolesData = await getRoles(companyId!);
        setRoles(rolesData);
      } catch (err) {
        console.error('Error loading roles:', err);
      }
    }

    loadRoles();
  }, [companyId]);

  const handleCurate = useCallback(async () => {
    if (!companyId || !selectedRoleId) {
      setError('Please select a role');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const curationResults = await curateCandidates(companyId, selectedRoleId, {
        limit: 15,
      });
      setResults(curationResults);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Curation failed');
    } finally {
      setLoading(false);
    }
  }, [companyId, selectedRoleId]);

  if (!companyId) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Please complete onboarding first</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 pt-6">
      {/* Curation Controls */}
      <div className="bg-white rounded-2xl border border-gray-100 p-8 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Curate Candidates</h2>

        <div className="space-y-4">
          {/* Role Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select a Role to Curate For
            </label>
            <select
              value={selectedRoleId}
              onChange={(e) => setSelectedRoleId(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
            >
              <option value="">Choose a role...</option>
              {roles.map((role) => (
                <option key={role.id} value={role.id}>
                  {role.title} {role.status && `(${role.status})`}
                </option>
              ))}
            </select>
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <Button
            onClick={handleCurate}
            loading={loading}
            className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
            size="lg"
          >
            {loading ? 'Curating...' : '🔬 Curate Candidates'}
          </Button>
        </div>
      </div>

      {/* Results */}
      {results && (
        <div className="space-y-6">
          {/* Stats Summary */}
          {/* Candidate List */}
          <div className="space-y-4">
            {results.candidates.map((candidate, index) => (
              <CandidateCard
                key={`candidate-${index}-${candidate.person_id || 'unknown'}`}
                candidate={candidate}
                rank={index + 1}
                roleId={results.role_id}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Candidate Card Component
function CandidateCard({
  candidate,
  rank,
  roleId,
}: {
  candidate: CuratedCandidate;
  rank: number;
  roleId: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const [context, setContext] = useState<CandidateContext | null>(null);
  const [loadingContext, setLoadingContext] = useState(false);
  const [recordingFeedback, setRecordingFeedback] = useState(false);
  const [feedbackStatus, setFeedbackStatus] = useState<string | null>(null);

  const handleFeedback = async (decision: string) => {
    setRecordingFeedback(true);
    try {
      await recordCandidateFeedback(candidate.person_id, roleId, decision);
      setFeedbackStatus(decision);
    } catch (err) {
      console.error('Failed to record feedback:', err);
      alert('Failed to record selection');
    } finally {
      setRecordingFeedback(false);
    }
  };

  const loadContext = async () => {
    if (context) {
      setExpanded(!expanded);
      return;
    }

    setLoadingContext(true);
    try {
      const contextData = await getCandidateContext(candidate.person_id, roleId);
      setContext(contextData);
      setExpanded(true);
    } catch (err) {
      console.error('Failed to load context:', err);
    } finally {
      setLoadingContext(false);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      {/* Card Header */}
      <div className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-4 flex-1">
            {/* Rank Badge */}
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center text-white font-bold">
              #{rank}
            </div>

            {/* Candidate Info */}
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h3 className="text-lg font-semibold text-gray-900">
                  {candidate.full_name}
                </h3>
                {candidate.was_enriched && (
                  <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded font-medium">
                    Enriched
                  </span>
                )}
              </div>

              <div className="text-sm text-gray-600 mb-2">
                {candidate.current_title}
                {candidate.current_company && ` @ ${candidate.current_company}`}
              </div>

              {candidate.location && (
                <div className="text-xs text-gray-500">{candidate.location}</div>
              )}

              {/* Score Badges */}
              <div className="flex items-center gap-2 mt-3">
                <ScoreBadge
                  label="Match"
                  score={candidate.match_score}
                  max={100}
                />
                <ScoreBadge
                  label="Confidence"
                  score={candidate.fit_confidence * 100}
                  max={100}
                />
                <ScoreBadge
                  label="Data"
                  score={candidate.data_completeness * 100}
                  max={100}
                />
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {candidate.linkedin_url && (
              <a
                href={candidate.linkedin_url}
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                title="View LinkedIn"
              >
                <LinkedInIcon className="w-5 h-5" />
              </a>
            )}
            {candidate.github_url && (
              <a
                href={candidate.github_url}
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                title="View GitHub"
              >
                <GitHubIcon className="w-5 h-5" />
              </a>
            )}
          </div>
        </div>

        {/* Why Consider - from Context */}
        {candidate.context.why_consider && candidate.context.why_consider.length > 0 && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <h4 className="text-sm font-semibold text-green-900 mb-2">
              Why Consider
            </h4>
            <ul className="space-y-1 text-sm text-green-800">
              {candidate.context.why_consider.map((wc, i) => (
                // Handle if it's an object (WhyConsiderPoint) or string
                <li key={`why-${candidate.person_id}-${i}`} className="flex items-start gap-2">
                  <span className="text-green-500 mt-1">✓</span>
                  <span>
                    {typeof wc === 'string'
                      ? wc
                      : `${wc.points?.[0] || 'Strong match'} (${wc.category || 'General'})`}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Unknowns - from Context */}
        {candidate.context.unknowns && candidate.context.unknowns.length > 0 && (
          <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <h4 className="text-sm font-semibold text-yellow-900 mb-2">
              Unknowns
            </h4>
            <ul className="space-y-1 text-sm text-yellow-800">
              {candidate.context.unknowns.map((unknown, i) => (
                <li key={`unknown-${candidate.person_id}-${i}`} className="flex items-start gap-2">
                  <span className="text-yellow-500 mt-1">?</span>
                  <span>{unknown}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Warm Path - from Context */}
        {candidate.context.warm_path && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-900">
            <span className="font-medium">Warm Path:</span> {candidate.context.warm_path}
          </div>
        )}

        {/* Expand for More Details */}
        <button
          onClick={loadContext}
          disabled={loadingContext}
          className="mt-4 w-full py-2 text-sm text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
        >
          {loadingContext ? 'Loading...' : expanded ? 'Hide Details' : 'View Full Analysis →'}
        </button>

        {/* Expanded Context */}
        {expanded && context && (
          <div className="mt-4 pt-4 border-t border-gray-200 space-y-4">
            {/* Skills Match logic removed for brevity as it depends on detailed_analysis which might differ */}
          </div>
        )}
      </div>

      {/* Action Footer */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex items-center justify-end gap-3">
        {feedbackStatus ? (
          <div className="flex items-center gap-2 text-sm font-medium text-green-600">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            Decision: {feedbackStatus.toUpperCase()} recorded
          </div>
        ) : (
          <>
            <button
              onClick={() => handleFeedback('pass')}
              disabled={recordingFeedback}
              className="px-4 py-2 text-sm text-gray-600 hover:bg-white hover:text-red-600 hover:border-red-200 rounded-lg border border-gray-300 transition-all disabled:opacity-50"
            >
              Pass
            </button>
            <button
              onClick={() => handleFeedback('need_more_info')}
              disabled={recordingFeedback}
              className="px-4 py-2 text-sm text-blue-600 hover:bg-blue-100 rounded-lg border border-blue-200 transition-all disabled:opacity-50"
            >
              Need More Info
            </button>
            <button
              onClick={() => handleFeedback('interview')}
              disabled={recordingFeedback}
              className="px-4 py-2 text-sm text-white bg-green-600 hover:bg-green-700 rounded-lg shadow-sm hover:shadow-md transition-all disabled:opacity-50"
            >
              {recordingFeedback ? 'Recording...' : 'Approve for Pipeline'}
            </button>
          </>
        )}
      </div>
    </div>
  );
}

// Score Badge Component
function ScoreBadge({
  label,
  score,
  max,
}: {
  label: string;
  score: number;
  max: number;
}) {
  const percentage = (score / max) * 100;
  const color =
    percentage >= 70
      ? 'text-green-700 bg-green-100'
      : percentage >= 40
        ? 'text-yellow-700 bg-yellow-100'
        : 'text-red-700 bg-red-100';

  return (
    <div className={`px-2 py-1 rounded text-xs font-medium ${color}`}>
      {label}: {score.toFixed(0)}/{max}
    </div>
  );
}

// Confidence Badge Component
function ConfidenceBadge({ confidence }: { confidence: 'HIGH' | 'MEDIUM' | 'LOW' }) {
  const colors = {
    HIGH: 'bg-green-100 text-green-700',
    MEDIUM: 'bg-yellow-100 text-yellow-700',
    LOW: 'bg-red-100 text-red-700',
  };

  return (
    <span className={`px-2 py-0.5 text-xs rounded ${colors[confidence]}`}>
      {confidence}
    </span>
  );
}

// Icons
function LinkedInIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
    </svg>
  );
}

function GitHubIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
    </svg>
  );
}
