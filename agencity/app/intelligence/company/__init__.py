"""
Company Intelligence - Pillar 4

Monitor companies where network members work.
Track events that might make them open to opportunities:

1. Layoffs - People are scared, might want stability
2. Acquisition - Uncertainty about future, culture change
3. Bad earnings - Budget cuts, morale down
4. Exec departure - Leadership instability
5. No funding in 18mo - Startup might be failing
6. IPO/Acquisition announced - Vesting changes, opportunities elsewhere

The goal: Be the first to reach out when something happens,
before they even start looking.
"""

from .event_monitor import CompanyEventMonitor
from .layoff_tracker import LayoffTracker
from .alert_generator import AlertGenerator

__all__ = ["CompanyEventMonitor", "LayoffTracker", "AlertGenerator"]
