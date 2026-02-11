"""
Readiness Scoring - Detect who is likely open to new opportunities.

Not everyone is looking to switch jobs. This module scores candidates
based on signals that indicate they might be "ready to move."
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# Companies with known recent layoffs (update periodically)
LAYOFF_COMPANIES = {
    "meta": "2024 layoffs",
    "facebook": "2024 layoffs",
    "google": "2024 layoffs",
    "alphabet": "2024 layoffs",
    "amazon": "2024 layoffs",
    "microsoft": "2024 layoffs",
    "salesforce": "2024 layoffs",
    "twitter": "2023 mass layoffs",
    "x corp": "2023 mass layoffs",
    "stripe": "2023 layoffs",
    "shopify": "2023 layoffs",
    "snap": "2024 layoffs",
    "snapchat": "2024 layoffs",
    "spotify": "2024 layoffs",
    "discord": "2024 layoffs",
    "twitch": "2024 layoffs",
    "linkedin": "2024 layoffs",
    "indeed": "2024 layoffs",
    "glassdoor": "2024 layoffs",
    "zillow": "2024 layoffs",
    "redfin": "2024 layoffs",
    "coinbase": "2023 layoffs",
    "robinhood": "2023 layoffs",
    "docusign": "2024 layoffs",
    "zoom": "2023 layoffs",
    "intel": "2024 layoffs",
    "cisco": "2024 layoffs",
    "dell": "2024 layoffs",
    "ibm": "2024 layoffs",
    "sap": "2024 layoffs",
    "vmware": "2024 layoffs",
    "unity": "2024 layoffs",
    "riot games": "2024 layoffs",
    "epic games": "2024 layoffs",
    "ea": "2024 layoffs",
    "electronic arts": "2024 layoffs",
}

# Title signals indicating openness
OPEN_TITLE_SIGNALS = [
    ("open to work", 0.9, "Title: Open to Work"),
    ("seeking opportunities", 0.9, "Title: Seeking Opportunities"),
    ("looking for", 0.8, "Title: Looking for opportunities"),
    ("available for", 0.8, "Title: Available"),
    ("freelance", 0.6, "Title: Freelancer (flexible)"),
    ("consultant", 0.6, "Title: Consultant (flexible)"),
    ("advisor", 0.5, "Title: Advisor (part-time available)"),
    ("between roles", 0.9, "Title: Between roles"),
    ("in transition", 0.9, "Title: In transition"),
    ("exploring", 0.7, "Title: Exploring opportunities"),
    ("ex-", 0.4, "Title: Recently left company"),
    ("former", 0.4, "Title: Former employee"),
]

# Bio signals
OPEN_BIO_SIGNALS = [
    ("open to opportunities", 0.8),
    ("looking for my next", 0.8),
    ("exploring new", 0.7),
    ("available for hire", 0.9),
    ("let's connect", 0.2),  # Weak but positive signal
    ("reach out", 0.2),
]


class ReadinessScorer:
    """
    Score candidates on their likelihood of being open to opportunities.

    Signals include:
    - Title keywords ("Open to Work", "Consultant", etc.)
    - Tenure at current company (sweet spot: 2-4 years)
    - Company layoff news
    - Profile activity (if detectable)
    """

    def score(self, person: dict) -> dict:
        """
        Score a person's readiness to move.

        Args:
            person: Person dict with title, company, tenure info, etc.

        Returns:
            Dict with readiness_score (0-1) and readiness_signals list
        """
        score = 0.0
        signals = []

        title = (person.get("current_title") or "").lower()
        company = (person.get("current_company") or "").lower()
        bio = (person.get("bio") or person.get("summary") or "").lower()

        # Check title signals
        title_score, title_signals = self._check_title_signals(title)
        score += title_score
        signals.extend(title_signals)

        # Check bio signals
        bio_score, bio_signals = self._check_bio_signals(bio)
        score += bio_score
        signals.extend(bio_signals)

        # Check company layoff signals
        layoff_score, layoff_signal = self._check_layoff_signals(company)
        score += layoff_score
        if layoff_signal:
            signals.append(layoff_signal)

        # Check tenure signals
        tenure_score, tenure_signal = self._check_tenure_signals(person)
        score += tenure_score
        if tenure_signal:
            signals.append(tenure_signal)

        # Check if at early-stage startup (higher risk, more likely to move)
        startup_score, startup_signal = self._check_startup_signals(company, person)
        score += startup_score
        if startup_signal:
            signals.append(startup_signal)

        # Normalize to 0-1
        score = min(1.0, score)

        return {
            "readiness_score": round(score, 3),
            "readiness_signals": signals
        }

    def _check_title_signals(self, title: str) -> tuple[float, list[str]]:
        """Check title for openness signals."""
        score = 0.0
        signals = []

        for pattern, weight, signal_text in OPEN_TITLE_SIGNALS:
            if pattern in title:
                score += weight
                signals.append(signal_text)

        return min(0.9, score), signals

    def _check_bio_signals(self, bio: str) -> tuple[float, list[str]]:
        """Check bio/summary for openness signals."""
        score = 0.0
        signals = []

        for pattern, weight in OPEN_BIO_SIGNALS:
            if pattern in bio:
                score += weight
                signals.append(f"Bio mentions: {pattern}")

        return min(0.5, score), signals

    def _check_layoff_signals(self, company: str) -> tuple[float, Optional[str]]:
        """Check if company has had recent layoffs."""
        for company_name, layoff_info in LAYOFF_COMPANIES.items():
            if company_name in company:
                return 0.3, f"Company had {layoff_info}"
        return 0.0, None

    def _check_tenure_signals(self, person: dict) -> tuple[float, Optional[str]]:
        """
        Check tenure at current company.

        Sweet spot: 2-4 years (vesting cliff, looking for next challenge)
        Red flag: < 6 months (just started, unlikely to move)
        """
        # Try to get start date from employment history
        employment = person.get("employment_history") or []
        start_date = person.get("current_job_start_date")

        if not start_date and employment:
            # Get most recent job
            for job in employment:
                if not job.get("end"):  # Current job
                    start_date = job.get("start")
                    break

        if not start_date:
            return 0.0, None

        try:
            # Parse date (handle various formats)
            if isinstance(start_date, str):
                # Try YYYY-MM format
                if len(start_date) == 7:
                    start = datetime.strptime(start_date, "%Y-%m")
                elif len(start_date) == 10:
                    start = datetime.strptime(start_date, "%Y-%m-%d")
                else:
                    return 0.0, None
            else:
                return 0.0, None

            tenure_months = (datetime.now() - start).days / 30

            if tenure_months < 6:
                return -0.3, "Just started (< 6 months) - unlikely to move"
            elif tenure_months < 12:
                return 0.0, None  # Neutral
            elif tenure_months < 24:
                return 0.1, f"Tenure: {tenure_months:.0f} months"
            elif tenure_months < 36:
                return 0.2, f"Tenure: {tenure_months/12:.1f} years (may be looking)"
            elif tenure_months < 48:
                return 0.3, f"Tenure: {tenure_months/12:.1f} years (vesting cliff zone)"
            else:
                return 0.2, f"Tenure: {tenure_months/12:.1f} years (long tenure)"

        except Exception as e:
            logger.debug(f"Error parsing tenure: {e}")
            return 0.0, None

    def _check_startup_signals(
        self,
        company: str,
        person: dict
    ) -> tuple[float, Optional[str]]:
        """
        Check if at early-stage/struggling startup.

        People at struggling startups are more likely to be open.
        """
        # Check for small company indicators in title
        title = (person.get("current_title") or "").lower()

        # Founder at small company might be looking if things aren't going well
        if "founder" in title or "co-founder" in title:
            return 0.2, "Founder (may be pivoting)"

        # "Stealth" or "Startup" in company name
        if "stealth" in company:
            return 0.3, "At stealth startup (high uncertainty)"

        if "startup" in company:
            return 0.2, "At early-stage startup"

        return 0.0, None

    def batch_score(self, people: list[dict]) -> list[dict]:
        """Score multiple people and add readiness data."""
        results = []
        for person in people:
            readiness = self.score(person)
            results.append({
                **person,
                **readiness
            })
        return results

    def filter_ready(
        self,
        people: list[dict],
        min_score: float = 0.2
    ) -> list[dict]:
        """Filter to only people above a readiness threshold."""
        scored = self.batch_score(people)
        return [p for p in scored if p["readiness_score"] >= min_score]

    def sort_by_readiness(
        self,
        people: list[dict],
        descending: bool = True
    ) -> list[dict]:
        """Sort people by readiness score."""
        scored = self.batch_score(people)
        return sorted(
            scored,
            key=lambda x: x["readiness_score"],
            reverse=descending
        )
