'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getRoles, getCurrentOrg, Role } from '@/lib/api';

export default function DashboardPage() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [orgId, setOrgId] = useState<string | null>(null);

  useEffect(() => {
    // First get the user's org, then fetch roles
    getCurrentOrg().then((orgResult) => {
      if (orgResult.data) {
        setOrgId(orgResult.data.id);
        getRoles(orgResult.data.id).then((result) => {
          if (result.data) {
            setRoles(result.data);
          }
          setLoading(false);
        });
      } else {
        setLoading(false);
      }
    });
  }, []);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="font-bold text-xl">ProofHire</h1>
          <nav className="flex items-center gap-4">
            <Link href="/roles/new" className="text-sm bg-slate-900 text-white px-4 py-2 rounded-md">
              New Role
            </Link>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-2">Dashboard</h2>
          <p className="text-slate-600">Manage your roles and review candidates</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-6 rounded-lg border">
            <div className="text-3xl font-bold">{roles.length}</div>
            <div className="text-slate-600 text-sm">Active Roles</div>
          </div>
          <div className="bg-white p-6 rounded-lg border">
            <div className="text-3xl font-bold">0</div>
            <div className="text-slate-600 text-sm">Pending Reviews</div>
          </div>
          <div className="bg-white p-6 rounded-lg border">
            <div className="text-3xl font-bold">0</div>
            <div className="text-slate-600 text-sm">Completed This Week</div>
          </div>
          <div className="bg-white p-6 rounded-lg border">
            <div className="text-3xl font-bold">--</div>
            <div className="text-slate-600 text-sm">Avg Proof Rate</div>
          </div>
        </div>

        {/* Roles List */}
        <div className="bg-white rounded-lg border">
          <div className="p-4 border-b">
            <h3 className="font-semibold">Your Roles</h3>
          </div>

          {loading ? (
            <div className="p-8 text-center text-slate-500">Loading...</div>
          ) : roles.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-slate-500 mb-4">No roles yet</p>
              <Link
                href="/roles/new"
                className="text-blue-600 hover:underline"
              >
                Create your first role
              </Link>
            </div>
          ) : (
            <div className="divide-y">
              {roles.map((role) => (
                <Link
                  key={role.id}
                  href={`/roles/${role.id}`}
                  className="p-4 flex items-center justify-between hover:bg-slate-50"
                >
                  <div>
                    <div className="font-medium">{role.title}</div>
                    <div className="text-sm text-slate-500">
                      Created {new Date(role.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span
                      className={`text-xs px-2 py-1 rounded-full ${
                        role.status === 'active'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {role.status}
                    </span>
                    <span className="text-slate-400">&rarr;</span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
