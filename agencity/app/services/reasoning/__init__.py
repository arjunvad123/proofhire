"""
Reasoning Layer - Advanced AI reasoning using Kimi K2.5

This module provides:
- Query reasoning: Generate intelligent search queries
- Candidate analysis: Deep analysis via agent swarm
- Ranking reasoning: Explain why candidates are ranked
- Context building: Generate rich "why consider" narratives
"""

from .kimi_engine import KimiReasoningEngine, kimi_engine

__all__ = ["KimiReasoningEngine", "kimi_engine"]
