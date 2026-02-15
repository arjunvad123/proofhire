'use client';

import React, { useEffect, useState } from 'react';
import { Person, getPeople, Role, getRoles, CuratedCandidate, curateCandidates, updateCandidateStatus, recordFeedback } from '@/lib/api';
import { CurationStatsCard } from '@/components/CurationStatsCard';
import { CandidateDetailedAnalysis } from '@/components/CandidateDetailedAnalysis';

export default function CandidatesPage() {
    // List Mode State
    const [candidates, setCandidates] = useState<Person[]>([]);

    // Match Mode State
    const [curatedCandidates, setCuratedCandidates] = useState<CuratedCandidate[]>([]);
    const [roles, setRoles] = useState<Role[]>([]);
    const [selectedRoleId, setSelectedRoleId] = useState<string>('');
    const [curationMetadata, setCurationMetadata] = useState<{
        totalSearched: number;
        enrichedCount: number;
        avgScore: number;
    } | null>(null);
    const [expandedCandidates, setExpandedCandidates] = useState<Set<string>>(new Set());

    // Shared State
    const [mounted, setMounted] = useState(false);
    const [loading, setLoading] = useState(true);
    const [filterStatus, setFilterStatus] = useState<string>('all');
    const [filterSource, setFilterSource] = useState<string>('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [companyId, setCompanyId] = useState<string>('');
    const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);

    // Define functions BEFORE useEffect
    async function loadData(cId: string) {
        console.log('📊 loadData called with company ID:', cId);
        setLoading(true);
        try {
            console.log('🔄 Fetching people and roles...');
            console.log('API endpoints:');
            console.log(`  - GET /companies/${cId}/people?limit=100&offset=0`);
            console.log(`  - GET /companies/${cId}/roles`);

            const startTime = Date.now();
            const [peopleRes, rolesRes] = await Promise.all([
                getPeople(cId, 100),
                getRoles(cId)
            ]);
            const elapsed = Date.now() - startTime;

            console.log(`✓ API calls completed in ${elapsed}ms`);
            console.log('✓ People response:', peopleRes);
            console.log('✓ People loaded:', peopleRes.people?.length || 0);
            console.log('✓ Roles loaded:', rolesRes?.length || 0);
            if (rolesRes && rolesRes.length > 0) {
                console.log('📋 Available roles:', rolesRes.map(r => r.title));
            }
            setCandidates(peopleRes.people || []);
            setRoles(rolesRes || []);
        } catch (error) {
            console.error('❌ Failed to load initial data:', error);
            console.error('Error details:', error instanceof Error ? error.message : error);
            showToast('Failed to load data. Check if backend is running on port 8001.', 'error');
        } finally {
            console.log('✓ Setting loading to false');
            setLoading(false);
        }
    }

    async function loadCuratedCandidates(roleId: string) {
        setLoading(true);
        try {
            console.log('Loading curated candidates for role:', roleId);
            const result = await curateCandidates(companyId, roleId, { limit: 30 });
            console.log('Curation result:', result);
            console.log('Candidates count:', result.candidates?.length || 0);
            console.log('Processing time:', result.processing_time_seconds, 'seconds');

            // Check if loaded from cache (should be < 1 second)
            const fromCache = result.processing_time_seconds < 1;
            if (fromCache) {
                console.log('✓ Loaded from cache (instant)');
            } else {
                console.log('⚠ Generated live (slow) - consider running cache generation script');
            }

            if (!result.candidates || result.candidates.length === 0) {
                console.warn('No candidates returned from curation');
                if (result.total_searched === 0) {
                    showToast('No candidates in your network yet. Import LinkedIn connections or add candidates first.', 'info');
                } else {
                    showToast(`Searched ${result.total_searched} candidates but none matched this role. Try adjusting role requirements.`, 'info');
                }
            } else if (!fromCache) {
                // Notify that cache should be generated for faster loads
                console.warn('💡 Tip: Run cache generation script for instant loading next time');
            }

            setCuratedCandidates(result.candidates || []);

            setCurationMetadata({
                totalSearched: result.total_searched || 0,
                enrichedCount: result.total_enriched || 0,
                avgScore: Math.round(result.average_fit_score || 0)
            });
        } catch (error) {
            console.error('Failed to curate candidates:', error);
            showToast(`Failed to generate shortlist: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
        } finally {
            setLoading(false);
        }
    }

    const showToast = (message: string, type: 'success' | 'error' | 'info') => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 3000);
    };

    const handleApprove = async (candidate: CuratedCandidate) => {
        try {
            await updateCandidateStatus(candidate.person_id, { status: 'sourced' });
            await recordFeedback({
                company_id: companyId,
                candidate_id: candidate.person_id,
                action: 'saved',
                notes: 'Approved from curation shortlist'
            });
            setCuratedCandidates(prev => prev.filter(c => c.person_id !== candidate.person_id));
            showToast(`${candidate.full_name} added to pipeline`, 'success');
        } catch (error) {
            console.error('Failed to approve candidate:', error);
            showToast('Failed to add to pipeline', 'error');
        }
    };

    const handleReject = async (candidate: CuratedCandidate) => {
        try {
            await recordFeedback({
                company_id: companyId,
                candidate_id: candidate.person_id,
                action: 'rejected',
                notes: 'Rejected from curation shortlist'
            });
            setCuratedCandidates(prev => prev.filter(c => c.person_id !== candidate.person_id));
            showToast(`${candidate.full_name} marked as passed`, 'info');
        } catch (error) {
            console.error('Failed to reject candidate:', error);
            showToast('Failed to record rejection', 'error');
        }
    };

    useEffect(() => {
        console.log('🚀 Candidates page mounted');
        setMounted(true);

        // Initialize company ID and load initial data
        const saved = localStorage.getItem('onboarding-state');
        console.log('📦 localStorage onboarding-state:', saved);

        if (saved) {
            const state = JSON.parse(saved);
            console.log('📦 Parsed state:', state);
            if (state.company?.id) {
                console.log('✓ Found company ID:', state.company.id);
                setCompanyId(state.company.id);
                loadData(state.company.id);
            } else {
                console.warn('⚠️ No company.id in onboarding-state');
                setLoading(false);
            }
        } else {
            console.warn('⚠️ No onboarding-state in localStorage - need to set Confido company');
            // For demo: Use Confido company ID directly
            const confidoId = '100b5ac1-1912-4970-a378-04d0169fd597';
            console.log('💡 Using Confido demo company ID:', confidoId);
            setCompanyId(confidoId);
            loadData(confidoId);
        }
    }, []);

    useEffect(() => {
        if (selectedRoleId && companyId) {
            loadCuratedCandidates(selectedRoleId);
        }
    }, [selectedRoleId, companyId]);

    // Prevent hydration mismatch - don't render until mounted
    if (!mounted) {
        return (
            <div className="space-y-4">
                <div className="flex items-center justify-center h-64">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-200 border-t-blue-600"></div>
                </div>
            </div>
        );
    }

    const isMatchMode = !!selectedRoleId;

    // Filter logic depends on mode
    const displayedItems = isMatchMode
        ? curatedCandidates.filter(c => {
            if (searchQuery) {
                const q = searchQuery.toLowerCase();
                return (
                    c.full_name.toLowerCase().includes(q) ||
                    (c.headline || '').toLowerCase().includes(q) ||
                    (c.current_company || '').toLowerCase().includes(q) ||
                    (c.context?.why_consider?.join(' ') || '').toLowerCase().includes(q)
                );
            }
            return true;
        })
        : candidates.filter(c => {
            // Status filter
            if (filterStatus !== 'all' && c.status !== filterStatus) return false;

            // Source filter
            if (filterSource === 'network' && !c.is_from_network) return false;
            if (filterSource === 'import' && !c.is_from_existing_db) return false;
            if (filterSource === 'search' && !c.is_from_people_search) return false;

            // Search query
            if (searchQuery) {
                const q = searchQuery.toLowerCase();
                return (
                    c.full_name.toLowerCase().includes(q) ||
                    (c.current_company || '').toLowerCase().includes(q) ||
                    (c.current_title || '').toLowerCase().includes(q)
                );
            }
            return true;
        });

    const stripMarkdown = (text: string) => {
        return text
            .replace(/#{1,6}\s?/g, '') // Remove headers
            .replace(/\*\*/g, '')      // Remove bold
            .replace(/\*/g, '')        // Remove italic
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '$1') // Remove links
            .trim();
    };

    return (
        <div className="space-y-4">
            {/* Context Header */}
            <div className="flex justify-between items-center bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                <div>
                    <h2 className="text-lg font-medium text-gray-900">
                        {isMatchMode ? 'Matches for Role' : 'Candidate Pool'}
                    </h2>
                    <p className="text-sm text-gray-500">
                        {isMatchMode
                            ? `Showing top matches for ${roles.find(r => r.id === selectedRoleId)?.title}`
                            : 'Browsing all candidates in your database'}
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-700">Select Role:</span>
                    <select
                        className="block w-64 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                        value={selectedRoleId}
                        onChange={(e) => setSelectedRoleId(e.target.value)}
                    >
                        <option value="">-- Browse All Candidates --</option>
                        {roles.map(role => (
                            <option key={role.id} value={role.id}>
                                {role.title} ({role.status})
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Curation Stats Card */}
            {isMatchMode && curationMetadata && curatedCandidates.length > 0 && (
                <CurationStatsCard
                    searched={curationMetadata.totalSearched}
                    enriched={curationMetadata.enrichedCount}
                    shortlisted={curatedCandidates.length}
                    avgScore={curationMetadata.avgScore}
                    processingTime={120}
                    aiAnalyzedCount={curatedCandidates.filter(c => c.context?.claude_reasoning).length}
                />
            )}

            {/* Filters & Actions */}
            <div className="flex flex-wrap items-center gap-3 bg-white p-3 rounded-lg border border-gray-200 shadow-sm">
                <div className="flex-1 min-w-[200px]">
                    <div className="relative rounded-lg shadow-sm">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                        </div>
                        <input
                            type="text"
                            placeholder={isMatchMode ? "Search matches..." : "Search candidates..."}
                            className="focus:ring-blue-500 focus:border-blue-500 block w-full pl-10 sm:text-sm border-gray-300 rounded-md py-2"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>
                </div>

                {!isMatchMode && (
                    <>
                        <select
                            className="px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                            value={filterStatus}
                            onChange={(e) => setFilterStatus(e.target.value)}
                        >
                            <option value="all">All Status</option>
                            <option value="sourced">Sourced</option>
                            <option value="contacted">Contacted</option>
                            <option value="replied">Replied</option>
                            <option value="interviewing">Interviewing</option>
                            <option value="offer">Offer</option>
                            <option value="hired">Hired</option>
                            <option value="rejected">Rejected</option>
                        </select>

                        <select
                            className="px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                            value={filterSource}
                            onChange={(e) => setFilterSource(e.target.value)}
                        >
                            <option value="all">All Sources</option>
                            <option value="network">Network</option>
                            <option value="import">Imported</option>
                            <option value="search">Search</option>
                        </select>
                    </>
                )}

                {isMatchMode && (
                    <div className="text-sm text-gray-500 italic px-2">
                        Sorting by Match Score
                    </div>
                )}

                <button
                    onClick={() => isMatchMode ? loadCuratedCandidates(selectedRoleId) : loadData(companyId)}
                    className="px-3 py-2 text-sm font-medium text-gray-700 bg-gray-50 border border-gray-300 rounded-md hover:bg-gray-100"
                >
                    Refresh
                </button>
            </div>

            {/* List */}
            <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
                {loading ? (
                    <div className="p-12 text-center">
                        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-200 border-t-blue-600 mb-2"></div>
                        <div className="text-gray-500 text-sm">
                            {isMatchMode ? 'Generating shortlist... This may take a moment.' : 'Loading data...'}
                        </div>
                    </div>
                ) : displayedItems.length === 0 ? (
                    <div className="p-12 text-center">
                        <div className="mb-4">
                            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                            </svg>
                        </div>
                        <h3 className="text-sm font-medium text-gray-900 mb-2">
                            {isMatchMode ? 'No matching candidates found' : 'No candidates found'}
                        </h3>
                        <p className="text-sm text-gray-500 mb-6">
                            {isMatchMode
                                ? candidates.length === 0
                                    ? 'You need to import candidates first to see matches for this role.'
                                    : `We searched ${curationMetadata?.totalSearched || 0} candidates but none matched the requirements for this role.`
                                : 'Try adjusting your filters or import candidates to get started.'}
                        </p>
                        {isMatchMode && candidates.length === 0 && (
                            <div className="space-y-2">
                                <p className="text-xs font-medium text-gray-700 mb-3">Get started by:</p>
                                <div className="flex flex-col sm:flex-row gap-2 justify-center">
                                    <button
                                        onClick={() => setSelectedRoleId('')}
                                        className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                                    >
                                        View All Candidates
                                    </button>
                                    <a
                                        href="/dashboard"
                                        className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                                    >
                                        Import Candidates
                                    </a>
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Candidate</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current Role</th>

                                {isMatchMode ? (
                                    <>
                                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Match Score</th>
                                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Analysis</th>
                                    </>
                                ) : (
                                    <>
                                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Source</th>
                                    </>
                                )}

                                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {displayedItems.flatMap((item: any) => {
                                // Unified data access for Person vs CuratedCandidate
                                const id = item.id || item.person_id;
                                const isCurated = isMatchMode;
                                const candidate = item;
                                const isExpanded = expandedCandidates.has(id);

                                const toggleExpand = () => {
                                    setExpandedCandidates(prev => {
                                        const next = new Set(prev);
                                        if (next.has(id)) {
                                            next.delete(id);
                                        } else {
                                            next.add(id);
                                        }
                                        return next;
                                    });
                                };

                                const rows = [
                                    <tr key={`${id}-main`} className="hover:bg-gray-50/80 transition-colors group">
                                        <td className="px-6 py-5 whitespace-nowrap">
                                            <div className="flex items-center">
                                                <div className="flex-shrink-0 h-10 w-10">
                                                    <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-sm font-semibold shadow-sm ring-2 ring-white ring-offset-2">
                                                        {candidate.full_name?.charAt(0)}
                                                    </div>
                                                </div>
                                                <div className="ml-4">
                                                    <div className="flex items-center gap-2">
                                                        <div className="text-sm font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">{candidate.full_name}</div>
                                                        {/* Enrichment indicators */}
                                                        {isCurated && candidate.context?.enrichment_details?.sources && candidate.context.enrichment_details.sources.length > 0 && (
                                                            <div className="flex items-center gap-1">
                                                                {candidate.context.enrichment_details.sources.includes('pdl') && (
                                                                    <span className="px-1.5 py-0.5 text-[9px] font-bold bg-blue-100 text-blue-700 rounded border border-blue-200 uppercase" title="PDL Enriched">
                                                                        PDL
                                                                    </span>
                                                                )}
                                                                {candidate.context.enrichment_details.sources.includes('perplexity') && (
                                                                    <span className="px-1.5 py-0.5 text-[9px] font-bold bg-purple-100 text-purple-700 rounded border border-purple-200 uppercase" title="Perplexity Research">
                                                                        AI
                                                                    </span>
                                                                )}
                                                            </div>
                                                        )}
                                                    </div>
                                                    <div className="text-xs text-gray-500 flex items-center gap-1.5 mt-0.5">
                                                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                                                        </svg>
                                                        {candidate.location || 'Remote'}
                                                    </div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-5 whitespace-nowrap">
                                            <div className="text-sm font-medium text-gray-900">{candidate.current_title || 'Unknown Title'}</div>
                                            <div className="text-xs text-gray-500 mt-0.5">{candidate.current_company || 'Unknown Company'}</div>
                                        </td>

                                        {isCurated ? (
                                            <>
                                                <td className="px-6 py-5 whitespace-nowrap">
                                                    <div className="flex flex-col gap-1.5">
                                                        <div className="flex items-center gap-2">
                                                            <div className="relative w-24 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                                                <div
                                                                    className={`absolute top-0 left-0 h-full rounded-full ${candidate.match_score > 75 ? 'bg-green-500' :
                                                                        candidate.match_score > 50 ? 'bg-amber-500' : 'bg-red-500'
                                                                        }`}
                                                                    style={{ width: `${candidate.match_score}%` }}
                                                                ></div>
                                                            </div>
                                                            <span className="text-sm font-bold text-gray-900">{Math.round(candidate.match_score)}%</span>
                                                        </div>
                                                        {/* Show Claude AI score if available */}
                                                        {candidate.context?.claude_reasoning ? (
                                                            <div className="text-[10px] text-indigo-600 uppercase tracking-tight font-bold flex items-center gap-1">
                                                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                                                                </svg>
                                                                AI: {Math.round(candidate.context.claude_reasoning.overall_score)}% ({Math.round(candidate.context.claude_reasoning.confidence * 100)}% conf)
                                                            </div>
                                                        ) : (
                                                            <div className="text-[10px] text-gray-500 uppercase tracking-tight font-medium">
                                                                Confidence: {Math.round(candidate.fit_confidence * 100)}%
                                                            </div>
                                                        )}
                                                    </div>
                                                </td>
                                                <td className="px-6 py-5">
                                                    <div className="flex flex-col gap-2">
                                                        {candidate.context?.warm_path && (
                                                            <span className="inline-flex items-center gap-1 text-[10px] font-bold text-green-700 bg-green-50 px-2 py-0.5 rounded border border-green-200 uppercase tracking-wide w-fit">
                                                                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                                                                    <path fillRule="evenodd" d="M12.395 2.553a1 1 0 00-1.45-.385c-.345.23-.614.558-.822.88-.214.33-.403.713-.57 1.116-.334.804-.614 1.768-.84 2.734a31.365 31.365 0 00-.613 3.58 2.64 2.64 0 01-.945-1.067c-.328-.68-.398-1.334-.398-1.817a1 1 0 00-1.463-.89c-.334.18-.59.458-.802.756-.212.3-.393.649-.553 1.02-.32.743-.585 1.637-.78 2.533A17.14 17.14 0 006 12a6 6 0 0012 0c0-1.638-.214-3.176-.605-4.553-.194-.684-.447-1.32-.764-1.86a10.151 10.151 0 00-1.026-1.503 9.4 9.4 0 00-.775-.815zM9.383 8.56c.06-.242.13-.487.211-.735.158-.485.342-.924.536-1.327a33.723 33.723 0 01.373-.75c.08.158.136.326.172.503.116.575.148 1.25.101 1.956a1 1 0 00.518.887 2.646 2.646 0 011.054 1.4c.159.49.236 1.045.236 1.606 0 .02-.001.04-.002.059a1 1 0 001.815.54 3.791 3.791 0 00.176-.411 1.64 1.54 0 00.101-.645l-.018-.1c-.02-.1-.043-.198-.07-.294A15.176 15.176 0 0014 12c0 1.105-.895 2-2 2s-2-.895-2-2c0-.528.204-1.01.537-1.37a1 1 0 00.063-1.328 1 1 0 00-.1-.137l-.022-.023c-.345-.375-.58-.85-.637-1.37a1.64 1.64 0 01.024-.54z" clipRule="evenodd" />
                                                                </svg>
                                                                {candidate.context.warm_path}
                                                            </span>
                                                        )}
                                                        {candidate.context?.why_consider?.[0] && (() => {
                                                            const rawReason = candidate.context.why_consider[0];
                                                            const text = typeof rawReason === 'string' ? rawReason : (rawReason.points?.[0] || rawReason.category);
                                                            const cleanText = stripMarkdown(text);
                                                            return (
                                                                <span className="text-[11px] text-gray-600 leading-relaxed max-w-sm line-clamp-2 italic">
                                                                    &quot;{cleanText}&quot;
                                                                </span>
                                                            );
                                                        })()}
                                                        <button
                                                            onClick={toggleExpand}
                                                            className="text-xs text-blue-600 hover:text-blue-800 font-medium text-left w-fit flex items-center gap-1 mt-1"
                                                        >
                                                            {isExpanded ? (
                                                                <>
                                                                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                                                                    </svg>
                                                                    Hide full analysis
                                                                </>
                                                            ) : (
                                                                <>
                                                                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                                                    </svg>
                                                                    Show full analysis
                                                                </>
                                                            )}
                                                        </button>
                                                    </div>
                                                </td>
                                            </>
                                        ) : (
                                            <>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <span className={`px-2.5 py-0.5 inline-flex text-xs leading-4 font-semibold rounded-full capitalize
                                                    ${candidate.status === 'hired' ? 'bg-green-100 text-green-800' :
                                                            candidate.status === 'rejected' ? 'bg-red-100 text-red-800' :
                                                                candidate.status === 'contacted' ? 'bg-blue-100 text-blue-800' :
                                                                    'bg-gray-100 text-gray-800'}`}>
                                                        {candidate.status || 'Sourced'}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-500">
                                                    <div className="flex flex-wrap gap-1">
                                                        {candidate.is_from_network && (
                                                            <span className="px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-100">Network</span>
                                                        )}
                                                        {candidate.is_from_existing_db && (
                                                            <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-100">Import</span>
                                                        )}
                                                        {candidate.is_from_people_search && (
                                                            <span className="px-2 py-0.5 rounded bg-orange-50 text-orange-700 border border-orange-100">Search</span>
                                                        )}
                                                    </div>
                                                </td>
                                            </>
                                        )}

                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                            {isCurated ? (
                                                <div className="flex gap-2 justify-end">
                                                    <button
                                                        onClick={() => handleApprove(candidate)}
                                                        className="px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors font-medium shadow-sm"
                                                    >
                                                        ✓ Yes
                                                    </button>
                                                    <button
                                                        onClick={() => handleReject(candidate)}
                                                        className="px-3 py-1.5 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors font-medium shadow-sm"
                                                    >
                                                        ✗ No
                                                    </button>
                                                </div>
                                            ) : (
                                                <button className="text-blue-600 hover:text-blue-900 border border-blue-200 px-3 py-1 rounded hover:bg-blue-50 transition-colors">
                                                    View Profile
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ];

                                if (isCurated && isExpanded) {
                                    rows.push(
                                        <tr key={`${id}-expanded`} className="bg-gray-50">
                                            <td colSpan={5} className="p-0">
                                                <CandidateDetailedAnalysis candidate={candidate} />
                                            </td>
                                        </tr>
                                    );
                                }

                                return rows;
                            })}
                        </tbody>
                    </table>
                )
                }
            </div>

            {/* Toast Notification */}
            {toast && (
                <div className="fixed bottom-4 right-4 z-50 animate-slide-in">
                    <div className={`px-4 py-3 rounded-lg shadow-lg border ${toast.type === 'success' ? 'bg-green-50 border-green-200 text-green-800' :
                        toast.type === 'error' ? 'bg-red-50 border-red-200 text-red-800' :
                            'bg-blue-50 border-blue-200 text-blue-800'
                        }`}>
                        <div className="flex items-center gap-2">
                            <span className="text-lg">
                                {toast.type === 'success' ? '✓' : toast.type === 'error' ? '✗' : 'ℹ'}
                            </span>
                            <span className="font-medium">{toast.message}</span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
