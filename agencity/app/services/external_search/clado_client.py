"""
Clado API Client

Clado.ai provides natural language people search across 800M+ profiles.
Uses parallel LLM inference to evaluate candidates against queries.

Pricing: ~$0.01 per result
"""

import httpx
from typing import Optional
from pydantic import BaseModel
from app.config import settings


class CladoProfile(BaseModel):
    """Profile returned from Clado search."""

    id: str
    full_name: str
    headline: Optional[str] = None
    location: Optional[str] = None

    # Current position
    current_title: Optional[str] = None
    current_company: Optional[str] = None

    # Experience
    experience: list[dict] = []  # [{company, title, duration, description}]

    # Education
    education: list[dict] = []  # [{school, degree, field, year}]

    # Skills and signals
    skills: list[str] = []

    # Links
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    twitter_url: Optional[str] = None
    personal_website: Optional[str] = None

    # Clado-specific
    match_score: float = 0.0  # How well they match the query
    match_explanation: Optional[str] = None  # Why Clado thinks they match


class CladoSearchResult(BaseModel):
    """Full search result from Clado."""

    profiles: list[CladoProfile]
    total_matches: int
    query_interpreted: str  # How Clado understood the query
    search_id: str  # For pagination/follow-up


class CladoClient:
    """
    Client for Clado.ai people search API.

    Clado uses natural language queries like:
    - "Software engineers who worked at Stripe"
    - "UGC creators with D2C brand experience"
    - "ML engineers who went to Stanford and worked at Google"

    The API runs parallel LLM inference to evaluate millions of profiles
    against the query and returns ranked matches.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'clado_api_key', None)
        self.base_url = "https://search.clado.ai/api"  # Clado API base URL
        self.enabled = bool(self.api_key)

    async def search(
        self,
        query: str,
        limit: int = 100,
        filters: Optional[dict] = None
    ) -> CladoSearchResult:
        """
        Search for people using natural language query.

        Args:
            query: Natural language search (e.g., "React developers in SF")
            limit: Max results to return (default 100)
            filters: Optional filters like location, company, school

        Returns:
            CladoSearchResult with matching profiles
        """
        if not self.enabled:
            return self._mock_search(query, limit)

        async with httpx.AsyncClient() as client:
            try:
                # Clado uses GET with query parameters
                response = await client.get(
                    f"{self.base_url}/search",
                    headers={
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    params={
                        "query": query,
                        "limit": limit,
                        "advanced_filtering": "true"  # Use AI filtering
                    },
                    timeout=60.0  # Clado can take time for complex queries
                )

                if response.status_code == 200:
                    data = response.json()
                    return CladoSearchResult(
                        profiles=[CladoProfile(**p) for p in data.get("profiles", [])],
                        total_matches=data.get("total_matches", 0),
                        query_interpreted=data.get("query_interpreted", query),
                        search_id=data.get("search_id", "")
                    )
                else:
                    print(f"Clado API error: {response.status_code}")
                    return CladoSearchResult(
                        profiles=[],
                        total_matches=0,
                        query_interpreted=query,
                        search_id=""
                    )

            except Exception as e:
                print(f"Clado API exception: {e}")
                return CladoSearchResult(
                    profiles=[],
                    total_matches=0,
                    query_interpreted=query,
                    search_id=""
                )

    async def enrich_profile(self, linkedin_url: str) -> Optional[CladoProfile]:
        """
        Get full profile data for a specific person.

        Args:
            linkedin_url: LinkedIn profile URL

        Returns:
            CladoProfile with full data or None
        """
        if not self.enabled:
            return None

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/enrich",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={"linkedin_url": linkedin_url},
                    timeout=30.0
                )

                if response.status_code == 200:
                    return CladoProfile(**response.json())
                return None

            except Exception as e:
                print(f"Clado enrich exception: {e}")
                return None

    def _mock_search(self, query: str, limit: int) -> CladoSearchResult:
        """
        Return mock data when API key not configured.
        Useful for development and testing.
        """
        # Parse query for mock response
        mock_profiles = []

        if "ugc" in query.lower() or "creator" in query.lower():
            mock_profiles = [
                CladoProfile(
                    id="clado-1",
                    full_name="Maya Rodriguez",
                    headline="UGC Creator | D2C Brand Partnerships",
                    location="Los Angeles, CA",
                    current_title="Freelance UGC Creator",
                    current_company="Self-Employed",
                    experience=[
                        {"company": "Glossier", "title": "Brand Ambassador", "duration": "2 years"},
                        {"company": "Self-Employed", "title": "UGC Creator", "duration": "3 years"}
                    ],
                    education=[
                        {"school": "UCLA", "degree": "BA", "field": "Communications", "year": "2020"}
                    ],
                    skills=["Content Creation", "TikTok", "Instagram", "Video Editing", "D2C Marketing"],
                    linkedin_url="https://linkedin.com/in/mayarodriguez",
                    match_score=0.92,
                    match_explanation="Strong D2C experience with Glossier, active UGC portfolio"
                ),
                CladoProfile(
                    id="clado-2",
                    full_name="Alex Kim",
                    headline="Content Creator & Social Media Strategist",
                    location="San Francisco, CA",
                    current_title="Senior Content Creator",
                    current_company="Allbirds",
                    experience=[
                        {"company": "Allbirds", "title": "Senior Content Creator", "duration": "1 year"},
                        {"company": "Warby Parker", "title": "Content Creator", "duration": "2 years"}
                    ],
                    education=[
                        {"school": "UC Berkeley", "degree": "BA", "field": "Media Studies", "year": "2019"}
                    ],
                    skills=["UGC", "Brand Storytelling", "Video Production", "Social Media"],
                    linkedin_url="https://linkedin.com/in/alexkim-content",
                    match_score=0.88,
                    match_explanation="D2C experience at Allbirds and Warby Parker"
                ),
                CladoProfile(
                    id="clado-3",
                    full_name="Jordan Lee",
                    headline="TikTok Creator | 500K+ Followers",
                    location="New York, NY",
                    current_title="Influencer & UGC Creator",
                    current_company="Independent",
                    experience=[
                        {"company": "Independent", "title": "TikTok Creator", "duration": "4 years"},
                        {"company": "Multiple D2C Brands", "title": "UGC Partner", "duration": "2 years"}
                    ],
                    skills=["TikTok", "UGC", "Viral Content", "Brand Partnerships"],
                    linkedin_url="https://linkedin.com/in/jordanlee-creator",
                    twitter_url="https://twitter.com/jordanleecreates",
                    match_score=0.85,
                    match_explanation="Large TikTok following, multiple D2C brand partnerships"
                )
            ]
        elif "engineer" in query.lower() or "developer" in query.lower():
            mock_profiles = [
                CladoProfile(
                    id="clado-4",
                    full_name="Sarah Chen",
                    headline="Senior Software Engineer | Ex-Stripe",
                    location="San Francisco, CA",
                    current_title="Staff Engineer",
                    current_company="Figma",
                    experience=[
                        {"company": "Figma", "title": "Staff Engineer", "duration": "2 years"},
                        {"company": "Stripe", "title": "Senior Engineer", "duration": "3 years"},
                        {"company": "Google", "title": "Software Engineer", "duration": "2 years"}
                    ],
                    education=[
                        {"school": "Stanford", "degree": "MS", "field": "Computer Science", "year": "2017"}
                    ],
                    skills=["Python", "TypeScript", "React", "Distributed Systems", "API Design"],
                    linkedin_url="https://linkedin.com/in/sarahchen-eng",
                    github_url="https://github.com/sarahchen",
                    match_score=0.95,
                    match_explanation="Strong pedigree: Figma, Stripe, Google. Stanford CS."
                ),
                CladoProfile(
                    id="clado-5",
                    full_name="David Park",
                    headline="Full Stack Developer | React + Node",
                    location="Seattle, WA",
                    current_title="Senior Developer",
                    current_company="Airbnb",
                    experience=[
                        {"company": "Airbnb", "title": "Senior Developer", "duration": "3 years"},
                        {"company": "Microsoft", "title": "Software Engineer", "duration": "2 years"}
                    ],
                    education=[
                        {"school": "University of Washington", "degree": "BS", "field": "Computer Science", "year": "2018"}
                    ],
                    skills=["React", "Node.js", "TypeScript", "GraphQL", "AWS"],
                    linkedin_url="https://linkedin.com/in/davidpark-dev",
                    github_url="https://github.com/davidpark",
                    match_score=0.89,
                    match_explanation="Airbnb and Microsoft experience, strong full-stack skills"
                )
            ]
        else:
            # Generic response
            mock_profiles = [
                CladoProfile(
                    id="clado-generic-1",
                    full_name="Sample Candidate",
                    headline="Professional matching your query",
                    location="United States",
                    match_score=0.75,
                    match_explanation=f"Matched query: {query}"
                )
            ]

        return CladoSearchResult(
            profiles=mock_profiles[:limit],
            total_matches=len(mock_profiles),
            query_interpreted=query,
            search_id="mock-search-001"
        )


# Singleton instance
clado_client = CladoClient()
