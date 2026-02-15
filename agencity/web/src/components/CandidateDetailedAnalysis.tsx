import { CuratedCandidate } from '@/lib/api';
import { EnrichmentBadge } from '@/components/EnrichmentBadge';
import { ClaudeAgentScores } from '@/components/ClaudeAgentScores';
import { PerplexityResearchCard } from '@/components/PerplexityResearchCard';

interface StrengthBadgeProps {
    strength: string;
}

function StrengthBadge({ strength }: StrengthBadgeProps) {
    const colors = {
        high: 'bg-green-100 text-green-800 border-green-200',
        medium: 'bg-amber-100 text-amber-800 border-amber-200',
        low: 'bg-orange-100 text-orange-800 border-orange-200',
        unknown: 'bg-gray-100 text-gray-800 border-gray-200'
    };

    const color = colors[strength.toLowerCase() as keyof typeof colors] || colors.unknown;

    return (
        <span className={`px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide rounded border ${color}`}>
            {strength}
        </span>
    );
}

interface CandidateDetailedAnalysisProps {
    candidate: CuratedCandidate;
}

export function CandidateDetailedAnalysis({ candidate }: CandidateDetailedAnalysisProps) {
    // Parse why_consider - can be array of strings or structured objects
    const whyConsiderItems = candidate.context?.why_consider || [];

    return (
        <div className="space-y-6 p-6 bg-gradient-to-br from-gray-50 to-white border-t border-gray-200">
            {/* Header */}
            <div className="flex items-start justify-between">
                <div>
                    <h3 className="text-lg font-bold text-gray-900">Full Analysis</h3>
                    <p className="text-sm text-gray-600 mt-1">Complete LLM reasoning and data breakdown</p>
                </div>
                <div className="flex items-center gap-2">
                    {candidate.was_enriched && (
                        <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-semibold text-blue-700 bg-blue-50 rounded border border-blue-200">
                            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            Enriched
                        </span>
                    )}
                </div>
            </div>

            {/* NEW SECTION: Enrichment Sources */}
            {candidate.context?.enrichment_details && (
                <section>
                    <h4 className="font-bold text-sm text-gray-900 mb-3 flex items-center gap-2">
                        <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                        </svg>
                        Data Sources
                    </h4>
                    <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
                        <EnrichmentBadge
                            sources={candidate.context.enrichment_details.sources}
                            dataQualityScore={candidate.context.enrichment_details.data_quality_score}
                        />
                        {candidate.context.enrichment_details.pdl_fields.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-gray-200">
                                <p className="text-xs text-gray-600 mb-2">
                                    <span className="font-semibold">PDL Enriched Fields:</span>
                                </p>
                                <div className="flex flex-wrap gap-1">
                                    {candidate.context.enrichment_details.pdl_fields.map((field) => (
                                        <span key={field} className="px-2 py-0.5 text-xs bg-blue-50 text-blue-700 rounded border border-blue-200">
                                            {field}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
                        <div className="mt-3 pt-3 border-t border-gray-200">
                            <p className="text-xs text-gray-500 italic">
                                Last enriched: {candidate.was_enriched ? 'Recently' : 'Not enriched'}
                            </p>
                        </div>
                    </div>
                </section>
            )}

            {/* NEW SECTION: Claude AI Analysis */}
            {candidate.context?.claude_reasoning && (
                <section>
                    <ClaudeAgentScores
                        agentScores={candidate.context.claude_reasoning.agent_scores}
                        overallScore={candidate.context.claude_reasoning.overall_score}
                        confidence={candidate.context.claude_reasoning.confidence}
                        weightedCalculation={candidate.context.claude_reasoning.weighted_calculation}
                    />
                </section>
            )}

            {/* Why Consider - Grouped by Category */}
            {whyConsiderItems.length > 0 && (
                <section>
                    <h4 className="font-bold text-sm text-gray-900 mb-3 flex items-center gap-2">
                        <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Why Consider This Candidate
                    </h4>
                    <div className="space-y-4">
                        {whyConsiderItems.map((item, idx) => {
                            // Handle both string and structured formats
                            let category = 'General';
                            let points: string[] = [];
                            let strength = 'medium';

                            if (typeof item === 'string') {
                                points = [item];
                            } else if (item && typeof item === 'object') {
                                category = item.category || 'General';
                                points = item.points || [];
                                strength = item.strength || 'medium';
                            }

                            if (points.length === 0) return null;

                            return (
                                <div key={idx} className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
                                    <div className="flex items-center gap-2 mb-2">
                                        <span className="font-semibold text-sm text-gray-900">{category}</span>
                                        <StrengthBadge strength={strength} />
                                    </div>
                                    <ul className="text-sm text-gray-700 space-y-1.5 ml-1">
                                        {points.map((point, i) => (
                                            <li key={i} className="flex items-start gap-2">
                                                <span className="text-blue-600 mt-0.5">•</span>
                                                <span>{point}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            );
                        })}
                    </div>
                </section>
            )}

            {/* Skills Breakdown */}
            {candidate.context?.detailed_analysis?.skills_match && (
                <section>
                    <h4 className="font-bold text-sm text-gray-900 mb-3 flex items-center gap-2">
                        <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                        </svg>
                        Skills Analysis
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-green-50 rounded-lg border border-green-200 p-4">
                            <p className="text-xs font-bold text-green-700 mb-2 uppercase tracking-wide">Matched Skills</p>
                            <div className="flex flex-wrap gap-2">
                                {candidate.context.detailed_analysis.skills_match.matched.map((skill: string) => (
                                    <span key={skill} className="px-2.5 py-1 bg-white text-green-800 text-xs font-medium rounded border border-green-300 shadow-sm">
                                        ✓ {skill}
                                    </span>
                                ))}
                                {candidate.context.detailed_analysis.skills_match.matched.length === 0 && (
                                    <span className="text-xs text-green-600 italic">No matched skills found</span>
                                )}
                            </div>
                        </div>
                        <div className="bg-red-50 rounded-lg border border-red-200 p-4">
                            <p className="text-xs font-bold text-red-700 mb-2 uppercase tracking-wide">Missing Skills</p>
                            <div className="flex flex-wrap gap-2">
                                {candidate.context.detailed_analysis.skills_match.missing.map((skill: string) => (
                                    <span key={skill} className="px-2.5 py-1 bg-white text-red-800 text-xs font-medium rounded border border-red-300 shadow-sm">
                                        ✗ {skill}
                                    </span>
                                ))}
                                {candidate.context.detailed_analysis.skills_match.missing.length === 0 && (
                                    <span className="text-xs text-red-600 italic">No missing skills</span>
                                )}
                            </div>
                        </div>
                    </div>
                </section>
            )}

            {/* NEW SECTION: Research Insights */}
            {candidate.context?.enrichment_details?.research_highlights &&
             candidate.context.enrichment_details.research_highlights.length > 0 && (
                <section>
                    <PerplexityResearchCard
                        highlights={candidate.context.enrichment_details.research_highlights}
                    />
                </section>
            )}

            {/* Unknowns */}
            {candidate.context?.unknowns && candidate.context.unknowns.length > 0 && (
                <section>
                    <h4 className="font-bold text-sm text-gray-900 mb-3 flex items-center gap-2">
                        <svg className="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Open Questions
                    </h4>
                    <div className="bg-amber-50 rounded-lg border border-amber-200 p-4">
                        <ul className="text-sm text-amber-900 space-y-2">
                            {candidate.context.unknowns.map((unknown, i) => (
                                <li key={i} className="flex items-start gap-2">
                                    <span className="text-amber-600 mt-0.5">?</span>
                                    <span>{unknown}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                </section>
            )}

            {/* Suggested Interview Questions */}
            {candidate.context?.suggested_interview_questions && candidate.context.suggested_interview_questions.length > 0 && (
                <section>
                    <h4 className="font-bold text-sm text-gray-900 mb-3 flex items-center gap-2">
                        <svg className="w-4 h-4 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                        </svg>
                        Suggested Interview Questions
                    </h4>
                    <div className="bg-indigo-50 rounded-lg border border-indigo-200 p-4">
                        <ol className="text-sm text-indigo-900 space-y-2 list-decimal list-inside">
                            {candidate.context.suggested_interview_questions.map((question, i) => (
                                <li key={i}>{question}</li>
                            ))}
                        </ol>
                    </div>
                </section>
            )}

            {/* Data Completeness */}
            <section>
                <h4 className="font-bold text-sm text-gray-900 mb-3 flex items-center gap-2">
                    <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    Profile Completeness
                </h4>
                <div className="bg-white rounded-lg border border-gray-200 p-4">
                    <div className="flex items-center gap-3">
                        <div className="flex-1">
                            <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                    className={`h-full transition-all duration-500 ${
                                        candidate.data_completeness >= 0.7 ? 'bg-green-500' :
                                        candidate.data_completeness >= 0.4 ? 'bg-amber-500' : 'bg-red-500'
                                    }`}
                                    style={{ width: `${candidate.data_completeness * 100}%` }}
                                />
                            </div>
                        </div>
                        <span className="text-sm font-bold text-gray-900 w-12 text-right">
                            {Math.round(candidate.data_completeness * 100)}%
                        </span>
                    </div>
                    <div className="mt-3 flex items-center gap-2 text-xs">
                        {candidate.was_enriched ? (
                            <span className="text-green-700 font-medium">
                                ✓ Profile enriched with external data sources
                            </span>
                        ) : (
                            <span className="text-amber-700 font-medium">
                                ⚠ Limited data available - enrichment not performed
                            </span>
                        )}
                    </div>
                    <div className="mt-2 text-xs text-gray-600">
                        <p>Data completeness measures how much information we have across 10 key fields: email, LinkedIn, headline, location, company, title, skills, experience, education, and projects.</p>
                    </div>
                </div>
            </section>

            {/* Standout Signal */}
            {candidate.context?.standout_signal && (
                <section>
                    <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border-2 border-purple-300 p-4">
                        <div className="flex items-start gap-3">
                            <div className="flex-shrink-0 w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center text-white">
                                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                </svg>
                            </div>
                            <div>
                                <h4 className="font-bold text-sm text-purple-900 mb-1">Standout Signal</h4>
                                <p className="text-sm text-purple-800">{candidate.context.standout_signal}</p>
                            </div>
                        </div>
                    </div>
                </section>
            )}
        </div>
    );
}
