"""
Shortlist Builder - Formats search results for Slack delivery
"""

from typing import List, Dict
from app.models.unified_candidate import UnifiedCandidate, SimpleScore


class ShortlistBuilder:
    """
    Builds and formats shortlists for Slack delivery.

    Simple version without Proof Briefs (your cofounder will add that later).
    """

    def build_shortlist(
        self,
        search_results: dict,
        target_size: int = 12
    ) -> List[dict]:
        """
        Build a shortlist from search results.

        Strategy:
        - 70% from tier_1 (warm)
        - 30% from tier_2 (cold)
        """

        shortlist = []

        tier_1 = search_results.get("tier_1_warm", [])
        tier_2 = search_results.get("tier_2_cold", [])

        # Take from tier 1 (warm candidates)
        warm_count = int(target_size * 0.70)
        shortlist.extend(tier_1[:warm_count])

        # Fill remainder from tier 2 (cold candidates)
        cold_count = target_size - len(shortlist)
        shortlist.extend(tier_2[:cold_count])

        return shortlist

    def format_for_slack(
        self,
        shortlist: List[dict],
        stats: dict
    ) -> List[dict]:
        """
        Format shortlist as Slack blocks.

        Returns list of Slack blocks for chat.postMessage.
        """

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🎯 Shortlist: {len(shortlist)} candidates"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"_Searched {stats.get('total_unique', 0):,} unique candidates (Hermes + Network)_"
                }
            },
            {"type": "divider"}
        ]

        # Add each candidate
        for i, item in enumerate(shortlist, 1):
            candidate: UnifiedCandidate = item["candidate"]
            score: SimpleScore = item["score"]

            candidate_blocks = self._format_candidate(i, candidate, score)
            blocks.extend(candidate_blocks)

        return blocks

    def _format_candidate(
        self,
        rank: int,
        candidate: UnifiedCandidate,
        score: SimpleScore
    ) -> List[dict]:
        """Format a single candidate as Slack blocks."""

        # Source badges
        badges = []
        if "hermes" in candidate.sources:
            badges.append("📋 Hermes")
        if "network" in candidate.sources:
            badges.append("🔗 Network")
        if len(candidate.sources) > 1:
            badges.append("✨ Multi-source")

        # Warmth indicator
        warmth_emoji = "🟢" if score.is_warm else "🔴"

        # Header text
        header_text = (
            f"*#{rank} - {candidate.full_name}*\n"
            f"{candidate.current_title or 'Unknown title'} @ {candidate.current_company or 'Unknown company'}\n"
            f"Score: {score.total_score:.0f}/100 {warmth_emoji} ({score.warmth:.0f} warmth)\n"
            f"_{' | '.join(badges)}_"
        )

        # Details section
        details_lines = []

        # Skills
        if candidate.skills:
            skills_preview = ", ".join(candidate.skills[:5])
            if len(candidate.skills) > 5:
                skills_preview += f" (+{len(candidate.skills) - 5} more)"
            details_lines.append(f"*Skills:* {skills_preview}")

        # Education
        if candidate.university:
            edu_text = candidate.university
            if candidate.major:
                edu_text += f" - {', '.join(candidate.major[:2])}"
            details_lines.append(f"*Education:* {edu_text}")

        # GitHub
        if candidate.github_username:
            details_lines.append(f"*GitHub:* <https://github.com/{candidate.github_username}|@{candidate.github_username}>")

        # Location
        if candidate.location:
            details_lines.append(f"*Location:* {candidate.location}")

        # Warm path
        if candidate.warm_path_description:
            details_lines.append(f"*Warm Path:* {candidate.warm_path_description}")

        # Next step
        details_lines.append(f"*Next Step:* {score.suggested_next_step}")

        details_text = "\n".join(details_lines)

        return [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": header_text}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": details_text}
            },
            {"type": "divider"}
        ]
