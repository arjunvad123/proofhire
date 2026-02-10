"""Data sources for candidate search."""

from app.sources.base import DataSource
from app.sources.github import GitHubSource
from app.sources.network import NetworkSource

__all__ = [
    "DataSource",
    "GitHubSource",
    "NetworkSource",
]
