"""
Reinforcement Learning Module

Provides:
- Reward Model: Scores reasoning quality based on outcomes
- GRPO Trainer: Trains the model using Group Relative Policy Optimization
- Online Learner: Continuous improvement from new feedback
"""

from .reward_model import RewardModel, reward_model

__all__ = ["RewardModel", "reward_model"]
