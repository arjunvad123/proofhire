import { ResearchHighlight } from '@/lib/api';

interface PerplexityResearchCardProps {
  highlights: ResearchHighlight[];
}

const ICON_MAP: Record<string, string> = {
  github: '💻',
  publication: '📚',
  achievement: '🏆',
  skill: '🔬',
};

export function PerplexityResearchCard({ highlights }: PerplexityResearchCardProps) {
  if (highlights.length === 0) {
    return null;
  }

  // Group highlights by type
  const groupedHighlights: Record<string, ResearchHighlight[]> = {};
  highlights.forEach((highlight) => {
    if (!groupedHighlights[highlight.type]) {
      groupedHighlights[highlight.type] = [];
    }
    groupedHighlights[highlight.type].push(highlight);
  });

  const typeLabels: Record<string, string> = {
    github: 'GitHub Projects & Code',
    publication: 'Publications & Talks',
    achievement: 'Notable Achievements',
    skill: 'Technical Skills',
  };

  return (
    <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg border border-purple-200 p-5 shadow-sm">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg flex items-center justify-center">
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <h3 className="text-sm font-bold text-gray-900">Deep Research Insights</h3>
        <span className="ml-auto text-xs font-medium text-purple-700 bg-purple-100 px-2 py-0.5 rounded border border-purple-200">
          Perplexity AI
        </span>
      </div>

      {/* Grouped Highlights */}
      <div className="space-y-4">
        {Object.entries(groupedHighlights).map(([type, items]) => (
          <div key={type} className="bg-white rounded-lg p-4 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lg">{ICON_MAP[type] || '📌'}</span>
              <h4 className="text-sm font-semibold text-gray-900">
                {typeLabels[type] || type}
              </h4>
              <span className="ml-auto text-xs text-gray-500">
                {items.length} {items.length === 1 ? 'item' : 'items'}
              </span>
            </div>

            <ul className="space-y-2">
              {items.map((item, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                  <span className="text-purple-500 mt-0.5">•</span>
                  <div className="flex-1">
                    {item.url ? (
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 hover:underline font-medium"
                      >
                        {item.description}
                      </a>
                    ) : (
                      <span>{item.description}</span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {/* Footer Note */}
      <div className="mt-4 pt-3 border-t border-purple-200">
        <p className="text-xs text-gray-600 italic flex items-center gap-1">
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Research findings from public sources and professional profiles
        </p>
      </div>
    </div>
  );
}
