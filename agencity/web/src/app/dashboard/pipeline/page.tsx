'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { getPipeline, updateCandidateStatus, PipelineCandidate as ApiPipelineCandidate } from '@/lib/api';

// Types for candidate pipeline
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

  // Status tracking (simple 3-stage pipeline)
  status: 'sourced' | 'contacted' | 'scheduled';
  contacted_at?: string;
  scheduled_at?: string;
  notes?: string;
}

export default function PipelinePage() {
  const [mounted, setMounted] = useState(false);
  const [companyId, setCompanyId] = useState<string | null>(null);
  const [candidates, setCandidates] = useState<CandidatePipeline[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'date' | 'score' | 'status'>('date');

  // Get company ID
  useEffect(() => {
    setMounted(true);
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
  }, []);

  // Load pipeline data
  useEffect(() => {
    if (!companyId) return;
    loadPipeline();
  }, [companyId]);

  async function loadPipeline() {
    if (!companyId) return;

    setLoading(true);
    try {
      const data = await getPipeline(companyId, {
        status: selectedStatus as any,
        sort: sortBy,
        limit: 50
      });
      setCandidates(data.candidates as any);
    } catch (error) {
      console.error('Error loading pipeline:', error);
      setCandidates([]);
    } finally {
      setLoading(false);
    }
  }

  const candidatesByStatus = {
    all: candidates,
    sourced: candidates.filter((c) => c.status === 'sourced'),
    contacted: candidates.filter((c) => c.status === 'contacted'),
    scheduled: candidates.filter((c) => c.status === 'scheduled'),
  };

  const filteredCandidates = selectedStatus === 'all' ? candidates : candidatesByStatus[selectedStatus as keyof typeof candidatesByStatus] || [];

  // Prevent hydration mismatch
  if (!mounted || loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-3 gap-4">
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
          title="Scheduled"
          count={candidatesByStatus.scheduled.length}
          color="green"
          onClick={() => setSelectedStatus('scheduled')}
          active={selectedStatus === 'scheduled'}
        />
      </div>

      {/* Filters & Controls */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSelectedStatus('all')}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${selectedStatus === 'all'
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
  const [updating, setUpdating] = useState(false);

  const handleUpdateStatus = async (newStatus: 'sourced' | 'contacted' | 'scheduled') => {
    setUpdating(true);
    try {
      await updateCandidateStatus(candidate.id, { status: newStatus });
      await onUpdate();
    } catch (error) {
      console.error('Failed to update status:', error);
      alert('Failed to update candidate status');
    } finally {
      setUpdating(false);
    }
  };

  const warmthColors = {
    network: 'bg-green-100 text-green-700',
    warm: 'bg-yellow-100 text-yellow-700',
    cold: 'bg-gray-100 text-gray-700',
  };

  const statusColors = {
    sourced: 'bg-gray-100 text-gray-700',
    contacted: 'bg-blue-100 text-blue-700',
    scheduled: 'bg-green-100 text-green-700',
  };

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

          {/* Timeline */}
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span>Sourced {new Date(candidate.sourced_at).toLocaleDateString()}</span>
            {candidate.contacted_at && (
              <>
                <span>•</span>
                <span>Contacted {new Date(candidate.contacted_at).toLocaleDateString()}</span>
              </>
            )}
            {candidate.scheduled_at && (
              <>
                <span>•</span>
                <span>Scheduled {new Date(candidate.scheduled_at).toLocaleDateString()}</span>
              </>
            )}
          </div>

          {/* Actions */}
          {showActions && (
            <div className="mt-3 pt-3 border-t border-gray-200 flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                {candidate.status === 'sourced' && (
                  <button
                    onClick={() => handleUpdateStatus('contacted')}
                    disabled={updating}
                    className="px-3 py-1.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {updating ? 'Updating...' : 'Mark as Contacted'}
                  </button>
                )}
                {candidate.status === 'contacted' && (
                  <button
                    onClick={() => handleUpdateStatus('scheduled')}
                    disabled={updating}
                    className="px-3 py-1.5 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {updating ? 'Updating...' : 'Mark as Scheduled'}
                  </button>
                )}
                <button className="px-3 py-1.5 bg-white border border-gray-200 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50">
                  Add Note
                </button>
                <a
                  href={`mailto:${candidate.email}`}
                  className="px-3 py-1.5 bg-white border border-gray-200 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50"
                >
                  Send Email
                </a>
              </div>

              {/* Undo Button */}
              {candidate.status !== 'sourced' && (
                <button
                  onClick={() => {
                    const prevStatus = candidate.status === 'scheduled' ? 'contacted' : 'sourced';
                    handleUpdateStatus(prevStatus);
                  }}
                  disabled={updating}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-orange-600 hover:text-orange-700 text-sm font-medium transition-colors"
                  title={`Move back to ${candidate.status === 'scheduled' ? 'Contacted' : 'Sourced'}`}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
                  </svg>
                  Undo Move
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
