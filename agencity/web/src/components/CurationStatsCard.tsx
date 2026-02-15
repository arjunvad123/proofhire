export interface CurationStatsCardProps {
  searched: number;
  enriched: number;
  shortlisted: number;
  avgScore: number;
  processingTime?: number;
  aiAnalyzedCount?: number;
}

export function CurationStatsCard({
  searched,
  enriched,
  shortlisted,
  avgScore,
  processingTime = 120,
  aiAnalyzedCount,
}: CurationStatsCardProps) {
  const enrichmentRate = searched > 0 ? Math.round((enriched / searched) * 100) : 0;
  const costSavings = 100 - enrichmentRate;
  const aiAnalyzedRate = shortlisted > 0 && aiAnalyzedCount ? Math.round((aiAnalyzedCount / shortlisted) * 100) : 0;

  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-800">Curation Summary</h3>
        <span className="text-xs text-gray-500 flex items-center gap-1.5 uppercase tracking-wider font-medium">
          <svg className="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          ~{Math.round(processingTime / 60)} min processing
        </span>
      </div>

      <div className="grid grid-cols-5 gap-3">
        <div className="bg-white rounded-lg p-3 border border-gray-200/60 shadow-sm">
          <div className="text-2xl font-bold text-gray-900 tracking-tight">{searched.toLocaleString()}</div>
          <div className="text-[10px] text-gray-500 uppercase tracking-widest mt-1 font-semibold">Searched</div>
        </div>

        <div className="bg-white rounded-lg p-3 border border-gray-200/60 shadow-sm">
          <div className="text-2xl font-bold text-blue-600 tracking-tight">{enriched}</div>
          <div className="text-[10px] text-gray-500 uppercase tracking-widest mt-1 font-semibold">Enriched ({enrichmentRate}%)</div>
        </div>

        {aiAnalyzedCount !== undefined && aiAnalyzedCount > 0 && (
          <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-lg p-3 border border-indigo-200/60 shadow-sm">
            <div className="text-2xl font-bold text-indigo-600 tracking-tight">{aiAnalyzedCount}</div>
            <div className="text-[10px] text-indigo-700 uppercase tracking-widest mt-1 font-semibold">AI-Analyzed ({aiAnalyzedRate}%)</div>
          </div>
        )}

        <div className="bg-white rounded-lg p-3 border border-gray-200/60 shadow-sm">
          <div className="text-2xl font-bold text-purple-600 tracking-tight">{shortlisted}</div>
          <div className="text-[10px] text-gray-500 uppercase tracking-widest mt-1 font-semibold">Shortlist</div>
        </div>

        <div className="bg-white rounded-lg p-3 border border-gray-200/60 shadow-sm">
          <div className="text-2xl font-bold text-green-600 tracking-tight">{avgScore}/100</div>
          <div className="text-[10px] text-gray-500 uppercase tracking-widest mt-1 font-semibold">Avg Score</div>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between text-xs">
        <span className="text-gray-600 flex items-center gap-1.5 font-medium">
          <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Cost savings: <span className="text-green-700 font-bold">{costSavings}%</span> (enriched only top {enrichmentRate}%)
        </span>
        <span className="text-green-700 font-bold bg-green-50/50 px-2 py-1 rounded border border-green-200 flex items-center gap-1 uppercase tracking-tighter text-[10px]">
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
          Optimized enrichment strategy
        </span>
      </div>
    </div>
  );
}
