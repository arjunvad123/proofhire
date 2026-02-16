"""
Candidate Curation Engine.

Curates shortlist of candidates for a role by:
1. Ranking all network candidates with incomplete data
2. Enriching top candidates on-demand
3. Deep research on top 5 candidates (Perplexity)
4. Re-ranking with enriched data
5. Building rich context for final shortlist
"""

from typing import List, Dict, Any, Optional
from app.models.curation import (
    UnifiedCandidate,
    FitScore,
    CuratedCandidate,
    CandidateContext,
    WhyConsiderPoint,
    MatchStrength,
    EnrichmentDetails,
    ClaudeReasoning,
    AgentScore,
    ResearchHighlight
)
from app.services.candidate_builder import CandidateBuilder
from app.services.research.perplexity_researcher import DeepResearchEngine
from app.services.external_search.pdl_client import PDLClient
from app.config import settings
import re
from datetime import datetime, timedelta


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

        # Get role and company context
        role = await self._get_role(role_id)
        company_dna = await self._get_company_dna(company_id)
        umo = await self._get_umo(company_id)

        print(f"\n{'='*60}")
        print(f"🎯 Starting Candidate Curation")
        print(f"📋 Role: {role.get('title', 'Unknown')}")
        print(f"🏢 Company: {company_dna.get('name', 'Unknown')}")
        print(f"{'='*60}")

        # 1. Get all network candidates
        network_people = await self._get_network_people(company_id)
        print(f"📊 Searching {len(network_people)} network connections...")

        # 2. Build unified candidates in BATCH
        person_ids = [p['id'] for p in network_people]
        candidates = await self.builder.build_many(person_ids)
        print(f"✅ Loaded {len(candidates)} candidate profiles")

        # 3. Calculate fit for each candidate
        ranked_candidates = []

        for candidate in candidates:
            # Calculate fit score
            fit = self._calculate_fit(candidate, role, company_dna, umo)

            ranked_candidates.append({
                'candidate': candidate,
                'fit_score': fit.score,
                'confidence': fit.confidence,
                'fit_breakdown': fit,
                'needs_enrichment': fit.needs_enrichment
            })

        # 4. Initial ranking
        ranked_candidates.sort(key=lambda x: x['fit_score'], reverse=True)

        top_score = ranked_candidates[0]['fit_score'] if ranked_candidates else 0
        avg_confidence = sum(c['confidence'] for c in ranked_candidates) / len(ranked_candidates) if ranked_candidates else 0

        print(f"\n{'-'*60}")
        print(f"📈 Rule-based Top Score: {top_score:.1f} | Avg Conf: {avg_confidence:.2f}")

        # 5. Enrich TOP 5 candidates with PDL
        top_n_to_enrich = 5
        top_candidates = ranked_candidates[:top_n_to_enrich]
        to_enrich = [c for c in top_candidates if c['candidate'].linkedin_url]

        if to_enrich:
            print(f"🔍 Enriching top {len(to_enrich)} candidates via PDL...")
            enriched_count = await self._enrich_candidates_pdl_only(to_enrich)
            print(f"✅ Enriched {enriched_count}/{len(to_enrich)} candidates")

            for item in to_enrich:
                item['candidate'] = await self.builder.build(item['candidate'].person_id)
                item['was_enriched'] = True

        # 6. Claude reasoning on enriched candidates
        if to_enrich and enriched_count > 0:
            print(f"🧠 Analyzing deep insights with Claude...")
            claude_scored_candidates = await self._score_with_claude_reasoning(
                to_enrich,
                role,
                company_dna,
                umo
            )

            for item in claude_scored_candidates:
                for ranked_item in ranked_candidates:
                    if ranked_item['candidate'].person_id == item['candidate'].person_id:
                        ranked_item['final_score'] = (item['claude_score'] * 0.7) + (item['fit_score'] * 0.3)
                        ranked_item['claude_score'] = item['claude_score']
                        ranked_item['claude_confidence'] = item['claude_confidence']
                        ranked_item['claude_reasoning'] = item.get('claude_reasoning')
                        break

            ranked_candidates.sort(key=lambda x: x.get('final_score', x['fit_score']), reverse=True)
            new_top = ranked_candidates[0].get('final_score', ranked_candidates[0]['fit_score'])
            print(f"✨ Re-ranked. New Top Score: {new_top:.1f}")

        # 7. Deep research on top 10 candidates using Perplexity
        if settings.perplexity_api_key:
            final_top_n = 10
            final_top_research = ranked_candidates[:final_top_n]
            print(f"🔬 Running deep research on top {len(final_top_research)} candidates...")

            research_engine = DeepResearchEngine(settings.perplexity_api_key)

            try:
                # Extract candidates for research
                candidates_to_research = [item['candidate'] for item in final_top_research]

                # Run deep research
                enhanced_candidates = await research_engine.enhance_candidates(
                    candidates_to_research,
                    role_title=role.get('title', ''),
                    role_skills=role.get('required_skills', []),
                    top_n=final_top_n
                )


                # Update candidates with research insights
                for i, enhanced in enumerate(enhanced_candidates):
                    final_top_5[i]['candidate'] = enhanced
                    final_top_5[i]['has_deep_research'] = True

            except Exception as e:
                print(f"⚠️  Deep research failed: {e}")
                # Continue without deep research

        # 8. Build rich context for final shortlist
        shortlist = []

        for item in ranked_candidates[:limit]:
            # Build enrichment details
            enrichment_details = self._build_enrichment_details(item['candidate'])

            # Build Claude reasoning if available
            claude_reasoning = None
            if item.get('claude_reasoning'):
                claude_reasoning = self._build_claude_reasoning_details(
                    item.get('claude_score', item['fit_score']),
                    item.get('claude_confidence', item['confidence']),
                    item['claude_reasoning'],
                    item['fit_score']
                )

            context = await self._build_context(
                item['candidate'],
                role,
                company_dna,
                umo,
                enrichment_details=enrichment_details,
                claude_reasoning=claude_reasoning
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
                skills=item['candidate'].skills if hasattr(item['candidate'], 'skills') else [],
                experience=item['candidate'].experience if hasattr(item['candidate'], 'experience') else [],
                education=item['candidate'].education if hasattr(item['candidate'], 'education') else [],
                match_score=item.get('final_score', item['fit_score']),
                fit_confidence=item['confidence'],
                context=context,
                was_enriched=item.get('was_enriched', False),
                data_completeness=item['candidate'].data_completeness
            )

            shortlist.append(curated)

        print(f"\n{'-'*60}")
        print(f"✅ Curation complete: {len(shortlist)} candidates shortlisted")
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
        min_years = role.get('years_experience_min') or 0
        max_years = role.get('years_experience_max') or 10

        # Handle None values with safe defaults
        if min_years is None:
            min_years = 0
        if max_years is None:
            max_years = 10

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
        umo: Optional[dict],
        enrichment_details: Optional[EnrichmentDetails] = None,
        claude_reasoning: Optional[ClaudeReasoning] = None
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

        # 0. Deep research insights (if available)
        if hasattr(candidate, 'deep_research') and candidate.deep_research:
            research = candidate.deep_research
            raw_insights = research.get('raw_research', '')

            if raw_insights and len(raw_insights) > 100:
                # Parse Perplexity research into structured insights
                insights = self._parse_research_insights(raw_insights, role)

                # Add research-based points to why_consider
                if insights.get('technical_skills'):
                    why_consider.append(WhyConsiderPoint(
                        category="Deep Research: Technical Skills",
                        strength=MatchStrength.HIGH,
                        points=[f"🔬 {point}" for point in insights['technical_skills'][:3]]
                    ))

                if insights.get('achievements'):
                    why_consider.append(WhyConsiderPoint(
                        category="Deep Research: Achievements",
                        strength=MatchStrength.HIGH,
                        points=[f"🏆 {point}" for point in insights['achievements'][:3]]
                    ))

                if insights.get('online_presence'):
                    why_consider.append(WhyConsiderPoint(
                        category="Deep Research: Online Presence",
                        strength=MatchStrength.MEDIUM,
                        points=[f"🌐 {point}" for point in insights['online_presence'][:2]]
                    ))

                # Extract standout signal
                if insights.get('standout'):
                    standout_signal = f"🔬 Research: {insights['standout']}"

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
            warm_path=warm_path,
            enrichment_details=enrichment_details,
            claude_reasoning=claude_reasoning
        )

    def _parse_research_insights(self, raw_research: str, role: dict) -> Dict[str, Any]:
        """
        Parse Perplexity research response into structured insights.
        """
        insights = {
            'technical_skills': [],
            'achievements': [],
            'online_presence': [],
            'standout': None
        }

        def clean_line(text: str) -> str:
            # Remove markdown headers, bolding, and list chars
            cleaned = re.sub(r'#{1,6}\s?', '', text)
            cleaned = cleaned.replace('**', '').replace('*', '')
            cleaned = cleaned.strip(' -•*>')
            return cleaned

        lines = raw_research.split('\n')
        for line in lines:
            line_clean = clean_line(line)
            if not line_clean or len(line_clean) < 5:
                continue

            line_lower = line_clean.lower()

            # Technical skills
            if any(kw in line_lower for kw in ['programming', 'framework', 'language', 'stack', 'aws', 'python', 'javascript', 'typescript', 'rust', 'go']):
                if len(insights['technical_skills']) < 5:
                    insights['technical_skills'].append(line_clean)

            # Achievements
            elif any(kw in line_lower for kw in ['won', 'award', 'published', 'hackathon', 'founder', 'created', 'built', 'led']):
                if len(insights['achievements']) < 5:
                    insights['achievements'].append(line_clean)

            # Online presence
            elif any(kw in line_lower for kw in ['blog', 'article', 'stackoverflow', 'twitter', 'linkedin', 'medium', 'open source']):
                if len(insights['online_presence']) < 5:
                    insights['online_presence'].append(line_clean)

        if insights['achievements']:
            insights['standout'] = insights['achievements'][0]
        elif insights['technical_skills']:
            insights['standout'] = insights['technical_skills'][0]

        return insights

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

    async def _enrich_candidates_pdl_only(self, candidates_to_enrich: List[dict]) -> int:
        """
        Enrich candidates using PDL ONLY (no RapidAPI).

        Strategy:
        - Enrich top 5 candidates at a time
        - Skip if enrichment exists AND is < 30 days old
        - Only use PDL (~$0.10 per enrichment)

        Returns count of successfully enriched candidates.
        """
        enriched_count = 0
        cache_hits = 0
        total_cost = 0.0

        # Initialize PDL client
        if not settings.pdl_api_key:
            print("⚠️  PDL API key not configured - skipping enrichment")
            return 0

        pdl_client = PDLClient(api_key=settings.pdl_api_key)

        for item in candidates_to_enrich:
            candidate = item['candidate']
            person_id = candidate.person_id
            linkedin_url = candidate.linkedin_url

            if not linkedin_url:
                print(f"  ⏭️  Skipping {candidate.full_name} (no LinkedIn URL)")
                continue

            # Check if enrichment already exists and is fresh
            existing = await self._get_enrichment(person_id)
            if existing:
                updated_at = existing.get('updated_at')
                if updated_at:
                    # Parse timestamp
                    if isinstance(updated_at, str):
                        updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))

                    age_days = (datetime.now(updated_at.tzinfo) - updated_at).days

                    if age_days < 30:
                        print(f"  ✓ {candidate.full_name} (cached, {age_days}d old)")
                        # Update candidate with existing enrichment
                        self._apply_enrichment(candidate, existing)
                        item['was_enriched'] = True
                        cache_hits += 1
                        continue

            # Enrich with PDL
            print(f"  🔍 Enriching {candidate.full_name} via PDL...")
            pdl_profile = await pdl_client.enrich_profile(linkedin_url)

            if pdl_profile:
                # Convert PDL format to our format
                enrichment_data = {
                    'skills': pdl_profile.skills,
                    'experience': pdl_profile.experience,
                    'education': pdl_profile.education,
                    'headline': pdl_profile.headline,
                    'location': pdl_profile.location
                }

                # Store enrichment in database
                await self._store_enrichment(person_id, enrichment_data, 'pdl')

                # Apply enrichment to candidate
                self._apply_enrichment(candidate, enrichment_data)

                # Recalculate completeness
                candidate.data_completeness = candidate.calculate_completeness()

                enriched_count += 1
                total_cost += 0.10  # PDL cost per enrichment
                item['was_enriched'] = True

                print(f"    ✓ Success ($0.10)")
            else:
                print(f"    ✗ Failed to enrich {candidate.full_name}")

        if enriched_count > 0:
            print(f"💰 Total enrichment cost: ${total_cost:.2f} ({cache_hits} cache hits)")

        return enriched_count

    async def _score_with_claude_reasoning(
        self,
        candidates: List[dict],
        role: dict,
        company_dna: dict,
        umo: Optional[dict]
    ) -> List[dict]:
        """
        Use Claude reasoning engine to re-score enriched candidates.

        Uses Agent Swarm pattern (Skill, Trajectory, Fit, Timing agents).

        Returns candidates with added fields:
        - claude_score: 0-100 score from Claude
        - claude_confidence: 0-1 confidence
        - claude_reasoning: dict with agent breakdowns
        """
        from app.services.reasoning.claude_engine import claude_engine

        if not settings.anthropic_api_key:
            print("⚠️  Claude API key not configured - using rule-based scores only")
            for item in candidates:
                item['claude_score'] = item['fit_score']
                item['claude_confidence'] = item['confidence']
            return candidates

        # Prepare candidates for Claude analysis
        candidate_dicts = []
        for item in candidates:
            c = item['candidate']
            candidate_dicts.append({
                'id': c.person_id,
                'full_name': c.full_name,
                'current_title': c.current_title,
                'current_company': c.current_company,
                'headline': c.headline,
                'location': c.location,
                'skills': c.skills,
                'experience': c.experience,
                'education': c.education,
                'linkedin_url': c.linkedin_url,
                'github_url': c.github_url
            })

        # Run Claude analysis in batch
        try:
            analyses = await claude_engine.analyze_candidates_batch(
                candidates=candidate_dicts,
                role_title=role.get('title', ''),
                required_skills=role.get('required_skills', []),
                company_context={
                    'stage': company_dna.get('stage', 'early'),
                    'size': company_dna.get('employee_count', 'small'),
                    'culture': umo.get('culture_description', 'fast-moving startup') if umo else 'fast-moving startup'
                },
                max_concurrent=3  # Conservative rate limiting
            )

            # Map analyses back to candidates
            for item, analysis in zip(candidates, analyses):
                # Calculate overall Claude score (weighted average of agent scores)
                # Weights: Skills 40%, Trajectory 30%, Fit 20%, Timing 10%
                claude_score = (
                    analysis.skill_score * 0.4 +
                    analysis.trajectory_score * 0.3 +
                    analysis.fit_score * 0.2 +
                    analysis.timing_score * 0.1
                )

                item['claude_score'] = claude_score
                item['claude_confidence'] = analysis.confidence
                item['claude_reasoning'] = {
                    'skill': {'score': analysis.skill_score, 'reasoning': analysis.skill_reasoning},
                    'trajectory': {'score': analysis.trajectory_score, 'reasoning': analysis.trajectory_reasoning},
                    'fit': {'score': analysis.fit_score, 'reasoning': analysis.fit_reasoning},
                    'timing': {'score': analysis.timing_score, 'reasoning': analysis.timing_reasoning}
                }

                print(f"  🧠 {item['candidate'].full_name}: Claude={claude_score:.1f} (S={analysis.skill_score:.0f}, T={analysis.trajectory_score:.0f}, F={analysis.fit_score:.0f})")

        except Exception as e:
            print(f"⚠️  Claude reasoning failed: {e}")
            # Fallback to rule-based scores
            for item in candidates:
                item['claude_score'] = item['fit_score']
                item['claude_confidence'] = item['confidence']

        return candidates

    def _apply_enrichment(self, candidate: UnifiedCandidate, enrichment_data: dict):
        """Apply enrichment data to a candidate object."""
        if 'skills' in enrichment_data and enrichment_data['skills']:
            candidate.skills = enrichment_data['skills']

        if 'experience' in enrichment_data and enrichment_data['experience']:
            candidate.experience = enrichment_data['experience']

        if 'education' in enrichment_data and enrichment_data['education']:
            candidate.education = enrichment_data['education']

        if 'headline' in enrichment_data and enrichment_data['headline']:
            candidate.headline = enrichment_data['headline']

        if 'location' in enrichment_data and enrichment_data['location']:
            candidate.location = enrichment_data['location']

        candidate.has_enrichment = True
        candidate.enrichment_source = enrichment_data.get('enrichment_source', 'unknown')

    async def _get_enrichment(self, person_id: str) -> Optional[dict]:
        """Get existing enrichment for a person."""
        try:
            response = self.supabase.table('person_enrichments')\
                .select('*')\
                .eq('person_id', person_id)\
                .execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
        except Exception as e:
            print(f"⚠️  Error fetching enrichment: {e}")

        return None

    async def _store_enrichment(self, person_id: str, enrichment_data: dict, source: str):
        """Store enrichment data in database."""
        try:
            # Check if enrichment already exists
            existing = await self._get_enrichment(person_id)

            payload = {
                'person_id': person_id,
                'skills': enrichment_data.get('skills', []),
                'experience': enrichment_data.get('experience', []),
                'education': enrichment_data.get('education', []),
                'enrichment_source': source,
                'updated_at': datetime.utcnow().isoformat()
            }

            if existing:
                # Update existing
                self.supabase.table('person_enrichments')\
                    .update(payload)\
                    .eq('person_id', person_id)\
                    .execute()
            else:
                # Insert new
                payload['created_at'] = datetime.utcnow().isoformat()
                self.supabase.table('person_enrichments')\
                    .insert(payload)\
                    .execute()

            # IMPORTANT: Also update the people table with location data from enrichment
            people_updates = {}
            if enrichment_data.get('location'):
                people_updates['location'] = enrichment_data['location']
            if enrichment_data.get('headline'):
                # Update headline if it's more detailed than current
                people_updates['headline'] = enrichment_data['headline']

            if people_updates:
                self.supabase.table('people')\
                    .update(people_updates)\
                    .eq('id', person_id)\
                    .execute()
                print(f"    📍 Updated location: {enrichment_data.get('location')}")

            print(f"    💾 Stored enrichment (source: {source})")
        except Exception as e:
            print(f"    ⚠️  Error storing enrichment: {e}")

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

    def _build_enrichment_details(self, candidate: UnifiedCandidate) -> Optional[EnrichmentDetails]:
        """Build enrichment details from candidate data."""
        if not candidate.has_enrichment and not hasattr(candidate, 'deep_research'):
            return None

        sources = []
        pdl_fields = []
        research_highlights = []

        # Check PDL enrichment
        if candidate.has_enrichment:
            sources.append('pdl')
            # Determine which fields were enriched by PDL
            if candidate.skills:
                pdl_fields.append('skills')
            if candidate.experience:
                pdl_fields.append('experience')
            if candidate.education:
                pdl_fields.append('education')

        # Check Perplexity research
        if hasattr(candidate, 'deep_research') and candidate.deep_research:
            sources.append('perplexity')
            research = candidate.deep_research
            raw_insights = research.get('raw_research', '')

            if raw_insights:
                # Parse research into structured highlights
                insights = self._parse_research_insights(raw_insights, {})

                # GitHub projects
                for item in insights.get('technical_skills', [])[:3]:
                    research_highlights.append(ResearchHighlight(
                        type='skill',
                        title='Technical Skill',
                        description=item
                    ))

                # Achievements
                for item in insights.get('achievements', [])[:3]:
                    research_highlights.append(ResearchHighlight(
                        type='achievement',
                        title='Achievement',
                        description=item
                    ))

                # Online presence
                for item in insights.get('online_presence', [])[:2]:
                    research_highlights.append(ResearchHighlight(
                        type='github',
                        title='Online Presence',
                        description=item
                    ))

        return EnrichmentDetails(
            sources=sources,
            pdl_fields=pdl_fields,
            research_highlights=research_highlights,
            data_quality_score=candidate.data_completeness
        )

    def _build_claude_reasoning_details(
        self,
        claude_score: float,
        confidence: float,
        agent_reasoning: dict,
        rule_based_score: float
    ) -> ClaudeReasoning:
        """Build Claude reasoning details from agent scores."""
        agent_scores = {}

        # Map agent scores
        for agent_name, agent_data in agent_reasoning.items():
            agent_scores[f'{agent_name}_agent'] = AgentScore(
                score=agent_data['score'],
                reasoning=agent_data['reasoning']
            )

        # Calculate weighted explanation
        weighted_calc = f"70% Claude ({claude_score:.0f}) + 30% rule-based ({rule_based_score:.0f}) = {(claude_score * 0.7 + rule_based_score * 0.3):.0f}"

        return ClaudeReasoning(
            overall_score=claude_score,
            confidence=confidence,
            agent_scores=agent_scores,
            weighted_calculation=weighted_calc
        )
