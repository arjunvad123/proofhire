'use client';

import { useEffect, useState } from 'react';
import {
  getRoles,
  getActivationRequests,
  getNetworkStats,
  type Role,
  type ActivationRequest,
  type NetworkStats,
} from '@/lib/api';
import { Button } from '@/components/ui/button';

export default function NetworkPage() {
  const [companyId, setCompanyId] = useState<string | null>(null);
  const [roles, setRoles] = useState<Role[]>([]);
  const [selectedRoleId, setSelectedRoleId] = useState<string>('');
  const [selectedRoleTitle, setSelectedRoleTitle] = useState<string>('');
  const [activationRequests, setActivationRequests] = useState<ActivationRequest[]>([]);
  const [networkStats, setNetworkStats] = useState<NetworkStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

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

  // Load roles and stats
  useEffect(() => {
    if (!companyId) return;

    async function loadData() {
      try {
        const [rolesData, statsData] = await Promise.all([
          getRoles(companyId!),
          getNetworkStats(companyId!).catch(() => null),
        ]);
        setRoles(rolesData);
        setNetworkStats(statsData);
      } catch (error) {
        console.error('Error loading data:', error);
      }
    }

    loadData();
  }, [companyId]);

  const handleRoleSelect = (roleId: string) => {
    const role = roles.find(r => r.id === roleId);
    setSelectedRoleId(roleId);
    setSelectedRoleTitle(role?.title || '');
  };

  const handleGenerateMessages = async () => {
    if (!companyId || !selectedRoleTitle) return;

    setLoading(true);
    try {
      const requests = await getActivationRequests(companyId, selectedRoleTitle);
      setActivationRequests(requests);
    } catch (error) {
      console.error('Error generating messages:', error);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async (text: string, id: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  if (!companyId) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Please complete onboarding first</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl p-6 text-white">
        <h1 className="text-2xl font-bold mb-2">Activate Your Network</h1>
        <p className="text-purple-100">
          Generate personalized &quot;Who would you recommend?&quot; messages to send to your network.
          These are tailored to each person&apos;s background and expertise.
        </p>
      </div>

      {/* Stats */}
      {networkStats?.network && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="text-2xl font-bold text-gray-900">{networkStats.network.total_nodes}</div>
            <div className="text-sm text-gray-500">Total Connections</div>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="text-2xl font-bold text-gray-900">{networkStats.network.by_type?.engineer || 0}</div>
            <div className="text-sm text-gray-500">Engineers to Ask</div>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="text-2xl font-bold text-gray-900">{networkStats.network.by_type?.engineering_manager || 0}</div>
            <div className="text-sm text-gray-500">Managers to Ask</div>
          </div>
        </div>
      )}

      {/* Role Selector */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Select Role to Hire For</h2>
        <div className="flex gap-4">
          <select
            value={selectedRoleId}
            onChange={(e) => handleRoleSelect(e.target.value)}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Choose a role...</option>
            {roles.map((role) => (
              <option key={role.id} value={role.id}>
                {role.title} {role.level && `(${role.level})`}
              </option>
            ))}
          </select>
          <Button
            onClick={handleGenerateMessages}
            disabled={!selectedRoleId}
            loading={loading}
          >
            Generate Messages
          </Button>
        </div>
      </div>

      {/* Activation Requests */}
      {activationRequests.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">
              People to Ask ({activationRequests.length})
            </h2>
            <span className="text-sm text-gray-500">
              Sorted by likelihood to know great candidates
            </span>
          </div>

          {activationRequests.map((request, index) => (
            <div
              key={request.id || index}
              className="bg-white rounded-xl border border-gray-200 overflow-hidden"
            >
              {/* Header */}
              <div className="p-4 bg-gray-50 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center text-purple-600 font-medium">
                    {index + 1}
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">{request.target_name}</div>
                    <div className="text-sm text-gray-500">
                      {request.target_title} at {request.target_company}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs font-medium">
                    Priority: {Math.round(request.priority_score * 100)}%
                  </span>
                  {request.target_linkedin_url && (
                    <a
                      href={request.target_linkedin_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                    >
                      <LinkedInIcon className="w-5 h-5" />
                    </a>
                  )}
                </div>
              </div>

              {/* Why them */}
              <div className="px-4 py-3 border-b border-gray-100">
                <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Why ask them</div>
                <div className="text-sm text-gray-700">{request.reason}</div>
              </div>

              {/* Message */}
              <div className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-xs text-gray-500 uppercase tracking-wider">Message</div>
                  <button
                    onClick={() => copyToClipboard(request.message, request.id)}
                    className={`flex items-center gap-1 px-3 py-1 rounded text-sm font-medium transition-colors ${
                      copiedId === request.id
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {copiedId === request.id ? (
                      <>
                        <CheckIcon className="w-4 h-4" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <CopyIcon className="w-4 h-4" />
                        Copy
                      </>
                    )}
                  </button>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg text-sm text-gray-700 whitespace-pre-wrap font-mono">
                  {request.message}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {activationRequests.length === 0 && !loading && selectedRoleId && (
        <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
          <div className="text-gray-500">
            Click &quot;Generate Messages&quot; to create personalized outreach for your network
          </div>
        </div>
      )}

      {/* Tips */}
      <div className="bg-blue-50 rounded-xl border border-blue-200 p-6">
        <h3 className="font-semibold text-blue-900 mb-3">Tips for Network Activation</h3>
        <ul className="space-y-2 text-sm text-blue-800">
          <li className="flex items-start gap-2">
            <span className="text-blue-600 mt-0.5">1.</span>
            <span>Send messages via LinkedIn DM or email - pick whichever feels more natural for each person</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600 mt-0.5">2.</span>
            <span>Personalize further if you have recent context (their new project, promotion, etc.)</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600 mt-0.5">3.</span>
            <span>Follow up after 3-5 days if no response - people are busy!</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600 mt-0.5">4.</span>
            <span>When they recommend someone, use &quot;Ask for Intro&quot; to request a warm introduction</span>
          </li>
        </ul>
      </div>
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

function CopyIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
    </svg>
  );
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  );
}
