"""
Query Autocomplete - Suggest search queries based on history and patterns.

Features:
- Prefix matching with trie data structure
- History-based suggestions
- Popular query boosting
- Company-specific patterns
- Industry-standard roles

Usage:
    autocomplete = QueryAutocomplete()
    suggestions = await autocomplete.suggest("ML Eng", company_id="...")
    # Returns: ["ML Engineer", "ML Engineer PyTorch", "ML Engineering Manager"]
"""

import logging
from typing import Optional
from collections import defaultdict
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.core.database import get_supabase_client

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class TrieNode:
    """Node in a trie for fast prefix matching."""
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.queries = []  # Full queries that pass through this node
        self.count = 0     # How many times queries with this prefix were used


class QuerySuggestion(BaseModel):
    """A suggested query with metadata."""
    query: str
    score: float           # Relevance score (0-1)
    source: str            # "history", "popular", "pattern"
    times_used: int = 0
    last_used: Optional[datetime] = None


# =============================================================================
# COMMON ROLE PATTERNS (Industry Standard)
# =============================================================================

ROLE_PATTERNS = {
    # Engineering
    "software": ["Software Engineer", "Software Developer", "Software Architect"],
    "senior": ["Senior Software Engineer", "Senior Backend Engineer", "Senior Frontend Engineer"],
    "staff": ["Staff Engineer", "Staff Software Engineer", "Staff Backend Engineer"],
    "principal": ["Principal Engineer", "Principal Software Engineer"],
    "ml": ["ML Engineer", "Machine Learning Engineer", "ML Research Engineer", "ML Ops Engineer"],
    "data": ["Data Engineer", "Data Scientist", "Data Analyst", "Data Platform Engineer"],
    "backend": ["Backend Engineer", "Backend Developer", "Senior Backend Engineer"],
    "frontend": ["Frontend Engineer", "Frontend Developer", "Senior Frontend Engineer"],
    "fullstack": ["Fullstack Engineer", "Full Stack Developer", "Senior Fullstack Engineer"],
    "devops": ["DevOps Engineer", "SRE", "Site Reliability Engineer", "Platform Engineer"],
    "mobile": ["Mobile Engineer", "iOS Engineer", "Android Engineer", "React Native Developer"],
    "security": ["Security Engineer", "AppSec Engineer", "Security Architect"],

    # Product & Design
    "product": ["Product Manager", "Senior Product Manager", "Product Lead", "Group PM"],
    "design": ["Product Designer", "UX Designer", "UI Designer", "Design Lead"],

    # Leadership
    "engineering manager": ["Engineering Manager", "Senior Engineering Manager", "Director of Engineering"],
    "head": ["Head of Engineering", "Head of Product", "Head of Design", "Head of Data"],
    "vp": ["VP Engineering", "VP Product", "VP Design"],
    "cto": ["CTO", "Chief Technology Officer"],

    # Go-to-Market
    "sales": ["Sales Representative", "Account Executive", "Sales Manager", "Head of Sales"],
    "marketing": ["Marketing Manager", "Growth Marketing", "Head of Marketing"],
    "customer": ["Customer Success Manager", "Customer Support", "Head of Customer Success"],
}

# Skills commonly associated with roles
ROLE_SKILL_PATTERNS = {
    "ML Engineer": ["Python", "PyTorch", "TensorFlow", "Machine Learning"],
    "Backend Engineer": ["Python", "Go", "Java", "PostgreSQL", "AWS"],
    "Frontend Engineer": ["React", "TypeScript", "JavaScript", "CSS"],
    "Data Engineer": ["Python", "SQL", "Spark", "Airflow", "dbt"],
    "DevOps Engineer": ["Kubernetes", "Docker", "AWS", "Terraform", "CI/CD"],
    "Product Manager": ["Product Strategy", "Agile", "Data Analysis"],
}


class QueryAutocomplete:
    """
    Fast query autocomplete using trie + history.

    Combines:
    1. User's search history (most relevant)
    2. Company's search history (team patterns)
    3. Popular queries across platform
    4. Industry-standard role patterns
    """

    def __init__(self):
        self._trie = TrieNode()
        self._history_cache = {}  # company_id -> list of past queries
        self._initialized = False
        self._supabase = None

        # Pre-populate with common patterns
        self._populate_patterns()

    @property
    def supabase(self):
        if self._supabase is None:
            self._supabase = get_supabase_client()
        return self._supabase

    def _populate_patterns(self):
        """Pre-populate trie with common role patterns."""
        for prefix, roles in ROLE_PATTERNS.items():
            for role in roles:
                self._add_to_trie(role.lower(), role, source="pattern")

    def _add_to_trie(self, key: str, full_query: str, source: str = "pattern"):
        """Add a query to the trie."""
        node = self._trie
        for char in key.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            node.count += 1

            # Store the full query at this node
            existing = [q for q in node.queries if q["query"] == full_query]
            if existing:
                existing[0]["count"] += 1
            else:
                node.queries.append({
                    "query": full_query,
                    "source": source,
                    "count": 1
                })

        node.is_end = True

    def _search_trie(self, prefix: str, limit: int = 10) -> list[dict]:
        """Search trie for queries matching prefix."""
        node = self._trie

        # Navigate to prefix node
        for char in prefix.lower():
            if char not in node.children:
                return []
            node = node.children[char]

        # Collect all queries from this node
        results = []
        self._collect_queries(node, results, limit * 3)  # Get extra for filtering

        # Sort by count (popularity)
        results.sort(key=lambda x: x["count"], reverse=True)

        return results[:limit]

    def _collect_queries(self, node: TrieNode, results: list, limit: int):
        """Recursively collect queries from trie node."""
        if len(results) >= limit:
            return

        # Add queries at this node
        for q in node.queries:
            if q not in results:
                results.append(q)

        # Recurse to children
        for child in node.children.values():
            self._collect_queries(child, results, limit)

    async def load_history(self, company_id: str, user_id: Optional[str] = None):
        """Load search history from database."""
        try:
            # Query search history table
            query = self.supabase.table("search_history")\
                .select("*")\
                .eq("company_id", company_id)\
                .order("created_at", desc=True)\
                .limit(500)

            if user_id:
                query = query.eq("user_id", user_id)

            result = query.execute()

            # Add to trie
            for record in result.data or []:
                query_text = record.get("query") or record.get("role_title")
                if query_text:
                    self._add_to_trie(
                        query_text.lower(),
                        query_text,
                        source="history"
                    )

            self._history_cache[company_id] = result.data or []

        except Exception as e:
            logger.warning(f"Could not load search history: {e}")

    async def record_search(
        self,
        company_id: str,
        user_id: str,
        query: str,
        role_title: str,
        required_skills: list[str] = []
    ):
        """Record a search for future autocomplete."""
        try:
            self.supabase.table("search_history").insert({
                "company_id": company_id,
                "user_id": user_id,
                "query": query,
                "role_title": role_title,
                "required_skills": required_skills,
                "created_at": datetime.utcnow().isoformat()
            }).execute()

            # Add to trie immediately
            self._add_to_trie(role_title.lower(), role_title, source="history")
            self._add_to_trie(query.lower(), query, source="history")

        except Exception as e:
            logger.warning(f"Could not record search: {e}")

    async def suggest(
        self,
        partial_query: str,
        company_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 8
    ) -> list[QuerySuggestion]:
        """
        Get autocomplete suggestions for a partial query.

        Args:
            partial_query: What the user has typed so far
            company_id: For company-specific suggestions
            user_id: For user-specific suggestions
            limit: Max suggestions to return

        Returns:
            List of QuerySuggestion objects, sorted by relevance
        """
        if len(partial_query) < 2:
            return []

        # Load history if company_id provided and not cached
        if company_id and company_id not in self._history_cache:
            await self.load_history(company_id, user_id)

        # Search trie
        matches = self._search_trie(partial_query, limit * 2)

        # Convert to QuerySuggestion
        suggestions = []
        seen_queries = set()

        for match in matches:
            query = match["query"]

            # Skip duplicates
            if query.lower() in seen_queries:
                continue
            seen_queries.add(query.lower())

            # Calculate score
            score = self._calculate_score(match, partial_query)

            suggestions.append(QuerySuggestion(
                query=query,
                score=score,
                source=match["source"],
                times_used=match["count"]
            ))

        # Sort by score
        suggestions.sort(key=lambda x: x.score, reverse=True)

        # Add skill-enhanced suggestions
        if partial_query.lower() in ROLE_SKILL_PATTERNS:
            role = partial_query
            skills = ROLE_SKILL_PATTERNS.get(partial_query, [])[:2]
            if skills:
                enhanced = f"{role} with {' and '.join(skills)}"
                suggestions.insert(1, QuerySuggestion(
                    query=enhanced,
                    score=0.85,
                    source="enhanced",
                    times_used=0
                ))

        return suggestions[:limit]

    def _calculate_score(self, match: dict, partial_query: str) -> float:
        """Calculate relevance score for a match."""
        score = 0.5  # Base score

        # Boost for history matches
        if match["source"] == "history":
            score += 0.3

        # Boost for popularity
        count = match.get("count", 1)
        score += min(0.2, count * 0.02)

        # Boost for exact prefix match
        if match["query"].lower().startswith(partial_query.lower()):
            score += 0.1

        return min(1.0, score)

    def suggest_with_skills(
        self,
        role_title: str,
        limit: int = 5
    ) -> list[str]:
        """
        Suggest query variations with common skills.

        Example:
            suggest_with_skills("ML Engineer")
            -> ["ML Engineer", "ML Engineer with PyTorch", "ML Engineer Python"]
        """
        suggestions = [role_title]

        # Get skills for this role
        skills = ROLE_SKILL_PATTERNS.get(role_title, [])

        for skill in skills[:limit-1]:
            suggestions.append(f"{role_title} with {skill}")

        return suggestions


# =============================================================================
# DATABASE MIGRATION
# =============================================================================

MIGRATION_SQL = """
-- Search history for autocomplete
CREATE TABLE IF NOT EXISTS search_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    query TEXT NOT NULL,
    role_title TEXT,
    required_skills TEXT[],
    results_count INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_search_history_company ON search_history(company_id);
CREATE INDEX idx_search_history_query ON search_history(query);
CREATE INDEX idx_search_history_created ON search_history(created_at DESC);
"""
