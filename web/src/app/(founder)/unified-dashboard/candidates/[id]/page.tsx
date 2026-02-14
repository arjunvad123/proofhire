'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';

// Types
interface CandidateDetail {
  // Agencity data
  id: string;
  name: string;
  email: string;
  title: string;
  company: string;
  location?: string;
  linkedin_url?: string;
  github_url?: string;

  // Scoring
  score: number;
  fit_score: number;
  warmth_score: number;
  timing_score?: number;

  // Warmth
  warmth_level: 'network' | 'warm' | 'cold';
  warm_path?: {
    type: 'direct' | 'school' | 'company' | '2nd_degree';
    description: string;
    connector?: string;
    strength: number;
  };

  // Skills & Experience
  skills: string[];
  experience_years?: number;
  previous_companies?: string[];
  education?: Array<{
    school: string;
    degree: string;
    field: string;
    year: string;
  }>;

  // Intelligence
  timing_signals?: string[];
  why_consider?: string;
  unknowns?: string[];

  // Status
  status: 'sourced' | 'contacted' | 'interviewing' | 'invited' | 'in_simulation' | 'reviewed';
  sourced_at: string;
  contacted_at?: string;
  invited_at?: string;

  // ProofHire integration
  proofhire_application_id?: string;
  simulation_status?: 'queued' | 'running' | 'completed' | 'failed';
  brief_available?: boolean;
}

export default function CandidateDetailPage() {
  const params = useParams();
  const router = useRouter();
  const candidateId = params.id as string;

  const [candidate, setCandidate] = useState<CandidateDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'intelligence' | 'activity'>('overview');

  useEffect(() => {
    loadCandidate();
  }, [candidateId]);

  async function loadCandidate() {
    setLoading(true);
    try {
      // TODO: Fetch from API
      // Mock data
      setCandidate({
        id: candidateId,
        name: 'Sarah Chen',
        email: 'sarah.chen@example.com',
        title: 'Senior ML Engineer',
        company: 'Google',
        location: 'San Francisco, CA',
        linkedin_url: 'https://linkedin.com/in/sarachen',
        github_url: 'https://github.com/sarachen',

        score: 94,
        fit_score: 85,
        warmth_score: 100,
        timing_score: 70,

        warmth_level: 'network',
        warm_path: {
          type: 'direct',
          description: 'You met at YC Demo Day 2022',
          strength: 100,
        },

        skills: ['Python', 'PyTorch', 'Machine Learning', 'TensorFlow', 'MLOps', 'Deep Learning', 'Computer Vision'],
        experience_years: 5,
        previous_companies: ['Meta', 'DeepMind (Intern)'],
        education: [
          {
            school: 'Stanford University',
            degree: 'MS',
            field: 'Computer Science',
            year: '2019',
          },
          {
            school: 'UC Berkeley',
            degree: 'BS',
            field: 'Computer Science',
            year: '2017',
          },
        ],

        timing_signals: [
          '4-year vesting cliff approaching (47 months at Google)',
          'Profile updated 3 days ago',
          'Recently joined 2 ML groups',
        ],
        why_consider: 'Sarah has 5 years of ML experience at Google, working on large-scale recommendation systems. Her PyTorch expertise matches your requirements perfectly, and she\'s approaching her 4-year vesting cliff - a common trigger for job changes. Her background at Meta before Google shows she thrives in fast-paced environments.',
        unknowns: [
          'Salary expectations unclear (likely $350K+ at current Google level)',
          'Remote work preference unknown',
          'Team size preference (currently on 12-person team)',
          'Interest in early-stage startups vs scale-ups',
        ],

        status: 'sourced',
        sourced_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      });
    } catch (error) {
      console.error('Error loading candidate:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleInviteToProofHire() {
    // TODO: Implement invite logic
    alert('Invite to ProofHire simulation');
  }

  async function handleContact() {
    // TODO: Implement contact logic
    alert('Contact candidate');
  }

  async function handleSave() {
    // TODO: Implement save logic
    alert('Candidate saved');
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!candidate) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Candidate not found</h2>
          <Link href="/unified-dashboard" className="text-blue-600 hover:underline">
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const warmthColors = {
    network: 'bg-green-50 text-green-700 border-green-200',
    warm: 'bg-yellow-50 text-yellow-700 border-yellow-200',
    cold: 'bg-gray-50 text-gray-700 border-gray-200',
  };

  const warmthLabels = {
    network: 'IN NETWORK',
    warm: 'WARM PATH',
    cold: 'COLD',
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.back()}
              className="p-2 hover:bg-gray-50 rounded-lg"
            >
              <ArrowLeftIcon />
            </button>
            <h1 className="text-xl font-bold text-black">Candidate Details</h1>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-3 gap-6">
          {/* Left Column - Main Info */}
          <div className="col-span-2 space-y-6">
            {/* Header Card */}
            <div className="bg-white rounded-lg shadow border border-gray-200 p-8">
              <div className="flex items-start gap-6">
                {/* Avatar */}
                <div className="w-24 h-24 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold text-3xl">
                  {candidate.name.charAt(0)}
                </div>

                {/* Info */}
                <div className="flex-1">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h2 className="text-3xl font-bold text-black mb-1">{candidate.name}</h2>
                      <p className="text-lg text-gray-600 mb-2">
                        {candidate.title} @ {candidate.company}
                      </p>
                      {candidate.location && (
                        <p className="text-sm text-gray-500">{candidate.location}</p>
                      )}
                    </div>
                    <div className="text-right">
                      <div className="text-5xl font-bold text-black mb-1">{candidate.score}</div>
                      <div className="text-sm text-gray-500">Overall Score</div>
                    </div>
                  </div>

                  {/* Badges */}
                  <div className="flex items-center gap-2 mb-4">
                    <span
                      className={`px-3 py-1 rounded-full text-sm font-medium border ${
                        warmthColors[candidate.warmth_level]
                      }`}
                    >
                      {warmthLabels[candidate.warmth_level]}
                    </span>
                    <span className="px-3 py-1 rounded-full text-sm font-medium bg-blue-50 text-blue-700 border border-blue-200">
                      {candidate.experience_years}+ Years Experience
                    </span>
                  </div>

                  {/* Links */}
                  <div className="flex items-center gap-3">
                    {candidate.linkedin_url && (
                      <a
                        href={candidate.linkedin_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline text-sm flex items-center gap-1"
                      >
                        <LinkedInIcon />
                        LinkedIn
                      </a>
                    )}
                    {candidate.github_url && (
                      <a
                        href={candidate.github_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline text-sm flex items-center gap-1"
                      >
                        <GithubIcon />
                        GitHub
                      </a>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Tabs */}
            <div className="bg-white rounded-lg shadow border border-gray-200">
              <div className="border-b border-gray-200 px-6">
                <div className="flex gap-1">
                  <TabButton
                    active={activeTab === 'overview'}
                    onClick={() => setActiveTab('overview')}
                  >
                    Overview
                  </TabButton>
                  <TabButton
                    active={activeTab === 'intelligence'}
                    onClick={() => setActiveTab('intelligence')}
                  >
                    Intelligence
                  </TabButton>
                  <TabButton
                    active={activeTab === 'activity'}
                    onClick={() => setActiveTab('activity')}
                  >
                    Activity
                  </TabButton>
                </div>
              </div>

              <div className="p-6">
                {activeTab === 'overview' && (
                  <OverviewTab candidate={candidate} />
                )}
                {activeTab === 'intelligence' && (
                  <IntelligenceTab candidate={candidate} />
                )}
                {activeTab === 'activity' && (
                  <ActivityTab candidate={candidate} />
                )}
              </div>
            </div>
          </div>

          {/* Right Column - Actions & Sidebar */}
          <div className="space-y-6">
            {/* Actions Card */}
            <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-black mb-4">Actions</h3>
              <div className="space-y-3">
                {!candidate.proofhire_application_id && (
                  <button
                    onClick={handleInviteToProofHire}
                    className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
                  >
                    Invite to ProofHire
                  </button>
                )}
                {candidate.proofhire_application_id && candidate.brief_available && (
                  <Link
                    href={`/candidates/${candidate.proofhire_application_id}`}
                    className="block w-full px-4 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 text-center"
                  >
                    View Evaluation Brief
                  </Link>
                )}
                <button
                  onClick={handleContact}
                  className="w-full px-4 py-3 bg-white border border-gray-200 text-gray-900 rounded-lg font-medium hover:bg-gray-50"
                >
                  Contact Candidate
                </button>
                <button
                  onClick={handleSave}
                  className="w-full px-4 py-3 bg-white border border-gray-200 text-gray-900 rounded-lg font-medium hover:bg-gray-50"
                >
                  Save for Later
                </button>
                <button className="w-full px-4 py-3 bg-white border border-gray-200 text-red-600 rounded-lg font-medium hover:bg-red-50">
                  Not Interested
                </button>
              </div>
            </div>

            {/* Scores Card */}
            <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-black mb-4">Scores Breakdown</h3>
              <div className="space-y-4">
                <ScoreBar label="Fit" value={candidate.fit_score} color="blue" />
                <ScoreBar label="Warmth" value={candidate.warmth_score} color="green" />
                {candidate.timing_score && (
                  <ScoreBar label="Timing" value={candidate.timing_score} color="yellow" />
                )}
              </div>
            </div>

            {/* Status Card */}
            <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-black mb-4">Status</h3>
              <div className="space-y-3">
                <StatusItem
                  label="Sourced"
                  date={candidate.sourced_at}
                  active={true}
                />
                {candidate.contacted_at && (
                  <StatusItem
                    label="Contacted"
                    date={candidate.contacted_at}
                    active={true}
                  />
                )}
                {candidate.invited_at && (
                  <StatusItem
                    label="Invited to Simulation"
                    date={candidate.invited_at}
                    active={true}
                  />
                )}
                {candidate.proofhire_application_id && (
                  <StatusItem
                    label="ProofHire Application"
                    active={true}
                  />
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

// Tab Content Components
function OverviewTab({ candidate }: { candidate: CandidateDetail }) {
  return (
    <div className="space-y-6">
      {/* Why Consider */}
      {candidate.why_consider && (
        <div>
          <h4 className="text-sm font-semibold text-gray-900 mb-2">Why Consider</h4>
          <p className="text-gray-700 leading-relaxed">{candidate.why_consider}</p>
        </div>
      )}

      {/* Skills */}
      <div>
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Skills</h4>
        <div className="flex flex-wrap gap-2">
          {candidate.skills.map((skill) => (
            <span
              key={skill}
              className="px-3 py-1.5 bg-gray-100 text-gray-700 text-sm rounded-lg"
            >
              {skill}
            </span>
          ))}
        </div>
      </div>

      {/* Experience */}
      <div>
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Experience</h4>
        <div className="space-y-3">
          <div className="p-3 bg-gray-50 rounded-lg">
            <div className="font-medium text-gray-900">{candidate.title}</div>
            <div className="text-sm text-gray-600">{candidate.company}</div>
          </div>
          {candidate.previous_companies?.map((company) => (
            <div key={company} className="p-3 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-600">{company}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Education */}
      {candidate.education && candidate.education.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-900 mb-3">Education</h4>
          <div className="space-y-3">
            {candidate.education.map((edu, idx) => (
              <div key={idx} className="p-3 bg-gray-50 rounded-lg">
                <div className="font-medium text-gray-900">{edu.school}</div>
                <div className="text-sm text-gray-600">
                  {edu.degree} in {edu.field} • {edu.year}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Unknowns */}
      {candidate.unknowns && candidate.unknowns.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-900 mb-3">Unknowns</h4>
          <ul className="space-y-2">
            {candidate.unknowns.map((unknown, idx) => (
              <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                <span className="text-yellow-600 mt-1">•</span>
                <span>{unknown}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function IntelligenceTab({ candidate }: { candidate: CandidateDetail }) {
  return (
    <div className="space-y-6">
      {/* Warm Path */}
      {candidate.warm_path && (
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
          <h4 className="text-sm font-semibold text-blue-900 mb-2">
            Warm Path ({candidate.warm_path.strength}% strength)
          </h4>
          <p className="text-blue-800 mb-2">{candidate.warm_path.description}</p>
          {candidate.warm_path.connector && (
            <p className="text-sm text-blue-700">via {candidate.warm_path.connector}</p>
          )}
        </div>
      )}

      {/* Timing Signals */}
      {candidate.timing_signals && candidate.timing_signals.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-900 mb-3">Timing Signals</h4>
          <div className="space-y-2">
            {candidate.timing_signals.map((signal, idx) => (
              <div key={idx} className="flex items-start gap-3 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                <ClockIcon />
                <span className="text-sm text-gray-900">{signal}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Network Insights */}
      <div>
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Network Insights</h4>
        <div className="space-y-2 text-sm text-gray-700">
          <div className="flex items-center gap-2">
            <CheckIcon />
            <span>Connected via {candidate.warm_path?.type || 'network'}</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckIcon />
            <span>High engagement on LinkedIn (updated recently)</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckIcon />
            <span>Active in ML communities</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function ActivityTab({ candidate }: { candidate: CandidateDetail }) {
  return (
    <div className="space-y-4">
      <ActivityItem
        action="Sourced from search"
        timestamp={candidate.sourced_at}
        description="Found via ML Engineer search with network filter"
      />
      {candidate.contacted_at && (
        <ActivityItem
          action="Contacted"
          timestamp={candidate.contacted_at}
          description="Outreach message sent via LinkedIn"
        />
      )}
      {candidate.invited_at && (
        <ActivityItem
          action="Invited to ProofHire"
          timestamp={candidate.invited_at}
          description="Simulation invitation sent to email"
        />
      )}
    </div>
  );
}

// Helper Components
function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
        active
          ? 'border-blue-600 text-blue-600'
          : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
      }`}
    >
      {children}
    </button>
  );
}

function ScoreBar({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: 'blue' | 'green' | 'yellow';
}) {
  const colors = {
    blue: 'bg-blue-600',
    green: 'bg-green-600',
    yellow: 'bg-yellow-600',
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-900">{label}</span>
        <span className="text-sm font-semibold text-gray-900">{value}/100</span>
      </div>
      <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full ${colors[color]} transition-all duration-300`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

function StatusItem({
  label,
  date,
  active,
}: {
  label: string;
  date?: string;
  active: boolean;
}) {
  return (
    <div className="flex items-start gap-3">
      <div className={`w-2 h-2 rounded-full mt-2 ${active ? 'bg-green-500' : 'bg-gray-300'}`} />
      <div className="flex-1">
        <div className="text-sm font-medium text-gray-900">{label}</div>
        {date && (
          <div className="text-xs text-gray-500">
            {new Date(date).toLocaleString()}
          </div>
        )}
      </div>
    </div>
  );
}

function ActivityItem({
  action,
  timestamp,
  description,
}: {
  action: string;
  timestamp: string;
  description: string;
}) {
  return (
    <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
        <ActivityIcon />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-gray-900">{action}</div>
        <div className="text-xs text-gray-600">{description}</div>
        <div className="text-xs text-gray-500 mt-1">
          {new Date(timestamp).toLocaleString()}
        </div>
      </div>
    </div>
  );
}

// Icons
function ArrowLeftIcon() {
  return (
    <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
    </svg>
  );
}

function LinkedInIcon() {
  return (
    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
    </svg>
  );
}

function GithubIcon() {
  return (
    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
    </svg>
  );
}

function ClockIcon() {
  return (
    <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  );
}

function ActivityIcon() {
  return (
    <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  );
}
