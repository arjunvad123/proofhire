"""
Network Index Service

Indexes the founder's network by company, school, and skills
to enable warm path finding for external candidates.

This is the bridge between the network and external search results.
"""

from typing import Optional
from collections import defaultdict
from pydantic import BaseModel
from app.services.company_db import company_db


class NetworkContact(BaseModel):
    """A contact in the founder's network."""

    person_id: str
    full_name: str
    linkedin_url: Optional[str] = None
    current_company: Optional[str] = None
    current_title: Optional[str] = None
    # Experience data for temporal overlap checking
    experience: list[dict] = []  # [{company, title, start_date, end_date}]


class CompanyIndex(BaseModel):
    """Index entry for a company."""

    company_name: str
    normalized_name: str  # Lowercase, stripped
    contacts: list[NetworkContact]
    count: int


class SchoolIndex(BaseModel):
    """Index entry for a school."""

    school_name: str
    normalized_name: str
    contacts: list[NetworkContact]
    count: int


class NetworkIndex(BaseModel):
    """Full network index for warm path finding."""

    company_id: str
    total_contacts: int
    companies: dict[str, CompanyIndex]  # normalized_name -> index
    schools: dict[str, SchoolIndex]  # normalized_name -> index
    skills: dict[str, list[NetworkContact]]  # skill -> contacts


class NetworkIndexService:
    """
    Builds and queries network indices for warm path finding.

    The index allows O(1) lookup of:
    - Which contacts worked at company X
    - Which contacts went to school Y
    - Which contacts have skill Z
    """

    def __init__(self):
        self._cache: dict[str, NetworkIndex] = {}

    async def build_index(self, company_id: str, force_rebuild: bool = False) -> NetworkIndex:
        """
        Build the network index for a company.

        Args:
            company_id: The company's UUID
            force_rebuild: Rebuild even if cached

        Returns:
            NetworkIndex with all company/school/skill mappings
        """
        # Check cache
        if not force_rebuild and company_id in self._cache:
            return self._cache[company_id]

        # Fetch all people in network
        people = await company_db.get_people(company_id, limit=5000)

        # Fetch enrichments for experience/education
        enrichments = await self._get_enrichments(company_id)

        # Build indices
        companies: dict[str, CompanyIndex] = {}
        schools: dict[str, SchoolIndex] = {}
        skills: dict[str, list[NetworkContact]] = defaultdict(list)

        for person in people:
            # Handle both dict and Pydantic model
            if hasattr(person, 'model_dump'):
                p = person.model_dump()
            elif hasattr(person, 'dict'):
                p = person.dict()
            else:
                p = person if isinstance(person, dict) else {}

            # Get enrichment for this person (need it early for contact creation)
            person_id = str(p.get("id", ""))
            enrichment = enrichments.get(person_id, {})

            contact = NetworkContact(
                person_id=person_id,
                full_name=p.get("full_name") or "Unknown",
                linkedin_url=p.get("linkedin_url"),
                current_company=p.get("current_company"),
                current_title=p.get("current_title"),
                experience=enrichment.get("experience", [])
            )

            # Index by current company
            current_company = p.get("current_company")
            if current_company:
                normalized = self._normalize(current_company)
                if normalized not in companies:
                    companies[normalized] = CompanyIndex(
                        company_name=current_company,
                        normalized_name=normalized,
                        contacts=[],
                        count=0
                    )
                companies[normalized].contacts.append(contact)
                companies[normalized].count += 1


            # Index by past companies (from experience)
            for exp in enrichment.get("experience", []):
                company_name = exp.get("company")
                if company_name:
                    normalized = self._normalize(company_name)
                    if normalized not in companies:
                        companies[normalized] = CompanyIndex(
                            company_name=company_name,
                            normalized_name=normalized,
                            contacts=[],
                            count=0
                        )
                    # Avoid duplicates
                    if contact not in companies[normalized].contacts:
                        companies[normalized].contacts.append(contact)
                        companies[normalized].count += 1

            # Index by schools (from education)
            for edu in enrichment.get("education", []):
                school_name = edu.get("school")
                if school_name:
                    normalized = self._normalize(school_name)
                    if normalized not in schools:
                        schools[normalized] = SchoolIndex(
                            school_name=school_name,
                            normalized_name=normalized,
                            contacts=[],
                            count=0
                        )
                    if contact not in schools[normalized].contacts:
                        schools[normalized].contacts.append(contact)
                        schools[normalized].count += 1

            # Index by skills
            for skill in enrichment.get("skills", []):
                skill_name = skill.get("name") if isinstance(skill, dict) else str(skill)
                if skill_name:
                    normalized = self._normalize(skill_name)
                    if contact not in skills[normalized]:
                        skills[normalized].append(contact)

        index = NetworkIndex(
            company_id=company_id,
            total_contacts=len(people),
            companies=companies,
            schools=schools,
            skills=dict(skills)
        )

        # Cache it
        self._cache[company_id] = index

        return index

    async def _get_enrichments(self, company_id: str) -> dict:
        """Fetch all person enrichments for a company's network."""
        try:
            # Get enrichments from Supabase
            enrichments = await company_db._request(
                "GET",
                "person_enrichments",
                params={
                    "select": "person_id,experience,education,skills"
                }
            )

            # Index by person_id
            return {e.get("person_id"): e for e in enrichments}
        except Exception as e:
            print(f"Error fetching enrichments: {e}")
            return {}

    def _normalize(self, text: str) -> str:
        """Normalize company/school/skill names for matching."""
        if not text:
            return ""
        # Lowercase, strip, remove common suffixes
        normalized = text.lower().strip()
        for suffix in [" inc", " inc.", " llc", " ltd", " corp", " corporation"]:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
        return normalized

    def find_company_contacts(
        self,
        index: NetworkIndex,
        company_name: str
    ) -> list[NetworkContact]:
        """Find contacts who worked at a specific company."""
        normalized = self._normalize(company_name)

        # Exact match
        if normalized in index.companies:
            return index.companies[normalized].contacts

        # Fuzzy match (contains)
        for key, company_index in index.companies.items():
            if normalized in key or key in normalized:
                return company_index.contacts

        return []

    def find_school_contacts(
        self,
        index: NetworkIndex,
        school_name: str
    ) -> list[NetworkContact]:
        """Find contacts who went to a specific school."""
        normalized = self._normalize(school_name)

        # Exact match
        if normalized in index.schools:
            return index.schools[normalized].contacts

        # Fuzzy match
        for key, school_index in index.schools.items():
            if normalized in key or key in normalized:
                return school_index.contacts

        return []

    def get_top_companies(self, index: NetworkIndex, limit: int = 20) -> list[str]:
        """Get the companies with most contacts in the network."""
        sorted_companies = sorted(
            index.companies.values(),
            key=lambda x: x.count,
            reverse=True
        )
        return [c.company_name for c in sorted_companies[:limit]]

    def get_top_schools(self, index: NetworkIndex, limit: int = 20) -> list[str]:
        """Get the schools with most contacts in the network."""
        sorted_schools = sorted(
            index.schools.values(),
            key=lambda x: x.count,
            reverse=True
        )
        return [s.school_name for s in sorted_schools[:limit]]

    def get_network_stats(self, index: NetworkIndex) -> dict:
        """Get summary statistics about the network."""
        return {
            "total_contacts": index.total_contacts,
            "unique_companies": len(index.companies),
            "unique_schools": len(index.schools),
            "unique_skills": len(index.skills),
            "top_companies": self.get_top_companies(index, 5),
            "top_schools": self.get_top_schools(index, 5)
        }


# Singleton instance
network_index_service = NetworkIndexService()
