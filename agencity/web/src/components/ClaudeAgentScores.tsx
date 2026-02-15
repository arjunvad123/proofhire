import { AgentScore } from '@/lib/api';

interface ClaudeAgentScoresProps {
  agentScores: {
    skills_agent?: AgentScore;
    skill_agent?: AgentScore;
    trajectory_agent?: AgentScore;
    fit_agent?: AgentScore;
    timing_agent?: AgentScore;
  };
  overallScore: number;
  confidence: number;
  weightedCalculation: string;
}

const AGENT_CONFIG = [
  { key: 'skills_agent', altKey: 'skill_agent', label: 'Skills Match', weight: '40%', icon: '🎯' },
  { key: 'trajectory_agent', label: 'Career Growth', weight: '30%', icon: '📈' },
  { key: 'fit_agent', label: 'Culture Fit', weight: '20%', icon: '🤝' },
  { key: 'timing_agent', label: 'Timing', weight: '10%', icon: '⏰' },
];

export function ClaudeAgentScores({
  agentScores,
  overallScore,
  confidence,
  weightedCalculation,
}: ClaudeAgentScoresProps) {
  const confidenceColor = confidence >= 0.8 ? 'text-green-600' :
                         confidence >= 0.6 ? 'text-amber-600' : 'text-orange-600';

  return (
    <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg border border-indigo-200 p-5 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <h3 className="text-sm font-bold text-gray-900">Claude AI Analysis</h3>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-indigo-600">
            {Math.round(overallScore)}<span className="text-lg text-gray-400">/100</span>
          </div>
          <div className={`text-xs font-medium ${confidenceColor}`}>
            {Math.round(confidence * 100)}% confidence
          </div>
        </div>
      </div>

      {/* Agent Scores */}
      <div className="space-y-3">
        {AGENT_CONFIG.map((config) => {
          // Try both key variants (skills_agent and skill_agent)
          const agentData = agentScores[config.key as keyof typeof agentScores] ||
                          (config.altKey ? agentScores[config.altKey as keyof typeof agentScores] : null);

          if (!agentData) return null;

          const scorePercent = Math.round(agentData.score);
          const barColor = scorePercent >= 75 ? 'bg-green-500' :
                          scorePercent >= 50 ? 'bg-amber-500' : 'bg-red-500';

          return (
            <div key={config.key} className="bg-white rounded-lg p-3 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-base">{config.icon}</span>
                  <span className="text-sm font-semibold text-gray-900">{config.label}</span>
                  <span className="text-xs text-gray-500 font-medium">({config.weight})</span>
                </div>
                <span className="text-sm font-bold text-gray-900">
                  {scorePercent}%
                </span>
              </div>

              {/* Progress Bar */}
              <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden mb-2">
                <div
                  className={`h-full ${barColor} transition-all duration-300`}
                  style={{ width: `${scorePercent}%` }}
                />
              </div>

              {/* Reasoning (truncated) */}
              {agentData.reasoning && (
                <p className="text-xs text-gray-600 line-clamp-2">
                  {agentData.reasoning}
                </p>
              )}
            </div>
          );
        })}
      </div>

      {/* Weighted Calculation */}
      <div className="mt-4 pt-4 border-t border-indigo-200">
        <div className="flex items-center gap-2 text-xs text-gray-700">
          <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
          <span className="font-medium">Calculation:</span>
          <span className="text-gray-600">{weightedCalculation}</span>
        </div>
      </div>
    </div>
  );
}
