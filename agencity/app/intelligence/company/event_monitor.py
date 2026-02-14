"""
Company Event Monitor - Track company events that affect hiring decisions.

Events that matter:
1. Layoffs - Fear, uncertainty, availability
2. Acquisition - Culture change, redundancy concerns
3. IPO - Liquidity events, might want to cash out and move
4. Funding rounds - Stability indicator (positive or concerning if none)
5. Exec departures - Leadership instability
6. Earnings - Performance indicator
7. Product launches/failures - Team morale

In production, this would monitor:
- News APIs (Google News, NewsAPI, Bing News)
- SEC filings (for public companies)
- Crunchbase (for funding)
- LinkedIn (for exec moves)
- Social media (for sentiment)
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional
from uuid import UUID

from app.services.company_db import CompanyDBService

logger = logging.getLogger(__name__)


# Event types and their impact on hiring
EVENT_IMPACT = {
    "layoff": {
        "readiness_boost": 0.4,
        "sentiment": "negative",
        "action": "Empathetic outreach - acknowledge difficulty, offer opportunity"
    },
    "acquisition": {
        "readiness_boost": 0.3,
        "sentiment": "uncertain",
        "action": "Check in - many people leave during integrations"
    },
    "merger": {
        "readiness_boost": 0.3,
        "sentiment": "uncertain",
        "action": "Similar to acquisition - redundancies likely"
    },
    "ipo": {
        "readiness_boost": 0.2,
        "sentiment": "positive",
        "action": "Wait 6 months for lockup to expire, then reach out"
    },
    "funding_round": {
        "readiness_boost": -0.1,  # Less likely to leave after new funding
        "sentiment": "positive",
        "action": "Company is growing - might be harder to recruit from"
    },
    "exec_departure": {
        "readiness_boost": 0.2,
        "sentiment": "uncertain",
        "action": "Leadership change - check if reports are affected"
    },
    "bad_earnings": {
        "readiness_boost": 0.2,
        "sentiment": "negative",
        "action": "Company struggling - people may want stability"
    },
    "product_shutdown": {
        "readiness_boost": 0.3,
        "sentiment": "negative",
        "action": "Team may be reassigned or laid off"
    },
    "hiring_freeze": {
        "readiness_boost": 0.2,
        "sentiment": "negative",
        "action": "People may feel stuck - good time to offer growth"
    },
    "rto_mandate": {
        "readiness_boost": 0.2,
        "sentiment": "negative",
        "action": "Remote workers may be looking to leave"
    }
}


class CompanyEventMonitor:
    """
    Monitor company events and their impact on the network.

    Tracks events at companies where network members work
    and generates alerts when something happens.
    """

    def __init__(self, company_id: UUID):
        self.company_id = company_id
        self.db = CompanyDBService()
        self._watched_companies = None

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

    async def get_watched_companies(self) -> dict:
        """
        Get companies to watch (where network members work).

        Returns companies sorted by number of network members.
        """
        if self._watched_companies:
            return self._watched_companies

        # Get all network connections
        all_people_raw = await self.db.get_people(
            self.company_id,
            limit=999999,  # Get all (pagination handles this)
            filters={"is_from_network": True}
        )
        all_people = [self._to_dict(p) for p in all_people_raw]

        # Count by company
        company_counts = {}
        for person in all_people:
            company = person.get("current_company")
            if company:
                company_lower = company.lower().strip()
                if company_lower not in company_counts:
                    company_counts[company_lower] = {
                        "display_name": company,
                        "count": 0,
                        "members": []
                    }
                company_counts[company_lower]["count"] += 1
                company_counts[company_lower]["members"].append({
                    "id": str(person.get("id")),
                    "name": person.get("full_name"),
                    "title": person.get("current_title")
                })

        # Sort by count
        sorted_companies = sorted(
            company_counts.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )

        self._watched_companies = {
            "total_companies": len(company_counts),
            "total_network_members": len(all_people),
            "companies": [
                {
                    "name": data["display_name"],
                    "normalized_name": name,
                    "network_members": data["count"],
                    "sample_members": data["members"][:3]
                }
                for name, data in sorted_companies[:50]  # Top 50
            ]
        }

        return self._watched_companies

    async def check_for_events(self, company_name: str) -> list[dict]:
        """
        Check for recent events at a company.

        In production, this would query news APIs and databases.
        For now, returns placeholder events based on known data.
        """
        from .layoff_tracker import LayoffTracker

        events = []

        # Check layoff tracker
        layoff_tracker = LayoffTracker(self.company_id)
        layoff_info = layoff_tracker.get_layoff_info(company_name)

        if layoff_info:
            events.append({
                "type": "layoff",
                "company": company_name,
                "date": layoff_info.get("date"),
                "details": {
                    "headcount": layoff_info.get("headcount"),
                    "percentage": layoff_info.get("percentage"),
                    "scale": layoff_info.get("scale"),
                    "divisions": layoff_info.get("divisions", [])
                },
                "impact": EVENT_IMPACT["layoff"],
                "source": layoff_info.get("source", "unknown")
            })

        return events

    async def get_all_events(self) -> dict:
        """
        Get all recent events affecting watched companies.

        Returns events grouped by type and urgency.
        """
        watched = await self.get_watched_companies()

        all_events = []
        companies_with_events = set()

        for company_data in watched["companies"]:
            company_name = company_data["name"]
            events = await self.check_for_events(company_name)

            for event in events:
                event["network_impact"] = {
                    "members_affected": company_data["network_members"],
                    "sample_members": company_data["sample_members"]
                }
                all_events.append(event)
                companies_with_events.add(company_name.lower())

        # Group by type
        by_type = {}
        for event in all_events:
            event_type = event.get("type", "unknown")
            if event_type not in by_type:
                by_type[event_type] = []
            by_type[event_type].append(event)

        # Sort within each type by network impact
        for event_type in by_type:
            by_type[event_type].sort(
                key=lambda x: x.get("network_impact", {}).get("members_affected", 0),
                reverse=True
            )

        return {
            "total_events": len(all_events),
            "companies_affected": len(companies_with_events),
            "total_watched_companies": watched["total_companies"],
            "by_type": by_type,
            "all_events": all_events
        }

    def get_event_impact(self, event_type: str) -> dict:
        """Get the impact profile for an event type."""
        return EVENT_IMPACT.get(event_type, {
            "readiness_boost": 0.0,
            "sentiment": "unknown",
            "action": "Monitor and assess"
        })

    async def get_company_intelligence_report(self, company_name: str) -> dict:
        """
        Get a full intelligence report for a specific company.

        Includes:
        - Network members at the company
        - Recent events
        - Recommended actions
        """
        # Get network members at this company
        all_people_raw = await self.db.get_people(
            self.company_id,
            limit=999999,  # Get all (pagination handles this)
            filters={"is_from_network": True}
        )
        all_people = [self._to_dict(p) for p in all_people_raw]

        members_at_company = [
            {
                "id": str(p.get("id")),
                "name": p.get("full_name"),
                "title": p.get("current_title"),
                "linkedin_url": p.get("linkedin_url")
            }
            for p in all_people
            if (p.get("current_company") or "").lower() == company_name.lower()
        ]

        # Get events
        events = await self.check_for_events(company_name)

        # Generate recommendations
        recommendations = []
        for event in events:
            impact = event.get("impact", {})
            recommendations.append({
                "based_on": event.get("type"),
                "action": impact.get("action"),
                "urgency": "high" if impact.get("readiness_boost", 0) >= 0.3 else "medium"
            })

        if not recommendations:
            recommendations.append({
                "based_on": "no_recent_events",
                "action": "No concerning events - standard outreach approach",
                "urgency": "low"
            })

        return {
            "company": company_name,
            "network_members": {
                "count": len(members_at_company),
                "members": members_at_company
            },
            "recent_events": events,
            "recommendations": recommendations,
            "overall_sentiment": events[0]["impact"]["sentiment"] if events else "neutral"
        }
