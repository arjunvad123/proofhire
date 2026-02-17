import React from 'react';

interface CurationSummaryProps {
    totalSearched: number;
    enrichedCount: number;
    enrichmentRate: number;
    shortlistCount: number;
    avgScore: number;
    processingTimeSeconds: number;
    costSavings?: string;
    costSavingsDetail?: string;
}

const CurationSummary: React.FC<CurationSummaryProps> = ({
    totalSearched,
    enrichedCount,
    enrichmentRate,
    shortlistCount,
    avgScore,
    processingTimeSeconds,
    costSavings = '100%',
    costSavingsDetail = 'enriched only top 0%',
}) => {
    // Format processing time (e.g., "~2 min")
    const formatTime = (seconds: number) => {
        if (seconds < 60) return `~${seconds.toFixed(0)}s processing`;
        const mins = Math.floor(seconds / 60);
        return `~${mins} min processing`;
    };

    return (
        <div className="bg-white rounded-3xl border border-gray-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-10 mb-10 overflow-hidden relative">
            {/* Subtle background decoration */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-slate-50 rounded-full blur-3xl -mr-32 -mt-32 opacity-50 pointer-events-none" />

            <div className="flex items-center justify-between mb-12 relative z-10">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-slate-900">Curation Summary</h2>
                    <p className="text-slate-500 text-sm mt-1 uppercase tracking-wider font-semibold">AI Research Performance</p>
                </div>
                <div className="flex items-center gap-2 px-4 py-2 bg-slate-50 rounded-full border border-slate-100 shadow-sm">
                    <div className="w-1.5 h-1.5 bg-sky-500 rounded-full animate-pulse" />
                    <span className="text-slate-600 text-[11px] font-bold uppercase tracking-widest">
                        {formatTime(processingTimeSeconds)}
                    </span>
                </div>
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 relative z-10">
                <StatGroup
                    value={totalSearched.toLocaleString()}
                    label="Searched"
                    icon={<SearchIcon />}
                />
                <StatGroup
                    value={enrichedCount.toString()}
                    label="Enriched"
                    sublabel={`(${enrichmentRate.toFixed(0)}%)`}
                    highlight
                    icon={<EnrichIcon />}
                />
                <StatGroup
                    value={shortlistCount.toString()}
                    label="Shortlist"
                    icon={<ShortlistIcon />}
                />
                <StatGroup
                    value={`${avgScore.toFixed(0)}/100`}
                    label="Avg Score"
                    icon={<ScoreIcon />}
                />
            </div>
        </div>
    );
};

// Internal sub-components for a cleaner layout
function StatGroup({ value, label, sublabel, highlight, icon }: any) {
    return (
        <div className="group relative">
            <div className="flex items-center gap-3 mb-3">
                <div className={`p-2 rounded-xl transition-colors ${highlight ? 'bg-sky-50 text-sky-600' : 'bg-slate-50 text-slate-400 group-hover:bg-slate-100 group-hover:text-slate-600'}`}>
                    {icon}
                </div>
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest group-hover:text-slate-500 transition-colors">
                    {label}
                </span>
            </div>
            <div className="flex items-baseline gap-2">
                <div className={`text-4xl font-extrabold tracking-tight transition-transform group-hover:scale-[1.02] duration-300 ${highlight ? 'text-sky-600' : 'text-slate-900'}`}>
                    {value}
                </div>
                {sublabel && (
                    <span className="text-sm font-bold text-sky-500 bg-sky-50/50 px-2 py-0.5 rounded-md">
                        {sublabel}
                    </span>
                )}
            </div>
        </div>
    );
}

function SearchIcon() {
    return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
    );
}

function EnrichIcon() {
    return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
    );
}

function ShortlistIcon() {
    return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
    );
}

function ScoreIcon() {
    return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
        </svg>
    );
}

export default CurationSummary;
