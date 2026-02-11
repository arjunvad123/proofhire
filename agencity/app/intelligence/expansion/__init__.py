"""
Former Colleague Expansion - Pillar 3

The key insight: Same company + Same time = They actually know each other.

For each person in the network, we can find their former colleagues
by querying for people who worked at the same company during
overlapping time periods.

This gives us:
1. Warm paths to new candidates (network member can intro)
2. High-quality connections (actually worked together)
3. Scalable discovery (can find hundreds of warm connections)
"""

from .colleague_expander import ColleagueExpander
from .warm_path_finder import WarmPathFinder

__all__ = ["ColleagueExpander", "WarmPathFinder"]
