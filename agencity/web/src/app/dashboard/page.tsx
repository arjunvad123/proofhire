'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getCompany, getRoles, getNetworkStats, getDailyDigest, type CompanyWithStats, type Role, type NetworkStats } from '@/lib/api';

interface DailyDigest {
  date: string;
  summary: string;
  priority_actions: {
    priority: string;
    category: string;
    action: string;
    targets: string[];
  }[];
  stats: Record<string, number>;
}

export default function DashboardPage() {
  const [company, setCompany] = useState<CompanyWithStats | null>(null);
  const [roles, setRoles] = useState<Role[]>([]);
  const [networkStats, setNetworkStats] = useState<NetworkStats | null>(null);
  const [digest, setDigest] = useState<DailyDigest | null>(null);
  const [loading, setLoading] = useState(true);
  const [companyId, setCompanyId] = useState<string | null>(null);

  useEffect(() => {
    // Get company ID from localStorage
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

  useEffect(() => {
    if (!companyId) return;

    async function loadData() {
      setLoading(true);
      try {
        const [companyData, rolesData, statsData, digestData] = await Promise.all([
          getCompany(companyId!).catch(() => null),
          getRoles(companyId!).catch(() => []),
          getNetworkStats(companyId!).catch(() => null),
          getDailyDigest(companyId!).catch(() => null),
        ]);

        setCompany(companyData);
        setRoles(rolesData);
        setNetworkStats(statsData);
        setDigest(digestData);
      } catch (error) {
        console.error('Error loading dashboard:', error);
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
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Welcome to Agencity</h2>
        <p className="text-gray-600 mb-6">Complete onboarding to get started</p>
        <Link
          href="/onboarding"
          className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
        >
          Start Onboarding
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard
          title="Network Size"
          value={networkStats?.network?.total_nodes?.toLocaleString() || company?.people_count?.toLocaleString() || '0'}
          subtitle="imported connections"
          icon={<NetworkIcon />}
          color="blue"
        />
        <StatCard
          title="Open Roles"
          value={roles.filter(r => r.status === 'active').length.toString()}
          subtitle={`of ${roles.length} total`}
          icon={<BriefcaseIcon />}
          color="green"
        />
        <StatCard
          title="Engineers"
          value={networkStats?.network?.by_type?.engineer?.toString() || '0'}
          subtitle="in your network"
          icon={<CodeIcon />}
          color="purple"
        />
        <StatCard
          title="Companies"
          value={Object.keys(networkStats?.network?.top_companies || {}).length.toString()}
          subtitle="represented"
          icon={<BuildingIcon />}
          color="orange"
        />
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            href="/dashboard/search"
            className="flex items-center gap-4 p-4 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors"
          >
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <SearchIcon className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <div className="font-medium text-gray-900">Search Candidates</div>
              <div className="text-sm text-gray-500">Find people in your network</div>
            </div>
          </Link>
          <Link
            href="/dashboard/intelligence"
            className="flex items-center gap-4 p-4 rounded-lg border border-gray-200 hover:border-purple-300 hover:bg-purple-50 transition-colors"
          >
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <LightningIcon className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <div className="font-medium text-gray-900">View Intelligence</div>
              <div className="text-sm text-gray-500">Timing alerts & insights</div>
            </div>
          </Link>
          <Link
            href="/dashboard/network"
            className="flex items-center gap-4 p-4 rounded-lg border border-gray-200 hover:border-green-300 hover:bg-green-50 transition-colors"
          >
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <UserPlusIcon className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <div className="font-medium text-gray-900">Activate Network</div>
              <div className="text-sm text-gray-500">Ask for recommendations</div>
            </div>
          </Link>
        </div>
      </div>

      {/* Priority Actions from Daily Digest */}
      {digest && digest.priority_actions.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Today&apos;s Priority Actions</h2>
            <span className="text-sm text-gray-500">{digest.date}</span>
          </div>
          <div className="space-y-3">
            {digest.priority_actions.slice(0, 5).map((action, index) => (
              <div
                key={index}
                className={`flex items-start gap-3 p-3 rounded-lg ${
                  action.priority === 'high'
                    ? 'bg-red-50 border border-red-100'
                    : action.priority === 'medium'
                    ? 'bg-yellow-50 border border-yellow-100'
                    : 'bg-gray-50 border border-gray-100'
                }`}
              >
                <div
                  className={`w-2 h-2 rounded-full mt-2 ${
                    action.priority === 'high'
                      ? 'bg-red-500'
                      : action.priority === 'medium'
                      ? 'bg-yellow-500'
                      : 'bg-gray-400'
                  }`}
                />
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900">{action.action}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {action.category} • {action.targets.slice(0, 3).join(', ')}
                    {action.targets.length > 3 && ` +${action.targets.length - 3} more`}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Open Roles */}
      {roles.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Open Roles</h2>
            <Link href="/dashboard/settings" className="text-sm text-blue-600 hover:underline">
              Manage Roles
            </Link>
          </div>
          <div className="space-y-3">
            {roles.slice(0, 5).map((role) => (
              <div
                key={role.id}
                className="flex items-center justify-between p-3 rounded-lg bg-gray-50"
              >
                <div>
                  <div className="font-medium text-gray-900">{role.title}</div>
                  <div className="text-sm text-gray-500">
                    {role.level && `${role.level} • `}
                    {role.required_skills.slice(0, 3).join(', ')}
                  </div>
                </div>
                <Link
                  href={`/dashboard/search?role_id=${role.id}`}
                  className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
                >
                  Find Candidates
                </Link>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Stat Card Component
function StatCard({
  title,
  value,
  subtitle,
  icon,
  color,
}: {
  title: string;
  value: string;
  subtitle: string;
  icon: React.ReactNode;
  color: 'blue' | 'green' | 'purple' | 'orange';
}) {
  const colors = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    purple: 'bg-purple-100 text-purple-600',
    orange: 'bg-orange-100 text-orange-600',
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colors[color]}`}>
          {icon}
        </div>
        <div className="text-sm font-medium text-gray-500">{title}</div>
      </div>
      <div className="text-3xl font-bold text-gray-900">{value}</div>
      <div className="text-sm text-gray-500 mt-1">{subtitle}</div>
    </div>
  );
}

// Icons
function NetworkIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
    </svg>
  );
}

function BriefcaseIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  );
}

function CodeIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
    </svg>
  );
}

function BuildingIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
    </svg>
  );
}

function SearchIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
  );
}

function LightningIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  );
}

function UserPlusIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
    </svg>
  );
}
