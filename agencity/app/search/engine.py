"""
Search Engine - The main orchestrator for network-driven people search.

This is the entry point that:
1. Analyzes the network for high-value pathways
2. Generates targeted queries for each API
3. Executes searches in parallel
4. Deduplicates and ranks results
5. Cross-references with existing network
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.config import settings
from app.search.analyzers.network import NetworkAnalyzer
from app.search.generators.query import QueryGenerator
from app.search.models import (
    DiscoveredCandidate,
    SearchPathway,
    SearchResults,
    SearchTarget,
)
from app.search.scoring.pathway import PathwayScorer
from app.search.scoring.ranker import CandidateRanker
from app.search.sources.base import SearchSource
from app.search.sources.github import GitHubSource
from app.search.sources.google import GoogleSearchSource
from app.search.sources.pdl import PDLSource
from app.search.sources.perplexity import PerplexitySource

logger = logging.getLogger(__name__)


class SearchEngine:
    """
    Main search engine that orchestrates network-driven people search.

    Usage:
        engine = SearchEngine(company_id)

        target = SearchTarget(
            role_title="Senior ML Engineer",
            required_skills=["Python", "TensorFlow"],
            preferred_backgrounds=["FAANG", "YC"]
        )

        results = await engine.search(target)
        for candidate in results.candidates:
            print(f"{candidate.full_name} - Score: {candidate.final_score}")
    """

    def __init__(self, company_id: UUID):
        self.company_id = company_id

        # Initialize components
        self.network_analyzer = NetworkAnalyzer(company_id)
        self.pathway_scorer = PathwayScorer()
        self.query_generator = QueryGenerator()
        self.ranker = CandidateRanker(company_id)

        # Initialize sources
        self.sources: list[SearchSource] = []
        self._init_sources()

    def _init_sources(self):
        """Initialize search sources from config."""
        # People Data Labs
        pdl_key = getattr(settings, "pdl_api_key", None)
        if pdl_key:
            self.sources.append(PDLSource(api_key=pdl_key))
            logger.info("PDL source configured")

        # Google Custom Search
        google_key = getattr(settings, "google_cse_api_key", None)
        google_cx = getattr(settings, "google_cse_id", None)
        if google_key and google_cx:
            self.sources.append(GoogleSearchSource(
                api_key=google_key,
                search_engine_id=google_cx
            ))
            logger.info("Google CSE source configured")

        # GitHub
        github_token = getattr(settings, "github_token", None)
        if github_token:
            self.sources.append(GitHubSource(api_key=github_token))
            logger.info("GitHub source configured")
        else:
            # GitHub works without auth (lower rate limits)
            self.sources.append(GitHubSource())
            logger.info("GitHub source configured (unauthenticated)")

        # Perplexity
        perplexity_key = getattr(settings, "perplexity_api_key", None)
        if perplexity_key:
            self.sources.append(PerplexitySource(api_key=perplexity_key))
            logger.info("Perplexity source configured")

        logger.info(f"Initialized {len(self.sources)} search sources")

    async def search(
        self,
        target: SearchTarget,
        max_pathways: int = 20,
        max_results_per_source: int = 50
    ) -> SearchResults:
        """
        Execute a network-driven search.

        Args:
            target: What we're searching for
            max_pathways: Maximum pathways to explore
            max_results_per_source: Max results per source per pathway

        Returns:
            SearchResults with ranked candidates
        """
        started_at = datetime.utcnow()
        logger.info(f"Starting search for: {target.role_title}")

        # Step 1: Analyze network
        logger.info("Step 1: Analyzing network...")
        network_nodes = await self.network_analyzer.analyze_network()
        logger.info(f"Found {len(network_nodes)} network nodes")

        # Step 2: Score pathways
        logger.info("Step 2: Scoring pathways...")
        pathways = self.pathway_scorer.score_pathways(
            network_nodes, target, top_k=max_pathways
        )
        logger.info(f"Selected {len(pathways)} top pathways")

        # Step 3: Generate queries for each pathway
        logger.info("Step 3: Generating queries...")
        for pathway in pathways:
            self.query_generator.generate_queries(pathway, target)

        # Log some example pathways
        for i, pathway in enumerate(pathways[:3]):
            logger.info(
                f"  Pathway {i+1}: {pathway.gateway_node.full_name} "
                f"({pathway.gateway_node.node_type.value}) - "
                f"EV: {pathway.expected_value:.2f}"
            )

        # Step 4: Execute searches in parallel
        logger.info("Step 4: Executing searches...")
        all_candidates = await self._execute_searches(
            pathways, max_results_per_source
        )
        logger.info(f"Found {len(all_candidates)} raw candidates")

        # Step 5: Deduplicate
        logger.info("Step 5: Deduplicating...")
        deduplicated = self.ranker.deduplicate_candidates(all_candidates)
        logger.info(f"After dedup: {len(deduplicated)} candidates")

        # Step 6: Rank
        logger.info("Step 6: Ranking...")
        ranked = await self.ranker.rank_candidates(deduplicated, target)

        # Build results
        completed_at = datetime.utcnow()
        duration = (completed_at - started_at).total_seconds()

        results = SearchResults(
            target=target,
            pathways_explored=len(pathways),
            queries_executed=self._count_queries(pathways),
            candidates=ranked[:target.max_results],
            total_raw_results=len(all_candidates),
            deduplicated_count=len(deduplicated),
            results_by_source=self._count_by_source(all_candidates),
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration,
        )

        logger.info(
            f"Search complete in {duration:.1f}s. "
            f"Found {len(results.candidates)} candidates."
        )

        return results

    async def _execute_searches(
        self,
        pathways: list[SearchPathway],
        max_results: int
    ) -> list[DiscoveredCandidate]:
        """Execute searches across all sources and pathways."""
        all_candidates = []

        # Create search tasks for each (source, pathway) combination
        tasks = []
        for source in self.sources:
            for pathway in pathways:
                tasks.append(
                    self._search_with_source(source, pathway, max_results)
                )

        # Execute in parallel with some concurrency limit
        semaphore = asyncio.Semaphore(10)

        async def limited_search(task):
            async with semaphore:
                return await task

        results = await asyncio.gather(
            *[limited_search(task) for task in tasks],
            return_exceptions=True
        )

        # Collect results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Search task failed: {result}")
            elif result:
                all_candidates.extend(result)

        return all_candidates

    async def _search_with_source(
        self,
        source: SearchSource,
        pathway: SearchPathway,
        max_results: int
    ) -> list[DiscoveredCandidate]:
        """Execute search with a specific source and pathway."""
        try:
            return await source.search(pathway, max_results)
        except Exception as e:
            logger.error(
                f"Search failed for {source.name} via {pathway.gateway_node.full_name}: {e}"
            )
            return []

    def _count_queries(self, pathways: list[SearchPathway]) -> int:
        """Count total queries across all pathways."""
        count = 0
        for p in pathways:
            count += len(p.pdl_queries)
            count += len(p.google_queries)
            count += len(p.github_queries)
            count += len(p.perplexity_queries)
        return count

    def _count_by_source(
        self, candidates: list[DiscoveredCandidate]
    ) -> dict[str, int]:
        """Count candidates by source."""
        counts = {}
        for c in candidates:
            for source in c.sources:
                counts[source.api] = counts.get(source.api, 0) + 1
        return counts

    async def get_network_stats(self) -> dict:
        """Get statistics about the network."""
        return await self.network_analyzer.get_network_stats()

    async def explain_search(
        self,
        target: SearchTarget,
        top_k: int = 10
    ) -> list[dict]:
        """
        Explain how the search would work without executing it.
        Useful for understanding the search strategy.
        """
        # Analyze network
        network_nodes = await self.network_analyzer.analyze_network()

        # Score pathways
        pathways = self.pathway_scorer.score_pathways(
            network_nodes, target, top_k=top_k
        )

        # Generate queries
        for pathway in pathways:
            self.query_generator.generate_queries(pathway, target)

        # Build explanations
        explanations = []
        for pathway in pathways:
            explanation = {
                "gateway": {
                    "name": pathway.gateway_node.full_name,
                    "company": pathway.gateway_node.company,
                    "title": pathway.gateway_node.title,
                    "type": pathway.gateway_node.node_type.value,
                },
                "access_pattern": pathway.access_pattern.value,
                "expected_value": round(pathway.expected_value, 3),
                "estimated_results": pathway.estimated_results,
                "why": self.pathway_scorer.explain_pathway(pathway, target),
                "queries": {
                    "pdl": len(pathway.pdl_queries),
                    "google": len(pathway.google_queries),
                    "github": len(pathway.github_queries),
                    "perplexity": len(pathway.perplexity_queries),
                },
                "sample_queries": {
                    "pdl": pathway.pdl_queries[0] if pathway.pdl_queries else None,
                    "google": pathway.google_queries[0] if pathway.google_queries else None,
                }
            }
            explanations.append(explanation)

        return explanations
