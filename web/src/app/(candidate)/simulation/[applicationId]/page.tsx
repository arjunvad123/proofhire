'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { getApplication, startSimulation, submitSimulation, Application, SimulationRun } from '@/lib/api';

// Dynamically import Monaco to avoid SSR issues
const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false });

const INITIAL_CODE = `# Fix the bug in the rate limiter below
# The rate limiter should allow N requests per time window
# but is incorrectly blocking legitimate requests

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}

    def allow_request(self, client_id: str, timestamp: float) -> bool:
        # Clean up old entries
        cutoff = timestamp - self.window_seconds
        if client_id in self.requests:
            self.requests[client_id] = [
                t for t in self.requests[client_id] if t > cutoff
            ]

        # Check if request should be allowed
        if client_id not in self.requests:
            self.requests[client_id] = []

        # BUG: This comparison is wrong!
        if len(self.requests[client_id]) > self.max_requests:
            return False

        self.requests[client_id].append(timestamp)
        return True
`;

const WRITEUP_PROMPTS = [
  '1. What was the bug? Explain the root cause.',
  '2. What did you change to fix it?',
  '3. What tradeoffs did you consider?',
  '4. How would you monitor this in production?',
];

export default function SimulationPage() {
  const params = useParams();
  const router = useRouter();
  const applicationId = params.applicationId as string;

  const [application, setApplication] = useState<Application | null>(null);
  const [run, setRun] = useState<SimulationRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [code, setCode] = useState(INITIAL_CODE);
  const [writeup, setWriteup] = useState('');
  const [activeTab, setActiveTab] = useState<'code' | 'writeup'>('code');

  // Timer state
  const [timeRemaining, setTimeRemaining] = useState(60 * 60); // 60 minutes in seconds

  useEffect(() => {
    const init = async () => {
      const appResult = await getApplication(applicationId);
      if (appResult.data) {
        setApplication(appResult.data);

        // Start simulation if not already started
        if (appResult.data.status === 'applied') {
          const runResult = await startSimulation(applicationId);
          if (runResult.data) {
            setRun(runResult.data);
          }
        }
      }
      setLoading(false);
    };

    init();
  }, [applicationId]);

  // Timer countdown
  useEffect(() => {
    if (timeRemaining <= 0) return;

    const timer = setInterval(() => {
      setTimeRemaining((prev) => Math.max(0, prev - 1));
    }, 1000);

    return () => clearInterval(timer);
  }, [timeRemaining]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSubmit = async () => {
    if (!run) return;

    setSubmitting(true);

    const result = await submitSimulation(run.id, {
      code,
      writeup,
    });

    if (result.data) {
      router.push(`/status/${applicationId}`);
    }

    setSubmitting(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-white">Loading simulation...</div>
      </div>
    );
  }

  const isTimeWarning = timeRemaining < 10 * 60; // Less than 10 minutes
  const isTimeCritical = timeRemaining < 5 * 60; // Less than 5 minutes

  return (
    <div className="h-screen flex flex-col bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-white font-semibold">Bug Fix: Rate Limiting Service</h1>
          <span className="text-xs bg-slate-700 text-slate-300 px-2 py-1 rounded">
            Python
          </span>
        </div>
        <div className="flex items-center gap-4">
          <div
            className={`font-mono text-lg ${
              isTimeCritical
                ? 'text-red-400'
                : isTimeWarning
                ? 'text-amber-400'
                : 'text-white'
            }`}
          >
            {formatTime(timeRemaining)}
          </div>
          <button
            onClick={handleSubmit}
            disabled={submitting || !code || !writeup}
            className="bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50"
          >
            {submitting ? 'Submitting...' : 'Submit'}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Instructions Panel */}
        <div className="w-80 bg-slate-800 border-r border-slate-700 overflow-y-auto">
          <div className="p-4">
            <h2 className="text-white font-semibold mb-3">Instructions</h2>
            <div className="text-sm text-slate-300 space-y-3">
              <p>
                A rate limiting service has a bug. Some tests are failing.
              </p>
              <div>
                <h3 className="text-white font-medium mb-1">Your task:</h3>
                <ol className="list-decimal pl-4 space-y-1">
                  <li>Find and fix the bug</li>
                  <li>Add a regression test</li>
                  <li>Complete the writeup</li>
                </ol>
              </div>
              <div className="pt-3 border-t border-slate-700">
                <h3 className="text-white font-medium mb-2">Writeup Prompts:</h3>
                <ul className="space-y-2">
                  {WRITEUP_PROMPTS.map((prompt, i) => (
                    <li key={i} className="text-xs text-slate-400">
                      {prompt}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Editor Area */}
        <div className="flex-1 flex flex-col">
          {/* Tabs */}
          <div className="bg-slate-800 border-b border-slate-700 flex">
            <button
              onClick={() => setActiveTab('code')}
              className={`px-4 py-2 text-sm ${
                activeTab === 'code'
                  ? 'bg-slate-900 text-white border-b-2 border-blue-500'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Code
            </button>
            <button
              onClick={() => setActiveTab('writeup')}
              className={`px-4 py-2 text-sm ${
                activeTab === 'writeup'
                  ? 'bg-slate-900 text-white border-b-2 border-blue-500'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Writeup
            </button>
          </div>

          {/* Editor */}
          <div className="flex-1">
            {activeTab === 'code' ? (
              <MonacoEditor
                height="100%"
                language="python"
                theme="vs-dark"
                value={code}
                onChange={(value) => setCode(value || '')}
                options={{
                  fontSize: 14,
                  minimap: { enabled: false },
                  padding: { top: 16 },
                  scrollBeyondLastLine: false,
                }}
              />
            ) : (
              <div className="h-full p-4">
                <textarea
                  value={writeup}
                  onChange={(e) => setWriteup(e.target.value)}
                  placeholder="Write your explanation here. Address all the prompts in the instructions panel."
                  className="w-full h-full bg-slate-800 text-white p-4 rounded-lg border border-slate-700 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
