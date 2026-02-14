'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getCurrentOrg, getRoles, type Role } from '@/lib/api';

// Types
interface AgencityCandidate {
  id: string;
  name: string;
  email: string;
  title: string;
  company: string;
  location: string;
  score: number;
  fit_score: number;
  warmth_score: number;
  warmth_level: 'network' | 'warm' | 'cold';
  warm_path?: {
    type: 'direct' | 'school' | 'company' | '2nd_degree';
    description: string;
    connector?: string;
  };
  linkedin_url?: string;
  skills: string[];
  timing_signals?: string[];
  status?: 'sourced' | 'contacted' | 'interviewing' | 'invited' | 'in_simulation' | 'reviewed';
}

interface NetworkStats {
  total_contacts: number;
  companies: number;
  schools: number;
  engineers: number;
}

interface SearchHistory {
  id: string;
  query: string;
  results_count: number;
  timestamp: string;
}

export default function UnifiedDashboard() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [candidates, setCandidates] = useState<AgencityCandidate[]>([]);
  const [networkStats, setNetworkStats] = useState<NetworkStats | null>(null);
  const [searchHistory, setSearchHistory] = useState<SearchHistory[]>([]);
  const [savedCandidates, setSavedCandidates] = useState<AgencityCandidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [orgId, setOrgId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'search' | 'pipeline' | 'network'>('overview');

  useEffect(() => {
    getCurrentOrg().then((orgResult) => {
      if (orgResult.data) {
        setOrgId(orgResult.data.id);
        loadDashboardData(orgResult.data.id);
      } else {
        setLoading(false);
      }
    });
  }, []);

  async function loadDashboardData(organizationId: string) {
    setLoading(true);
    try {
      // Load ProofHire data
      const rolesResult = await getRoles(organizationId);
      if (rolesResult.data) {
        setRoles(rolesResult.data);
      }

      // TODO: Load Agencity data from API
      // Mock data for now
      setNetworkStats({
        total_contacts: 1247,
        companies: 312,
        schools: 89,
        engineers: 423,
      });

      // Mock candidates
      setCandidates([
        {
          id: '1',
          name: 'Sarah Chen',
          email: 'sarah.chen@example.com',
          title: 'Senior ML Engineer',
          company: 'Google',
          location: 'San Francisco, CA',
          score: 94,
          fit_score: 85,
          warmth_score: 100,
          warmth_level: 'network',
          warm_path: {
            type: 'direct',
            description: 'You met at YC Demo Day 2022',
          },
          linkedin_url: 'https://linkedin.com/in/sarachen',
          skills: ['Python', 'PyTorch', 'ML', 'TensorFlow'],
          timing_signals: ['4-year cliff approaching', 'Profile updated recently'],
          status: 'sourced',
        },
        {
          id: '2',
          name: 'Mike Johnson',
          email: 'mike.j@example.com',
          title: 'ML Lead',
          company: 'Meta',
          location: 'Menlo Park, CA',
          score: 91,
          fit_score: 88,
          warmth_score: 90,
          warmth_level: 'network',
          warm_path: {
            type: 'company',
            description: 'Former colleague at Startup X',
          },
          linkedin_url: 'https://linkedin.com/in/mikejohnson',
          skills: ['Machine Learning', 'Python', 'React', 'Leadership'],
          timing_signals: ['Profile updated this week'],
          status: 'contacted',
        },
        {
          id: '3',
          name: 'Emily Zhang',
          email: 'emily.zhang@example.com',
          title: 'Staff ML Engineer',
          company: 'Anthropic',
          location: 'San Francisco, CA',
          score: 88,
          fit_score: 90,
          warmth_score: 75,
          warmth_level: 'warm',
          warm_path: {
            type: '2nd_degree',
            description: 'Both attended Stanford CS PhD program',
            connector: 'David Lee',
          },
          linkedin_url: 'https://linkedin.com/in/emilyzhang',
          skills: ['Deep Learning', 'PyTorch', 'Python', 'Research'],
          timing_signals: ['Open to Work badge'],
          status: 'invited',
        },
      ]);

      setSavedCandidates([]);

      setSearchHistory([
        {
          id: '1',
          query: 'ML Engineer',
          results_count: 47,
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: '2',
          query: 'Backend Engineer',
          results_count: 32,
          timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        },
      ]);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const candidatesByStatus = {
    sourced: candidates.filter((c) => c.status === 'sourced'),
    contacted: candidates.filter((c) => c.status === 'contacted'),
    invited: candidates.filter((c) => c.status === 'invited'),
    in_simulation: candidates.filter((c) => c.status === 'in_simulation'),
    reviewed: candidates.filter((c) => c.status === 'reviewed'),
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-8">
              <h1 className="text-2xl font-bold text-black">ProofHire</h1>
              <nav className="flex items-center gap-1">
                <TabButton
                  active={activeTab === 'overview'}
                  onClick={() => setActiveTab('overview')}
                >
                  Overview
                </TabButton>
                <TabButton
                  active={activeTab === 'search'}
                  onClick={() => setActiveTab('search')}
                >
                  Search
                </TabButton>
                <TabButton
                  active={activeTab === 'pipeline'}
                  onClick={() => setActiveTab('pipeline')}
                >
                  Pipeline
                </TabButton>
                <TabButton
                  active={activeTab === 'network'}
                  onClick={() => setActiveTab('network')}
                >
                  Network
                </TabButton>
              </nav>
            </div>
            <div className="flex items-center gap-3">
              <button className="p-2 hover:bg-gray-50 rounded-lg">
                <BellIcon />
              </button>
              <button className="p-2 hover:bg-gray-50 rounded-lg">
                <UserIcon />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {activeTab === 'overview' && (
          <OverviewTab
            networkStats={networkStats}
            roles={roles}
            candidates={candidates}
            candidatesByStatus={candidatesByStatus}
            searchHistory={searchHistory}
          />
        )}
        {activeTab === 'search' && (
          <SearchTab
            searchHistory={searchHistory}
            roles={roles}
          />
        )}
        {activeTab === 'pipeline' && (
          <PipelineTab
            candidates={candidates}
            candidatesByStatus={candidatesByStatus}
          />
        )}
        {activeTab === 'network' && (
          <NetworkTab networkStats={networkStats} />
        )}
      </main>
    </div>
  );
}

// Tab Components
function OverviewTab({
  networkStats,
  roles,
  candidates,
  candidatesByStatus,
  searchHistory,
}: {
  networkStats: NetworkStats | null;
  roles: Role[];
  candidates: AgencityCandidate[];
  candidatesByStatus: Record<string, AgencityCandidate[]>;
  searchHistory: SearchHistory[];
}) {
  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-6">
        <StatCard
          title="Network Size"
          value={networkStats?.total_contacts.toLocaleString() || '0'}
          subtitle="imported connections"
          bgColor="bg-blue-50"
          textColor="text-blue-700"
        />
        <StatCard
          title="Active Roles"
          value={roles.filter((r) => r.status === 'active').length.toString()}
          subtitle={`of ${roles.length} total`}
          bgColor="bg-green-50"
          textColor="text-green-700"
        />
        <StatCard
          title="In Pipeline"
          value={candidates.length.toString()}
          subtitle="candidates tracking"
          bgColor="bg-purple-50"
          textColor="text-purple-700"
        />
        <StatCard
          title="In Evaluation"
          value={candidatesByStatus.in_simulation.length.toString()}
          subtitle="active simulations"
          bgColor="bg-yellow-50"
          textColor="text-yellow-700"
        />
      </div>

      {/* Search Bar */}
      <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-black mb-4">Find Candidates</h2>
        <div className="flex gap-3">
          <input
            type="text"
            placeholder="What role are you hiring for?"
            className="flex-1 px-5 py-3 rounded-2xl border-gray-200 bg-gray-50 focus:ring-2 focus:ring-blue-500/20 outline-none"
          />
          <button className="px-6 py-3 bg-blue-600 text-white rounded-2xl font-medium hover:bg-blue-700">
            Search
          </button>
        </div>
        <div className="mt-3 flex items-center gap-2 text-sm text-gray-500">
          <span>Quick:</span>
          <button className="text-blue-600 hover:underline">ML Engineer</button>
          <span>•</span>
          <button className="text-blue-600 hover:underline">Backend Engineer</button>
          <span>•</span>
          <button className="text-blue-600 hover:underline">Product Manager</button>
        </div>
      </div>

      {/* Candidate Pipeline Preview */}
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-black">Recent Candidates</h3>
            <Link href="#" className="text-sm text-blue-600 hover:underline">
              View All
            </Link>
          </div>
          <div className="space-y-3">
            {candidates.slice(0, 3).map((candidate) => (
              <CandidateCard key={candidate.id} candidate={candidate} compact />
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-black">Recent Searches</h3>
            <Link href="#" className="text-sm text-blue-600 hover:underline">
              View All
            </Link>
          </div>
          <div className="space-y-3">
            {searchHistory.map((search) => (
              <div
                key={search.id}
                className="p-3 rounded-lg bg-gray-50 hover:bg-gray-100 cursor-pointer"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-gray-900">{search.query}</div>
                    <div className="text-sm text-gray-500">
                      {search.results_count} results • {new Date(search.timestamp).toLocaleDateString()}
                    </div>
                  </div>
                  <button className="text-blue-600 text-sm hover:underline">View</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function SearchTab({
  searchHistory,
  roles,
}: {
  searchHistory: SearchHistory[];
  roles: Role[];
}) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-black mb-2">Search Candidates</h2>
        <p className="text-gray-600">Find people in your network and beyond</p>
      </div>

      {/* Search Interface */}
      <div className="bg-white rounded-lg shadow border border-gray-200 p-8">
        <div className="max-w-2xl mx-auto space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">
              What role are you hiring for?
            </label>
            <input
              type="text"
              placeholder="e.g., ML Engineer, Backend Engineer, Product Manager"
              className="w-full px-5 py-3 rounded-2xl border-gray-200 bg-gray-50 focus:ring-2 focus:ring-blue-500/20 outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">
              Required Skills
            </label>
            <input
              type="text"
              placeholder="Python, React, Machine Learning"
              className="w-full px-5 py-3 rounded-2xl border-gray-200 bg-gray-50 focus:ring-2 focus:ring-blue-500/20 outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-2">
                Experience Level
              </label>
              <select className="w-full px-5 py-3 rounded-2xl border-gray-200 bg-gray-50 focus:ring-2 focus:ring-blue-500/20 outline-none">
                <option>Any</option>
                <option>Entry Level (0-2 years)</option>
                <option>Mid Level (3-5 years)</option>
                <option>Senior (5-8 years)</option>
                <option>Staff+ (8+ years)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-2">
                Search Mode
              </label>
              <select className="w-full px-5 py-3 rounded-2xl border-gray-200 bg-gray-50 focus:ring-2 focus:ring-blue-500/20 outline-none">
                <option>Full (Network + External)</option>
                <option>Network Only</option>
                <option>Quick Search</option>
              </select>
            </div>
          </div>

          <button className="w-full px-6 py-3 bg-blue-600 text-white rounded-2xl font-medium hover:bg-blue-700">
            Search Candidates
          </button>
        </div>
      </div>

      {/* Search History */}
      <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-black mb-4">Search History</h3>
        <div className="space-y-3">
          {searchHistory.map((search) => (
            <div
              key={search.id}
              className="flex items-center justify-between p-4 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 cursor-pointer"
            >
              <div>
                <div className="font-medium text-gray-900">{search.query}</div>
                <div className="text-sm text-gray-500">
                  {search.results_count} results • {new Date(search.timestamp).toLocaleDateString()}
                </div>
              </div>
              <button className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">
                View Results
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function PipelineTab({
  candidates,
  candidatesByStatus,
}: {
  candidates: AgencityCandidate[];
  candidatesByStatus: Record<string, AgencityCandidate[]>;
}) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-black mb-2">Candidate Pipeline</h2>
        <p className="text-gray-600">Track candidates from sourcing to hire</p>
      </div>

      {/* Pipeline Stats */}
      <div className="grid grid-cols-5 gap-4">
        <PipelineStageCard
          title="Sourced"
          count={candidatesByStatus.sourced.length}
          color="gray"
        />
        <PipelineStageCard
          title="Contacted"
          count={candidatesByStatus.contacted.length}
          color="blue"
        />
        <PipelineStageCard
          title="Invited"
          count={candidatesByStatus.invited.length}
          color="purple"
        />
        <PipelineStageCard
          title="In Simulation"
          count={candidatesByStatus.in_simulation.length}
          color="yellow"
        />
        <PipelineStageCard
          title="Reviewed"
          count={candidatesByStatus.reviewed.length}
          color="green"
        />
      </div>

      {/* All Candidates */}
      <div className="bg-white rounded-lg shadow border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-black">All Candidates</h3>
            <div className="flex items-center gap-3">
              <select className="px-3 py-2 rounded-lg border-gray-200 bg-gray-50 text-sm">
                <option>All Stages</option>
                <option>Sourced</option>
                <option>Contacted</option>
                <option>Invited</option>
                <option>In Simulation</option>
                <option>Reviewed</option>
              </select>
              <select className="px-3 py-2 rounded-lg border-gray-200 bg-gray-50 text-sm">
                <option>Sort by Score</option>
                <option>Sort by Date</option>
                <option>Sort by Status</option>
              </select>
            </div>
          </div>
        </div>
        <div className="divide-y divide-gray-200">
          {candidates.map((candidate) => (
            <CandidateCard key={candidate.id} candidate={candidate} />
          ))}
        </div>
      </div>
    </div>
  );
}

function NetworkTab({ networkStats }: { networkStats: NetworkStats | null }) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-black mb-2">Your Network</h2>
        <p className="text-gray-600">Manage and expand your professional network</p>
      </div>

      {/* Network Overview */}
      <div className="grid grid-cols-4 gap-6">
        <StatCard
          title="Total Contacts"
          value={networkStats?.total_contacts.toLocaleString() || '0'}
          subtitle="imported from LinkedIn"
          bgColor="bg-blue-50"
          textColor="text-blue-700"
        />
        <StatCard
          title="Companies"
          value={networkStats?.companies.toString() || '0'}
          subtitle="represented"
          bgColor="bg-green-50"
          textColor="text-green-700"
        />
        <StatCard
          title="Schools"
          value={networkStats?.schools.toString() || '0'}
          subtitle="connected"
          bgColor="bg-purple-50"
          textColor="text-purple-700"
        />
        <StatCard
          title="Engineers"
          value={networkStats?.engineers.toString() || '0'}
          subtitle="in network"
          bgColor="bg-orange-50"
          textColor="text-orange-700"
        />
      </div>

      {/* Top Companies */}
      <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-black mb-4">Top Companies</h3>
        <div className="space-y-3">
          <NetworkCompanyRow company="Google" count={23} />
          <NetworkCompanyRow company="Meta" count={18} />
          <NetworkCompanyRow company="Anthropic" count={12} />
          <NetworkCompanyRow company="OpenAI" count={9} />
          <NetworkCompanyRow company="Stripe" count={7} />
        </div>
      </div>

      {/* Actions */}
      <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-black mb-4">Network Actions</h3>
        <div className="space-y-3">
          <button className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 text-left">
            Import More Connections
          </button>
          <button className="w-full px-6 py-3 bg-white border border-gray-200 text-gray-900 rounded-lg font-medium hover:bg-gray-50 text-left">
            Request Recommendations
          </button>
          <button className="w-full px-6 py-3 bg-white border border-gray-200 text-gray-900 rounded-lg font-medium hover:bg-gray-50 text-left">
            View Network Map
          </button>
        </div>
      </div>
    </div>
  );
}

// Reusable Components
function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
        active
          ? 'bg-gray-100 text-black'
          : 'text-gray-600 hover:text-black hover:bg-gray-50'
      }`}
    >
      {children}
    </button>
  );
}

function StatCard({
  title,
  value,
  subtitle,
  bgColor,
  textColor,
}: {
  title: string;
  value: string;
  subtitle: string;
  bgColor: string;
  textColor: string;
}) {
  return (
    <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
      <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium mb-3 ${bgColor} ${textColor}`}>
        {title}
      </div>
      <div className="text-3xl font-bold text-black">{value}</div>
      <div className="text-sm text-gray-500 mt-1">{subtitle}</div>
    </div>
  );
}

function CandidateCard({
  candidate,
  compact = false,
}: {
  candidate: AgencityCandidate;
  compact?: boolean;
}) {
  const warmthColors = {
    network: 'text-green-700 bg-green-50',
    warm: 'text-yellow-700 bg-yellow-50',
    cold: 'text-gray-700 bg-gray-50',
  };

  const warmthLabels = {
    network: 'NETWORK',
    warm: 'WARM',
    cold: 'COLD',
  };

  if (compact) {
    return (
      <div className="p-3 rounded-lg bg-gray-50 hover:bg-gray-100 cursor-pointer">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="font-medium text-gray-900">{candidate.name}</div>
            <div className="text-sm text-gray-500">
              {candidate.title} @ {candidate.company}
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-black">{candidate.score}</div>
            <div className="text-xs text-gray-500">score</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 hover:bg-gray-50 transition-colors">
      <div className="flex items-start gap-4">
        {/* Avatar */}
        <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-semibold text-lg">
          {candidate.name.charAt(0)}
        </div>

        {/* Content */}
        <div className="flex-1">
          <div className="flex items-start justify-between mb-2">
            <div>
              <div className="flex items-center gap-2">
                <h4 className="font-semibold text-gray-900">{candidate.name}</h4>
                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    warmthColors[candidate.warmth_level]
                  }`}
                >
                  {warmthLabels[candidate.warmth_level]}
                </span>
                <span className="text-2xl font-bold text-black">{candidate.score}</span>
              </div>
              <div className="text-sm text-gray-600">
                {candidate.title} @ {candidate.company}
              </div>
              <div className="text-sm text-gray-500">{candidate.location}</div>
            </div>
          </div>

          {/* Scores */}
          <div className="grid grid-cols-2 gap-4 mb-3">
            <div>
              <div className="text-xs text-gray-500 mb-1">Fit Score</div>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-600"
                    style={{ width: `${candidate.fit_score}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-gray-900">{candidate.fit_score}</span>
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-1">Warmth Score</div>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-600"
                    style={{ width: `${candidate.warmth_score}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-gray-900">{candidate.warmth_score}</span>
              </div>
            </div>
          </div>

          {/* Warm Path */}
          {candidate.warm_path && (
            <div className="mb-3 p-3 bg-blue-50 rounded-lg border border-blue-100">
              <div className="text-sm text-blue-900">
                <span className="font-medium">Warm Path:</span> {candidate.warm_path.description}
                {candidate.warm_path.connector && (
                  <span className="text-blue-700"> via {candidate.warm_path.connector}</span>
                )}
              </div>
            </div>
          )}

          {/* Skills */}
          <div className="flex flex-wrap gap-2 mb-3">
            {candidate.skills.slice(0, 4).map((skill) => (
              <span
                key={skill}
                className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full"
              >
                {skill}
              </span>
            ))}
            {candidate.skills.length > 4 && (
              <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full">
                +{candidate.skills.length - 4} more
              </span>
            )}
          </div>

          {/* Timing Signals */}
          {candidate.timing_signals && candidate.timing_signals.length > 0 && (
            <div className="flex items-center gap-2 mb-3">
              <ClockIcon />
              <span className="text-sm text-gray-600">
                {candidate.timing_signals.join(' • ')}
              </span>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-2">
            <button className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">
              View Details
            </button>
            <button className="px-4 py-2 bg-white border border-gray-200 text-gray-900 text-sm rounded-lg hover:bg-gray-50">
              Save
            </button>
            {candidate.status === 'sourced' && (
              <button className="px-4 py-2 bg-white border border-gray-200 text-gray-900 text-sm rounded-lg hover:bg-gray-50">
                Invite to ProofHire
              </button>
            )}
            {candidate.status === 'in_simulation' && (
              <button className="px-4 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700">
                View Brief
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function PipelineStageCard({
  title,
  count,
  color,
}: {
  title: string;
  count: number;
  color: string;
}) {
  const colors: Record<string, string> = {
    gray: 'bg-gray-50 text-gray-700 border-gray-200',
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
    purple: 'bg-purple-50 text-purple-700 border-purple-200',
    yellow: 'bg-yellow-50 text-yellow-700 border-yellow-200',
    green: 'bg-green-50 text-green-700 border-green-200',
  };

  return (
    <div className={`p-4 rounded-lg border ${colors[color]}`}>
      <div className="text-sm font-medium mb-1">{title}</div>
      <div className="text-3xl font-bold">{count}</div>
    </div>
  );
}

function NetworkCompanyRow({ company, count }: { company: string; count: number }) {
  return (
    <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-white border border-gray-200 flex items-center justify-center">
          <BuildingIcon />
        </div>
        <span className="font-medium text-gray-900">{company}</span>
      </div>
      <span className="text-sm text-gray-600">{count} contacts</span>
    </div>
  );
}

// Icons
function BellIcon() {
  return (
    <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
      />
    </svg>
  );
}

function UserIcon() {
  return (
    <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
      />
    </svg>
  );
}

function ClockIcon() {
  return (
    <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  );
}

function BuildingIcon() {
  return (
    <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
      />
    </svg>
  );
}
