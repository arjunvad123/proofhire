'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { useOnboarding } from '@/lib/onboarding-context';
import { completeOnboarding } from '@/lib/api';

export function CompleteStep() {
  const { state, setComplete, reset } = useOnboarding();
  const [completing, setCompleting] = useState(false);

  useEffect(() => {
    const complete = async () => {
      if (state.companyId && !state.isComplete) {
        setCompleting(true);
        try {
          await completeOnboarding(state.companyId);
          setComplete();
        } catch (err) {
          console.error('Failed to complete onboarding:', err);
        } finally {
          setCompleting(false);
        }
      }
    };

    complete();
  }, [state.companyId, state.isComplete, setComplete]);

  const stats = {
    roles: state.roles.length,
    connections:
      (state.linkedinImport?.records_created || 0) +
      (state.linkedinImport?.records_matched || 0),
    database:
      (state.databaseImport?.records_created || 0) +
      (state.databaseImport?.records_matched || 0),
    total:
      (state.linkedinImport?.records_created || 0) +
      (state.linkedinImport?.records_matched || 0) +
      (state.databaseImport?.records_created || 0) +
      (state.databaseImport?.records_matched || 0),
  };

  if (completing) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto" />
        <p className="mt-4 text-gray-600">Setting up your account...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="text-center">
        <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-4">
          <svg
            className="h-8 w-8 text-green-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>
        <h2 className="text-2xl font-bold text-gray-900">
          You&apos;re all set!
        </h2>
        <p className="mt-2 text-gray-600">
          Your hiring network is ready to go
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <p className="text-3xl font-bold text-gray-900">{stats.roles}</p>
          <p className="text-sm text-gray-500">
            {stats.roles === 1 ? 'Role' : 'Roles'} defined
          </p>
        </div>
        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <p className="text-3xl font-bold text-gray-900">{stats.connections}</p>
          <p className="text-sm text-gray-500">LinkedIn connections</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <p className="text-3xl font-bold text-gray-900">{stats.database}</p>
          <p className="text-sm text-gray-500">Database contacts</p>
        </div>
      </div>

      {/* Total */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
        <p className="text-lg font-medium text-blue-900">
          {stats.total} people in your network
        </p>
        <p className="text-sm text-blue-700 mt-1">
          Ready to search and discover candidates
        </p>
      </div>

      {/* Next steps */}
      <div className="border border-gray-200 rounded-lg p-4">
        <h3 className="font-medium text-gray-900 mb-3">What&apos;s next?</h3>
        <ul className="space-y-3 text-sm text-gray-600">
          <li className="flex items-start gap-3">
            <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium">
              1
            </span>
            <span>
              <strong>Use @hermes in Slack</strong> to search for candidates
              with natural language queries
            </span>
          </li>
          <li className="flex items-start gap-3">
            <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium">
              2
            </span>
            <span>
              <strong>Enrichment runs automatically</strong> - profiles will be
              enhanced with public information over time
            </span>
          </li>
          <li className="flex items-start gap-3">
            <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium">
              3
            </span>
            <span>
              <strong>Import more data anytime</strong> - add more connections
              or database exports as you grow
            </span>
          </li>
        </ul>
      </div>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row gap-3 pt-4">
        <Button
          variant="outline"
          className="flex-1"
          onClick={() => {
            reset();
            window.location.reload();
          }}
        >
          Start Over
        </Button>
        <Button
          className="flex-1"
          onClick={() => {
            window.location.href = '/dashboard';
          }}
        >
          Go to Dashboard
        </Button>
      </div>
    </div>
  );
}
