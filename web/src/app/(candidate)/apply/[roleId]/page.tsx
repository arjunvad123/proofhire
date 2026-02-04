'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getRole, createApplication, Role } from '@/lib/api';

export default function ApplyPage() {
  const params = useParams();
  const router = useRouter();
  const roleId = params.roleId as string;

  const [role, setRole] = useState<Role | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [consent, setConsent] = useState(false);

  useEffect(() => {
    getRole(roleId).then((result) => {
      if (result.data) {
        setRole(result.data);
      }
      setLoading(false);
    });
  }, [roleId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    const result = await createApplication(roleId, {
      name,
      email,
      consent,
    });

    if (result.data) {
      router.push(`/simulation/${result.data.id}`);
    }

    setSubmitting(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-slate-500">Loading...</div>
      </div>
    );
  }

  if (!role) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-slate-500">Role not found</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-2xl mx-auto px-4 py-6 text-center">
          <div className="text-sm text-slate-500 mb-2">Application for</div>
          <h1 className="text-2xl font-bold">{role.title}</h1>
        </div>
      </header>

      {/* Application Form */}
      <main className="max-w-2xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg border p-6">
          <h2 className="text-lg font-semibold mb-6">Your Information</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-slate-700 mb-1">
                Full Name
              </label>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-slate-400"
                required
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-1">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-slate-400"
                required
              />
            </div>

            <div className="pt-4 border-t mt-6">
              <h3 className="font-medium mb-3">About the Assessment</h3>
              <div className="text-sm text-slate-600 space-y-2">
                <p>You will complete a coding simulation that involves:</p>
                <ul className="list-disc pl-5 space-y-1">
                  <li>Diagnosing and fixing a bug in a codebase</li>
                  <li>Adding regression tests</li>
                  <li>Writing a brief explanation of your approach</li>
                </ul>
                <p className="mt-3">
                  Time limit: <strong>60 minutes</strong>
                </p>
              </div>
            </div>

            <div className="pt-4 border-t mt-6">
              <label className="flex items-start gap-3">
                <input
                  type="checkbox"
                  checked={consent}
                  onChange={(e) => setConsent(e.target.checked)}
                  className="mt-1"
                  required
                />
                <span className="text-sm text-slate-600">
                  I consent to having my submission evaluated and shared with the hiring
                  company. I understand that my code, test results, and writeup will be
                  reviewed as part of the application process.
                </span>
              </label>
            </div>

            <button
              type="submit"
              disabled={!consent || submitting}
              className="w-full bg-slate-900 text-white py-3 rounded-lg hover:bg-slate-800 disabled:opacity-50 mt-6"
            >
              {submitting ? 'Starting...' : 'Start Assessment'}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-slate-500 mt-6">
          By starting, you agree to our terms of service and privacy policy.
        </p>
      </main>
    </div>
  );
}
