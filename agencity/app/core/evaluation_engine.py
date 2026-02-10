"""
Evaluation Engine - Honest candidate assessment.

Key principle: NO CLAIMS WE CAN'T VERIFY.
We separate known facts from observed signals from unknowns.
"""

import json
import logging

from app.models.blueprint import RoleBlueprint
from app.models.candidate import CandidateData
from app.models.evaluation import EvaluatedCandidate
from app.services.llm import LLMService

logger = logging.getLogger(__name__)


class EvaluationEngine:
    """
    Evaluates candidates honestly against a blueprint.

    Three-tier evaluation:
    1. Known Facts - Verifiable from the data
    2. Observed Signals - Reasonable inferences from behavior
    3. Unknown - What we can't determine from this data
    """

    def __init__(self, llm_service: LLMService | None = None):
        self.llm = llm_service or LLMService()

    async def evaluate(
        self,
        candidate: CandidateData,
        blueprint: RoleBlueprint,
    ) -> EvaluatedCandidate:
        """
        Evaluate a candidate against the blueprint.

        Returns an honest assessment with known/observed/unknown breakdown.
        """
        # Extract known facts (no LLM needed - just data)
        known_facts = self._extract_known_facts(candidate)

        # Extract observed signals (may use LLM for relevance matching)
        observed_signals = await self._extract_signals(candidate, blueprint)

        # Identify unknowns based on blueprint requirements
        unknown = self._identify_unknowns(candidate, blueprint)

        # Generate why_consider and next_step (LLM-assisted)
        why_consider, next_step = await self._generate_reasoning(
            candidate, blueprint, known_facts, observed_signals, unknown
        )

        # Compute internal relevance score (not shown to users)
        relevance_score = self._compute_relevance(
            candidate, blueprint, known_facts, observed_signals
        )

        return EvaluatedCandidate(
            candidate=candidate,
            known_facts=known_facts,
            observed_signals=observed_signals,
            unknown=unknown,
            why_consider=why_consider,
            next_step=next_step,
            relevance_score=relevance_score,
        )

    def _extract_known_facts(self, candidate: CandidateData) -> list[str]:
        """
        Extract only verifiable facts from candidate data.

        These are things we KNOW to be true, not inferences.
        """
        facts = []

        # Education
        if candidate.school:
            fact = candidate.school
            if candidate.graduation_year:
                fact += f", Class of {candidate.graduation_year}"
            facts.append(fact)

        if candidate.major:
            facts.append(f"{candidate.major} major")

        # Clubs (verifiable if from official source)
        for club in candidate.clubs:
            facts.append(f"Member of {club}")

        # GitHub existence (not skill claims)
        if candidate.github_username:
            facts.append(f"Active GitHub account (@{candidate.github_username})")

        # Hackathon participation (verifiable from Devpost)
        for hackathon in candidate.hackathons:
            if hackathon.won_prize and hackathon.prize:
                facts.append(f"Won {hackathon.prize} at {hackathon.name}")
            else:
                facts.append(f"Participated in {hackathon.name}")

        return facts

    async def _extract_signals(
        self,
        candidate: CandidateData,
        blueprint: RoleBlueprint,
    ) -> list[str]:
        """
        Extract signals relevant to the blueprint.

        These are observations, not claims about ability.
        "Has 2 LLM repos" not "Strong LLM skills"
        """
        signals = []

        # GitHub signals
        if candidate.github_repos:
            # Count repos by type
            total_repos = len(candidate.github_repos)
            if total_repos > 0:
                signals.append(f"GitHub: {total_repos} public repositories")

            # Look for relevant repos
            relevant = candidate.get_relevant_repos(blueprint.must_haves)
            if relevant:
                signals.append(
                    f"GitHub: {len(relevant)} projects related to {blueprint.role_title}"
                )

            # LLM/ML specific repos
            llm_repos = [r for r in candidate.github_repos if r.has_llm_usage]
            if llm_repos:
                signals.append(f"GitHub: {len(llm_repos)} projects using LLM APIs")

            ml_repos = [r for r in candidate.github_repos if r.has_ml_code]
            if ml_repos:
                signals.append(f"GitHub: {len(ml_repos)} ML/AI related projects")

        # Activity signals
        if candidate.github_activity:
            activity = candidate.github_activity
            if activity.commits_last_90_days > 50:
                signals.append(
                    f"Active contributor ({activity.commits_last_90_days} commits in 90 days)"
                )
            if activity.active_days_per_week >= 3:
                signals.append(
                    f"Consistent activity ({activity.active_days_per_week:.1f} days/week)"
                )

        # Hackathon signals
        if candidate.hackathons:
            wins = [h for h in candidate.hackathons if h.won_prize]
            if wins:
                signals.append(f"Won {len(wins)} hackathon prizes")
            else:
                signals.append(f"Competed in {len(candidate.hackathons)} hackathons")

        return signals

    def _identify_unknowns(
        self,
        candidate: CandidateData,
        blueprint: RoleBlueprint,
    ) -> list[str]:
        """
        What does the blueprint require that we CAN'T verify?

        This is where we're honest about our limitations.
        """
        unknowns = []

        # Always unknown from public data
        unknowns.append("Actual skill depth (verify in conversation)")
        unknowns.append("Work style and communication")
        unknowns.append("Interest in this specific opportunity")

        # Blueprint-specific unknowns
        success = blueprint.success_criteria.lower()

        if "fast" in success or "ship" in success or "speed" in success:
            unknowns.append("Shipping speed in team environment")

        if "production" in success or "deploy" in success:
            if not any("production" in str(r).lower() for r in candidate.github_repos):
                unknowns.append("Production system experience")

        if "lead" in success or "team" in success:
            unknowns.append("Leadership and collaboration style")

        # Check must-haves we can't verify
        for must_have in blueprint.must_haves:
            must_lower = must_have.lower()
            # If it's a soft skill, we can't verify it
            soft_skills = ["communication", "teamwork", "leadership", "fast learner"]
            if any(skill in must_lower for skill in soft_skills):
                unknowns.append(f"{must_have} (soft skill - verify in conversation)")

        return unknowns[:5]  # Limit to top 5 unknowns

    async def _generate_reasoning(
        self,
        candidate: CandidateData,
        blueprint: RoleBlueprint,
        known_facts: list[str],
        observed_signals: list[str],
        unknown: list[str],
    ) -> tuple[str, str]:
        """
        Generate why_consider and next_step using LLM.
        """
        prompt = f"""You are evaluating a candidate for a startup role.

Role Blueprint:
{blueprint.model_dump_json(indent=2)}

Candidate:
- Name: {candidate.name}
- Known Facts: {known_facts}
- Observed Signals: {observed_signals}
- Unknown: {unknown}

Write two things:
1. why_consider: A brief (1-2 sentences) explanation of why this person might be worth a conversation. Focus on the CONNECTION to what the founder described. Be specific.

2. next_step: A specific question or thing to verify in the first conversation. Based on the unknowns, what's most important to clarify?

Respond with ONLY valid JSON:
{{"why_consider": "...", "next_step": "..."}}"""

        response = await self.llm.complete(prompt)

        try:
            text = response.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text)
            return data.get("why_consider", ""), data.get("next_step", "")
        except (json.JSONDecodeError, ValueError):
            logger.warning(f"Failed to parse reasoning: {response[:200]}")
            return (
                "Matches some criteria from the search.",
                "Ask about their relevant experience and interest.",
            )

    def _compute_relevance(
        self,
        candidate: CandidateData,
        blueprint: RoleBlueprint,
        known_facts: list[str],
        observed_signals: list[str],
    ) -> float:
        """
        Compute internal relevance score for ranking.

        This is NEVER shown to users as a "match score".
        It's only used to rank candidates in the shortlist.
        """
        score = 0.0

        # Location match
        if blueprint.location_preferences:
            for pref in blueprint.location_preferences:
                if candidate.school and pref.lower() in candidate.school.lower():
                    score += 0.2
                if candidate.location and pref.lower() in candidate.location.lower():
                    score += 0.1

        # Skills/must-haves match
        if blueprint.must_haves:
            matches = 0
            for must_have in blueprint.must_haves:
                # Check in signals
                if any(must_have.lower() in s.lower() for s in observed_signals):
                    matches += 1
                # Check in candidate skills
                if any(must_have.lower() in s.lower() for s in candidate.skills):
                    matches += 1
            score += 0.3 * (matches / len(blueprint.must_haves))

        # Activity bonus
        if candidate.github_activity:
            if candidate.github_activity.commits_last_90_days > 50:
                score += 0.1
            if candidate.github_activity.active_days_per_week >= 3:
                score += 0.1

        # Hackathon wins bonus
        if candidate.has_hackathon_wins():
            score += 0.15

        # More known facts = more confidence
        score += 0.05 * min(len(known_facts), 5)

        # More signals = more evidence
        score += 0.05 * min(len(observed_signals), 5)

        return min(score, 1.0)  # Cap at 1.0
