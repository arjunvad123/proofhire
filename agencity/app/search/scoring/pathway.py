"""
Pathway Scorer - Scores network nodes based on their likelihood
of connecting you to relevant candidates.

This is the brain of network-driven search. It answers:
"Given that I need X, which of my connections is most likely to know X?"
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


class PathwayScorer:
    """
    Scores network nodes based on their potential to surface
    relevant candidates for a given search target.
    """

    # Which node types are valuable for which role categories
    ROLE_TO_NODE_AFFINITY = {
        # Engineering roles
        "engineer": {
            NodeType.ENGINEERING_MANAGER: 0.9,  # Knows their team
            NodeType.FOUNDER: 0.8,              # Built engineering teams
            NodeType.ENGINEER: 0.7,             # Knows peers
            NodeType.RECRUITER: 0.75,           # Screened many
            NodeType.PROFESSOR: 0.6,            # Knows students going to industry
            NodeType.VC_INVESTOR: 0.5,          # Portfolio companies
        },
        # Research/ML roles
        "researcher": {
            NodeType.PROFESSOR: 0.95,           # Best source for researchers
            NodeType.RESEARCHER: 0.85,          # Knows peers
            NodeType.FOUNDER: 0.6,              # If AI/ML company
            NodeType.VC_INVESTOR: 0.5,          # AI portfolio
        },
        # Leadership roles
        "executive": {
            NodeType.VC_INVESTOR: 0.9,          # Know many execs
            NodeType.FOUNDER: 0.85,             # Know other founders
            NodeType.EXECUTIVE: 0.8,            # Know peers
            NodeType.RECRUITER: 0.6,            # Executive recruiters
        },
        # Sales/BD roles
        "sales": {
            NodeType.FOUNDER: 0.7,              # Built sales teams
            NodeType.EXECUTIVE: 0.65,           # Know sales leaders
            NodeType.VC_INVESTOR: 0.5,          # Portfolio
        },
    }

    # Access pattern value for different role categories
    ACCESS_PATTERN_VALUE = {
        "engineer": {
            AccessPattern.COMPANY_TEAM: 0.9,
            AccessPattern.COMPANY_ALUMNI: 0.8,
            AccessPattern.OSS_CONTRIBUTORS: 0.85,
            AccessPattern.SCHOOL_ALUMNI: 0.6,
            AccessPattern.SCHOOL_STUDENTS: 0.7,
            AccessPattern.PORTFOLIO_COMPANIES: 0.5,
        },
        "researcher": {
            AccessPattern.SCHOOL_STUDENTS: 0.95,
            AccessPattern.RESEARCH_NETWORK: 0.9,
            AccessPattern.SCHOOL_ALUMNI: 0.8,
            AccessPattern.COMPANY_TEAM: 0.5,
        },
        "executive": {
            AccessPattern.PORTFOLIO_COMPANIES: 0.9,
            AccessPattern.INVESTOR_NETWORK: 0.85,
            AccessPattern.INDUSTRY_NETWORK: 0.8,
            AccessPattern.COMPANY_ALUMNI: 0.6,
        },
    }

    # Skill affinities - which node types are good for which skills
    SKILL_NODE_AFFINITY = {
        "machine learning": [NodeType.PROFESSOR, NodeType.RESEARCHER],
        "python": [NodeType.ENGINEER, NodeType.ENGINEERING_MANAGER],
        "javascript": [NodeType.ENGINEER],
        "data science": [NodeType.RESEARCHER, NodeType.PROFESSOR],
        "devops": [NodeType.ENGINEERING_MANAGER, NodeType.ENGINEER],
        "mobile": [NodeType.ENGINEER],
        "cloud": [NodeType.ENGINEER, NodeType.ENGINEERING_MANAGER],
    }

    def score_pathways(
        self,
        nodes: list[NetworkNode],
        target: SearchTarget,
        top_k: int = 50
    ) -> list[SearchPathway]:
        """
        Score all network nodes and return top pathways for the search target.
        """
        logger.info(f"Scoring {len(nodes)} nodes for target: {target.role_title}")

        # Determine role category
        role_category = self._categorize_role(target.role_title)
        logger.info(f"Role category: {role_category}")

        pathways = []

        for node in nodes:
            # Score each access pattern separately
            for pattern in node.access_patterns:
                pathway = self._score_pathway(node, pattern, target, role_category)
                if pathway.expected_value > 0.1:  # Threshold
                    pathways.append(pathway)

        # Sort by expected value
        pathways.sort(key=lambda p: p.expected_value, reverse=True)

        logger.info(f"Generated {len(pathways)} pathways, returning top {top_k}")
        return pathways[:top_k]

    def _categorize_role(self, role_title: str) -> str:
        """Categorize a role title into a broad category."""
        role_lower = role_title.lower()

        if any(word in role_lower for word in [
            "engineer", "developer", "swe", "programmer", "devops", "sre"
        ]):
            return "engineer"

        if any(word in role_lower for word in [
            "researcher", "scientist", "phd", "ml", "machine learning", "ai"
        ]):
            # ML engineers are still engineers but with research affinity
            if "engineer" in role_lower:
                return "engineer"
            return "researcher"

        if any(word in role_lower for word in [
            "ceo", "cto", "cfo", "vp", "director", "head", "chief", "executive"
        ]):
            return "executive"

        if any(word in role_lower for word in [
            "sales", "account", "business development", "bd"
        ]):
            return "sales"

        return "engineer"  # Default

    def _score_pathway(
        self,
        node: NetworkNode,
        pattern: AccessPattern,
        target: SearchTarget,
        role_category: str
    ) -> SearchPathway:
        """Score a single pathway (node + access pattern)."""

        # 1. Node type affinity for this role
        node_affinity = self.ROLE_TO_NODE_AFFINITY.get(role_category, {})
        type_score = node_affinity.get(node.node_type, 0.3)

        # 2. Access pattern value for this role
        pattern_value = self.ACCESS_PATTERN_VALUE.get(role_category, {})
        pattern_score = pattern_value.get(pattern, 0.3)

        # 3. Skill match bonus
        skill_bonus = self._calculate_skill_bonus(node, target)

        # 4. Company/school match bonus
        context_bonus = self._calculate_context_bonus(node, target)

        # 5. Seniority factor (senior people have better networks)
        seniority_factor = 0.5 + (node.seniority_score * 0.5)

        # 6. Connection strength (how likely to help)
        warmth_factor = 0.5 + (node.connection_strength * 0.5)

        # 7. Reach normalization (more reach = more expected results)
        reach_factor = min(1.0, node.estimated_reach / 100)

        # Calculate final expected value
        relevance = (
            type_score * 0.25 +
            pattern_score * 0.25 +
            skill_bonus * 0.2 +
            context_bonus * 0.15 +
            seniority_factor * 0.15
        )

        expected_value = relevance * warmth_factor * reach_factor

        # Estimate number of results
        estimated_results = int(node.estimated_reach * relevance * 0.3)

        return SearchPathway(
            gateway_node=node,
            access_pattern=pattern,
            expected_value=expected_value,
            relevance_to_target=relevance,
            estimated_results=estimated_results,
            # Queries will be generated later by QueryGenerator
            pdl_queries=[],
            google_queries=[],
            github_queries=[],
            perplexity_queries=[],
        )

    def _calculate_skill_bonus(
        self,
        node: NetworkNode,
        target: SearchTarget
    ) -> float:
        """Calculate bonus based on skill overlap."""
        bonus = 0.0

        # Check if node's industry/skills align with target skills
        for skill in target.required_skills:
            skill_lower = skill.lower()

            # Check if node type is good for this skill
            preferred_types = self.SKILL_NODE_AFFINITY.get(skill_lower, [])
            if node.node_type in preferred_types:
                bonus += 0.15

            # Check if node has related skills/industries
            if skill_lower in [s.lower() for s in node.skills]:
                bonus += 0.1

            for industry in node.industries:
                if skill_lower in industry.lower():
                    bonus += 0.1

        return min(1.0, bonus)

    def _calculate_context_bonus(
        self,
        node: NetworkNode,
        target: SearchTarget
    ) -> float:
        """Calculate bonus based on company/school/industry overlap."""
        bonus = 0.0

        # Target companies match
        for company in node.companies:
            if company.lower() in [c.lower() for c in target.target_companies]:
                bonus += 0.3

            # Check preferred backgrounds (FAANG, YC, etc.)
            for bg in target.preferred_backgrounds:
                if bg.lower() in company.lower():
                    bonus += 0.2

        # Target schools match
        for school in node.schools:
            if school.lower() in [s.lower() for s in target.target_schools]:
                bonus += 0.25

        # Industry match
        for industry in node.industries:
            if industry.lower() in [i.lower() for i in target.target_industries]:
                bonus += 0.15

        return min(1.0, bonus)

    def explain_pathway(self, pathway: SearchPathway, target: SearchTarget) -> str:
        """Generate a human-readable explanation of why this pathway is valuable."""
        node = pathway.gateway_node
        reasons = []

        # Node type explanation
        type_explanations = {
            NodeType.PROFESSOR: f"As a professor, {node.full_name} has access to students and researchers",
            NodeType.VC_INVESTOR: f"As an investor, {node.full_name} knows people across portfolio companies",
            NodeType.FOUNDER: f"As a founder, {node.full_name} has built teams and knows the startup network",
            NodeType.ENGINEERING_MANAGER: f"As an engineering manager, {node.full_name} knows their team and adjacent teams",
            NodeType.RECRUITER: f"As a recruiter, {node.full_name} has screened many candidates",
            NodeType.EXECUTIVE: f"As an executive, {node.full_name} has broad industry connections",
        }

        if node.node_type in type_explanations:
            reasons.append(type_explanations[node.node_type])

        # Company context
        if node.company:
            reasons.append(f"Currently at {node.company}")

        # Access pattern
        pattern_explanations = {
            AccessPattern.COMPANY_TEAM: "Can connect you to their coworkers",
            AccessPattern.SCHOOL_STUDENTS: "Has access to current and former students",
            AccessPattern.PORTFOLIO_COMPANIES: "Knows people across their portfolio",
            AccessPattern.OSS_CONTRIBUTORS: "Connected to open source contributors",
        }

        if pathway.access_pattern in pattern_explanations:
            reasons.append(pattern_explanations[pathway.access_pattern])

        # Estimated reach
        reasons.append(f"Estimated reach: ~{node.estimated_reach} people")

        return " | ".join(reasons)
