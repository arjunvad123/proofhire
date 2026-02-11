"""
Layoff Tracker - Track layoff announcements and their impact on the network.

Layoffs are one of the strongest timing signals:
1. People who survived might be nervous about being next
2. People who were laid off are actively looking
3. Company morale is typically low after layoffs
4. This is a good time to reach out with empathy

Data sources (in production):
- News APIs (Google News, NewsAPI)
- Layoff tracking sites (layoffs.fyi, levels.fyi)
- SEC filings (for public companies)
- Social media monitoring
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional
from uuid import UUID

from app.services.company_db import CompanyDBService

logger = logging.getLogger(__name__)


# Known layoffs (in production, this would be updated from news APIs)
# Format: company -> {date, headcount, percentage, scale, source}
KNOWN_LAYOFFS = {
    # 2024 Layoffs
    "google": {
        "date": "2024-01-10",
        "headcount": 1000,
        "percentage": None,
        "scale": "medium",
        "divisions": ["Pixel", "Nest", "Fitbit", "Assistant"],
        "source": "news"
    },
    "meta": {
        "date": "2024-04-24",
        "headcount": 500,
        "percentage": None,
        "scale": "small",
        "divisions": ["WhatsApp", "Instagram", "Reality Labs"],
        "source": "news"
    },
    "amazon": {
        "date": "2024-01-10",
        "headcount": 500,
        "percentage": None,
        "scale": "small",
        "divisions": ["Prime Video", "MGM Studios", "Twitch"],
        "source": "news"
    },
    "microsoft": {
        "date": "2024-01-25",
        "headcount": 1900,
        "percentage": 8,
        "scale": "medium",
        "divisions": ["Gaming", "Xbox", "Activision Blizzard"],
        "source": "news"
    },
    "salesforce": {
        "date": "2024-01-24",
        "headcount": 700,
        "percentage": 1,
        "scale": "small",
        "divisions": ["Sales", "Engineering"],
        "source": "news"
    },
    "intel": {
        "date": "2024-08-01",
        "headcount": 15000,
        "percentage": 15,
        "scale": "massive",
        "divisions": ["All divisions"],
        "source": "news"
    },
    "dell": {
        "date": "2024-02-05",
        "headcount": 6000,
        "percentage": 5,
        "scale": "large",
        "divisions": ["Sales", "Marketing"],
        "source": "news"
    },
    "cisco": {
        "date": "2024-02-14",
        "headcount": 4000,
        "percentage": 5,
        "scale": "large",
        "divisions": ["Engineering", "Sales"],
        "source": "news"
    },
    "twilio": {
        "date": "2024-02-13",
        "headcount": 1500,
        "percentage": 17,
        "scale": "large",
        "divisions": ["All divisions"],
        "source": "news"
    },
    "snap": {
        "date": "2024-02-05",
        "headcount": 500,
        "percentage": 10,
        "scale": "medium",
        "divisions": ["Engineering", "Product"],
        "source": "news"
    },
    "discord": {
        "date": "2024-01-11",
        "headcount": 170,
        "percentage": 17,
        "scale": "medium",
        "divisions": ["Engineering"],
        "source": "news"
    },
    "spotify": {
        "date": "2024-01-22",
        "headcount": 1500,
        "percentage": 17,
        "scale": "large",
        "divisions": ["All divisions"],
        "source": "news"
    },
    "zoom": {
        "date": "2024-02-05",
        "headcount": 150,
        "percentage": 2,
        "scale": "small",
        "divisions": ["Sales"],
        "source": "news"
    },
    "docusign": {
        "date": "2024-02-15",
        "headcount": 400,
        "percentage": 6,
        "scale": "medium",
        "divisions": ["Engineering", "Sales"],
        "source": "news"
    },
    "paypal": {
        "date": "2024-01-30",
        "headcount": 2500,
        "percentage": 9,
        "scale": "large",
        "divisions": ["All divisions"],
        "source": "news"
    },
    "ebay": {
        "date": "2024-01-23",
        "headcount": 1000,
        "percentage": 9,
        "scale": "medium",
        "divisions": ["Engineering", "Product"],
        "source": "news"
    },
    "unity": {
        "date": "2024-01-08",
        "headcount": 1800,
        "percentage": 25,
        "scale": "massive",
        "divisions": ["All divisions"],
        "source": "news"
    },
    "riot games": {
        "date": "2024-01-22",
        "headcount": 530,
        "percentage": 11,
        "scale": "medium",
        "divisions": ["Game development"],
        "source": "news"
    },
}


class LayoffTracker:
    """
    Track layoff announcements and their impact on the network.

    In production, this would:
    1. Monitor news APIs for layoff announcements
    2. Track layoffs.fyi and similar sites
    3. Update the KNOWN_LAYOFFS data periodically
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

    def get_layoff_info(self, company_name: str) -> Optional[dict]:
        """Get layoff information for a company."""
        company_lower = company_name.lower()

        # Check exact match first
        if company_lower in KNOWN_LAYOFFS:
            return {
                "company": company_name,
                **KNOWN_LAYOFFS[company_lower]
            }

        # Check partial matches
        for known_company, info in KNOWN_LAYOFFS.items():
            if known_company in company_lower or company_lower in known_company:
                return {
                    "company": company_name,
                    "matched_to": known_company,
                    **info
                }

        return None

    async def get_network_layoff_exposure(self) -> dict:
        """
        Analyze how many network members are at companies with recent layoffs.

        Returns breakdown by company and urgency.
        """
        # Get all network connections
        all_people_raw = await self.db.get_people(
            self.company_id,
            limit=10000,
            filters={"is_from_network": True}
        )
        all_people = [self._to_dict(p) for p in all_people_raw]

        affected_people = []
        companies_with_layoffs = {}

        for person in all_people:
            company = person.get("current_company")
            if not company:
                continue

            layoff_info = self.get_layoff_info(company)

            if layoff_info:
                # Track by company
                matched = layoff_info.get("matched_to", company.lower())
                if matched not in companies_with_layoffs:
                    companies_with_layoffs[matched] = {
                        "layoff_info": layoff_info,
                        "network_members": []
                    }

                companies_with_layoffs[matched]["network_members"].append({
                    "id": str(person.get("id")),
                    "name": person.get("full_name"),
                    "title": person.get("current_title"),
                    "company": person.get("current_company"),
                    "linkedin_url": person.get("linkedin_url")
                })

                affected_people.append({
                    **person,
                    "layoff_info": layoff_info
                })

        # Calculate urgency based on recency and scale
        for company, data in companies_with_layoffs.items():
            layoff_date = data["layoff_info"].get("date")
            scale = data["layoff_info"].get("scale", "unknown")

            if layoff_date:
                days_ago = (date.today() - datetime.strptime(layoff_date, "%Y-%m-%d").date()).days

                if days_ago <= 30 and scale in ["large", "massive"]:
                    data["urgency"] = "critical"
                elif days_ago <= 60:
                    data["urgency"] = "high"
                elif days_ago <= 180:
                    data["urgency"] = "medium"
                else:
                    data["urgency"] = "low"
            else:
                data["urgency"] = "medium"

        return {
            "total_network_members": len(all_people),
            "affected_members": len(affected_people),
            "affected_percentage": round(len(affected_people) / len(all_people) * 100, 1) if all_people else 0,
            "companies_with_layoffs": len(companies_with_layoffs),
            "by_company": {
                company: {
                    "count": len(data["network_members"]),
                    "urgency": data.get("urgency"),
                    "layoff_date": data["layoff_info"].get("date"),
                    "scale": data["layoff_info"].get("scale"),
                    "members": data["network_members"][:5]  # Top 5
                }
                for company, data in companies_with_layoffs.items()
            },
            "recommended_actions": self._get_recommended_actions(companies_with_layoffs)
        }

    def _get_recommended_actions(self, companies: dict) -> list[dict]:
        """Generate recommended actions based on layoff exposure."""
        actions = []

        # Sort by urgency
        critical = [(c, d) for c, d in companies.items() if d.get("urgency") == "critical"]
        high = [(c, d) for c, d in companies.items() if d.get("urgency") == "high"]

        for company, data in critical:
            count = len(data["network_members"])
            actions.append({
                "urgency": "critical",
                "company": company,
                "action": f"Reach out to {count} people at {company.title()} - recent major layoffs",
                "reason": "Company just had massive layoffs - people are nervous and looking"
            })

        for company, data in high:
            count = len(data["network_members"])
            actions.append({
                "urgency": "high",
                "company": company,
                "action": f"Check in with {count} people at {company.title()}",
                "reason": "Recent layoffs - good time to reconnect"
            })

        return actions[:10]  # Top 10 actions

    def is_company_affected(self, company_name: str) -> bool:
        """Quick check if a company has recent layoffs."""
        return self.get_layoff_info(company_name) is not None
