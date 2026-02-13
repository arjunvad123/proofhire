"""
Query Generator

Uses LLM to generate intelligent natural language queries for Clado/PDL
based on role requirements and network context.
"""

import json
from typing import Optional
from openai import AsyncOpenAI
from pydantic import BaseModel
from app.config import settings


class GeneratedQuery(BaseModel):
    """A generated search query with context."""

    query: str  # Natural language query for Clado
    intent: str  # What we're trying to find
    priority: int  # 1-5, higher = more important
    expected_results: str  # What kind of candidates we expect


class QuerySet(BaseModel):
    """Set of queries to run for comprehensive search."""

    primary_query: GeneratedQuery  # Main search
    expansion_queries: list[GeneratedQuery]  # Additional angles
    network_context_used: list[str]  # What network info influenced queries


class QueryGenerator:
    """
    Generates smart search queries using LLM.

    Takes role requirements + network context and produces
    natural language queries optimized for Clado/PDL APIs.
    """

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate_queries(
        self,
        role_title: str,
        required_skills: list[str],
        preferred_skills: list[str] = [],
        location: Optional[str] = None,
        years_experience: Optional[int] = None,
        network_companies: list[str] = [],  # Companies in founder's network
        network_schools: list[str] = [],    # Schools in founder's network
        company_stage: Optional[str] = None,
        additional_context: Optional[str] = None
    ) -> QuerySet:
        """
        Generate a set of search queries based on role and network.

        Args:
            role_title: The position title (e.g., "Senior React Developer")
            required_skills: Must-have skills
            preferred_skills: Nice-to-have skills
            location: Preferred location
            years_experience: Minimum years of experience
            network_companies: Companies that founder has connections at
            network_schools: Schools that founder has connections at
            company_stage: startup, growth, enterprise
            additional_context: Any other relevant info

        Returns:
            QuerySet with primary and expansion queries
        """

        prompt = self._build_prompt(
            role_title=role_title,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            location=location,
            years_experience=years_experience,
            network_companies=network_companies,
            network_schools=network_schools,
            company_stage=company_stage,
            additional_context=additional_context
        )

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cheap for query generation
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert recruiter who writes natural language search queries for people databases.

Your queries will be used to search a database of 800M+ professional profiles using parallel LLM inference.

Write queries that are:
1. Natural and specific (not keyword soup)
2. Include company/school names when relevant for warm paths
3. Focus on verifiable signals (titles, companies, skills)
4. Avoid subjective terms (passionate, rockstar, ninja)

Output valid JSON only."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            return QuerySet(
                primary_query=GeneratedQuery(**result["primary_query"]),
                expansion_queries=[
                    GeneratedQuery(**q) for q in result.get("expansion_queries", [])
                ],
                network_context_used=result.get("network_context_used", [])
            )

        except Exception as e:
            print(f"Query generation error: {e}")
            # Fallback to simple query
            return self._fallback_queries(role_title, required_skills, location)

    def _build_prompt(
        self,
        role_title: str,
        required_skills: list[str],
        preferred_skills: list[str],
        location: Optional[str],
        years_experience: Optional[int],
        network_companies: list[str],
        network_schools: list[str],
        company_stage: Optional[str],
        additional_context: Optional[str]
    ) -> str:
        """Build the LLM prompt for query generation."""

        prompt = f"""Generate search queries for finding candidates.

ROLE: {role_title}
REQUIRED SKILLS: {', '.join(required_skills) if required_skills else 'Not specified'}
PREFERRED SKILLS: {', '.join(preferred_skills) if preferred_skills else 'Not specified'}
LOCATION: {location or 'Any'}
EXPERIENCE: {f'{years_experience}+ years' if years_experience else 'Not specified'}
COMPANY STAGE: {company_stage or 'Not specified'}

NETWORK CONTEXT (founder has connections at these companies/schools):
- Companies: {', '.join(network_companies[:10]) if network_companies else 'None provided'}
- Schools: {', '.join(network_schools[:10]) if network_schools else 'None provided'}

{f'ADDITIONAL CONTEXT: {additional_context}' if additional_context else ''}

Generate queries that:
1. Find candidates with the right skills and experience
2. Prioritize people from network-adjacent companies/schools (warm intros possible)
3. Include backup queries for broader search

Output JSON in this format:
{{
  "primary_query": {{
    "query": "natural language search query",
    "intent": "what we're looking for",
    "priority": 1,
    "expected_results": "type of candidates expected"
  }},
  "expansion_queries": [
    {{
      "query": "alternative angle query",
      "intent": "why this angle",
      "priority": 2,
      "expected_results": "what we might find"
    }}
  ],
  "network_context_used": ["company1", "school1"]
}}

Generate 1 primary query and 2-3 expansion queries."""

        return prompt

    def _fallback_queries(
        self,
        role_title: str,
        required_skills: list[str],
        location: Optional[str]
    ) -> QuerySet:
        """Fallback queries when LLM fails."""

        skills_str = ', '.join(required_skills[:3]) if required_skills else ''
        location_str = f' in {location}' if location else ''

        primary = f"{role_title} with {skills_str} experience{location_str}"

        return QuerySet(
            primary_query=GeneratedQuery(
                query=primary,
                intent=f"Find {role_title}s",
                priority=1,
                expected_results="Candidates matching core requirements"
            ),
            expansion_queries=[
                GeneratedQuery(
                    query=f"Senior {role_title}{location_str}",
                    intent="Find experienced candidates",
                    priority=2,
                    expected_results="More senior candidates"
                )
            ],
            network_context_used=[]
        )


# Example usage for UGC creators:
async def example_ugc_query():
    """Example: Generate queries for finding UGC creators."""

    generator = QueryGenerator()

    queries = await generator.generate_queries(
        role_title="UGC Creator",
        required_skills=["Content Creation", "TikTok", "Video Production"],
        preferred_skills=["D2C Brand Experience", "Instagram"],
        location="United States",
        years_experience=2,
        network_companies=["Glossier", "Allbirds", "Warby Parker", "Casper"],
        network_schools=["UCLA", "USC", "NYU"],
        company_stage="startup",
        additional_context="Looking for someone who can create authentic product content for a D2C skincare brand"
    )

    print("Primary Query:", queries.primary_query.query)
    print("\nExpansion Queries:")
    for q in queries.expansion_queries:
        print(f"  - {q.query} (intent: {q.intent})")
    print("\nNetwork context used:", queries.network_context_used)

    return queries


# Singleton instance
query_generator = QueryGenerator()
