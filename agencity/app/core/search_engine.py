"""
Search Engine - Combines multiple data sources.

Orchestrates search across our network, GitHub, hackathons, etc.
and returns deduplicated, enriched candidates.
"""

import asyncio
import logging
from datetime import datetime

from app.core.evaluation_engine import EvaluationEngine
from app.models.blueprint import RoleBlueprint
from app.models.candidate import CandidateData
from app.models.evaluation import EvaluatedCandidate, Shortlist
from app.sources.base import DataSource
from app.sources.github import GitHubSource
from app.sources.network import NetworkSource

logger = logging.getLogger(__name__)


class SearchEngine:
    """
    Orchestrates multi-source candidate search.

    Flow:
    1. Search all sources in parallel (by priority)
    2. Dedupe candidates across sources
    3. Enrich candidates with additional data
    4. Evaluate against blueprint
    5. Rank and return shortlist
    """

    def __init__(
        self,
        sources: list[DataSource] | None = None,
        evaluation_engine: EvaluationEngine | None = None,
    ):
        # Default sources
        self.sources = sources or [
            NetworkSource(),
            GitHubSource(),
            # TODO: Add DevpostSource, UniversityClubSource, etc.
        ]

        # Sort by priority
        self.sources.sort(key=lambda s: s.priority)

        self.evaluation = evaluation_engine or EvaluationEngine()

    async def search(
        self,
        blueprint: RoleBlueprint,
        limit: int = 50,
        evaluate: bool = True,
    ) -> Shortlist:
        """
        Search all sources and return evaluated shortlist.

        Args:
            blueprint: What we're looking for
            limit: Max candidates in final shortlist
            evaluate: Whether to run evaluation (set False for quick search)

        Returns:
            Shortlist with evaluated candidates
        """
        start_time = datetime.utcnow()

        # 1. Search all available sources in parallel
        logger.info(f"Searching {len(self.sources)} sources for: {blueprint.role_title}")

        search_tasks = []
        available_sources = []

        for source in self.sources:
            if await source.is_available():
                available_sources.append(source)
                search_tasks.append(source.search(blueprint, limit=limit * 2))

        # Run searches in parallel
        results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # Collect candidates from all sources
        all_candidates = []
        sources_used = []

        for source, result in zip(available_sources, results):
            if isinstance(result, Exception):
                logger.error(f"Search failed for {source.name}: {result}")
                continue

            logger.info(f"{source.name}: found {len(result)} candidates")
            all_candidates.extend(result)
            sources_used.append(source.name)

        # 2. Dedupe by email/github/name
        deduped = self._dedupe_candidates(all_candidates)
        logger.info(f"After dedupe: {len(deduped)} unique candidates")

        # 3. Enrich candidates with additional data
        enriched = await self._enrich_candidates(deduped, available_sources)

        # 4. Evaluate candidates against blueprint
        if evaluate:
            evaluated = await self._evaluate_candidates(enriched, blueprint)
        else:
            # Quick mode - just wrap in EvaluatedCandidate without LLM
            evaluated = [
                EvaluatedCandidate(
                    candidate=c,
                    known_facts=[],
                    observed_signals=[],
                    unknown=["Full evaluation pending"],
                    why_consider="",
                    next_step="",
                    relevance_score=c.initial_relevance_score,
                )
                for c in enriched
            ]

        # 5. Rank by relevance and create shortlist
        evaluated.sort(key=lambda e: e.relevance_score, reverse=True)

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Search completed in {duration:.1f}s, returning {min(len(evaluated), limit)} candidates")

        return Shortlist(
            conversation_id="",  # Will be set by caller
            candidates=evaluated[:limit],
            search_sources=sources_used,
            total_searched=len(all_candidates),
            generated_at=datetime.utcnow().isoformat(),
        )

    def _dedupe_candidates(self, candidates: list[CandidateData]) -> list[CandidateData]:
        """
        Deduplicate candidates across sources.

        Priority: email > github > name
        When merging, combine data from all sources.
        """
        seen_emails = {}
        seen_github = {}
        seen_names = {}
        unique = []

        for candidate in candidates:
            # Check email first
            if candidate.email and candidate.email in seen_emails:
                # Merge with existing
                existing = seen_emails[candidate.email]
                self._merge_candidate_data(existing, candidate)
                continue

            # Check GitHub username
            if candidate.github_username and candidate.github_username in seen_github:
                existing = seen_github[candidate.github_username]
                self._merge_candidate_data(existing, candidate)
                continue

            # Check name (fuzzy - exact match only for now)
            if candidate.name in seen_names:
                existing = seen_names[candidate.name]
                self._merge_candidate_data(existing, candidate)
                continue

            # New candidate
            unique.append(candidate)
            if candidate.email:
                seen_emails[candidate.email] = candidate
            if candidate.github_username:
                seen_github[candidate.github_username] = candidate
            seen_names[candidate.name] = candidate

        return unique

    def _merge_candidate_data(
        self,
        existing: CandidateData,
        new: CandidateData,
    ) -> None:
        """Merge data from new into existing candidate."""
        # Add source
        for source in new.sources:
            if source not in existing.sources:
                existing.sources.append(source)

        # Fill in missing fields
        if not existing.email and new.email:
            existing.email = new.email
        if not existing.github_username and new.github_username:
            existing.github_username = new.github_username
        if not existing.school and new.school:
            existing.school = new.school
        if not existing.major and new.major:
            existing.major = new.major

        # Extend lists
        existing.clubs.extend([c for c in new.clubs if c not in existing.clubs])
        existing.hackathons.extend(new.hackathons)
        existing.skills.extend([s for s in new.skills if s not in existing.skills])

    async def _enrich_candidates(
        self,
        candidates: list[CandidateData],
        sources: list[DataSource],
    ) -> list[CandidateData]:
        """
        Enrich candidates with additional data from sources.

        Only enrich candidates that have relevant identifiers.
        """
        enriched = []

        for candidate in candidates:
            for source in sources:
                try:
                    candidate = await source.enrich(candidate)
                except Exception as e:
                    logger.warning(f"Enrichment failed for {candidate.name} from {source.name}: {e}")

            enriched.append(candidate)

        return enriched

    async def _evaluate_candidates(
        self,
        candidates: list[CandidateData],
        blueprint: RoleBlueprint,
    ) -> list[EvaluatedCandidate]:
        """
        Evaluate all candidates against the blueprint.

        This is the expensive part (LLM calls) - could be parallelized.
        """
        evaluated = []

        # Evaluate in parallel (with concurrency limit)
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent evaluations

        async def eval_with_limit(candidate: CandidateData) -> EvaluatedCandidate:
            async with semaphore:
                return await self.evaluation.evaluate(candidate, blueprint)

        tasks = [eval_with_limit(c) for c in candidates]
        evaluated = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out failures
        return [e for e in evaluated if isinstance(e, EvaluatedCandidate)]
