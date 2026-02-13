"""
Prediction Layer - Anticipate What Founders Need Before They Ask

This module provides predictive intelligence:

1. Query Autocomplete - Suggest search queries based on history
2. Role Suggestion - Predict what roles they'll need next
3. Candidate Surfacing - Surface candidates who just became available
4. Skill Prediction - Auto-suggest requirements for roles
5. Warm Path Alerts - Alert when network creates new opportunities
6. Interview Prediction - Predict which candidates they'll interview

Architecture:
┌─────────────────────────────────────────────────────────────┐
│                    PREDICTION ENGINE                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Query     │  │    Role     │  │  Candidate  │         │
│  │ Autocomplete│  │  Suggester  │  │  Surfacer   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Skill     │  │  Warm Path  │  │  Interview  │         │
│  │  Predictor  │  │   Alerter   │  │  Predictor  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
"""

from .engine import PredictionEngine, prediction_engine
from .query_autocomplete import QueryAutocomplete
from .role_suggester import RoleSuggester
from .candidate_surfacer import CandidateSurfacer
from .skill_predictor import SkillPredictor
from .warm_path_alerter import WarmPathAlerter
from .interview_predictor import InterviewPredictor

__all__ = [
    "PredictionEngine",
    "prediction_engine",
    "QueryAutocomplete",
    "RoleSuggester",
    "CandidateSurfacer",
    "SkillPredictor",
    "WarmPathAlerter",
    "InterviewPredictor"
]
