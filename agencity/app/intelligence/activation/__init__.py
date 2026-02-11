"""
Network Activation - Pillar 1

The highest-signal, lowest-tech approach:
Ask your network "Who's the best ML engineer you've ever worked with?"

Why this works:
1. Your network has already done the filtering (they know who's actually good)
2. Warm intro is guaranteed (they recommended the person)
3. Trust transfers through the relationship
"""

from .reverse_reference import ReverseReferenceGenerator
from .message_generator import ActivationMessageGenerator

__all__ = ["ReverseReferenceGenerator", "ActivationMessageGenerator"]
