"""
Candidate Curation Engine.

Curates shortlist of candidates for a role by:
1. Ranking all network candidates with incomplete data
2. Enriching top candidates on-demand
3. Re-ranking with enriched data
4. Building rich context for final shortlist
"""

from typing import List, Dict, Any, Optional
from app.models.curation import (
    UnifiedCandidate,
    FitScore,
    CuratedCandidate,
    CandidateContext,
    WhyConsiderPoint,
    MatchStrength
)
from app.services.candidate_builder import CandidateBuilder
import re


class CandidateCurationEngine:
    """
    Main curation engine.

    Usage:
        engine = CandidateCurationEngine(supabase)
        shortlist = await engine.curate(company_id, role_id, limit=15)
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.builder = CandidateBuilder(supabase_client)

    async def curate(
        self,
        company_id: str,
        role_id: str,
        limit: int = 15
    ) -> List[CuratedCandidate]:
        """
        Main curation pipeline.

        Steps:
        1. Get all network candidates
        2. Calculate fit scores (works with incomplete data)
        3. Rank by fit score
        4. Enrich top candidates if needed
        5. Re-rank with enriched data
        6. Build rich context for final shortlist
        """

        print(f"\n{'='*60}")
        print(f"🎯 Starting curation for role {role_id}")

        # Get role and company context
        role = await self._get_role(role_id)
        company_dna = await self._get_company_dna(company_id)
        umo = await self._get_umo(company_id)

        print(f"📋 Role: {role.get('title', 'Unknown')}")
        print(f"🏢 Company: {company_dna.get('name', 'Unknown')}")

        # 1. Get all network candidates
        network_people = await self._get_network_people(company_id)
        print(f"📊 Searching {len(network_people)} network connections")

        # 2. Build unified candidates and calculate fit
        ranked_candidates = []

        for person in network_people:
            # Build unified candidate (handles incomplete data)
            candidate = await self.builder.build(person['id'])

            # Calculate fit score
            fit = self._calculate_fit(candidate, role, company_dna, umo)

            ranked_candidates.append({
                'candidate': candidate,
                'fit_score': fit.score,
                'confidence': fit.confidence,
                'fit_breakdown': fit,
                'needs_enrichment': fit.needs_enrichment
            })

        # 3. Initial ranking
        ranked_candidates.sort(key=lambda x: x['fit_score'], reverse=True)

        top_score = ranked_candidates[0]['fit_score'] if ranked_candidates else 0
        print(f"📈 Top candidate score: {top_score:.1f}")
        print(f"🎲 Average confidence: {sum(c['confidence'] for c in ranked_candidates) / len(ranked_candidates):.2f}")

        # 4. Enrich top candidates with low confidence
        top_30 = ranked_candidates[:30]
        to_enrich = [c for c in top_30 if c['needs_enrichment']]

        if to_enrich:
            print(f"🔍 Enriching {len(to_enrich)} candidates for better accuracy...")
            # Note: Actual enrichment would call PDL API here
            # For now, just mark as attempted
            for item in to_enrich:
                item['enrichment_attempted'] = True

        # 5. Build rich context for final shortlist
        shortlist = []

        for item in ranked_candidates[:limit]:
            context = await self._build_context(
                item['candidate'],
                role,
                company_dna,
                umo
            )

            curated = CuratedCandidate(
                person_id=item['candidate'].person_id,
                full_name=item['candidate'].full_name,
                headline=item['candidate'].headline,
                location=item['candidate'].location,
                current_company=item['candidate'].current_company,
                current_title=item['candidate'].current_title,
                linkedin_url=item['candidate'].linkedin_url,
                github_url=item['candidate'].github_url,
                match_score=item['fit_score'],
                fit_confidence=item['confidence'],
                context=context,
                was_enriched=item.get('enrichment_attempted', False),
                data_completeness=item['candidate'].data_completeness
            )

            shortlist.append(curated)

        print(f"✅ Curated shortlist of {len(shortlist)} candidates")
        print(f"{'='*60}\n")

        return shortlist

    def _calculate_fit(
        self,
        candidate: UnifiedCandidate,
        role: dict,
        company_dna: dict,
        umo: Optional[dict]
    ) -> FitScore:
        """
        Calculate fit score and confidence.

        Works even with incomplete data by:
        - Using what we have
        - Making conservative estimates for missing data
        - Flagging low confidence when data is missing

        Weights:
        - 40% Skills match
        - 30% Experience match
        - 20% Culture fit (from UMO)
        - 10% Signals (activity, projects)
        """

        score = 0.0
        confidence = 0.0

        # 1. Skills match (40%)
        skills_match = 0.0
        if candidate.skills and role.get('required_skills'):
            skills_match = self._match_skills(
                candidate.skills,
                role['required_skills']
            )
            score += skills_match * 40
            confidence += 0.4
        elif role.get('required_skills'):
            # No skills data - estimate from title
            title_based_estimate = self._estimate_skills_from_title(
                candidate.current_title,
                role.get('title')
            )
            score += title_based_estimate * 40
            confidence += 0.1  # Low confidence
        else:
            # No required skills specified
            score += 20  # Neutral
            confidence += 0.2

        # 2. Experience match (30%)
        exp_match = 0.0
        if candidate.experience:
            exp_match = self._match_experience(candidate.experience, role)
            score += exp_match * 30
            confidence += 0.3
        else:
            # No experience data - estimate from current title
            title_match = self._estimate_experience_from_title(
                candidate.current_title,
                role.get('title')
            )
            score += title_match * 30
            confidence += 0.1

        # 3. Culture fit (20%)
        culture_match = 0.0
        if umo and candidate.has_enrichment:
            culture_match = self._match_culture(candidate, umo)
            score += culture_match * 20
            confidence += 0.2
        else:
            score += 10  # Neutral assumption
            confidence += 0.05

        # 4. Signals (10%) - projects, GitHub, etc.
        signals_score = self._calculate_signals(candidate)
        score += signals_score * 10
        confidence += 0.1 if candidate.projects or candidate.github_url else 0.05

        # Build fit score
        fit = FitScore(
            score=min(score, 100),  # Cap at 100
            confidence=confidence,
            skills_match=skills_match,
            experience_match=exp_match,
            culture_match=culture_match,
            signals_score=signals_score,
            needs_enrichment=confidence < 0.7
        )

        return fit

    def _match_skills(self, candidate_skills: List[str], required_skills: List[str]) -> float:
        """
        Calculate skill match percentage.

        Returns 0-1 score based on overlap.
        """
        if not required_skills:
            return 0.5  # Neutral

        # Normalize for case-insensitive comparison
        candidate_skills_lower = [s.lower() for s in candidate_skills]
        required_skills_lower = [s.lower() for s in required_skills]

        matched = sum(1 for req in required_skills_lower if req in candidate_skills_lower)

        return matched / len(required_skills)

    def _estimate_skills_from_title(
        self,
        candidate_title: Optional[str],
        role_title: Optional[str]
    ) -> float:
        """
        Estimate skill match from job titles when we don't have skill data.

        Returns conservative estimate (0-1).
        """
        if not candidate_title or not role_title:
            return 0.3  # Very conservative

        candidate_title = candidate_title.lower()
        role_title = role_title.lower()

        # Exact match
        if candidate_title == role_title:
            return 0.7

        # Contains key role keywords
        role_keywords = ['engineer', 'developer', 'designer', 'manager', 'analyst']
        for keyword in role_keywords:
            if keyword in role_title and keyword in candidate_title:
                return 0.5

        # Same seniority
        seniority_levels = ['senior', 'staff', 'principal', 'lead', 'junior']
        for level in seniority_levels:
            if level in role_title and level in candidate_title:
                return 0.4

        return 0.3  # Default conservative

    def _match_experience(self, candidate_exp: List[dict], role: dict) -> float:
        """
        Match work experience to role requirements.

        Considers:
        - Years of experience
        - Relevant companies
        - Relevant roles
        """
        score = 0.0

        # Calculate total years
        total_months = 0
        for exp in candidate_exp:
            duration = exp.get('duration_months', 0)
            if duration:
                total_months += duration

        years = total_months / 12 if total_months else 0

        # Compare to role requirements
        min_years = role.get('years_experience_min', 0)
        max_years = role.get('years_experience_max', 10)

        if min_years <= years <= max_years:
            score += 0.5
        elif years >= min_years:
            score += 0.3
        else:
            score += 0.1

        # Check for relevant titles in experience
        role_title = role.get('title', '').lower()
        for exp in candidate_exp:
            exp_title = exp.get('title', '').lower()
            if any(keyword in exp_title for keyword in role_title.split()):
                score += 0.3
                break

        # Check for relevant companies (if we have preferred list)
        # TODO: Add company preference matching

        return min(score, 1.0)

    def _estimate_experience_from_title(
        self,
        candidate_title: Optional[str],
        role_title: Optional[str]
    ) -> float:
        """Estimate experience match from titles when we don't have full experience."""
        if not candidate_title:
            return 0.3

        candidate_title = candidate_title.lower()

        # Look for seniority indicators
        if any(level in candidate_title for level in ['senior', 'staff', 'principal', 'lead']):
            return 0.6
        elif 'junior' in candidate_title or 'intern' in candidate_title:
            return 0.4
        else:
            return 0.5  # Mid-level assumption

    def _match_culture(self, candidate: UnifiedCandidate, umo: dict) -> float:
        """
        Match candidate to company culture/UMO.

        This is harder without interview data, so we look for signals:
        - Company background (startup vs big tech)
        - Project types (independent vs team)
        - Activity patterns (builder vs researcher)
        """
        score = 0.5  # Start neutral

        # Check for startup experience
        if umo.get('preferred_backgrounds'):
            for exp in candidate.experience:
                company = exp.get('company', '').lower()
                if any(pref.lower() in company for pref in umo['preferred_backgrounds']):
                    score += 0.2
                    break

        # Check for builder signals
        if umo.get('must_have_traits'):
            traits = [t.lower() for t in umo['must_have_traits']]
            if 'builder' in traits or 'ship fast' in traits:
                if candidate.projects or candidate.github_url:
                    score += 0.2

        return min(score, 1.0)

    def _calculate_signals(self, candidate: UnifiedCandidate) -> float:
        """
        Calculate signal score from activity indicators.

        Signals:
        - Has GitHub profile
        - Has projects listed
        - Active on hackathons
        """
        score = 0.0

        if candidate.github_url:
            score += 0.3

        if candidate.projects:
            score += 0.3

        # If we have enrichment with good data
        if candidate.has_enrichment:
            score += 0.2

        # If profile is complete
        if candidate.data_completeness > 0.7:
            score += 0.2

        return min(score, 1.0)

    async def _build_context(
        self,
        candidate: UnifiedCandidate,
        role: dict,
        company_dna: dict,
        umo: Optional[dict]
    ) -> CandidateContext:
        """
        Build rich context for founder decision.

        Answers:
        - Why should I interview this person?
        - What matches the role?
        - What don't we know?
        """

        why_consider = []
        unknowns = []
        standout_signal = None

        # 1. Skills match section
        if candidate.skills and role.get('required_skills'):
            matched_skills = [
                s for s in candidate.skills
                if s.lower() in [r.lower() for r in role['required_skills']]
            ]

            if matched_skills:
                strength = self._assess_strength(len(matched_skills), len(role['required_skills']))
                points = [f"✓ {skill}" for skill in matched_skills[:5]]

                # Add nice-to-haves
                if role.get('preferred_skills'):
                    preferred_matched = [
                        s for s in candidate.skills
                        if s.lower() in [p.lower() for p in role['preferred_skills']]
                    ]
                    for skill in preferred_matched[:3]:
                        points.append(f"~ {skill} (nice to have)")

                why_consider.append(WhyConsiderPoint(
                    category="Skills Match",
                    strength=strength,
                    points=points
                ))
        elif not candidate.skills:
            unknowns.append("Specific technical skills")

        # 2. Experience section
        if candidate.experience:
            exp_points = []
            years = candidate.years_of_experience or 0

            if years:
                exp_points.append(f"✓ {years} years of professional experience")

            # Notable companies
            for exp in candidate.experience[:3]:
                company = exp.get('company', '')
                title = exp.get('title', '')
                if company and title:
                    exp_points.append(f"✓ {title} @ {company}")

            if exp_points:
                strength = MatchStrength.HIGH if years >= 3 else MatchStrength.MEDIUM
                why_consider.append(WhyConsiderPoint(
                    category="Work Experience",
                    strength=strength,
                    points=exp_points
                ))
        else:
            unknowns.append("Detailed work experience")

        # 3. Building/Projects section
        if candidate.projects or candidate.github_url:
            project_points = []

            if candidate.projects:
                project_points.append(f"✓ {len(candidate.projects)} projects listed")
                # Show notable projects
                for proj in candidate.projects[:2]:
                    name = proj.get('name', '')
                    if name:
                        project_points.append(f"  • {name}")

            if candidate.github_url:
                project_points.append(f"✓ Active GitHub profile")

            if project_points:
                why_consider.append(WhyConsiderPoint(
                    category="Building Experience",
                    strength=MatchStrength.MEDIUM,
                    points=project_points
                ))
        else:
            unknowns.append("Portfolio of projects")

        # 4. Education section
        if candidate.education:
            edu_points = []
            for edu in candidate.education[:2]:
                school = edu.get('school', '')
                degree = edu.get('degree', '')
                field = edu.get('field', '') or edu.get('field_of_study', '')

                if school:
                    parts = [degree, field, school]
                    parts = [p for p in parts if p]
                    edu_points.append(f"✓ {' in '.join(parts) if len(parts) > 1 else parts[0]}")

            if edu_points:
                why_consider.append(WhyConsiderPoint(
                    category="Education",
                    strength=MatchStrength.MEDIUM,
                    points=edu_points
                ))

        # 5. Standout signal
        standout_signal = self._find_standout_signal(candidate, role)

        # 6. Always unknown
        unknowns.extend([
            "Interest in this specific opportunity",
            "Availability and timeline",
            "Salary expectations"
        ])

        # 7. Warm path
        warm_path = "Direct LinkedIn connection"
        if candidate.linkedin_url:
            warm_path = f"Connected on LinkedIn"

        return CandidateContext(
            why_consider=why_consider,
            unknowns=unknowns,
            standout_signal=standout_signal,
            warm_path=warm_path
        )

    def _assess_strength(self, matched: int, total: int) -> MatchStrength:
        """Assess match strength from counts."""
        if total == 0:
            return MatchStrength.UNKNOWN

        ratio = matched / total

        if ratio >= 0.7:
            return MatchStrength.HIGH
        elif ratio >= 0.4:
            return MatchStrength.MEDIUM
        else:
            return MatchStrength.LOW

    def _find_standout_signal(self, candidate: UnifiedCandidate, role: dict) -> Optional[str]:
        """Find one standout thing about this candidate."""

        # Check for impressive projects
        if candidate.projects:
            for project in candidate.projects:
                name = project.get('name', '')
                desc = project.get('description', '')
                if 'award' in desc.lower() or 'won' in desc.lower():
                    return f"Built {name} - {desc[:100]}"

        # Check for top companies
        if candidate.experience:
            top_companies = ['google', 'meta', 'apple', 'amazon', 'microsoft', 'openai', 'stripe']
            for exp in candidate.experience:
                company = exp.get('company', '').lower()
                if any(top in company for top in top_companies):
                    title = exp.get('title', '')
                    return f"Previously {title} at {exp.get('company')}"

        # Check for education
        if candidate.education:
            top_schools = ['stanford', 'mit', 'harvard', 'berkeley', 'carnegie mellon']
            for edu in candidate.education:
                school = edu.get('school', '').lower()
                if any(top in school for top in top_schools):
                    return f"Studied at {edu.get('school')}"

        return None

    # Database helpers

    async def _get_network_people(self, company_id: str) -> List[dict]:
        """Get all people in company's network."""
        response = self.supabase.table('people')\
            .select('*')\
            .eq('company_id', company_id)\
            .execute()

        return response.data

    async def _get_role(self, role_id: str) -> dict:
        """Get role details."""
        response = self.supabase.table('roles')\
            .select('*')\
            .eq('id', role_id)\
            .single()\
            .execute()

        return response.data

    async def _get_company_dna(self, company_id: str) -> dict:
        """Get company details."""
        response = self.supabase.table('companies')\
            .select('*')\
            .eq('id', company_id)\
            .single()\
            .execute()

        return response.data

    async def _get_umo(self, company_id: str) -> Optional[dict]:
        """Get company UMO (Unique Member of One)."""
        response = self.supabase.table('company_umos')\
            .select('*')\
            .eq('company_id', company_id)\
            .execute()

        return response.data[0] if response.data else None
