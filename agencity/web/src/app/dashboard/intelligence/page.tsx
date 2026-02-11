'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  getTimingAlerts,
  getLayoffExposure,
  getNetworkStats,
  type TimingAnalysis,
  type LayoffExposure,
  type NetworkStats,
} from '@/lib/api';

export default function IntelligencePage() {
  const [companyId, setCompanyId] = useState<string | null>(null);
  const [timingAlerts, setTimingAlerts] = useState<TimingAnalysis[]>([]);
  const [layoffExposure, setLayoffExposure] = useState<LayoffExposure | null>(null);
  const [networkStats, setNetworkStats] = useState<NetworkStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'timing' | 'layoffs' | 'overview'>('timing');

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

  // Load intelligence data
  useEffect(() => {
    if (!companyId) return;

    async function loadData() {
      setLoading(true);
      try {
        const [timing, layoffs, stats] = await Promise.all([
          getTimingAlerts(companyId!).catch(() => []),
          getLayoffExposure(companyId!).catch(() => null),
          getNetworkStats(companyId!).catch(() => null),
        ]);

        setTimingAlerts(timing);
        setLayoffExposure(layoffs);
        setNetworkStats(stats);
      } catch (error) {
        console.error('Error loading intelligence:', error);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [companyId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!companyId) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Please complete onboarding first</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <ClockIcon className="w-5 h-5 text-purple-600" />
            </div>
            <div className="text-sm font-medium text-gray-500">Ready to Move</div>
          </div>
          <div className="text-3xl font-bold text-gray-900">
            {timingAlerts.filter(a => a.readiness_score >= 0.7).length}
          </div>
          <div className="text-sm text-gray-500">high readiness candidates</div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
              <AlertIcon className="w-5 h-5 text-red-600" />
            </div>
            <div className="text-sm font-medium text-gray-500">Layoff Affected</div>
          </div>
          <div className="text-3xl font-bold text-gray-900">
            {layoffExposure?.affected_members || 0}
          </div>
          <div className="text-sm text-gray-500">
            across {layoffExposure?.companies_with_layoffs || 0} companies
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <NetworkIcon className="w-5 h-5 text-green-600" />
            </div>
            <div className="text-sm font-medium text-gray-500">Network Coverage</div>
          </div>
          <div className="text-3xl font-bold text-gray-900">
            {Object.keys(networkStats?.network?.top_companies || {}).length}
          </div>
          <div className="text-sm text-gray-500">unique companies represented</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="border-b border-gray-200">
          <nav className="flex">
            {[
              { id: 'timing', label: 'Timing Intelligence', count: timingAlerts.length },
              { id: 'layoffs', label: 'Layoff Exposure', count: layoffExposure?.affected_members || 0 },
              { id: 'overview', label: 'Network Overview', count: null },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
                {tab.count !== null && (
                  <span className="ml-2 px-2 py-0.5 bg-gray-100 rounded-full text-xs">
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'timing' && (
            <TimingTab alerts={timingAlerts} />
          )}
          {activeTab === 'layoffs' && (
            <LayoffTab exposure={layoffExposure} />
          )}
          {activeTab === 'overview' && (
            <OverviewTab stats={networkStats} />
          )}
        </div>
      </div>
    </div>
  );
}

// Timing Tab Component
function TimingTab({ alerts }: { alerts: TimingAnalysis[] }) {
  if (alerts.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No timing signals detected yet. Import your network to see insights.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-600 mb-4">
        These candidates show signals indicating they may be ready for a change.
      </p>
      {alerts.map((alert, index) => (
        <div
          key={alert.person_id || index}
          className={`p-4 rounded-lg border ${
            alert.readiness_score >= 0.7
              ? 'border-green-200 bg-green-50'
              : alert.readiness_score >= 0.4
              ? 'border-yellow-200 bg-yellow-50'
              : 'border-gray-200 bg-gray-50'
          }`}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center text-gray-600 font-medium border">
                {alert.person_name.charAt(0)}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-900">{alert.person_name}</span>
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                    alert.readiness_score >= 0.7
                      ? 'bg-green-200 text-green-800'
                      : alert.readiness_score >= 0.4
                      ? 'bg-yellow-200 text-yellow-800'
                      : 'bg-gray-200 text-gray-800'
                  }`}>
                    {Math.round(alert.readiness_score * 100)}% ready
                  </span>
                </div>
                <div className="text-sm text-gray-600">
                  {alert.current_title} at {alert.current_company}
                </div>

                {/* Signals */}
                <div className="mt-2 space-y-1">
                  {alert.signals.map((signal, i) => (
                    <div key={i} className="flex items-center gap-2 text-xs">
                      <span className={`w-1.5 h-1.5 rounded-full ${
                        signal.score_impact >= 0.2 ? 'bg-green-500' :
                        signal.score_impact >= 0.1 ? 'bg-yellow-500' :
                        'bg-gray-400'
                      }`}></span>
                      <span className="text-gray-600">{signal.description}</span>
                    </div>
                  ))}
                </div>

                {/* Recommended Action */}
                {alert.recommended_action && (
                  <div className="mt-2 text-xs font-medium text-purple-600">
                    Suggested: {alert.recommended_action}
                  </div>
                )}
              </div>
            </div>

            {/* LinkedIn Link */}
            {alert.linkedin_url && (
              <a
                href={alert.linkedin_url}
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
              >
                <LinkedInIcon className="w-5 h-5" />
              </a>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

// Layoff Tab Component
function LayoffTab({ exposure }: { exposure: LayoffExposure | null }) {
  if (!exposure || exposure.affected_members === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No layoff exposure detected in your network.
      </div>
    );
  }

  const companies = Object.entries(exposure.by_company).sort(
    ([, a], [, b]) => b.count - a.count
  );

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="p-4 bg-red-50 rounded-lg border border-red-200">
        <div className="text-lg font-semibold text-red-900">
          {exposure.affected_members} people ({exposure.affected_percentage.toFixed(1)}% of your network)
        </div>
        <div className="text-sm text-red-700">
          are at companies that have had recent layoffs
        </div>
      </div>

      {/* By Company */}
      <div className="space-y-4">
        {companies.map(([company, data]) => (
          <div key={company} className="border border-gray-200 rounded-lg overflow-hidden">
            <div className="p-4 bg-gray-50 flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-900 capitalize">{company}</div>
                <div className="text-sm text-gray-500">
                  Layoff: {data.layoff_date} • Scale: {data.scale}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  data.urgency === 'high' ? 'bg-red-100 text-red-700' :
                  data.urgency === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {data.urgency} urgency
                </span>
                <span className="text-sm font-medium text-gray-600">
                  {data.count} people
                </span>
              </div>
            </div>

            {/* Members */}
            <div className="p-4 space-y-2">
              {data.members.slice(0, 5).map((member) => (
                <div key={member.id} className="flex items-center justify-between">
                  <div>
                    <span className="font-medium text-gray-900">{member.name}</span>
                    <span className="text-gray-500 ml-2">{member.title}</span>
                  </div>
                  {member.linkedin_url && (
                    <a
                      href={member.linkedin_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 text-sm hover:underline"
                    >
                      LinkedIn
                    </a>
                  )}
                </div>
              ))}
              {data.members.length > 5 && (
                <div className="text-sm text-gray-500 pt-2">
                  +{data.members.length - 5} more
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Overview Tab Component
function OverviewTab({ stats }: { stats: NetworkStats | null }) {
  if (!stats || !stats.network) {
    return (
      <div className="text-center py-12 text-gray-500">
        No network data available. Import your LinkedIn connections to see insights.
      </div>
    );
  }

  const roleBreakdown = Object.entries(stats.network.by_type).sort(
    ([, a], [, b]) => b - a
  );

  return (
    <div className="space-y-6">
      {/* Role Breakdown */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-4">Role Breakdown</h3>
        <div className="space-y-3">
          {roleBreakdown.map(([role, count]) => {
            const percentage = (count / stats.network.total_nodes) * 100;
            return (
              <div key={role}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="capitalize text-gray-700">{role.replace('_', ' ')}</span>
                  <span className="text-gray-500">{count} ({percentage.toFixed(1)}%)</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-600 rounded-full"
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="text-2xl font-bold text-gray-900">{stats.network.total_nodes}</div>
          <div className="text-sm text-gray-500">Total Connections</div>
        </div>
        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="text-2xl font-bold text-gray-900">{stats.network.total_estimated_reach.toLocaleString()}</div>
          <div className="text-sm text-gray-500">Estimated Reach</div>
        </div>
      </div>
    </div>
  );
}

// Icons
function ClockIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function AlertIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  );
}

function NetworkIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
    </svg>
  );
}

function LinkedInIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
    </svg>
  );
}
