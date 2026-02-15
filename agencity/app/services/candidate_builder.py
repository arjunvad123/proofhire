"""
Builds UnifiedCandidate from database records.

Handles incomplete data gracefully - works with just people table,
or enriched with person_enrichments.
"""

from typing import Optional
from app.models.curation import UnifiedCandidate


class CandidateBuilder:
    """
    Builds UnifiedCandidate from Supabase data.

    Priority:
    1. person_enrichments (if exists)
    2. people table (always exists)
    3. Fill missing with empty/None
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def build(self, person_id: str) -> UnifiedCandidate:
        """
        Build unified candidate profile.

        Args:
            person_id: UUID of person in people table

        Returns:
            UnifiedCandidate with all available data
        """

        # Fetch person (always exists)
        person_response = self.supabase.table('people')\
            .select('*')\
            .eq('id', person_id)\
            .single()\
            .execute()

        person = person_response.data

        # Fetch enrichment (may not exist)
        enrichment_response = self.supabase.table('person_enrichments')\
            .select('*')\
            .eq('person_id', person_id)\
            .execute()

        enrichment = enrichment_response.data[0] if enrichment_response.data else None

        # Build unified profile
        candidate = UnifiedCandidate(
            person_id=person['id'],
            full_name=person['full_name'],
            email=person.get('email'),
            linkedin_url=person.get('linkedin_url'),
            github_url=person.get('github_url'),
            headline=person.get('headline'),
            location=person.get('location'),
            current_company=person.get('current_company'),
            current_title=person.get('current_title'),

            # From enrichment (empty if not enriched)
            skills=self._extract_skills(enrichment),
            experience=self._extract_experience(enrichment),
            education=self._extract_education(enrichment),
            projects=self._extract_projects(enrichment),

            # Metadata
            enrichment_source=enrichment.get('enrichment_source') if enrichment else None,
            has_enrichment=enrichment is not None
        )

        # Calculate completeness
        candidate.data_completeness = candidate.calculate_completeness()

        return candidate

    async def build_many(self, person_ids: list[str]) -> list[UnifiedCandidate]:
        """Build multiple candidates in batch (optimized)."""
        if not person_ids:
            return []

        # Batch large queries to avoid PostgreSQL limits
        # Max 500 IDs per query to prevent "JSON could not be generated" errors
        # (Supabase has limits on response size for SELECT *)
        BATCH_SIZE = 500

        print(f"📊 Building {len(person_ids)} candidates in batches of {BATCH_SIZE}...")

        all_people = []
        all_enrichments = []

        for i in range(0, len(person_ids), BATCH_SIZE):
            batch_ids = person_ids[i:i + BATCH_SIZE]

            # Fetch people in batch
            people_response = self.supabase.table('people')\
                .select('*')\
                .in_('id', batch_ids)\
                .execute()
            all_people.extend(people_response.data)

            # Fetch enrichments in batch
            enrichments_response = self.supabase.table('person_enrichments')\
                .select('*')\
                .in_('person_id', batch_ids)\
                .execute()
            all_enrichments.extend(enrichments_response.data)

        # Index enrichments by person_id for quick lookup
        enrichments_by_id = {
            e['person_id']: e
            for e in all_enrichments
        } if all_enrichments else {}

        # Build candidates
        candidates = []
        for person in all_people:
            enrichment = enrichments_by_id.get(person['id'])

            candidate = UnifiedCandidate(
                person_id=person['id'],
                full_name=person['full_name'],
                email=person.get('email'),
                linkedin_url=person.get('linkedin_url'),
                github_url=person.get('github_url'),
                headline=person.get('headline'),
                location=person.get('location'),
                current_company=person.get('current_company'),
                current_title=person.get('current_title'),

                # From enrichment (empty if not enriched)
                skills=self._extract_skills(enrichment),
                experience=self._extract_experience(enrichment),
                education=self._extract_education(enrichment),
                projects=self._extract_projects(enrichment),

                # Metadata
                enrichment_source=enrichment.get('enrichment_source') if enrichment else None,
                has_enrichment=enrichment is not None
            )

            # Calculate completeness
            candidate.data_completeness = candidate.calculate_completeness()
            candidates.append(candidate)

        return candidates

    def _extract_skills(self, enrichment: Optional[dict]) -> list[str]:
        """Extract skills from enrichment."""
        if not enrichment or not enrichment.get('skills'):
            return []

        skills = enrichment['skills']

        # Handle both list of strings and list of dicts
        normalized = []
        for skill in skills:
            if isinstance(skill, dict):
                normalized.append(skill.get('name', str(skill)))
            else:
                normalized.append(str(skill))

        # Deduplicate
        return list(set(normalized))

    def _extract_experience(self, enrichment: Optional[dict]) -> list[dict]:
        """Extract experience from enrichment."""
        if not enrichment or not enrichment.get('experience'):
            return []

        return enrichment['experience']

    def _extract_education(self, enrichment: Optional[dict]) -> list[dict]:
        """Extract education from enrichment."""
        if not enrichment or not enrichment.get('education'):
            return []

        return enrichment['education']

    def _extract_projects(self, enrichment: Optional[dict]) -> list[dict]:
        """Extract projects from enrichment."""
        if not enrichment or not enrichment.get('projects'):
            return []

        return enrichment['projects']
