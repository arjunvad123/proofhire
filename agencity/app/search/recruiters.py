"""
Recruiter Identification - Find recruiters in your network.

Recruiters are the highest-signal contacts for finding candidates.
They literally know who is actively looking for jobs.
One conversation with a recruiter > 1000 API calls.
"""

import logging
from typing import Optional
from uuid import UUID

from app.services.company_db import CompanyDBService

logger = logging.getLogger(__name__)

# Title patterns that indicate recruiting role
RECRUITER_TITLE_PATTERNS = [
    # Direct recruiting titles
    ("recruiter", 1.0),
    ("recruiting", 1.0),
    ("talent acquisition", 1.0),
    ("talent partner", 0.9),
    ("sourcer", 0.9),
    ("sourcing", 0.8),

    # HR with recruiting focus
    ("hr business partner", 0.5),
    ("people operations", 0.4),
    ("people partner", 0.4),

    # Headhunter / agency
    ("headhunter", 1.0),
    ("executive search", 1.0),
    ("search consultant", 0.9),
    ("placement", 0.8),

    # Management
    ("head of talent", 0.9),
    ("director of talent", 0.9),
    ("vp talent", 0.9),
    ("chief people", 0.6),
]

# Specialty indicators
SPECIALTY_PATTERNS = {
    "tech": [
        "technical recruiter",
        "engineering recruiter",
        "tech recruiter",
        "software",
        "developer",
        "ml", "ai", "machine learning",
        "data science",
    ],
    "executive": [
        "executive search",
        "executive recruiter",
        "c-suite",
        "leadership",
        "vp ", "director",
    ],
    "finance": [
        "finance recruiter",
        "fintech",
        "banking",
        "investment",
    ],
    "sales": [
        "sales recruiter",
        "revenue",
        "gtm",
        "go-to-market",
    ],
    "product": [
        "product recruiter",
        "product manager",
        "pm ",
    ],
    "design": [
        "design recruiter",
        "ux ", "ui ",
        "creative",
    ],
    "general": [],  # Fallback
}

# Company patterns indicating recruiting firm
RECRUITING_FIRMS = [
    "hired",
    "linkedin",
    "indeed",
    "glassdoor",
    "lever",
    "greenhouse",
    "korn ferry",
    "heidrick",
    "spencer stuart",
    "russell reynolds",
    "egon zehnder",
    "robert half",
    "randstad",
    "manpower",
    "adecco",
    "kelly services",
    "hays",
    "michael page",
    "talent.io",
    "toptal",
    "triplebyte",
    "turing",
    "andela",
    "a.team",
    "gun.io",
]


class RecruiterFinder:
    """
    Identify and classify recruiters in the network.

    Recruiters are incredibly valuable for finding candidates because:
    1. They know who is actively looking
    2. They have pre-screened candidates
    3. A single conversation can yield 5-10 qualified candidates
    """

    def __init__(self, company_id: UUID):
        self.company_id = company_id
        self.db = CompanyDBService()

    def _to_dict(self, obj) -> dict:
        """Convert a Pydantic model or object to a dict."""
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        elif hasattr(obj, "dict"):
            return obj.dict()
        elif isinstance(obj, dict):
            return obj
        else:
            return dict(obj)

    async def find_recruiters(
        self,
        specialty: str = None
    ) -> list[dict]:
        """
        Find all recruiters in the network.

        Args:
            specialty: Optional filter by specialty (tech, finance, etc.)

        Returns:
            List of recruiters with their specialty and recruiter_score
        """
        # Get all network connections and convert to dicts
        all_people_raw = await self.db.get_people(
            self.company_id,
            limit=999999,  # Get all (pagination handles this)
            filters={"is_from_network": True}
        )
        all_people = [self._to_dict(p) for p in all_people_raw]

        recruiters = []

        for person in all_people:
            recruiter_info = self._classify_recruiter(person)

            if recruiter_info["is_recruiter"]:
                # Apply specialty filter if provided
                if specialty and recruiter_info["specialty"] != specialty:
                    if recruiter_info["specialty"] != "general":
                        continue

                recruiters.append({
                    **person,
                    **recruiter_info,
                    "tier": 3,  # Tier 3 = ask for referrals
                    "action": "Ask for referrals",
                })

        # Sort by recruiter score (confidence they can help)
        recruiters.sort(key=lambda x: x["recruiter_score"], reverse=True)

        logger.info(f"Found {len(recruiters)} recruiters in network")

        return recruiters

    def _classify_recruiter(self, person: dict) -> dict:
        """Classify if a person is a recruiter and their specialty."""
        title = (person.get("current_title") or "").lower()
        company = (person.get("current_company") or "").lower()
        bio = (person.get("bio") or person.get("summary") or "").lower()

        result = {
            "is_recruiter": False,
            "recruiter_score": 0.0,
            "specialty": "general",
            "recruiter_signals": [],
        }

        # Check title patterns
        for pattern, score in RECRUITER_TITLE_PATTERNS:
            if pattern in title:
                result["is_recruiter"] = True
                result["recruiter_score"] = max(result["recruiter_score"], score)
                result["recruiter_signals"].append(f"Title: {pattern}")

        # Check if at recruiting firm
        for firm in RECRUITING_FIRMS:
            if firm in company:
                result["is_recruiter"] = True
                result["recruiter_score"] = max(result["recruiter_score"], 0.8)
                result["recruiter_signals"].append(f"Works at recruiting firm: {firm}")
                break

        # If not a recruiter, return early
        if not result["is_recruiter"]:
            return result

        # Determine specialty
        combined_text = f"{title} {bio}"
        for specialty, patterns in SPECIALTY_PATTERNS.items():
            for pattern in patterns:
                if pattern in combined_text:
                    result["specialty"] = specialty
                    result["recruiter_signals"].append(f"Specialty: {specialty}")
                    break
            if result["specialty"] != "general":
                break

        return result

    async def get_tech_recruiters(self) -> list[dict]:
        """Convenience method to get tech recruiters."""
        return await self.find_recruiters(specialty="tech")

    async def get_recruiter_summary(self) -> dict:
        """Get a summary of recruiters in the network."""
        all_recruiters = await self.find_recruiters()

        by_specialty = {}
        for r in all_recruiters:
            spec = r["specialty"]
            by_specialty[spec] = by_specialty.get(spec, 0) + 1

        top_recruiters = all_recruiters[:5]

        return {
            "total_recruiters": len(all_recruiters),
            "by_specialty": by_specialty,
            "top_recruiters": [
                {
                    "name": r.get("full_name"),
                    "title": r.get("current_title"),
                    "company": r.get("current_company"),
                    "specialty": r.get("specialty"),
                    "linkedin_url": r.get("linkedin_url"),
                }
                for r in top_recruiters
            ],
            "recommendation": self._generate_recommendation(all_recruiters)
        }

    def _generate_recommendation(self, recruiters: list[dict]) -> str:
        """Generate a recommendation for how to use recruiters."""
        if not recruiters:
            return "No recruiters found in your network. Consider connecting with tech recruiters."

        tech_count = sum(1 for r in recruiters if r["specialty"] == "tech")

        if tech_count >= 3:
            return f"You have {tech_count} tech recruiters in your network. Reach out to them for ML engineer referrals - this is your highest-signal move."
        elif tech_count >= 1:
            return f"You have {tech_count} tech recruiter(s). They likely know candidates actively looking. Start there."
        else:
            return f"You have {len(recruiters)} recruiters but none specialized in tech. Consider reaching out to the general recruiters or connecting with tech-focused ones."


class RecruiterOutreach:
    """Generate outreach messages for recruiters."""

    @staticmethod
    def generate_message(
        recruiter: dict,
        role_title: str,
        required_skills: list[str] = None
    ) -> str:
        """Generate a personalized outreach message."""
        name = recruiter.get("full_name", "").split()[0]  # First name
        skills_str = ", ".join(required_skills[:3]) if required_skills else ""

        message = f"""Hi {name},

Hope you're doing well! I'm looking to hire a {role_title}"""

        if skills_str:
            message += f" with experience in {skills_str}"

        message += """.

Given your experience in recruiting, I thought you might know some great candidates. Would love to chat if you have anyone in mind who might be a fit, or if you could point me in the right direction.

Happy to share more details about the role. Let me know if you have a few minutes this week!

Thanks,
[Your name]"""

        return message
