'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { getApplication, Application } from '@/lib/api';

export default function StatusPage() {
  const params = useParams();
  const applicationId = params.applicationId as string;
  const [application, setApplication] = useState<Application | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      const result = await getApplication(applicationId);
      if (result.data) {
        setApplication(result.data);
      }
      setLoading(false);
    };

    fetchStatus();

    // Poll for updates
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, [applicationId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-slate-500">Loading...</div>
      </div>
    );
  }

  const getStatusDisplay = () => {
    switch (application?.status) {
      case 'simulation_completed':
        return {
          title: 'Submission Received',
          description: 'Your submission is being evaluated. This usually takes a few minutes.',
          icon: '⏳',
          color: 'text-amber-600',
        };
      case 'evaluated':
        return {
          title: 'Evaluation Complete',
          description: 'Your submission has been evaluated and sent to the hiring team.',
          icon: '✓',
          color: 'text-green-600',
        };
      default:
        return {
          title: 'Processing',
          description: 'Your submission is being processed.',
          icon: '⏳',
          color: 'text-slate-600',
        };
    }
  };

  const status = getStatusDisplay();

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <div className="max-w-md w-full text-center p-8">
        <div className={`text-6xl mb-6 ${status.color}`}>{status.icon}</div>
        <h1 className="text-2xl font-bold mb-2">{status.title}</h1>
        <p className="text-slate-600 mb-8">{status.description}</p>

        {application?.status === 'evaluated' && (
          <div className="bg-white rounded-lg border p-6 text-left mb-6">
            <h2 className="font-semibold mb-3">What happens next?</h2>
            <ol className="space-y-2 text-sm text-slate-600">
              <li className="flex gap-2">
                <span className="text-slate-400">1.</span>
                The hiring team will review your evidence-based brief
              </li>
              <li className="flex gap-2">
                <span className="text-slate-400">2.</span>
                If there are areas to explore, they may schedule a follow-up interview
              </li>
              <li className="flex gap-2">
                <span className="text-slate-400">3.</span>
                You&apos;ll hear back within 5 business days
              </li>
            </ol>
          </div>
        )}

        {application?.status === 'simulation_completed' && (
          <div className="animate-pulse flex items-center justify-center gap-2 text-slate-500">
            <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" />
            <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
            <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
          </div>
        )}

        <Link
          href="/"
          className="text-sm text-slate-500 hover:text-slate-700"
        >
          Return to home
        </Link>
      </div>
    </div>
  );
}
