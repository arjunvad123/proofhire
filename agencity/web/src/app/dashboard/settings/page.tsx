'use client';

import { useEffect, useState } from 'react';
import { getCompany, getRoles, type CompanyWithStats, type Role } from '@/lib/api';
import { Button } from '@/components/ui/button';

export default function SettingsPage() {
  const [companyId, setCompanyId] = useState<string | null>(null);
  const [company, setCompany] = useState<CompanyWithStats | null>(null);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);

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

  useEffect(() => {
    if (!companyId) return;

    async function loadData() {
      setLoading(true);
      try {
        const [companyData, rolesData] = await Promise.all([
          getCompany(companyId!),
          getRoles(companyId!),
        ]);
        setCompany(companyData);
        setRoles(rolesData);
      } catch (error) {
        console.error('Error loading settings:', error);
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

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Company Info */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Company Information</h2>
        {company && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-gray-500">Company Name</div>
              <div className="font-medium text-gray-900">{company.name}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Domain</div>
              <div className="font-medium text-gray-900">{company.domain || 'Not set'}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Industry</div>
              <div className="font-medium text-gray-900">{company.industry || 'Not set'}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Stage</div>
              <div className="font-medium text-gray-900">{company.stage || 'Not set'}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Team Size</div>
              <div className="font-medium text-gray-900">{company.team_size || 'Not set'}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Network Size</div>
              <div className="font-medium text-gray-900">{company.people_count} connections</div>
            </div>
            <div className="col-span-2">
              <div className="text-sm text-gray-500">Tech Stack</div>
              <div className="flex flex-wrap gap-2 mt-1">
                {company.tech_stack.map((tech, i) => (
                  <span key={i} className="px-2 py-1 bg-gray-100 rounded text-sm text-gray-700">
                    {tech}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Roles */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Open Roles</h2>
          <Button variant="outline" size="sm">
            Add Role
          </Button>
        </div>
        {roles.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No roles created yet
          </div>
        ) : (
          <div className="space-y-3">
            {roles.map((role) => (
              <div
                key={role.id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
              >
                <div>
                  <div className="font-medium text-gray-900">{role.title}</div>
                  <div className="text-sm text-gray-500">
                    {role.level && `${role.level} • `}
                    {role.department && `${role.department} • `}
                    {role.required_skills.slice(0, 3).join(', ')}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    role.status === 'active'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-100 text-gray-700'
                  }`}>
                    {role.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Data Sources */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Data Sources</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <LinkedInIcon className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <div className="font-medium text-gray-900">LinkedIn Import</div>
                <div className="text-sm text-gray-500">
                  {company?.linkedin_imported ? 'Imported' : 'Not imported'}
                </div>
              </div>
            </div>
            {company?.linkedin_imported && (
              <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">
                Connected
              </span>
            )}
          </div>
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <DatabaseIcon className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <div className="font-medium text-gray-900">Existing Database</div>
                <div className="text-sm text-gray-500">
                  {company?.existing_db_imported ? 'Imported' : 'Not imported'}
                </div>
              </div>
            </div>
            {company?.existing_db_imported && (
              <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">
                Imported
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Integrations */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Integrations</h2>
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <SlackIcon className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <div className="font-medium text-gray-900">Slack Bot (@hermes)</div>
              <div className="text-sm text-gray-500">
                Search candidates directly from Slack
              </div>
            </div>
          </div>
          <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">
            Active
          </span>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="bg-white rounded-xl border border-red-200 p-6">
        <h2 className="text-lg font-semibold text-red-900 mb-4">Danger Zone</h2>
        <div className="flex items-center justify-between">
          <div>
            <div className="font-medium text-gray-900">Reset Onboarding</div>
            <div className="text-sm text-gray-500">Clear all data and start over</div>
          </div>
          <Button
            variant="outline"
            className="border-red-300 text-red-600 hover:bg-red-50"
            onClick={() => {
              if (confirm('Are you sure? This will clear all your data.')) {
                localStorage.removeItem('onboarding-state');
                window.location.href = '/onboarding';
              }
            }}
          >
            Reset
          </Button>
        </div>
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

function DatabaseIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
    </svg>
  );
}

function SlackIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zM15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z" />
    </svg>
  );
}
