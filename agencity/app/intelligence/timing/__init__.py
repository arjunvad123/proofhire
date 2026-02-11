"""
Timing Intelligence - Pillar 2

Predict who's ready to move BEFORE they know it.

Key timing signals:
1. Vesting cliff approaching (4-year anniversary)
2. Company had layoffs (fear + available talent)
3. Manager departed (org instability)
4. Title signals ("consultant", "advisor", "open to")
5. Profile updated recently (active job market)

The goal: Reach out BEFORE they're "Open to Work"
When everyone sees "Open to Work", you're competing with 100 recruiters.
"""

from .readiness_scorer import ReadinessScorer
from .tenure_tracker import TenureTracker
from .vesting_predictor import VestingPredictor

__all__ = ["ReadinessScorer", "TenureTracker", "VestingPredictor"]
