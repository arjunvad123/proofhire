"""
Query Generator - Generates targeted queries for each search API
based on network pathways.

The key insight: your network nodes provide CONTEXT for queries.
Instead of "find ML engineers" (too broad), we generate:
- "ML engineers at [company where my connection works]"
- "PhD students from [university where my connection teaches]"
- "Contributors to [repo my connection maintains]"
"""

import logging
from typing import Optional

from app.search.models import (
    AccessPattern,
    NetworkNode,
    NodeType,
    SearchPathway,
    SearchTarget,
)

logger = logging.getLogger(__name__)


class QueryGenerator:
    """
    Generates targeted search queries from network pathways.
    Each pathway becomes specific queries for different APIs.
    """

    def generate_queries(
        self,
        pathway: SearchPathway,
        target: SearchTarget
    ) -> SearchPathway:
        """
        Generate queries for all APIs based on the pathway.
        Modifies the pathway in place and returns it.
        """
        node = pathway.gateway_node
        pattern = pathway.access_pattern

        # Generate queries for each API
        pathway.pdl_queries = self._generate_pdl_queries(node, pattern, target)
        pathway.google_queries = self._generate_google_queries(node, pattern, target)
        pathway.github_queries = self._generate_github_queries(node, pattern, target)
        pathway.perplexity_queries = self._generate_perplexity_queries(node, pattern, target)

        return pathway

    def _generate_pdl_queries(
        self,
        node: NetworkNode,
        pattern: AccessPattern,
        target: SearchTarget
    ) -> list[dict]:
        """
        Generate People Data Labs queries.
        PDL uses Elasticsearch-style queries with 'term' for exact match.
        """
        queries = []

        # Base query structure - PDL uses 'term' not 'match'
        base_query = {
            "size": 100,
            "query": {
                "bool": {
                    "must": [],
                    "should": []
                }
            }
        }

        # Add title/role filter using job_title_role (PDL field)
        if target.role_title:
            role_lower = target.role_title.lower()
            if "engineer" in role_lower:
                base_query["query"]["bool"]["must"].append({
                    "term": {"job_title_role": "engineering"}
                })
            elif "scientist" in role_lower:
                base_query["query"]["bool"]["must"].append({
                    "term": {"job_title_role": "research"}
                })
            elif "manager" in role_lower or "director" in role_lower:
                base_query["query"]["bool"]["must"].append({
                    "term": {"job_title_role": "manager"}
                })

        # Add skills filter - PDL skills field accepts terms
        for skill in target.required_skills[:2]:  # Limit to top 2
            base_query["query"]["bool"]["should"].append({
                "term": {"skills": skill.lower()}
            })

        # Pattern-specific queries
        if pattern == AccessPattern.COMPANY_TEAM:
            # Search for people at the same company
            if node.company:
                query = self._deep_copy_query(base_query)
                query["query"]["bool"]["must"].append({
                    "term": {"job_company_name": node.company.lower()}
                })
                queries.append({
                    "description": f"People at {node.company}",
                    "query": query
                })

        elif pattern == AccessPattern.COMPANY_ALUMNI:
            # Search for ex-employees
            if node.company:
                query = self._deep_copy_query(base_query)
                query["query"]["bool"]["must"].append({
                    "term": {"experience.company.name": node.company.lower()}
                })
                queries.append({
                    "description": f"Ex-{node.company} employees",
                    "query": query
                })

        elif pattern == AccessPattern.SCHOOL_STUDENTS:
            # Search for students/alumni of the school
            for school in node.schools:
                query = self._deep_copy_query(base_query)
                query["query"]["bool"]["must"].append({
                    "term": {"education.school.name": school.lower()}
                })
                queries.append({
                    "description": f"Alumni of {school}",
                    "query": query
                })

        elif pattern == AccessPattern.SCHOOL_ALUMNI:
            # Similar to above
            for school in node.schools:
                query = self._deep_copy_query(base_query)
                query["query"]["bool"]["must"].append({
                    "term": {"education.school.name": school.lower()}
                })
                queries.append({
                    "description": f"Graduates from {school}",
                    "query": query
                })

        elif pattern == AccessPattern.PORTFOLIO_COMPANIES:
            # For VCs, search across their known portfolio
            # We'd need to know their portfolio, for now search by industry
            for industry in node.industries:
                query = self._deep_copy_query(base_query)
                query["query"]["bool"]["should"].append({
                    "term": {"industry": industry.lower()}
                })
                query["query"]["bool"]["should"].append({
                    "term": {"job_company_size": "1-10"}  # Startup size
                })
                queries.append({
                    "description": f"{industry} startups (via {node.full_name})",
                    "query": query
                })

        elif pattern == AccessPattern.INDUSTRY_NETWORK:
            # General industry search
            for industry in node.industries:
                query = self._deep_copy_query(base_query)
                query["query"]["bool"]["must"].append({
                    "term": {"industry": industry.lower()}
                })
                queries.append({
                    "description": f"{industry} professionals",
                    "query": query
                })

        # Add location filter if specified
        if target.locations:
            for query_dict in queries:
                query_dict["query"]["query"]["bool"]["should"].append({
                    "term": {"location_name": target.locations[0].lower()}
                })

        return queries

    def _generate_google_queries(
        self,
        node: NetworkNode,
        pattern: AccessPattern,
        target: SearchTarget
    ) -> list[str]:
        """
        Generate Google Custom Search queries.
        These are text queries, often with site: operators.
        """
        queries = []

        role_terms = " ".join(self._extract_role_terms(target.role_title))
        skills_str = " ".join(target.required_skills[:2]) if target.required_skills else ""

        # Pattern-specific queries
        if pattern == AccessPattern.COMPANY_TEAM:
            if node.company:
                queries.append(
                    f'site:linkedin.com/in "{node.company}" {role_terms}'
                )
                queries.append(
                    f'"{node.company}" {role_terms} {skills_str}'
                )

        elif pattern == AccessPattern.COMPANY_ALUMNI:
            if node.company:
                queries.append(
                    f'site:linkedin.com/in "ex-{node.company}" OR "former {node.company}" {role_terms}'
                )

        elif pattern == AccessPattern.SCHOOL_STUDENTS:
            for school in node.schools:
                queries.append(
                    f'site:linkedin.com/in "{school}" {role_terms} {skills_str}'
                )
                queries.append(
                    f'"{school}" PhD {role_terms} startup'
                )

        elif pattern == AccessPattern.SCHOOL_ALUMNI:
            for school in node.schools:
                queries.append(
                    f'site:linkedin.com/in "{school}" alumni {role_terms}'
                )

        elif pattern == AccessPattern.OSS_CONTRIBUTORS:
            # Search GitHub for contributors
            queries.append(
                f'site:github.com {skills_str} {role_terms}'
            )

        elif pattern == AccessPattern.RESEARCH_NETWORK:
            for school in node.schools:
                queries.append(
                    f'site:scholar.google.com "{school}" {skills_str}'
                )
            queries.append(
                f'"{node.full_name}" collaborator {role_terms}'
            )

        elif pattern == AccessPattern.PORTFOLIO_COMPANIES:
            # For VCs
            if node.company:
                queries.append(
                    f'"{node.company}" portfolio {role_terms}'
                )
            queries.append(
                f'site:linkedin.com/in "{node.full_name}" connection {role_terms}'
            )

        elif pattern == AccessPattern.INDUSTRY_NETWORK:
            for industry in node.industries:
                queries.append(
                    f'site:linkedin.com/in {industry} {role_terms} {skills_str}'
                )

        # Add preferred background queries
        for bg in target.preferred_backgrounds[:2]:
            if pattern == AccessPattern.COMPANY_ALUMNI:
                queries.append(
                    f'site:linkedin.com/in "ex-{bg}" {role_terms}'
                )

        return queries[:5]  # Limit queries

    def _generate_github_queries(
        self,
        node: NetworkNode,
        pattern: AccessPattern,
        target: SearchTarget
    ) -> list[dict]:
        """
        Generate GitHub API queries.
        These are structured queries for the GitHub Search API.
        """
        queries = []

        # Only generate GitHub queries for relevant patterns
        relevant_patterns = [
            AccessPattern.OSS_CONTRIBUTORS,
            AccessPattern.COMPANY_TEAM,
            AccessPattern.SCHOOL_STUDENTS,
        ]

        if pattern not in relevant_patterns:
            return queries

        # Check if target is engineering-related
        role_lower = target.role_title.lower()
        if not any(word in role_lower for word in [
            "engineer", "developer", "programmer", "swe"
        ]):
            return queries

        # Build language filter from skills
        languages = []
        skill_to_language = {
            "python": "Python",
            "javascript": "JavaScript",
            "typescript": "TypeScript",
            "java": "Java",
            "go": "Go",
            "rust": "Rust",
            "ruby": "Ruby",
            "c++": "C++",
        }
        for skill in target.required_skills:
            if skill.lower() in skill_to_language:
                languages.append(skill_to_language[skill.lower()])

        if pattern == AccessPattern.COMPANY_TEAM:
            if node.company:
                # Search for org members (direct org membership)
                company_slug = node.company.lower().replace(" ", "").replace(".", "")
                queries.append({
                    "type": "org_members",
                    "org": company_slug,
                    "description": f"GitHub org members at {node.company}"
                })
                # Search company's repos and get contributors
                # (GitHub user search doesn't support company: qualifier)
                for skill in target.required_skills[:2]:
                    queries.append({
                        "type": "repo_search",
                        "query": f"org:{company_slug} {skill}",
                        "get_contributors": True,
                        "description": f"{skill} repos at {node.company}"
                    })
                # Also search for repos mentioning the company
                queries.append({
                    "type": "repo_search",
                    "query": f"{node.company} stars:>50",
                    "get_contributors": True,
                    "description": f"Popular repos related to {node.company}"
                })

        elif pattern == AccessPattern.OSS_CONTRIBUTORS:
            # Search for repos related to skills and get contributors
            for skill in target.required_skills[:2]:
                queries.append({
                    "type": "repo_search",
                    "query": f"{skill} stars:>100",
                    "get_contributors": True,
                    "description": f"Contributors to popular {skill} repos"
                })

        elif pattern == AccessPattern.SCHOOL_STUDENTS:
            for school in node.schools:
                # Some universities have GitHub orgs
                school_slug = school.lower().replace(" ", "-").replace("university of ", "")
                queries.append({
                    "type": "user_search",
                    "query": f"location:{school_slug}",
                    "description": f"GitHub users near {school}"
                })

        # Add language filter if we have languages
        if languages:
            for query in queries:
                query["languages"] = languages

        return queries

    def _generate_perplexity_queries(
        self,
        node: NetworkNode,
        pattern: AccessPattern,
        target: SearchTarget
    ) -> list[str]:
        """
        Generate Perplexity AI queries.
        These are natural language research questions.
        """
        queries = []

        role = target.role_title
        skills_str = ", ".join(target.required_skills[:3]) if target.required_skills else ""

        if pattern == AccessPattern.COMPANY_TEAM:
            if node.company:
                queries.append(
                    f"Who are the notable {role}s currently working at {node.company}? "
                    f"Focus on people with {skills_str} experience."
                )

        elif pattern == AccessPattern.COMPANY_ALUMNI:
            if node.company:
                queries.append(
                    f"Who are well-known {role}s who previously worked at {node.company} "
                    f"and have since joined startups or founded companies?"
                )

        elif pattern == AccessPattern.SCHOOL_STUDENTS:
            for school in node.schools:
                queries.append(
                    f"Who are notable {role}s or researchers from {school} "
                    f"who work in {skills_str}? Include recent graduates and PhD alumni."
                )

        elif pattern == AccessPattern.RESEARCH_NETWORK:
            if node.full_name:
                queries.append(
                    f"Who has collaborated with {node.full_name} on research? "
                    f"Who are their notable students or collaborators in industry?"
                )

        elif pattern == AccessPattern.PORTFOLIO_COMPANIES:
            if node.company:
                queries.append(
                    f"What are the portfolio companies of {node.company}? "
                    f"Who are the {role}s or technical leaders at those companies?"
                )

        elif pattern == AccessPattern.INDUSTRY_NETWORK:
            for industry in node.industries[:1]:
                queries.append(
                    f"Who are the top {role}s in the {industry} industry? "
                    f"Focus on people at startups with {skills_str} skills."
                )

        # Add a general network expansion query
        queries.append(
            f"Based on {node.full_name}'s background at {node.company}, "
            f"who in their professional network might be a good {role} candidate? "
            f"Consider their colleagues, collaborators, and industry connections."
        )

        return queries[:3]  # Limit queries

    def _extract_role_terms(self, role_title: str) -> list[str]:
        """Extract searchable terms from a role title."""
        # Common role term mappings
        terms = []
        role_lower = role_title.lower()

        if "senior" in role_lower:
            terms.append("senior")
        if "staff" in role_lower:
            terms.append("staff")
        if "principal" in role_lower:
            terms.append("principal")
        if "lead" in role_lower:
            terms.append("lead")

        if "engineer" in role_lower:
            terms.append("engineer")
        if "developer" in role_lower:
            terms.append("developer")
        if "scientist" in role_lower:
            terms.append("scientist")

        if "ml" in role_lower or "machine learning" in role_lower:
            terms.append("machine learning")
        if "data" in role_lower:
            terms.append("data")
        if "backend" in role_lower:
            terms.append("backend")
        if "frontend" in role_lower:
            terms.append("frontend")
        if "full" in role_lower and "stack" in role_lower:
            terms.append("full stack")
        if "infrastructure" in role_lower:
            terms.append("infrastructure")
        if "platform" in role_lower:
            terms.append("platform")
        if "devops" in role_lower or "sre" in role_lower:
            terms.append("devops")

        return terms if terms else [role_title]

    def _deep_copy_query(self, query: dict) -> dict:
        """Deep copy a query dict."""
        import copy
        return copy.deepcopy(query)
