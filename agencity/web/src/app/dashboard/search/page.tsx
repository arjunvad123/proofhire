'use client';

import { useEffect, useState, useCallback, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import {
  unifiedSearch,
  getRoles,
  type UnifiedSearchResponse,
  type UnifiedCandidate,
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
  const [results, setResults] = useState<UnifiedSearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastStrategyUsed, setLastStrategyUsed] = useState<'default' | 'broadened' | 'network_only'>('default');

  type SearchRunOptions = {
    queryOverride?: string;
    includeExternal?: boolean;
  };

  const broadenSearchQuery = (query: string): string => {
    const normalized = query.trim();
    if (!normalized) return query;
    return `${normalized} OR software engineer OR backend engineer OR full stack engineer`;
  };

  // Get company ID from localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('onboarding-state');
      if (saved) {
        try {
          const state = JSON.parse(saved);
          if (state.company?.id) {
            setCompanyId(state.company.id);
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

  const handleSearch = useCallback(async (roleId?: string, options: SearchRunOptions = {}) => {
    if (!companyId) return;

    const searchRoleId = roleId || selectedRoleId;
    const selectedRole = roles.find(r => r.id === searchRoleId);
    const searchQuery = options.queryOverride || customQuery || selectedRole?.title;

    if (!searchQuery) {
      setError('Please select a role or enter a search query');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const searchResults = await unifiedSearch({
        companyId,
        roleTitle: searchQuery,
        includeExternal: options.includeExternal ?? true,
        includeTiming: true,
        deepResearch: false,
        limit: 50,
      });
      setResults(searchResults);
      if (options.includeExternal === false) {
        setLastStrategyUsed('network_only');
      } else if (options.queryOverride) {
        setLastStrategyUsed('broadened');
      } else {
        setLastStrategyUsed('default');
      }
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

  // Group candidates by tier for display
  const tier1 = results?.candidates.filter(c => c.tier === 1) || [];
  const tier2 = results?.candidates.filter(c => c.tier === 2) || [];
  const tier3 = results?.candidates.filter(c => c.tier === 3) || [];
  const tier4 = results?.candidates.filter(c => c.tier === 4) || [];

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
                  {String(role.title)} {role.level && `(${String(role.level)})`}
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
          {results.degraded && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="text-sm font-semibold text-amber-900">
                    Search degraded: external yield is low
                  </div>
                  <div className="mt-1 text-sm text-amber-800">
                    Decision confidence: <span className="font-medium">{results.decision_confidence.toUpperCase()}</span>
                  </div>
                  {results.warnings.length > 0 && (
                    <ul className="mt-2 text-xs text-amber-800 list-disc pl-5 space-y-1">
                      {results.warnings.slice(0, 3).map((w, i) => (
                        <li key={i}>{w}</li>
                      ))}
                    </ul>
                  )}
                  {results.recommended_actions.length > 0 && (
                    <div className="mt-3">
                      <div className="text-xs font-semibold text-amber-900">Recommended Next Actions</div>
                      <ul className="mt-1 text-xs text-amber-800 list-disc pl-5 space-y-1">
                        {results.recommended_actions.slice(0, 4).map((action, i) => (
                          <li key={i}>{action}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <div className="mt-3 flex flex-wrap gap-2">
                    <Button
                      size="sm"
                      loading={loading}
                      onClick={async () => {
                        const baseQuery = customQuery || roles.find(r => r.id === selectedRoleId)?.title || results.role_title;
                        const broadened = broadenSearchQuery(baseQuery);
                        setCustomQuery(broadened);
                        await handleSearch(undefined, { queryOverride: broadened, includeExternal: true });
                      }}
                    >
                      Retry Broadened Query
                    </Button>
                    <Button
                      size="sm"
                      variant="secondary"
                      loading={loading}
                      onClick={async () => {
                        await handleSearch(undefined, { includeExternal: false });
                      }}
                    >
                      Run Network-Only Confidence Mode
                    </Button>
                  </div>
                </div>
                <div className="text-right text-xs text-amber-700">
                  <div>Clado: {results.external_provider_health?.clado?.ok ? 'ok' : 'down'}</div>
                  <div>PDL: {results.external_provider_health?.pdl?.ok ? 'ok' : 'down'}</div>
                </div>
              </div>
            </div>
          )}

          {/* Summary */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Found {results.total_found} candidates for &quot;{results.role_title}&quot;
            </h3>
            <div className="mb-4 flex flex-wrap items-center gap-2">
              <span className="px-2 py-1 rounded text-xs font-medium bg-indigo-100 text-indigo-700">
                Strategy: {lastStrategyUsed === 'default' ? 'DEFAULT' : lastStrategyUsed === 'broadened' ? 'BROADENED' : 'NETWORK_ONLY'}
              </span>
              <span className={`px-2 py-1 rounded text-xs font-medium ${results.external_yield_ok ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
                External Yield: {results.external_yield_ok ? 'OK' : 'LOW'}
              </span>
              <span className={`px-2 py-1 rounded text-xs font-medium ${results.decision_confidence === 'high' ? 'bg-green-100 text-green-700' : results.decision_confidence === 'medium' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}`}>
                Decision Confidence: {results.decision_confidence.toUpperCase()}
              </span>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{results.tier_1_network}</div>
                <div className="text-sm text-gray-600">In Network</div>
              </div>
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{results.tier_2_warm}</div>
                <div className="text-sm text-gray-600">Warm Intros</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-600">{results.tier_3_cold}</div>
                <div className="text-sm text-gray-600">Cold / Other</div>
              </div>
            </div>
            <div className="mt-4 text-xs text-gray-400 text-center">
              Search took {results.search_duration_seconds.toFixed(2)}s
            </div>
          </div>

          {/* Tier 1: Network */}
          {tier1.length > 0 && (
            <CandidateTier
              title="Direct Network"
              subtitle="People you know directly"
              candidates={tier1}
              tierColor="green"
              tierBadge="NETWORK"
            />
          )}

          {/* Tier 2: Warm Intros */}
          {tier2.length > 0 && (
            <CandidateTier
              title="Warm Introductions"
              subtitle="One intro away from your network"
              candidates={tier2}
              tierColor="blue"
              tierBadge="WARM"
            />
          )}

          {/* Tier 3: Cold / Others (Unified maps cold to tier 3 usually) */}
          {tier3.length > 0 && (
            <CandidateTier
              title="Cold Outreach"
              subtitle="No direct connection"
              candidates={tier3}
              tierColor="gray"
              tierBadge="COLD"
            />
          )}

          {/* Tier 4: Fallback if any */}
          {tier4.length > 0 && (
            <CandidateTier
              title="Others"
              subtitle="Additional matches"
              candidates={tier4}
              tierColor="gray"
              tierBadge="OTHER"
            />
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
  candidates: UnifiedCandidate[];
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
            <CandidateCard key={candidate.id} candidate={candidate} />
          ))}
        </div>
      )}
    </div>
  );
}

// Candidate Card Component
function CandidateCard({
  candidate,
}: {
  candidate: UnifiedCandidate;
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
            </div>
            <div className="text-sm text-gray-600">
              {candidate.current_title}
              {candidate.current_company && ` at ${candidate.current_company}`}
            </div>
            {candidate.location && (
              <div className="text-xs text-gray-500 mt-1">{candidate.location}</div>
            )}

            {/* Why Consider (Match Reasons) */}
            {candidate.why_consider && candidate.why_consider.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {candidate.why_consider.slice(0, 3).map((reason, i) => (
                  <span key={i} className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded">
                    {reason}
                  </span>
                ))}
              </div>
            )}

            {/* Warm Path Info */}
            {candidate.has_warm_path && candidate.warm_path_connector && (
              <div className="mt-2 text-xs font-medium text-blue-600">
                via {candidate.warm_path_connector} ({candidate.warm_path_relationship || 'Connection'})
              </div>
            )}
          </div>
        </div>

        {/* Scores & Actions */}
        <div className="flex items-center gap-4">
          {/* Scores */}
          <div className="text-right">
            <div className="flex items-center gap-2">
              <ScoreBadge label="Match" score={candidate.fit_score / 100} />
              {candidate.warmth_score > 0 && <ScoreBadge label="Warmth" score={candidate.warmth_score / 100} />}
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
            <span className="text-gray-500">Source:</span>
            <span className="ml-2 text-gray-900">{candidate.source}</span>
          </div>
          <div>
            <span className="text-gray-500">Combined Score:</span>
            <span className="ml-2 text-gray-900">{candidate.combined_score ? `${(candidate.combined_score).toFixed(0)}` : 'N/A'}</span>
          </div>
          {candidate.intro_message && (
            <div className="col-span-2 bg-blue-50 p-3 rounded">
              <span className="text-xs font-bold text-blue-700 block mb-1">DRAFT INTRO:</span>
              <p className="text-blue-900 italic">&quot;{candidate.intro_message}&quot;</p>
            </div>
          )}
          {candidate.research_highlights && candidate.research_highlights.length > 0 && (
            <div className="col-span-2">
              <span className="text-gray-500 block mb-1">Research Highlights:</span>
              <ul className="list-disc pl-5 space-y-1">
                {candidate.research_highlights.map((h, i) => (
                  <li key={i} className="text-gray-900">{h}</li>
                ))}
              </ul>
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
