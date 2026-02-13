"""
Feedback Collection System

Collects user actions on candidates to train the reward model:
- Views, saves, contacts, interviews, hires, rejections
- Implicit signals (time spent, scroll depth)
- Explicit feedback (ratings, comments)
"""

from .collector import FeedbackCollector, feedback_collector, FeedbackAction

__all__ = ["FeedbackCollector", "feedback_collector", "FeedbackAction"]
