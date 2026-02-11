"""
Alert Generator - Generate actionable alerts based on company intelligence.

Alerts are prioritized by:
1. Urgency (critical > high > medium > low)
2. Network impact (more people affected = higher priority)
3. Timing (more recent events = higher priority)

Each alert includes:
- What happened
- Who is affected
- What to do about it
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional
from uuid import UUID

from app.services.company_db import CompanyDBService
from .layoff_tracker import LayoffTracker
from .event_monitor import CompanyEventMonitor

logger = logging.getLogger(__name__)


class AlertGenerator:
    """
    Generate actionable alerts from company intelligence.

    Combines data from multiple sources:
    - Layoff tracker
    - Event monitor
    - Timing intelligence

    Produces prioritized list of actions.
    """

    def __init__(self, company_id: UUID):
        self.company_id = company_id
        self.db = CompanyDBService()
        self.layoff_tracker = LayoffTracker(company_id)
        self.event_monitor = CompanyEventMonitor(company_id)

    async def generate_all_alerts(self) -> dict:
        """
        Generate all alerts based on company intelligence.

        Returns alerts grouped by urgency.
        """
        alerts = []

        # Get layoff exposure
        layoff_exposure = await self.layoff_tracker.get_network_layoff_exposure()

        for company, data in layoff_exposure.get("by_company", {}).items():
            urgency = data.get("urgency", "medium")
            count = data.get("count", 0)
            scale = data.get("scale", "unknown")

            if urgency in ["critical", "high"]:
                alerts.append({
                    "id": f"layoff_{company}",
                    "type": "layoff_exposure",
                    "urgency": urgency,
                    "company": company,
                    "headline": f"{count} network members at {company.title()} - {scale} layoffs",
                    "details": {
                        "affected_count": count,
                        "layoff_date": data.get("layoff_date"),
                        "scale": scale,
                        "members": data.get("members", [])
                    },
                    "recommended_action": self._get_layoff_action(urgency, count, company),
                    "outreach_template": self._generate_layoff_outreach(company)
                })

        # Get general events
        events = await self.event_monitor.get_all_events()

        for event in events.get("all_events", []):
            # Skip layoffs (already handled above)
            if event.get("type") == "layoff":
                continue

            company = event.get("company", "Unknown")
            impact = event.get("network_impact", {})

            alerts.append({
                "id": f"{event.get('type')}_{company}".lower().replace(" ", "_"),
                "type": event.get("type"),
                "urgency": "medium",
                "company": company,
                "headline": f"{event.get('type', 'Event').title()} at {company}",
                "details": event.get("details", {}),
                "network_impact": impact,
                "recommended_action": event.get("impact", {}).get("action", "Monitor situation")
            })

        # Sort by urgency
        urgency_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        alerts.sort(key=lambda x: urgency_order.get(x.get("urgency", "low"), 99))

        # Group by urgency
        by_urgency = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }

        for alert in alerts:
            urgency = alert.get("urgency", "low")
            by_urgency[urgency].append(alert)

        return {
            "total_alerts": len(alerts),
            "summary": {
                "critical": len(by_urgency["critical"]),
                "high": len(by_urgency["high"]),
                "medium": len(by_urgency["medium"]),
                "low": len(by_urgency["low"])
            },
            "by_urgency": by_urgency,
            "all_alerts": alerts
        }

    def _get_layoff_action(self, urgency: str, count: int, company: str) -> str:
        """Generate recommended action for layoff alert."""
        if urgency == "critical":
            return f"URGENT: Reach out to all {count} people at {company.title()} this week. Acknowledge the difficult situation and offer support."
        elif urgency == "high":
            return f"Reach out to {count} people at {company.title()} soon. Check in on how they're doing and if they're open to new opportunities."
        else:
            return f"Consider reaching out to network members at {company.title()} to reconnect."

    def _generate_layoff_outreach(self, company: str) -> str:
        """Generate a template for layoff-sensitive outreach."""
        return f"""Hi [Name],

I heard about the changes at {company.title()} and wanted to reach out. I know this must be a challenging time, regardless of how you were directly affected.

If you're open to it, I'd love to catch up and hear how you're doing. And if you're considering new opportunities, I'm working on some exciting things that might be a fit.

No pressure at all - just wanted you to know I'm thinking of you.

[Your name]"""

    async def get_daily_digest(self) -> dict:
        """
        Generate a daily digest of alerts.

        Summarizes what's happening and what actions to take.
        """
        all_alerts = await self.generate_all_alerts()

        critical_count = all_alerts["summary"]["critical"]
        high_count = all_alerts["summary"]["high"]

        # Generate summary message
        if critical_count > 0:
            summary = f"URGENT: {critical_count} critical alerts require immediate attention"
        elif high_count > 0:
            summary = f"{high_count} high-priority alerts to review this week"
        else:
            summary = "No urgent alerts - focus on proactive outreach"

        # Top actions
        top_actions = []
        for alert in all_alerts["all_alerts"][:5]:
            top_actions.append({
                "action": alert.get("recommended_action"),
                "company": alert.get("company"),
                "affected_count": alert.get("details", {}).get("affected_count", 0)
            })

        return {
            "date": date.today().isoformat(),
            "summary": summary,
            "alert_counts": all_alerts["summary"],
            "top_actions": top_actions,
            "full_alerts": all_alerts
        }

    async def get_company_specific_alert(self, company_name: str) -> Optional[dict]:
        """
        Get alert for a specific company if one exists.

        Useful when looking at a specific person's profile.
        """
        all_alerts = await self.generate_all_alerts()

        for alert in all_alerts["all_alerts"]:
            if alert.get("company", "").lower() == company_name.lower():
                return alert

        return None
