interface EnrichmentBadgeProps {
  sources: string[];
  dataQualityScore: number;
}

export function EnrichmentBadge({ sources, dataQualityScore }: EnrichmentBadgeProps) {
  if (sources.length === 0) {
    return null;
  }

  const sourceColors: Record<string, string> = {
    pdl: 'bg-blue-100 text-blue-800 border-blue-200',
    perplexity: 'bg-purple-100 text-purple-800 border-purple-200',
    manual: 'bg-green-100 text-green-800 border-green-200'
  };

  const qualityPercent = Math.round(dataQualityScore * 100);
  const qualityColor = dataQualityScore >= 0.7 ? 'text-green-600' :
                       dataQualityScore >= 0.4 ? 'text-amber-600' : 'text-orange-600';

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {sources.map((source) => (
        <span
          key={source}
          className={`inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold rounded border uppercase tracking-wide ${
            sourceColors[source.toLowerCase()] || sourceColors.manual
          }`}
          title={`Enriched with ${source.toUpperCase()}`}
        >
          {source === 'pdl' && (
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
              <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
            </svg>
          )}
          {source === 'perplexity' && (
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
            </svg>
          )}
          {source.toUpperCase()}
        </span>
      ))}

      <span
        className={`inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold rounded border border-gray-300 bg-white ${qualityColor}`}
        title={`Data completeness: ${qualityPercent}%`}
      >
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        {qualityPercent}% Complete
      </span>
    </div>
  );
}
