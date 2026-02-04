'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { getBrief, Brief } from '@/lib/api';
import { CLAIM_DISPLAY_NAMES, DIMENSION_DISPLAY_NAMES } from '@/lib/types';

export default function BriefViewerPage() {
  const params = useParams();
  const applicationId = params.applicationId as string;
  const [brief, setBrief] = useState<Brief | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'proven' | 'unproven' | 'questions'>('proven');

  useEffect(() => {
    getBrief(applicationId).then((result) => {
      if (result.data) {
        setBrief(result.data);
      }
      setLoading(false);
    });
  }, [applicationId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-slate-500">Loading brief...</div>
      </div>
    );
  }

  if (!brief) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-slate-500">Brief not found</div>
      </div>
    );
  }

  const proofRatePercent = Math.round(brief.proof_rate * 100);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <Link href="/dashboard" className="text-sm text-slate-500 hover:text-slate-700">
              &larr; Back to Dashboard
            </Link>
            <h1 className="font-bold text-xl mt-1">Candidate Brief</h1>
          </div>
        </div>
      </header>

      {/* Brief Content */}
      <main className="max-w-5xl mx-auto px-4 py-8">
        {/* Summary Card */}
        <div className="bg-white rounded-lg border p-6 mb-6">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-2xl font-bold">{brief.candidate_name}</h2>
              <p className="text-slate-600">{brief.simulation_name}</p>
              <p className="text-sm text-slate-500 mt-1">
                Completed {new Date(brief.created_at).toLocaleDateString()}
              </p>
            </div>
            <div className="text-right">
              <div className="text-4xl font-bold">{proofRatePercent}%</div>
              <div className="text-slate-600">Proof Rate</div>
            </div>
          </div>

          {/* Proof Rate Bar */}
          <div className="mt-6">
            <div className="flex justify-between text-sm text-slate-600 mb-2">
              <span>{brief.proven_claims.length} proven</span>
              <span>{brief.unproven_claims.length} unproven</span>
            </div>
            <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500"
                style={{ width: `${proofRatePercent}%` }}
              />
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 border-b mb-6">
          <button
            onClick={() => setActiveTab('proven')}
            className={`pb-3 px-2 text-sm font-medium border-b-2 -mb-px ${
              activeTab === 'proven'
                ? 'border-slate-900 text-slate-900'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Proven ({brief.proven_claims.length})
          </button>
          <button
            onClick={() => setActiveTab('unproven')}
            className={`pb-3 px-2 text-sm font-medium border-b-2 -mb-px ${
              activeTab === 'unproven'
                ? 'border-slate-900 text-slate-900'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Unproven ({brief.unproven_claims.length})
          </button>
          <button
            onClick={() => setActiveTab('questions')}
            className={`pb-3 px-2 text-sm font-medium border-b-2 -mb-px ${
              activeTab === 'questions'
                ? 'border-slate-900 text-slate-900'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Interview Questions
          </button>
        </div>

        {/* Proven Claims */}
        {activeTab === 'proven' && (
          <div className="space-y-4">
            {brief.proven_claims.map((claim, i) => (
              <div key={i} className="bg-white rounded-lg border p-4">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-medium">
                      {CLAIM_DISPLAY_NAMES[claim.claim_type] || claim.claim_type}
                    </h3>
                    <p className="text-slate-600 text-sm mt-1">{claim.statement}</p>
                    <div className="flex gap-2 mt-2">
                      {claim.dimensions.map((dim) => (
                        <span
                          key={dim}
                          className="text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded"
                        >
                          {DIMENSION_DISPLAY_NAMES[dim] || dim}
                        </span>
                      ))}
                    </div>

                    {/* Evidence */}
                    <details className="mt-3">
                      <summary className="text-sm text-blue-600 cursor-pointer hover:underline">
                        View evidence ({claim.evidence_refs.length} items)
                      </summary>
                      <div className="mt-2 pl-4 border-l-2 border-slate-200 space-y-2">
                        {claim.evidence_refs.map((ref, j) => (
                          <div key={j} className="text-sm text-slate-600">
                            <span className="font-mono text-xs bg-slate-100 px-1 rounded">
                              {String(ref.type)}:{String(ref.id)}
                            </span>
                            <span className="ml-2">{String(ref.value)}</span>
                          </div>
                        ))}
                      </div>
                    </details>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Unproven Claims */}
        {activeTab === 'unproven' && (
          <div className="space-y-4">
            {brief.unproven_claims.map((claim, i) => (
              <div key={i} className="bg-white rounded-lg border p-4">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-amber-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-amber-600 text-sm font-bold">?</span>
                  </div>
                  <div>
                    <h3 className="font-medium">
                      {CLAIM_DISPLAY_NAMES[claim.claim_type] || claim.claim_type}
                    </h3>
                    <p className="text-slate-600 text-sm mt-1">{claim.statement}</p>
                    <p className="text-sm text-amber-700 mt-2 bg-amber-50 px-3 py-2 rounded">
                      Why unproven: {claim.reason}
                    </p>

                    {claim.suggested_questions.length > 0 && (
                      <div className="mt-3">
                        <div className="text-sm font-medium text-slate-700 mb-2">
                          Suggested questions:
                        </div>
                        <ul className="space-y-1">
                          {claim.suggested_questions.map((q, j) => (
                            <li key={j} className="text-sm text-slate-600 pl-4 relative">
                              <span className="absolute left-0">&bull;</span>
                              {q}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Interview Questions */}
        {activeTab === 'questions' && (
          <div className="bg-white rounded-lg border p-6">
            <h3 className="font-semibold mb-4">Recommended Interview Questions</h3>
            <p className="text-sm text-slate-600 mb-6">
              These questions are generated based on claims that could not be proven from
              the simulation evidence. Use them to explore these areas in a follow-up interview.
            </p>
            <ol className="space-y-4">
              {brief.suggested_interview_questions.map((question, i) => (
                <li key={i} className="flex gap-3">
                  <span className="w-6 h-6 bg-slate-100 rounded-full flex items-center justify-center flex-shrink-0 text-sm font-medium">
                    {i + 1}
                  </span>
                  <span className="text-slate-700">{question}</span>
                </li>
              ))}
            </ol>
          </div>
        )}
      </main>
    </div>
  );
}
