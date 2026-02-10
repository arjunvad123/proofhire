"""
Data sources for candidate search.

Priority Order:
P0 - Our Network (6,000+ opted-in candidates)
P1 - GitHub (100M+ developers)
P2 - Clado/LinkedIn (800M+ professionals)
P3 - Pearch/LinkedIn (alternative to Clado)
P4 - Devpost (2M+ hackathon participants)
P5 - Codeforces (600K+ competitive programmers)
P6 - Stack Overflow (millions of developers)
P7 - Hacker News (active job seekers)
P8 - ProductHunt (makers and builders)
"""

from app.sources.base import DataSource
from app.sources.network import NetworkSource
from app.sources.github import GitHubSource
from app.sources.clado import CladoSource
from app.sources.pearch import PearchSource
from app.sources.devpost import DevpostSource
from app.sources.codeforces import CodeforcesSource, LeetCodeSource
from app.sources.stackoverflow import StackOverflowSource
from app.sources.hackernews import HackerNewsSource
from app.sources.producthunt import ProductHuntSource

__all__ = [
    # Base
    "DataSource",
    # P0 - Internal
    "NetworkSource",
    # P1 - Code
    "GitHubSource",
    # P2-P3 - LinkedIn
    "CladoSource",
    "PearchSource",
    # P4 - Hackathons
    "DevpostSource",
    # P5 - Competitive Programming
    "CodeforcesSource",
    "LeetCodeSource",
    # P6 - Q&A
    "StackOverflowSource",
    # P7 - Job Seekers
    "HackerNewsSource",
    # P8 - Builders
    "ProductHuntSource",
]
