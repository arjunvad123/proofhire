"""
Role Suggester - Predict what roles a company will need next.

Uses:
- Company stage and size
- Recent hiring patterns
- Industry benchmarks
- Team composition gaps

Usage:
    suggester = RoleSuggester()
    suggestions = await suggester.suggest_next_roles(company_id="...")
    # Returns: [
    #   {"role": "DevOps Engineer", "confidence": 0.85, "reason": "No DevOps yet, 5 engineers"},
    #   {"role": "Product Manager", "confidence": 0.72, "reason": "Engineering:PM ratio is 8:0"}
    # ]
"""

import logging
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_supabase_client
from app.services.company_db import company_db

logger = logging.getLogger(__name__)


# =============================================================================
# HIRING PATTERNS BY STAGE
# =============================================================================

STAGE_PATTERNS = {
    "pre_seed": {
        "typical_team": ["Founder/CEO", "Technical Co-founder"],
        "next_hires": [
            ("Founding Engineer", 0.9, "Every pre-seed needs builders"),
            ("Designer", 0.5, "If product is consumer-facing"),
        ],
        "team_size": (1, 3)
    },
    "seed": {
        "typical_team": ["Founders", "2-4 Engineers"],
        "next_hires": [
            ("Senior Engineer", 0.85, "Scale the engineering team"),
            ("Product Designer", 0.7, "Improve user experience"),
            ("First PM", 0.5, "If founders are stretched thin"),
        ],
        "team_size": (3, 10)
    },
    "series_a": {
        "typical_team": ["Founders", "5-10 Engineers", "1-2 PMs", "Designer"],
        "next_hires": [
            ("Engineering Manager", 0.8, "Teams need leadership at 6+ engineers"),
            ("DevOps/SRE", 0.75, "Infrastructure becomes critical"),
            ("Data Engineer", 0.65, "Data-driven decisions matter"),
            ("Head of Product", 0.6, "Product strategy needs ownership"),
        ],
        "team_size": (10, 30)
    },
    "series_b": {
        "typical_team": ["Exec team", "15-30 Engineers", "3-5 PMs", "Design team"],
        "next_hires": [
            ("VP Engineering", 0.75, "Engineering org needs senior leadership"),
            ("Head of Design", 0.7, "Design team needs leadership"),
            ("Security Engineer", 0.65, "Security becomes table stakes"),
            ("ML Engineer", 0.6, "AI/ML opportunities emerge"),
            ("Head of People", 0.6, "Culture and hiring at scale"),
        ],
        "team_size": (30, 100)
    },
    "series_c_plus": {
        "typical_team": ["Full exec team", "50+ Engineers", "Specialized teams"],
        "next_hires": [
            ("Engineering Directors", 0.7, "Multiple eng orgs need leaders"),
            ("Staff Engineers", 0.7, "Technical leadership track"),
            ("Platform Team", 0.65, "Internal platform needs"),
            ("Developer Experience", 0.5, "Productivity at scale"),
        ],
        "team_size": (100, 500)
    }
}

# Ratio-based hiring signals
TEAM_RATIOS = {
    "engineer_to_pm": {
        "healthy": (5, 8),  # 5-8 engineers per PM
        "signal": "Consider hiring a PM",
        "threshold": 8
    },
    "engineer_to_designer": {
        "healthy": (4, 6),
        "signal": "Consider hiring a Designer",
        "threshold": 6
    },
    "engineer_to_devops": {
        "healthy": (8, 12),
        "signal": "Consider hiring DevOps/SRE",
        "threshold": 10
    },
    "engineer_to_em": {
        "healthy": (5, 8),
        "signal": "Consider hiring an Engineering Manager",
        "threshold": 7
    }
}


class RoleSuggestion(BaseModel):
    """A suggested role to hire."""
    role: str
    confidence: float      # 0-1
    reason: str
    priority: str          # "immediate", "soon", "future"
    based_on: str          # "stage", "ratio", "gap", "pattern"


class TeamComposition(BaseModel):
    """Current team composition."""
    total: int
    engineers: int
    pms: int
    designers: int
    devops: int
    managers: int
    data: int
    other: int


class RoleSuggester:
    """
    Suggest what roles a company should hire next.

    Combines:
    1. Company stage patterns ("Seed companies typically need...")
    2. Team ratio analysis ("Engineer:PM ratio is off")
    3. Gap analysis ("No DevOps yet with 10 engineers")
    4. Recent hiring patterns ("You've hired 3 engineers, maybe a PM next")
    """

    def __init__(self):
        self._supabase = None

    @property
    def supabase(self):
        if self._supabase is None:
            self._supabase = get_supabase_client()
        return self._supabase

    async def suggest_next_roles(
        self,
        company_id: str,
        limit: int = 5
    ) -> list[RoleSuggestion]:
        """
        Suggest what roles the company should hire next.

        Args:
            company_id: The company to analyze
            limit: Max suggestions to return

        Returns:
            List of RoleSuggestion, sorted by confidence
        """
        suggestions = []

        # Get company context
        company = await self._get_company_context(company_id)
        team = await self._analyze_team_composition(company_id)

        # 1. Stage-based suggestions
        stage_suggestions = self._suggest_by_stage(company.get("stage", "seed"), team)
        suggestions.extend(stage_suggestions)

        # 2. Ratio-based suggestions
        ratio_suggestions = self._suggest_by_ratios(team)
        suggestions.extend(ratio_suggestions)

        # 3. Gap-based suggestions
        gap_suggestions = self._suggest_by_gaps(team)
        suggestions.extend(gap_suggestions)

        # 4. Recent hiring pattern suggestions
        pattern_suggestions = await self._suggest_by_patterns(company_id)
        suggestions.extend(pattern_suggestions)

        # Deduplicate and sort by confidence
        seen_roles = set()
        unique_suggestions = []
        for s in sorted(suggestions, key=lambda x: x.confidence, reverse=True):
            if s.role.lower() not in seen_roles:
                seen_roles.add(s.role.lower())
                unique_suggestions.append(s)

        return unique_suggestions[:limit]

    async def _get_company_context(self, company_id: str) -> dict:
        """Get company context (stage, size, etc.)."""
        try:
            result = self.supabase.table("companies")\
                .select("*")\
                .eq("id", company_id)\
                .single()\
                .execute()
            return result.data or {}
        except:
            return {}

    async def _analyze_team_composition(self, company_id: str) -> TeamComposition:
        """Analyze current team composition from network data."""
        try:
            # Get all people in the company's network who work there
            people = await company_db.get_people(company_id, limit=1000)

            engineers = 0
            pms = 0
            designers = 0
            devops = 0
            managers = 0
            data_roles = 0
            other = 0

            for person in people:
                p = person.model_dump() if hasattr(person, "model_dump") else person
                title = (p.get("current_title") or "").lower()

                if any(kw in title for kw in ["engineer", "developer", "swe"]):
                    if "manager" in title or "director" in title:
                        managers += 1
                    elif any(kw in title for kw in ["devops", "sre", "platform", "infra"]):
                        devops += 1
                    elif any(kw in title for kw in ["data", "ml", "machine learning"]):
                        data_roles += 1
                    else:
                        engineers += 1
                elif any(kw in title for kw in ["product manager", "pm", "product lead"]):
                    pms += 1
                elif any(kw in title for kw in ["design", "ux", "ui"]):
                    designers += 1
                else:
                    other += 1

            return TeamComposition(
                total=len(people),
                engineers=engineers,
                pms=pms,
                designers=designers,
                devops=devops,
                managers=managers,
                data=data_roles,
                other=other
            )
        except Exception as e:
            logger.warning(f"Could not analyze team: {e}")
            return TeamComposition(
                total=0, engineers=0, pms=0, designers=0,
                devops=0, managers=0, data=0, other=0
            )

    def _suggest_by_stage(
        self,
        stage: str,
        team: TeamComposition
    ) -> list[RoleSuggestion]:
        """Suggest roles based on company stage."""
        suggestions = []

        # Map stage to pattern
        stage_key = stage.lower().replace(" ", "_").replace("-", "_")
        if stage_key not in STAGE_PATTERNS:
            stage_key = "seed"  # Default

        pattern = STAGE_PATTERNS[stage_key]

        for role, confidence, reason in pattern["next_hires"]:
            # Adjust confidence based on team size
            size_range = pattern["team_size"]
            if team.total < size_range[0]:
                confidence *= 0.8  # Too small
            elif team.total > size_range[1]:
                confidence *= 0.7  # Too big for this stage advice

            suggestions.append(RoleSuggestion(
                role=role,
                confidence=round(confidence, 2),
                reason=f"Stage-based: {reason}",
                priority="soon" if confidence > 0.7 else "future",
                based_on="stage"
            ))

        return suggestions

    def _suggest_by_ratios(self, team: TeamComposition) -> list[RoleSuggestion]:
        """Suggest roles based on team ratios."""
        suggestions = []

        # Engineer:PM ratio
        if team.pms == 0 and team.engineers >= 5:
            suggestions.append(RoleSuggestion(
                role="Product Manager",
                confidence=0.9,
                reason=f"You have {team.engineers} engineers and no PM",
                priority="immediate",
                based_on="ratio"
            ))
        elif team.pms > 0 and team.engineers / team.pms > 8:
            suggestions.append(RoleSuggestion(
                role="Product Manager",
                confidence=0.75,
                reason=f"Engineer:PM ratio is {team.engineers}:{team.pms}",
                priority="soon",
                based_on="ratio"
            ))

        # Engineer:Designer ratio
        if team.designers == 0 and team.engineers >= 4:
            suggestions.append(RoleSuggestion(
                role="Product Designer",
                confidence=0.85,
                reason=f"You have {team.engineers} engineers and no designer",
                priority="immediate",
                based_on="ratio"
            ))

        # Engineer:DevOps ratio
        if team.devops == 0 and team.engineers >= 8:
            suggestions.append(RoleSuggestion(
                role="DevOps Engineer",
                confidence=0.8,
                reason=f"You have {team.engineers} engineers and no DevOps",
                priority="immediate",
                based_on="ratio"
            ))

        # Engineer:Manager ratio
        if team.managers == 0 and team.engineers >= 6:
            suggestions.append(RoleSuggestion(
                role="Engineering Manager",
                confidence=0.85,
                reason=f"You have {team.engineers} engineers and no EM",
                priority="immediate",
                based_on="ratio"
            ))

        return suggestions

    def _suggest_by_gaps(self, team: TeamComposition) -> list[RoleSuggestion]:
        """Suggest roles based on obvious gaps."""
        suggestions = []

        # Data gap
        if team.data == 0 and team.total >= 15:
            suggestions.append(RoleSuggestion(
                role="Data Engineer",
                confidence=0.7,
                reason="No data roles with 15+ team members",
                priority="soon",
                based_on="gap"
            ))

        return suggestions

    async def _suggest_by_patterns(self, company_id: str) -> list[RoleSuggestion]:
        """Suggest based on recent hiring patterns."""
        suggestions = []

        try:
            # Get recent searches
            result = self.supabase.table("search_history")\
                .select("role_title")\
                .eq("company_id", company_id)\
                .order("created_at", desc=True)\
                .limit(10)\
                .execute()

            recent_roles = [r["role_title"] for r in result.data or [] if r.get("role_title")]

            # Count role types
            eng_count = sum(1 for r in recent_roles if "engineer" in r.lower())

            if eng_count >= 3:
                suggestions.append(RoleSuggestion(
                    role="Engineering Manager",
                    confidence=0.65,
                    reason=f"You've searched for {eng_count} engineering roles recently",
                    priority="soon",
                    based_on="pattern"
                ))

        except:
            pass

        return suggestions

    async def get_hiring_plan(
        self,
        company_id: str,
        months_ahead: int = 6
    ) -> dict:
        """
        Generate a suggested hiring plan.

        Returns:
            {
                "immediate": [...],   # Hire now
                "quarter_1": [...],   # Next 3 months
                "quarter_2": [...],   # 3-6 months
                "rationale": "..."
            }
        """
        suggestions = await self.suggest_next_roles(company_id, limit=10)

        plan = {
            "immediate": [],
            "quarter_1": [],
            "quarter_2": [],
            "rationale": ""
        }

        for s in suggestions:
            entry = {
                "role": s.role,
                "confidence": s.confidence,
                "reason": s.reason
            }

            if s.priority == "immediate":
                plan["immediate"].append(entry)
            elif s.priority == "soon":
                plan["quarter_1"].append(entry)
            else:
                plan["quarter_2"].append(entry)

        plan["rationale"] = self._generate_rationale(plan)

        return plan

    def _generate_rationale(self, plan: dict) -> str:
        """Generate human-readable rationale for the plan."""
        parts = []

        if plan["immediate"]:
            roles = [r["role"] for r in plan["immediate"]]
            parts.append(f"Immediate priority: {', '.join(roles)}")

        if plan["quarter_1"]:
            roles = [r["role"] for r in plan["quarter_1"]]
            parts.append(f"Next quarter: {', '.join(roles)}")

        return ". ".join(parts) if parts else "No immediate hiring needs identified."
