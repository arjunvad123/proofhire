'use client';

import { useEffect, useState, useCallback, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import {
  searchCandidates,
  getRoles,
  type SearchResults,
  type SearchCandidate,
  type Role,
} from '@/lib/api';
import { Button } from '@/components/ui/button';

export default function SearchPage() {
  return (
    <Suspense fallback={<SearchPageSkeleton />}>
      <SearchPageContent />
    </Suspense>
  );
}

function SearchPageSkeleton() {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-gray-200 p-6 animate-pulse">
        <div className="h-6 w-48 bg-gray-200 rounded mb-4"></div>
        <div className="h-10 bg-gray-200 rounded mb-4"></div>
        <div className="h-10 bg-gray-200 rounded"></div>
      </div>
    </div>
  );
}

function SearchPageContent() {
  const searchParams = useSearchParams();
  const [companyId, setCompanyId] = useState<string | null>(null);
  const [roles, setRoles] = useState<Role[]>([]);
  const [selectedRoleId, setSelectedRoleId] = useState<string>('');
  const [customQuery, setCustomQuery] = useState<string>('');
  const [results, setResults] = useState<SearchResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Get company ID from localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('onboarding-state');
      if (saved) {
        try {
          const state = JSON.parse(saved);
          if (state.companyId) {
            setCompanyId(state.companyId);
          }
        } catch {
          // ignore
        }
      }
    }
  }, []);

  // Load roles
  useEffect(() => {
    if (!companyId) return;

    async function loadRoles() {
      try {
        const rolesData = await getRoles(companyId!);
        setRoles(rolesData);

        // Check for role_id in URL params
        const roleIdParam = searchParams.get('role_id');
        if (roleIdParam && rolesData.some(r => r.id === roleIdParam)) {
          setSelectedRoleId(roleIdParam);
        }
      } catch (err) {
        console.error('Error loading roles:', err);
      }
    }

    loadRoles();
  }, [companyId, searchParams]);

  // Auto-search if role_id is in URL
  useEffect(() => {
    const roleIdParam = searchParams.get('role_id');
    if (roleIdParam && companyId && roles.some(r => r.id === roleIdParam)) {
      handleSearch(roleIdParam);
    }
  }, [companyId, roles, searchParams]);

  const handleSearch = useCallback(async (roleId?: string) => {
    if (!companyId) return;

    const searchRoleId = roleId || selectedRoleId;
    const selectedRole = roles.find(r => r.id === searchRoleId);
    const searchQuery = customQuery || selectedRole?.title;

    if (!searchQuery) {
      setError('Please select a role or enter a search query');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const searchResults = await searchCandidates(companyId, {
        query: searchQuery,
        limit: 50,
      });
      setResults(searchResults);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  }, [companyId, selectedRoleId, customQuery, roles]);

  if (!companyId) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Please complete onboarding first</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Search Controls */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Search for Candidates</h2>

        <div className="space-y-4">
          {/* Role Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select a Role
            </label>
            <select
              value={selectedRoleId}
              onChange={(e) => setSelectedRoleId(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Choose a role...</option>
              {roles.map((role) => (
                <option key={role.id} value={role.id}>
                  {role.title} {role.level && `(${role.level})`}
                </option>
              ))}
            </select>
          </div>

          {/* Or Custom Query */}
          <div className="flex items-center gap-4">
            <div className="flex-1 h-px bg-gray-200"></div>
            <span className="text-sm text-gray-500">or</span>
            <div className="flex-1 h-px bg-gray-200"></div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Custom Search Query
            </label>
            <input
              type="text"
              value={customQuery}
              onChange={(e) => setCustomQuery(e.target.value)}
              placeholder="e.g., ML Engineer with PyTorch experience"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <Button
            onClick={() => handleSearch()}
            loading={loading}
            className="w-full"
            size="lg"
          >
            Search Network
          </Button>
        </div>
      </div>

      {/* Results */}
      {results && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Found {results.total_candidates} candidates for &quot;{results.search_target}&quot;
            </h3>
            <div className="grid grid-cols-4 gap-4">
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{results.tier_1_count}</div>
                <div className="text-sm text-gray-600">In Network</div>
              </div>
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{results.tier_2_count}</div>
                <div className="text-sm text-gray-600">Warm Intros</div>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <div className="text-2xl font-bold text-orange-600">{results.tier_3_count}</div>
                <div className="text-sm text-gray-600">Recruiters</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-600">{results.tier_4_count}</div>
                <div className="text-sm text-gray-600">Cold</div>
              </div>
            </div>
            {results.primary_recommendation && (
              <p className="mt-4 text-sm text-gray-600 bg-blue-50 p-3 rounded-lg">
                {results.primary_recommendation}
              </p>
            )}
          </div>

          {/* Tier 1: Network */}
          {results.tier_1_network && results.tier_1_network.length > 0 && (
            <CandidateTier
              title="Direct Network"
              subtitle="People you know directly"
              candidates={results.tier_1_network}
              tierColor="green"
              tierBadge="NETWORK"
            />
          )}

          {/* Tier 2: Warm Intros */}
          {results.tier_2_one_intro && results.tier_2_one_intro.length > 0 && (
            <CandidateTier
              title="Warm Introductions"
              subtitle="One intro away from your network"
              candidates={results.tier_2_one_intro}
              tierColor="blue"
              tierBadge="WARM"
            />
          )}

          {/* Tier 3: Recruiters */}
          {results.tier_3_recruiters && results.tier_3_recruiters.length > 0 && (
            <CandidateTier
              title="Recruiters in Your Network"
              subtitle="Ask them for referrals"
              candidates={results.tier_3_recruiters}
              tierColor="orange"
              tierBadge="RECRUITER"
            />
          )}

          {/* Tier 4: Cold */}
          {results.tier_4_cold && results.tier_4_cold.length > 0 && (
            <CandidateTier
              title="Cold Outreach"
              subtitle="No direct connection"
              candidates={results.tier_4_cold}
              tierColor="gray"
              tierBadge="COLD"
            />
          )}

          {/* Recruiter Recommendation */}
          {results.recruiter_recommendation && (
            <div className="bg-gradient-to-r from-orange-50 to-yellow-50 rounded-xl border border-orange-200 p-6">
              <h3 className="text-lg font-semibold text-orange-900 mb-2">
                Recruiter Tip
              </h3>
              <p className="text-orange-800">{results.recruiter_recommendation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Candidate Tier Component
function CandidateTier({
  title,
  subtitle,
  candidates,
  tierColor,
  tierBadge,
}: {
  title: string;
  subtitle: string;
  candidates: SearchCandidate[];
  tierColor: 'purple' | 'green' | 'blue' | 'orange' | 'gray';
  tierBadge: string;
}) {
  const [expanded, setExpanded] = useState(true);

  const badgeColors = {
    purple: 'bg-purple-100 text-purple-700',
    green: 'bg-green-100 text-green-700',
    blue: 'bg-blue-100 text-blue-700',
    orange: 'bg-orange-100 text-orange-700',
    gray: 'bg-gray-100 text-gray-700',
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div
        className="p-4 border-b border-gray-200 flex items-center justify-between cursor-pointer hover:bg-gray-50"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <span className={`px-2 py-1 rounded text-xs font-medium ${badgeColors[tierColor]}`}>
            {tierBadge}
          </span>
          <div>
            <h3 className="font-semibold text-gray-900">{title}</h3>
            <p className="text-sm text-gray-500">{subtitle}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-gray-600">{candidates.length} candidates</span>
          <svg
            className={`w-5 h-5 text-gray-400 transition-transform ${expanded ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {expanded && (
        <div className="divide-y divide-gray-100">
          {candidates.map((candidate) => (
            <CandidateCard key={candidate.id} candidate={candidate} tierColor={tierColor} />
          ))}
        </div>
      )}
    </div>
  );
}

// Candidate Card Component
function CandidateCard({
  candidate,
  tierColor,
}: {
  candidate: SearchCandidate;
  tierColor: string;
}) {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div className="p-4 hover:bg-gray-50">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          {/* Avatar */}
          <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center text-gray-600 font-medium">
            {candidate.full_name.charAt(0)}
          </div>

          {/* Info */}
          <div>
            <div className="flex items-center gap-2">
              <span className="font-medium text-gray-900">{candidate.full_name}</span>
              {candidate.is_recruiter && (
                <span className="px-1.5 py-0.5 bg-orange-100 text-orange-700 text-xs rounded">
                  Recruiter
                </span>
              )}
            </div>
            <div className="text-sm text-gray-600">
              {candidate.current_title}
              {candidate.current_company && ` at ${candidate.current_company}`}
            </div>
            {candidate.location && (
              <div className="text-xs text-gray-500 mt-1">{candidate.location}</div>
            )}

            {/* Match Reasons */}
            {candidate.match_reasons && candidate.match_reasons.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {candidate.match_reasons.slice(0, 3).map((reason, i) => (
                  <span key={i} className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded">
                    {reason}
                  </span>
                ))}
              </div>
            )}

            {/* Readiness Signals */}
            {candidate.readiness_signals && candidate.readiness_signals.length > 0 && (
              <div className="mt-1 flex flex-wrap gap-1">
                {candidate.readiness_signals.slice(0, 2).map((signal, i) => (
                  <span key={i} className="px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded">
                    {signal}
                  </span>
                ))}
              </div>
            )}

            {/* Action */}
            {candidate.action && (
              <div className="mt-2 text-xs font-medium text-purple-600">
                {candidate.action}
              </div>
            )}
          </div>
        </div>

        {/* Scores & Actions */}
        <div className="flex items-center gap-4">
          {/* Scores */}
          <div className="text-right">
            <div className="flex items-center gap-2">
              <ScoreBadge label="Warmth" score={candidate.warmth_score} />
              <ScoreBadge label="Ready" score={candidate.readiness_score} />
            </div>
          </div>

          {/* Links */}
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
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="p-2 text-gray-400 hover:bg-gray-100 rounded-lg"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Expanded Details */}
      {showDetails && (
        <div className="mt-4 pt-4 border-t border-gray-100 grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Headline:</span>
            <span className="ml-2 text-gray-900">{candidate.headline || 'N/A'}</span>
          </div>
          <div>
            <span className="text-gray-500">Combined Score:</span>
            <span className="ml-2 text-gray-900">{candidate.combined_score ? `${(candidate.combined_score * 100).toFixed(0)}%` : 'N/A'}</span>
          </div>
          {candidate.recruiter_signals && candidate.recruiter_signals.length > 0 && (
            <div className="col-span-2">
              <span className="text-gray-500">Recruiter Signals:</span>
              <span className="ml-2 text-gray-900">{candidate.recruiter_signals.join(', ')}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Score Badge Component
function ScoreBadge({ label, score }: { label: string; score?: number }) {
  if (score === undefined || score === null) return null;
  const percentage = Math.round(score * 100);
  const color =
    percentage >= 70 ? 'text-green-600 bg-green-50' :
    percentage >= 40 ? 'text-yellow-600 bg-yellow-50' :
    'text-gray-600 bg-gray-50';

  return (
    <div className={`px-2 py-1 rounded text-xs font-medium ${color}`} title={label}>
      {percentage}%
    </div>
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
