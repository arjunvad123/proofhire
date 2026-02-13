"""
Reasoning Layer - Advanced AI reasoning using Claude

This module provides:
- Query reasoning: Generate intelligent search queries
- Candidate analysis: Deep analysis via agent swarm
- Ranking reasoning: Explain why candidates are ranked
- Context building: Generate rich "why consider" narratives

Note: Originally designed for Kimi K2.5, now uses Claude API.
      Kimi imports are maintained for backwards compatibility.
"""

from .claude_engine import (
    ClaudeReasoningEngine,
    claude_engine,
    # Backwards compatibility aliases
    KimiReasoningEngine,
    kimi_engine,
    # Data models
    QueryReasoning,
    CandidateAnalysis,
    RankingReasoning,
)

__all__ = [
    # Primary exports
    "ClaudeReasoningEngine",
    "claude_engine",
    # Backwards compatibility
    "KimiReasoningEngine",
    "kimi_engine",
    # Data models
    "QueryReasoning",
    "CandidateAnalysis",
    "RankingReasoning",
]
