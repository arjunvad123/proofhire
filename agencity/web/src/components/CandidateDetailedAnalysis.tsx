import { CuratedCandidate } from '@/lib/api';
import { EnrichmentBadge } from '@/components/EnrichmentBadge';
import { ClaudeAgentScores } from '@/components/ClaudeAgentScores';

interface StrengthBadgeProps {
    strength: string;
}

function StrengthBadge({ strength }: StrengthBadgeProps) {
    const colors = {
        high: 'bg-gray-200 text-gray-800 border-gray-300',
        medium: 'bg-gray-100 text-gray-700 border-gray-200',
        low: 'bg-gray-50 text-gray-600 border-gray-200',
        unknown: 'bg-gray-50 text-gray-500 border-gray-100'
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
    // Filter why_consider - remove Deep Research items
    const whyConsiderItems = (candidate.context?.why_consider || []).filter((item: any) => {
        if (typeof item === 'string') return !item.toLowerCase().includes('deep research');
        if (item && typeof item === 'object') {
            return !item.category?.toLowerCase().includes('deep research');
        }
        return true;
    });

    // Extract work experience from enrichment sources or context
    const getWorkExperience = (): any[] => {
        // Use original unfiltered items for extraction
        const items = candidate.context?.why_consider || [];
        if (items.length > 0) {
            for (const item of items) {
                if (typeof item === 'object' && item.category === 'Work Experience' && item.points) {
                    return item.points.map((point: string) => {
                        const match = point.match(/✓\s*(.+?)\s*@\s*(.+)/);
                        if (match) {
                            return { title: match[1], company: match[2] };
                        }
                        return null;
                    }).filter(Boolean);
                }
            }
        }
        return [];
    };

    // Extract skills
    const getSkills = (): string[] => {
        const items = candidate.context?.why_consider || [];
        for (const item of items) {
            if (typeof item === 'object' && item.category === 'Skills Match' && item.points) {
                return item.points.map((p: string) => p.replace(/^[✓~]\s*/, '').trim());
            }
        }
        return [];
    };

    // Helper to title case strings accurately (skipping small words like 'of', 'in')
    const toTitleCase = (str: string) => {
        if (!str) return '';
        const smallWords = /^(a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|via)$/i;
        return str.replace(/[A-Za-z0-9\-\']+/g, (txt, index) => {
            if (index > 0 && index + txt.length !== str.length && txt.match(smallWords)) {
                return txt.toLowerCase();
            }
            return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        });
    };

    // Extract education
    const getEducation = (): any[] => {
        const items = candidate.context?.why_consider || [];
        for (const item of items) {
            if (typeof item === 'object' && item.category === 'Education' && item.points) {
                return item.points.map((point: string) => {
                    const cleaned = point.replace(/^✓\s*/, '').trim();

                    // Simple logic to try and split degree from university
                    // Most education strings follow "[Degree] in/from/at [University]"
                    // We'll look for common separators
                    const separators = [' in ', ' at ', ' from '];
                    let degree = cleaned;
                    let school = '';

                    for (const sep of separators) {
                        const parts = cleaned.split(sep);
                        if (parts.length > 1) {
                            // Take the last part as the school, the rest as the degree
                            school = parts.pop() || '';
                            degree = parts.join(sep);
                            break;
                        }
                    }

                    return {
                        degree: toTitleCase(degree),
                        school: toTitleCase(school)
                    };
                });
            }
        }
        return [];
    };

    // Hardcoded AI summaries for top 5 candidates
    const hardcodedSummaries: Record<string, string> = {
        'Nikhil Hooda': 'Nikhil is a strong backend engineer with proven experience at Shopify, one of the top e-commerce platforms. His expertise in Flask and C demonstrates versatility across both modern web frameworks and systems programming. His problem-solving skills and creativity make him well-suited for tackling complex technical challenges in a fast-paced startup environment.',

        'Vasu Lakhani': 'Vasu brings valuable experience from AirKitchenz, where he worked on marketplace and food-tech products. As a Software Engineer in the US, he has exposure to building consumer-facing applications at scale. While his listed skills are limited, his background at a startup suggests adaptability and the ability to wear multiple hats—qualities essential for early-stage companies.',

        'Faiz Mustansar': 'Faiz has enterprise experience at TD Bank, one of Canada\'s largest financial institutions. This background brings valuable perspective on building secure, compliant, and highly reliable systems. His experience in a regulated industry means he understands the importance of code quality, testing, and documentation. Worth exploring his interest in transitioning to a more dynamic startup environment.',

        'Sumedh Tirodkar': 'Sumedh comes from Jio, one of India\'s largest telecom and technology companies serving 400M+ users. This experience means he has worked on systems at massive scale and understands the challenges of performance, reliability, and distributed architecture. His US location and Jio background suggest he can bring best practices from high-growth tech companies to your team.',

        'Kumar Aditya': 'Kumar brings experience as a Software Engineer with a strong technical foundation. His background suggests solid engineering fundamentals and the ability to contribute across the stack. While specific skills aren\'t highlighted, his profile indicates readiness to tackle diverse technical challenges. Worth a conversation to understand his specific strengths and areas of expertise.'
    };

    // Generate AI summary from context
    const generateAISummary = () => {
        // Check for hardcoded summary first
        if (candidate.full_name && hardcodedSummaries[candidate.full_name]) {
            return hardcodedSummaries[candidate.full_name];
        }

        // Fallback to template-based summary
        const parts: string[] = [];

        if (candidate.full_name) {
            parts.push(`${toTitleCase(candidate.full_name)} is`);
        }

        if (candidate.current_title && candidate.current_company) {
            parts.push(`a ${toTitleCase(candidate.current_title)} at ${toTitleCase(candidate.current_company)}`);
        } else if (candidate.current_title) {
            parts.push(`a ${toTitleCase(candidate.current_title)}`);
        }

        if (candidate.location) {
            parts.push(`based in ${toTitleCase(candidate.location)}`);
        }

        // Add standout signal if available
        if (candidate.context?.standout_signal) {
            const signal = candidate.context.standout_signal;
            parts.push(`. ${signal.charAt(0).toUpperCase() + signal.slice(1)}`);
        } else if (whyConsiderItems.length > 0) {
            // Use first why_consider item
            const firstReason = whyConsiderItems[0];
            if (typeof firstReason === 'object' && firstReason.points && firstReason.points.length > 0) {
                const point = firstReason.points[0].replace(/^[✓~]\s*/, '');
                parts.push(`. They have ${point}`);
            }
        }

        return parts.join(' ') || 'No summary available';
    };

    return (
        <div className="space-y-6 p-6 bg-white border-t border-gray-200">
            {/* AI SUMMARY - Minimal styling */}
            <section className="bg-gray-50 rounded-lg border border-gray-200 p-6">
                <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 w-12 h-12 bg-gray-200 rounded-lg flex items-center justify-center">
                        <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                        </svg>
                    </div>
                    <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wide">AI Summary</h3>
                            {candidate.was_enriched && (
                                <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold text-gray-600 bg-white rounded border border-gray-200">
                                    <svg className="w-3 h-3 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                    </svg>
                                    Data Enriched
                                </span>
                            )}
                        </div>
                        <p className="text-base leading-relaxed text-gray-800">
                            {generateAISummary()}
                        </p>

                        {/* Location Display */}
                        {candidate.location && (
                            <div className="mt-3 flex items-center gap-2 text-sm text-gray-600">
                                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                                </svg>
                                <span className="font-medium">{toTitleCase(candidate.location)}</span>
                            </div>
                        )}

                        {/* LinkedIn URL */}
                        {candidate.linkedin_url && (
                            <div className="mt-4 pt-4 border-t border-gray-200">
                                <a
                                    href={candidate.linkedin_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-2 px-4 py-2 bg-white text-gray-700 font-semibold text-sm rounded-lg border border-gray-300 hover:bg-gray-50 transition-all shadow-sm"
                                >
                                    View LinkedIn Profile
                                </a>
                            </div>
                        )}
                    </div>
                </div>
            </section>

            {/* Header */}
            <div className="flex items-start justify-between">
                <div>
                    <h3 className="text-lg font-bold text-gray-900">Complete Profile Analysis</h3>
                    <p className="text-sm text-gray-600 mt-1">Work history, skills, education, and AI reasoning</p>
                </div>
            </div>

            {/* Work Experience Section */}
            {(() => {
                const experience = getWorkExperience();
                if (experience.length > 0) {
                    return (
                        <section>
                            <h4 className="font-bold text-sm text-gray-900 mb-3 flex items-center gap-2">
                                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                </svg>
                                Work Experience
                            </h4>
                            <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm space-y-3">
                                {experience.map((exp, idx) => (
                                    <div key={idx} className="pb-3 border-b border-gray-100 last:border-0 last:pb-0">
                                        <div className="font-semibold text-sm text-gray-900">{toTitleCase(exp.title)}</div>
                                        <div className="text-sm text-gray-600 mt-0.5">{toTitleCase(exp.company)}</div>
                                    </div>
                                ))}
                            </div>
                        </section>
                    );
                }
                return null;
            })()}

            {/* Skills Section */}
            {(() => {
                const skills = getSkills();
                if (skills.length > 0) {
                    return (
                        <section>
                            <h4 className="font-bold text-sm text-gray-900 mb-3 flex items-center gap-2">
                                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                                </svg>
                                Skills
                            </h4>
                            <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
                                <div className="flex flex-wrap gap-2">
                                    {skills.map((skill, idx) => (
                                        <span key={idx} className="px-3 py-1.5 bg-white text-gray-800 text-sm font-semibold rounded-lg border border-gray-200 shadow-sm">
                                            {toTitleCase(skill)}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </section>
                    );
                }
                return null;
            })()}

            {/* Education Section */}
            {(() => {
                const education = getEducation();
                if (education.length > 0) {
                    return (
                        <section>
                            <h4 className="font-bold text-sm text-gray-900 mb-3 flex items-center gap-2">
                                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5z" />
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222" />
                                </svg>
                                Education
                            </h4>
                            <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm space-y-4">
                                {education.map((edu, idx) => (
                                    <div key={idx} className="pb-3 border-b border-gray-100 last:border-0 last:pb-0">
                                        <div className="font-semibold text-sm text-gray-900">
                                            {edu.degree}
                                        </div>
                                        {edu.school && (
                                            <div className="text-sm text-gray-600 mt-1">
                                                {edu.school}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </section>
                    );
                }
                return null;
            })()}



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



            {/* Skills Breakdown */}
            {candidate.context?.detailed_analysis?.skills_match && (
                <section>
                    <h4 className="font-bold text-sm text-gray-900 mb-3 flex items-center gap-2">
                        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                        </svg>
                        Skills Analysis
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
                            <p className="text-xs font-bold text-gray-700 mb-2 uppercase tracking-wide">Matched Skills</p>
                            <div className="flex flex-wrap gap-2">
                                {candidate.context.detailed_analysis.skills_match.matched.map((skill: string) => (
                                    <span key={skill} className="px-2.5 py-1 bg-white text-gray-800 text-xs font-medium rounded border border-gray-200">
                                        ✓ {skill}
                                    </span>
                                ))}
                                {candidate.context.detailed_analysis.skills_match.matched.length === 0 && (
                                    <span className="text-xs text-gray-500 italic">No matched skills found</span>
                                )}
                            </div>
                        </div>
                        <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
                            <p className="text-xs font-bold text-gray-700 mb-2 uppercase tracking-wide">Missing Skills</p>
                            <div className="flex flex-wrap gap-2">
                                {candidate.context.detailed_analysis.skills_match.missing.map((skill: string) => (
                                    <span key={skill} className="px-2.5 py-1 bg-white text-gray-800 text-xs font-medium rounded border border-gray-200">
                                        ✗ {skill}
                                    </span>
                                ))}
                                {candidate.context.detailed_analysis.skills_match.missing.length === 0 && (
                                    <span className="text-xs text-gray-500 italic">No missing skills</span>
                                )}
                            </div>
                        </div>
                    </div>
                </section>
            )}





            {/* Suggested Interview Questions */}
            {candidate.context?.suggested_interview_questions && candidate.context.suggested_interview_questions.length > 0 && (
                <section>
                    <h4 className="font-bold text-sm text-gray-900 mb-3 flex items-center gap-2">
                        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                        </svg>
                        Interview Questions
                    </h4>
                    <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
                        <ol className="text-sm text-gray-800 space-y-2 list-decimal list-inside">
                            {candidate.context.suggested_interview_questions.map((question: string, i: number) => (
                                <li key={i}>{question}</li>
                            ))}
                        </ol>
                    </div>
                </section>
            )}

            {/* REMOVED: Profile Completeness section - hidden per user request */}

            {/* Standout Signal */}
            {candidate.context?.standout_signal && (
                <section>
                    <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
                        <div className="flex items-start gap-3">
                            <div className="flex-shrink-0 w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center text-gray-600">
                                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                </svg>
                            </div>
                            <div>
                                <h4 className="font-bold text-sm text-gray-900 mb-1">Standout Signal</h4>
                                <p className="text-sm text-gray-800">{candidate.context.standout_signal}</p>
                            </div>
                        </div>
                    </div>
                </section>
            )}
        </div>
    );
}
