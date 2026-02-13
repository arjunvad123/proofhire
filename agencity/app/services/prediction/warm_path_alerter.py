"""
Warm Path Alerter - Alert when network changes create new opportunities.

Monitors:
- Contacts joining target companies
- Contacts getting promoted (become better connectors)
- New mutual connections
- Contact company changes

Usage:
    alerter = WarmPathAlerter()
    alerts = await alerter.get_alerts(company_id="...")
    # Returns: [
    #   {"type": "new_path", "message": "John joined Google - you can now reach...", ...}
    # ]
"""

import logging
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.services.company_db import company_db
from app.core.database import get_supabase_client

logger = logging.getLogger(__name__)


# =============================================================================
# TARGET COMPANIES (companies where warm paths are especially valuable)
# =============================================================================

TARGET_COMPANIES = {
    # Big Tech
    "google": {"tier": 1, "value": "access to top ML talent"},
    "meta": {"tier": 1, "value": "access to ads/social talent"},
    "apple": {"tier": 1, "value": "access to hardware/design talent"},
    "amazon": {"tier": 1, "value": "access to distributed systems talent"},
    "microsoft": {"tier": 1, "value": "access to enterprise talent"},
    "netflix": {"tier": 1, "value": "access to streaming/infra talent"},

    # High-growth
    "stripe": {"tier": 2, "value": "access to fintech talent"},
    "airbnb": {"tier": 2, "value": "access to marketplace talent"},
    "uber": {"tier": 2, "value": "access to mobility talent"},
    "doordash": {"tier": 2, "value": "access to logistics talent"},
    "coinbase": {"tier": 2, "value": "access to crypto talent"},
    "figma": {"tier": 2, "value": "access to design tool talent"},
    "notion": {"tier": 2, "value": "access to productivity talent"},
    "linear": {"tier": 2, "value": "access to dev tools talent"},
    "vercel": {"tier": 2, "value": "access to frontend talent"},
    "supabase": {"tier": 2, "value": "access to backend/db talent"},

    # AI/ML companies
    "openai": {"tier": 1, "value": "access to AI research talent"},
    "anthropic": {"tier": 1, "value": "access to AI safety talent"},
    "deepmind": {"tier": 1, "value": "access to AI research talent"},
    "cohere": {"tier": 2, "value": "access to NLP talent"},
    "scale": {"tier": 2, "value": "access to ML ops talent"},
}


class WarmPathAlert(BaseModel):
    """An alert about a new warm path opportunity."""
    id: str
    alert_type: str          # "new_path", "promotion", "new_connection"
    priority: str            # "high", "medium", "low"

    # The connector (person in your network)
    connector_id: str
    connector_name: str
    connector_title: Optional[str]

    # The change
    change_type: str         # "joined_company", "promoted", "new_connection"
    change_detail: str       # "Joined Google as Engineering Manager"

    # The opportunity
    opportunity: str         # "You can now reach people at Google"
    suggested_action: str    # "Ask John for intros to ML engineers at Google"

    # Metadata
    company_affected: Optional[str]
    created_at: datetime


class WarmPathAlerter:
    """
    Monitor network changes and alert on new warm path opportunities.

    Alerts when:
    1. A contact joins a target company (new access)
    2. A contact gets promoted (stronger connector)
    3. A new mutual connection is made
    4. A contact's company raises funding (growing team)
    """

    def __init__(self):
        self._supabase = None
        self._network_snapshot = {}  # For detecting changes

    @property
    def supabase(self):
        if self._supabase is None:
            self._supabase = get_supabase_client()
        return self._supabase

    async def get_alerts(
        self,
        company_id: str,
        days_lookback: int = 30,
        limit: int = 20
    ) -> list[WarmPathAlert]:
        """
        Get warm path alerts for a company.

        Args:
            company_id: The company to check
            days_lookback: How far back to look for changes
            limit: Max alerts to return

        Returns:
            List of WarmPathAlert, sorted by priority
        """
        alerts = []

        # Get current network
        people = await company_db.get_people(company_id, limit=5000)

        for person in people:
            p = person.model_dump() if hasattr(person, "model_dump") else person

            # Check for target company membership
            alert = self._check_target_company_alert(p)
            if alert:
                alerts.append(alert)

            # Check for recent company change
            change_alert = self._check_company_change_alert(p)
            if change_alert:
                alerts.append(change_alert)

            # Check for promotion signals
            promo_alert = self._check_promotion_alert(p)
            if promo_alert:
                alerts.append(promo_alert)

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        alerts.sort(key=lambda x: priority_order.get(x.priority, 3))

        return alerts[:limit]

    def _check_target_company_alert(self, person: dict) -> Optional[WarmPathAlert]:
        """Check if person is at a target company."""
        company = (person.get("current_company") or "").lower()

        for target, info in TARGET_COMPANIES.items():
            if target in company:
                priority = "high" if info["tier"] == 1 else "medium"

                return WarmPathAlert(
                    id=f"target-{person.get('id')}",
                    alert_type="target_company",
                    priority=priority,
                    connector_id=str(person.get("id", "")),
                    connector_name=person.get("full_name") or "Unknown",
                    connector_title=person.get("current_title"),
                    change_type="at_target_company",
                    change_detail=f"Works at {company.title()}",
                    opportunity=f"You have access to {company.title()} through your network",
                    suggested_action=f"Ask {person.get('full_name', 'them').split()[0]} for intros - {info['value']}",
                    company_affected=company.title(),
                    created_at=datetime.utcnow()
                )

        return None

    def _check_company_change_alert(self, person: dict) -> Optional[WarmPathAlert]:
        """Check if person recently changed companies."""
        # Look for signals of recent change
        employment = person.get("employment_history") or []

        if len(employment) >= 2:
            current = employment[0] if employment else {}
            previous = employment[1] if len(employment) > 1 else {}

            # Check if current job started recently (simulated)
            current_start = current.get("start_date") or current.get("start")
            if current_start:
                try:
                    if isinstance(current_start, str) and len(current_start) >= 7:
                        start_date = datetime.strptime(current_start[:7], "%Y-%m")
                        months_ago = (datetime.now() - start_date).days / 30

                        if months_ago <= 6:  # Changed in last 6 months
                            current_company = current.get("company") or person.get("current_company")
                            previous_company = previous.get("company")

                            # Check if moved to target company
                            current_lower = (current_company or "").lower()
                            for target, info in TARGET_COMPANIES.items():
                                if target in current_lower:
                                    return WarmPathAlert(
                                        id=f"change-{person.get('id')}",
                                        alert_type="company_change",
                                        priority="high",
                                        connector_id=str(person.get("id", "")),
                                        connector_name=person.get("full_name") or "Unknown",
                                        connector_title=person.get("current_title"),
                                        change_type="joined_company",
                                        change_detail=f"Recently joined {current_company} from {previous_company}",
                                        opportunity=f"NEW: You now have access to {current_company}",
                                        suggested_action=f"Congrats message + ask for intros",
                                        company_affected=current_company,
                                        created_at=datetime.utcnow()
                                    )
                except (ValueError, TypeError):
                    pass

        return None

    def _check_promotion_alert(self, person: dict) -> Optional[WarmPathAlert]:
        """Check if person was recently promoted (stronger connector)."""
        title = (person.get("current_title") or "").lower()

        # Look for leadership titles
        leadership_keywords = ["head of", "director", "vp", "chief", "lead", "manager"]

        if any(kw in title for kw in leadership_keywords):
            company = person.get("current_company") or "their company"

            # Only alert for target companies
            company_lower = company.lower()
            for target in TARGET_COMPANIES:
                if target in company_lower:
                    return WarmPathAlert(
                        id=f"promo-{person.get('id')}",
                        alert_type="promotion",
                        priority="medium",
                        connector_id=str(person.get("id", "")),
                        connector_name=person.get("full_name") or "Unknown",
                        connector_title=person.get("current_title"),
                        change_type="promoted",
                        change_detail=f"Now a leader at {company}",
                        opportunity=f"Stronger connector - can refer across teams",
                        suggested_action=f"Ask about team growth plans",
                        company_affected=company,
                        created_at=datetime.utcnow()
                    )

        return None

    async def get_target_company_coverage(
        self,
        company_id: str
    ) -> dict:
        """
        Get coverage of target companies in the network.

        Returns:
            {
                "google": {"contacts": 5, "strongest_connector": "John Doe"},
                "meta": {"contacts": 3, "strongest_connector": "Jane Smith"},
                ...
            }
        """
        people = await company_db.get_people(company_id, limit=5000)

        coverage = {}

        for person in people:
            p = person.model_dump() if hasattr(person, "model_dump") else person
            company = (p.get("current_company") or "").lower()
            title = (p.get("current_title") or "").lower()

            for target in TARGET_COMPANIES:
                if target in company:
                    if target not in coverage:
                        coverage[target] = {
                            "contacts": 0,
                            "connectors": [],
                            "strongest_connector": None
                        }

                    coverage[target]["contacts"] += 1
                    coverage[target]["connectors"].append({
                        "name": p.get("full_name"),
                        "title": p.get("current_title"),
                        "linkedin": p.get("linkedin_url")
                    })

                    # Track strongest connector (by title seniority)
                    if any(kw in title for kw in ["director", "vp", "head", "manager"]):
                        coverage[target]["strongest_connector"] = p.get("full_name")

        return coverage

    async def get_missing_coverage(
        self,
        company_id: str
    ) -> list[dict]:
        """
        Get target companies with no coverage.

        Returns companies the founder should try to get connections at.
        """
        coverage = await self.get_target_company_coverage(company_id)

        missing = []
        for target, info in TARGET_COMPANIES.items():
            if target not in coverage:
                missing.append({
                    "company": target.title(),
                    "tier": info["tier"],
                    "value": info["value"],
                    "suggestion": f"Try to connect with people at {target.title()}"
                })

        # Sort by tier
        missing.sort(key=lambda x: x["tier"])

        return missing
