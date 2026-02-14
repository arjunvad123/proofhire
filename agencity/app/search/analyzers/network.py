"""
Network Analyzer - Analyzes your network connections to identify
access patterns, classify node types, and extract searchable attributes.

This is the foundation of network-driven search. Every connection
becomes a potential gateway to candidates based on their role,
company, and position in their own network.
"""

import logging
import re
from collections import defaultdict
from typing import Optional
from uuid import UUID

from app.models.company import Person
from app.search.models import (
    AccessPattern,
    NetworkNode,
    NodeType,
)
from app.services.company_db import company_db

logger = logging.getLogger(__name__)


class NetworkAnalyzer:
    """
    Analyzes a company's network to extract access patterns and
    classify nodes for search routing.
    """

    # Title patterns for classification
    TITLE_PATTERNS = {
        NodeType.PROFESSOR: [
            r"\bprofessor\b", r"\bprof\.\b", r"\bfaculty\b",
            r"\bdepartment chair\b", r"\bacademic\b", r"\blecturer\b",
            r"\bteaching assistant\b", r"\bta\b", r"\bpostdoc\b",
            r"\bresearch scientist\b", r"\bphd\b"
        ],
        NodeType.VC_INVESTOR: [
            r"\bpartner\b.*\b(vc|venture|capital)\b",
            r"\b(vc|venture)\b.*\bpartner\b",
            r"\binvestor\b", r"\bangel\b", r"\bventure\b",
            r"\bprincipal\b.*\b(capital|ventures)\b",
            r"\bgeneral partner\b", r"\bgp\b.*\bventure\b"
        ],
        NodeType.FOUNDER: [
            r"\bfounder\b", r"\bco-founder\b", r"\bcofounder\b",
            r"\bceo\b.*\bfounder\b", r"\bowner\b"
        ],
        NodeType.EXECUTIVE: [
            r"\bceo\b", r"\bcto\b", r"\bcfo\b", r"\bcoo\b", r"\bcmo\b",
            r"\bchief\b", r"\bvp\b", r"\bvice president\b",
            r"\bdirector\b", r"\bhead of\b", r"\bevp\b", r"\bsvp\b"
        ],
        NodeType.ENGINEERING_MANAGER: [
            r"\bengineering manager\b", r"\beng manager\b",
            r"\btech lead\b", r"\btechnical lead\b",
            r"\bstaff engineer\b", r"\bprincipal engineer\b",
            r"\barchitect\b", r"\bteam lead\b"
        ],
        NodeType.RECRUITER: [
            r"\brecruiter\b", r"\btalent\b", r"\bhr\b",
            r"\bhuman resources\b", r"\bpeople\b.*\bops\b",
            r"\bheadhunter\b"
        ],
        NodeType.RESEARCHER: [
            r"\bresearcher\b", r"\bscientist\b", r"\bresearch\b",
            r"\br&d\b", r"\bphd\b"
        ],
        NodeType.ENGINEER: [
            r"\bengineer\b", r"\bdeveloper\b", r"\bprogrammer\b",
            r"\bswe\b", r"\bsoftware\b", r"\bbackend\b", r"\bfrontend\b",
            r"\bfull.?stack\b", r"\bdevops\b", r"\bsre\b", r"\bdata\b",
            r"\bml\b", r"\bmachine learning\b", r"\bai\b"
        ],
    }

    # Company patterns for additional classification
    VC_COMPANIES = [
        "a]16z", "andreessen", "sequoia", "greylock", "accel", "benchmark",
        "kleiner", "khosla", "general catalyst", "lightspeed", "index",
        "founders fund", "yc", "y combinator", "combinator", "neo",
        "first round", "bessemer", "insight", "tiger global"
    ]

    FAANG_COMPANIES = [
        "google", "meta", "facebook", "amazon", "apple", "microsoft",
        "netflix", "uber", "airbnb", "stripe", "openai", "anthropic",
        "deepmind"
    ]

    UNIVERSITIES = [
        "stanford", "mit", "berkeley", "cmu", "carnegie mellon",
        "harvard", "princeton", "caltech", "cornell", "yale",
        "columbia", "nyu", "ucla", "ucsd", "uc san diego", "georgia tech",
        "university of", "college"
    ]

    def __init__(self, company_id: UUID):
        self.company_id = company_id
        self._network_cache: Optional[list[NetworkNode]] = None

    async def analyze_network(self) -> list[NetworkNode]:
        """
        Analyze all people in the company's network and classify them.
        Returns a list of NetworkNodes with access patterns identified.
        """
        if self._network_cache:
            return self._network_cache

        # Get all people from the network (no limit)
        # Using a very large limit to ensure we get everything
        # The get_people method will paginate automatically
        people = await company_db.get_people(
            self.company_id,
            limit=999999,  # Effectively unlimited - pagination handles this
            filters={"is_from_network": True}
        )

        logger.info(f"Analyzing {len(people)} network connections")

        nodes = []
        for person in people:
            node = self._analyze_person(person)
            nodes.append(node)

        # Sort by estimated value (reach * seniority)
        nodes.sort(
            key=lambda n: n.estimated_reach * n.seniority_score,
            reverse=True
        )

        self._network_cache = nodes
        logger.info(f"Classified {len(nodes)} network nodes")

        return nodes

    def _analyze_person(self, person: Person) -> NetworkNode:
        """Analyze a single person and create a NetworkNode."""
        title = (person.current_title or "").lower()
        company = (person.current_company or "").lower()

        # Classify node type
        node_type = self._classify_node_type(title, company)

        # Identify access patterns based on type
        access_patterns = self._identify_access_patterns(node_type, title, company)

        # Estimate reach
        estimated_reach = self._estimate_reach(node_type, title, company)

        # Calculate seniority
        seniority = self._calculate_seniority(title)

        # Extract searchable attributes
        companies = self._extract_companies(person)
        schools = self._extract_schools(person)
        skills = self._extract_skills(person)
        industries = self._extract_industries(company, title)

        return NetworkNode(
            person_id=person.id,
            full_name=person.full_name,
            company=person.current_company,
            title=person.current_title,
            linkedin_url=person.linkedin_url,
            node_type=node_type,
            access_patterns=access_patterns,
            estimated_reach=estimated_reach,
            companies=companies,
            schools=schools,
            skills=skills,
            industries=industries,
            seniority_score=seniority,
            network_freshness=0.7,  # TODO: Calculate from activity
            connection_strength=person.trust_score or 0.5
        )

    def _classify_node_type(self, title: str, company: str) -> NodeType:
        """Classify a person's node type based on title and company."""

        # Check title patterns in priority order
        priority_order = [
            NodeType.VC_INVESTOR,      # VCs have unique access
            NodeType.PROFESSOR,        # Professors have student access
            NodeType.FOUNDER,          # Founders have team + investor access
            NodeType.EXECUTIVE,        # Executives have broad access
            NodeType.ENGINEERING_MANAGER,
            NodeType.RECRUITER,
            NodeType.RESEARCHER,
            NodeType.ENGINEER,
        ]

        for node_type in priority_order:
            patterns = self.TITLE_PATTERNS.get(node_type, [])
            for pattern in patterns:
                if re.search(pattern, title, re.IGNORECASE):
                    return node_type

        # Check company-based classification
        for vc_pattern in self.VC_COMPANIES:
            if vc_pattern in company:
                return NodeType.VC_INVESTOR

        for uni_pattern in self.UNIVERSITIES:
            if uni_pattern in company:
                # Could be professor, student, or researcher
                if any(word in title for word in ["professor", "faculty", "chair"]):
                    return NodeType.PROFESSOR
                elif any(word in title for word in ["research", "scientist", "phd"]):
                    return NodeType.RESEARCHER

        return NodeType.UNKNOWN

    def _identify_access_patterns(
        self, node_type: NodeType, title: str, company: str
    ) -> list[AccessPattern]:
        """Identify what access patterns this node provides."""
        patterns = []

        # Every employed person has some company access
        if company and company not in ["self-employed", "freelance", "n/a", "-"]:
            patterns.append(AccessPattern.COMPANY_TEAM)
            patterns.append(AccessPattern.COMPANY_ALUMNI)

        # Type-specific patterns
        if node_type == NodeType.PROFESSOR:
            patterns.append(AccessPattern.SCHOOL_STUDENTS)
            patterns.append(AccessPattern.SCHOOL_ALUMNI)
            patterns.append(AccessPattern.RESEARCH_NETWORK)

        elif node_type == NodeType.VC_INVESTOR:
            patterns.append(AccessPattern.PORTFOLIO_COMPANIES)
            patterns.append(AccessPattern.INVESTOR_NETWORK)

        elif node_type == NodeType.FOUNDER:
            patterns.append(AccessPattern.INVESTOR_NETWORK)
            patterns.append(AccessPattern.INDUSTRY_NETWORK)

        elif node_type == NodeType.EXECUTIVE:
            patterns.append(AccessPattern.INDUSTRY_NETWORK)

        elif node_type == NodeType.RECRUITER:
            patterns.append(AccessPattern.INDUSTRY_NETWORK)

        elif node_type == NodeType.RESEARCHER:
            patterns.append(AccessPattern.RESEARCH_NETWORK)

        # Check for OSS maintainer signals in title
        oss_signals = ["maintainer", "open source", "contributor", "committer"]
        if any(signal in title.lower() for signal in oss_signals):
            patterns.append(AccessPattern.OSS_CONTRIBUTORS)

        return patterns

    def _estimate_reach(self, node_type: NodeType, title: str, company: str) -> int:
        """
        Estimate how many people this node could potentially
        connect you to through their network.
        """
        base_reach = {
            NodeType.PROFESSOR: 200,        # Students + colleagues
            NodeType.VC_INVESTOR: 500,      # Portfolio companies
            NodeType.FOUNDER: 50,           # Team + network
            NodeType.EXECUTIVE: 100,        # Department + industry
            NodeType.ENGINEERING_MANAGER: 30,  # Team + adjacent
            NodeType.RECRUITER: 300,        # Candidates screened
            NodeType.RESEARCHER: 50,        # Collaborators
            NodeType.ENGINEER: 15,          # Close coworkers
            NodeType.OSS_MAINTAINER: 100,   # Contributors
            NodeType.COMMUNITY_ORGANIZER: 200,  # Community members
            NodeType.UNKNOWN: 10,
        }

        reach = base_reach.get(node_type, 10)

        # Adjust for seniority
        seniority_keywords = ["senior", "staff", "principal", "director", "head", "chief"]
        if any(kw in title.lower() for kw in seniority_keywords):
            reach = int(reach * 1.5)

        # Adjust for company size (rough proxy)
        for big_company in self.FAANG_COMPANIES:
            if big_company in company.lower():
                reach = int(reach * 2)
                break

        return reach

    def _calculate_seniority(self, title: str) -> float:
        """Calculate seniority score from 0-1."""
        title_lower = title.lower()

        # C-level / founders
        if any(word in title_lower for word in [
            "ceo", "cto", "cfo", "coo", "founder", "co-founder", "chief"
        ]):
            return 0.95

        # VP level
        if any(word in title_lower for word in [
            "vp", "vice president", "evp", "svp", "partner"
        ]):
            return 0.85

        # Director level
        if any(word in title_lower for word in [
            "director", "head of", "department chair"
        ]):
            return 0.75

        # Senior IC / Manager
        if any(word in title_lower for word in [
            "staff", "principal", "senior", "manager", "lead", "professor"
        ]):
            return 0.65

        # Mid level
        if any(word in title_lower for word in [
            "engineer", "developer", "analyst", "scientist"
        ]):
            return 0.45

        # Entry level
        if any(word in title_lower for word in [
            "intern", "junior", "associate", "assistant", "student"
        ]):
            return 0.25

        return 0.4  # Default

    def _extract_companies(self, person: Person) -> list[str]:
        """Extract company names for searchability."""
        companies = []
        if person.current_company:
            companies.append(person.current_company)
        # TODO: Add past companies from enrichment data
        return companies

    def _extract_schools(self, person: Person) -> list[str]:
        """Extract school names for searchability."""
        schools = []
        # Check if company is a university
        company = (person.current_company or "").lower()
        for uni in self.UNIVERSITIES:
            if uni in company:
                schools.append(person.current_company)
                break
        # TODO: Add education from enrichment data
        return schools

    def _extract_skills(self, person: Person) -> list[str]:
        """Extract skills from title."""
        title = (person.current_title or "").lower()
        skills = []

        # Common skill patterns in titles
        skill_patterns = {
            "python": ["python"],
            "javascript": ["javascript", "js", "node", "react", "vue", "angular"],
            "machine learning": ["ml", "machine learning", "ai", "deep learning"],
            "data science": ["data science", "data scientist", "analytics"],
            "devops": ["devops", "sre", "infrastructure", "platform"],
            "backend": ["backend", "back-end", "server"],
            "frontend": ["frontend", "front-end", "ui", "ux"],
            "mobile": ["mobile", "ios", "android", "flutter"],
            "cloud": ["aws", "gcp", "azure", "cloud"],
        }

        for skill, patterns in skill_patterns.items():
            if any(p in title for p in patterns):
                skills.append(skill)

        return skills

    def _extract_industries(self, company: str, title: str) -> list[str]:
        """Extract industry classifications."""
        industries = []
        combined = f"{company} {title}".lower()

        industry_patterns = {
            "ai_ml": ["ai", "artificial intelligence", "machine learning", "ml", "deep learning"],
            "fintech": ["fintech", "finance", "banking", "trading", "payments"],
            "healthtech": ["health", "medical", "biotech", "pharma"],
            "edtech": ["education", "edtech", "learning", "university"],
            "ecommerce": ["ecommerce", "e-commerce", "retail", "shopping"],
            "saas": ["saas", "software", "platform", "b2b"],
            "crypto": ["crypto", "blockchain", "web3", "defi"],
            "gaming": ["gaming", "games", "esports"],
        }

        for industry, patterns in industry_patterns.items():
            if any(p in combined for p in patterns):
                industries.append(industry)

        return industries

    async def get_network_stats(self) -> dict:
        """Get statistics about the analyzed network."""
        nodes = await self.analyze_network()

        stats = {
            "total_nodes": len(nodes),
            "by_type": defaultdict(int),
            "by_access_pattern": defaultdict(int),
            "total_estimated_reach": 0,
            "top_companies": defaultdict(int),
            "avg_seniority": 0.0,
        }

        for node in nodes:
            stats["by_type"][node.node_type.value] += 1
            stats["total_estimated_reach"] += node.estimated_reach
            stats["avg_seniority"] += node.seniority_score

            for pattern in node.access_patterns:
                stats["by_access_pattern"][pattern.value] += 1

            for company in node.companies:
                stats["top_companies"][company] += 1

        if nodes:
            stats["avg_seniority"] /= len(nodes)

        # Convert to regular dicts and sort
        stats["by_type"] = dict(sorted(
            stats["by_type"].items(),
            key=lambda x: x[1],
            reverse=True
        ))
        stats["by_access_pattern"] = dict(stats["by_access_pattern"])
        stats["top_companies"] = dict(sorted(
            stats["top_companies"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:20])

        return stats

    async def get_top_gateways(
        self,
        n: int = 50,
        node_types: Optional[list[NodeType]] = None,
        access_patterns: Optional[list[AccessPattern]] = None
    ) -> list[NetworkNode]:
        """
        Get the top N gateway nodes, optionally filtered by type
        or access pattern.
        """
        nodes = await self.analyze_network()

        if node_types:
            nodes = [n for n in nodes if n.node_type in node_types]

        if access_patterns:
            nodes = [
                n for n in nodes
                if any(p in access_patterns for p in n.access_patterns)
            ]

        return nodes[:n]
