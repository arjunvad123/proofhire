"""
External Search Services

Integrates with external people search providers (Clado, Apollo, Firecrawl)
to find candidates beyond the founder's network, while maintaining warm
path intelligence.

All providers run in parallel via asyncio.gather() and results are
deduplicated by LinkedIn URL.
"""

from .clado_client import CladoClient
from .apollo_client import ApolloClient
from .firecrawl_client import FirecrawlClient
from .query_generator import QueryGenerator

__all__ = ["CladoClient", "ApolloClient", "FirecrawlClient", "QueryGenerator"]
