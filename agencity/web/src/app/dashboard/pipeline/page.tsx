'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

// Types for ProofHire integration
interface CandidatePipeline {
  id: string;
  name: string;
  email: string;
  title: string;
  company: string;

  // Agencity data
  agencity_candidate_id: string;
  search_id?: string;
  sourced_at: string;
  warmth_score: number;
  warmth_level: 'network' | 'warm' | 'cold';
  warm_path?: {
    type: string;
    description: string;
    connector?: string;
  };

  // ProofHire integration
  proofhire_application_id?: string;
  proofhire_role_id?: string;
  simulation_status?: 'not_invited' | 'invited' | 'in_progress' | 'completed' | 'failed';
  simulation_started_at?: string;
  simulation_completed_at?: string;
  brief_available?: boolean;

  // Status tracking
  status: 'sourced' | 'contacted' | 'invited' | 'in_simulation' | 'reviewed' | 'interviewing' | 'hired' | 'rejected';
  contacted_at?: string;
  invited_at?: string;
  notes?: string;
}

export default function PipelinePage() {
  const [companyId, setCompanyId] = useState<string | null>(null);
  const [candidates, setCandidates] = useState<CandidatePipeline[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'date' | 'score' | 'status'>('date');

  // Get company ID
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('onboarding-state');
      if (saved) {
        try {
          const state = JSON.parse(saved);
          if (state.companyId) {
            setCompanyId(state.companyId);
            return;
          }
        } catch {
          // ignore
        }
      }

      // FALLBACK: Default to Confido for demo
      setCompanyId("100b5ac1-1912-4970-a378-04d0169fd597");
    }
  }, []);

  // Load pipeline data
  useEffect(() => {
    if (!companyId) return;
    loadPipeline();
  }, [companyId]);

  async function loadPipeline() {
    setLoading(true);
    try {
      // Fetch real pipeline data from Agencity API
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api';
      const response = await fetch(`${API_BASE}/pipeline/${companyId}`, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to load pipeline: ${response.statusText}`);
      }

      const data = await response.json();
      setCandidates(data.candidates || []);
    } catch (error) {
      console.error('Error loading pipeline:', error);
      // Set empty array on error
      setCandidates([]);
    } finally {
      setLoading(false);
    }
  }

  const candidatesByStatus = {
    all: candidates,
    sourced: candidates.filter((c) => c.status === 'sourced'),
    contacted: candidates.filter((c) => c.status === 'contacted'),
    invited: candidates.filter((c) => c.status === 'invited'),
    in_simulation: candidates.filter((c) => c.status === 'in_simulation'),
    reviewed: candidates.filter((c) => c.status === 'reviewed'),
  };

  const filteredCandidates = selectedStatus === 'all' ? candidates : candidatesByStatus[selectedStatus as keyof typeof candidatesByStatus] || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-5 gap-4">
        <StageCard
          title="Sourced"
          count={candidatesByStatus.sourced.length}
          color="gray"
          onClick={() => setSelectedStatus('sourced')}
          active={selectedStatus === 'sourced'}
        />
        <StageCard
          title="Contacted"
          count={candidatesByStatus.contacted.length}
          color="blue"
          onClick={() => setSelectedStatus('contacted')}
          active={selectedStatus === 'contacted'}
        />
        <StageCard
          title="Invited"
          count={candidatesByStatus.invited.length}
          color="purple"
          onClick={() => setSelectedStatus('invited')}
          active={selectedStatus === 'invited'}
        />
        <StageCard
          title="In Simulation"
          count={candidatesByStatus.in_simulation.length}
          color="yellow"
          onClick={() => setSelectedStatus('in_simulation')}
          active={selectedStatus === 'in_simulation'}
        />
        <StageCard
          title="Reviewed"
          count={candidatesByStatus.reviewed.length}
          color="green"
          onClick={() => setSelectedStatus('reviewed')}
          active={selectedStatus === 'reviewed'}
        />
      </div>

      {/* Filters & Controls */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSelectedStatus('all')}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                selectedStatus === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              All ({candidates.length})
            </button>
          </div>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
          >
            <option value="date">Sort by Date</option>
            <option value="score">Sort by Score</option>
            <option value="status">Sort by Status</option>
          </select>
        </div>
      </div>

      {/* Candidates List */}
      <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-200">
        {filteredCandidates.length === 0 ? (
          <div className="p-12 text-center">
            <p className="text-gray-500 mb-4">No candidates in this stage</p>
            <Link href="/dashboard/search">
              <Button>Search for Candidates</Button>
            </Link>
          </div>
        ) : (
          filteredCandidates.map((candidate) => (
            <CandidateRow key={candidate.id} candidate={candidate} onUpdate={loadPipeline} />
          ))
        )}
      </div>
    </div>
  );
}

// Stage Card Component
function StageCard({
  title,
  count,
  color,
  onClick,
  active,
}: {
  title: string;
  count: number;
  color: 'gray' | 'blue' | 'purple' | 'yellow' | 'green';
  onClick: () => void;
  active?: boolean;
}) {
  const colors = {
    gray: active ? 'bg-gray-100 border-gray-300' : 'bg-gray-50 border-gray-200',
    blue: active ? 'bg-blue-100 border-blue-300' : 'bg-blue-50 border-blue-200',
    purple: active ? 'bg-purple-100 border-purple-300' : 'bg-purple-50 border-purple-200',
    yellow: active ? 'bg-yellow-100 border-yellow-300' : 'bg-yellow-50 border-yellow-200',
    green: active ? 'bg-green-100 border-green-300' : 'bg-green-50 border-green-200',
  };

  return (
    <button
      onClick={onClick}
      className={`p-4 rounded-xl border-2 transition-all hover:shadow-md ${colors[color]}`}
    >
      <div className="text-3xl font-bold text-gray-900 mb-1">{count}</div>
      <div className="text-sm font-medium text-gray-600">{title}</div>
    </button>
  );
}

// Candidate Row Component
function CandidateRow({
  candidate,
  onUpdate,
}: {
  candidate: CandidatePipeline;
  onUpdate: () => void;
}) {
  const [showActions, setShowActions] = useState(false);

  const warmthColors = {
    network: 'bg-green-100 text-green-700',
    warm: 'bg-yellow-100 text-yellow-700',
    cold: 'bg-gray-100 text-gray-700',
  };

  const statusColors = {
    sourced: 'bg-gray-100 text-gray-700',
    contacted: 'bg-blue-100 text-blue-700',
    invited: 'bg-purple-100 text-purple-700',
    in_simulation: 'bg-yellow-100 text-yellow-700',
    reviewed: 'bg-green-100 text-green-700',
    interviewing: 'bg-orange-100 text-orange-700',
    hired: 'bg-green-100 text-green-700',
    rejected: 'bg-red-100 text-red-700',
  };

  async function handleInviteToProofHire() {
    try {
      const { inviteCandidateToProofHire } = await import('@/lib/proofhire-integration');

      // TODO: Get these from state/props
      const proofhireOrgId = 'org-id-here'; // From ProofHire org
      const proofhireRoleId = 'role-id-here'; // Selected role

      await inviteCandidateToProofHire({
        companyId: candidate.company, // Agencity company ID
        agencityCandidateId: candidate.agencity_candidate_id,
        agencitySearchId: candidate.search_id,
        candidateName: candidate.name,
        candidateEmail: candidate.email,
        proofhireRoleId,
        proofhireOrgId,
      });

      alert(`Successfully invited ${candidate.name} to ProofHire!`);
      onUpdate();
    } catch (error) {
      console.error('Failed to invite candidate:', error);
      alert(`Failed to invite candidate: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  function getProofHireLink() {
    if (!candidate.proofhire_application_id) return null;
    // Link to ProofHire evaluation
    return `http://localhost:3000/candidates/${candidate.proofhire_application_id}`;
  }

  return (
    <div className="p-4 hover:bg-gray-50 transition-colors">
      <div className="flex items-start gap-4">
        {/* Avatar */}
        <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-semibold text-lg flex-shrink-0">
          {candidate.name.charAt(0)}
        </div>

        {/* Main Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between mb-2">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-semibold text-gray-900">{candidate.name}</h3>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${warmthColors[candidate.warmth_level]}`}>
                  {candidate.warmth_level.toUpperCase()}
                </span>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[candidate.status]}`}>
                  {candidate.status.replace('_', ' ').toUpperCase()}
                </span>
              </div>
              <div className="text-sm text-gray-600">
                {candidate.title} @ {candidate.company}
              </div>
              <div className="text-xs text-gray-500">{candidate.email}</div>
            </div>
            <button
              onClick={() => setShowActions(!showActions)}
              className="p-2 hover:bg-gray-100 rounded-lg"
            >
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
              </svg>
            </button>
          </div>

          {/* Warm Path */}
          {candidate.warm_path && (
            <div className="mb-3 p-2 bg-blue-50 rounded-lg text-sm text-blue-900">
              <span className="font-medium">Warm Path:</span> {candidate.warm_path.description}
              {candidate.warm_path.connector && (
                <span className="text-blue-700"> via {candidate.warm_path.connector}</span>
              )}
            </div>
          )}

          {/* ProofHire Status */}
          {candidate.simulation_status && (
            <div className="mb-3">
              <div className="flex items-center gap-2 text-sm">
                <span className="text-gray-500">ProofHire:</span>
                {candidate.simulation_status === 'invited' && (
                  <span className="text-purple-700">Invitation sent</span>
                )}
                {candidate.simulation_status === 'in_progress' && (
                  <span className="text-yellow-700 flex items-center gap-1">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
                    Simulation in progress
                  </span>
                )}
                {candidate.simulation_status === 'completed' && candidate.brief_available && (
                  <span className="text-green-700">✓ Evaluation complete</span>
                )}
              </div>
            </div>
          )}

          {/* Timeline */}
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span>Sourced {new Date(candidate.sourced_at).toLocaleDateString()}</span>
            {candidate.contacted_at && (
              <>
                <span>•</span>
                <span>Contacted {new Date(candidate.contacted_at).toLocaleDateString()}</span>
              </>
            )}
            {candidate.invited_at && (
              <>
                <span>•</span>
                <span>Invited {new Date(candidate.invited_at).toLocaleDateString()}</span>
              </>
            )}
          </div>

          {/* Actions */}
          {showActions && (
            <div className="mt-3 pt-3 border-t border-gray-200 flex items-center gap-2">
              {!candidate.proofhire_application_id && (
                <Button size="sm" onClick={handleInviteToProofHire}>
                  Invite to ProofHire
                </Button>
              )}
              {candidate.brief_available && getProofHireLink() && (
                <a
                  href={getProofHireLink()!}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3 py-1.5 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700"
                >
                  View Evaluation Brief
                </a>
              )}
              <button className="px-3 py-1.5 bg-white border border-gray-200 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50">
                Add Note
              </button>
              <button className="px-3 py-1.5 bg-white border border-gray-200 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50">
                Mark as Contacted
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
