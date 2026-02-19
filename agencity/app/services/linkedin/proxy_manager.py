"""
Residential proxy management for LinkedIn automation.

Handles:
- Proxy pool management
- Location-based proxy selection
- Proxy rotation
"""

import random
from typing import Optional, Dict, List
from dataclasses import dataclass

from app.config import settings


@dataclass
class ProxyConfig:
    """Proxy configuration."""
    server: str
    username: Optional[str] = None
    password: Optional[str] = None


class ProxyManager:
    """Manages residential proxy pool for LinkedIn automation."""

    # Mapping of locations to proxy regions
    LOCATION_TO_REGION = {
        'san francisco': 'us-ca',
        'california': 'us-ca',
        'los angeles': 'us-ca',
        'new york': 'us-ny',
        'chicago': 'us-il',
        'seattle': 'us-wa',
        'boston': 'us-ma',
        'austin': 'us-tx',
        'london': 'gb-london',
        'berlin': 'de-berlin',
        'paris': 'fr-paris',
        'singapore': 'sg-singapore',
        'toronto': 'ca-toronto',
    }

    def __init__(self):
        """Initialize proxy manager."""
        self.provider = settings.proxy_provider
        self.username = settings.proxy_username
        self.password = settings.proxy_password

    def get_proxy_for_location(self, location: Optional[str]) -> Optional[Dict[str, str]]:
        """
        Get proxy configuration for a location.

        Args:
            location: User's location string (e.g., "San Francisco, CA")

        Returns:
            Proxy config dict for Playwright or None if no proxy configured
        """
        if not self.provider or not self.username:
            return None

        # Determine region from location
        region = self._get_region_from_location(location)

        # Get proxy URL based on provider
        if self.provider == 'smartproxy':
            proxy_url = self._get_smartproxy_url(region)
        elif self.provider == 'brightdata':
            proxy_url = self._get_brightdata_url(region)
        else:
            # Default to US proxy
            proxy_url = self._get_smartproxy_url('us')

        return {
            'server': proxy_url,
            'username': self.username,
            'password': self.password
        }

    def get_scraper_proxy(self, proxy_location: str) -> Optional[Dict[str, str]]:
        """
        Get proxy for scraper account.

        Args:
            proxy_location: Proxy region code (e.g., 'us-ca', 'gb-london')

        Returns:
            Proxy config dict
        """
        if not self.provider or not self.username:
            return None

        if self.provider == 'smartproxy':
            proxy_url = self._get_smartproxy_url(proxy_location)
        elif self.provider == 'brightdata':
            proxy_url = self._get_brightdata_url(proxy_location)
        else:
            proxy_url = self._get_smartproxy_url('us')

        return {
            'server': proxy_url,
            'username': self.username,
            'password': self.password
        }

    def _get_region_from_location(self, location: Optional[str]) -> str:
        """Extract region code from location string."""
        if not location:
            return 'us'  # Default to US

        location_lower = location.lower()

        # Check known locations
        for loc_key, region in self.LOCATION_TO_REGION.items():
            if loc_key in location_lower:
                return region

        # Check for country codes
        if 'uk' in location_lower or 'united kingdom' in location_lower:
            return 'gb-london'
        if 'canada' in location_lower:
            return 'ca-toronto'
        if 'germany' in location_lower:
            return 'de-berlin'
        if 'france' in location_lower:
            return 'fr-paris'

        # Default to US
        return 'us'

    def _get_smartproxy_url(self, region: str) -> str:
        """
        Get Smartproxy URL for region.

        Smartproxy format: http://gate.smartproxy.com:7000
        With session: http://user-{username}-session-{session}:pass@gate.smartproxy.com:7000
        """
        # Generate random session ID for sticky session
        session_id = random.randint(1000000, 9999999)

        # Smartproxy uses country codes
        country = self._region_to_country_code(region)

        return f'http://gate.smartproxy.com:7000'

    def _get_brightdata_url(self, region: str) -> str:
        """
        Get Bright Data (formerly Luminati) URL for region.

        Format: http://brd.superproxy.io:22225
        """
        return 'http://brd.superproxy.io:22225'

    def _region_to_country_code(self, region: str) -> str:
        """Convert region code to country code."""
        if region.startswith('us-'):
            return 'us'
        elif region.startswith('gb-'):
            return 'gb'
        elif region.startswith('de-'):
            return 'de'
        elif region.startswith('fr-'):
            return 'fr'
        elif region.startswith('ca-'):
            return 'ca'
        elif region.startswith('sg-'):
            return 'sg'
        return 'us'

    def get_available_regions(self) -> List[str]:
        """Get list of available proxy regions."""
        return [
            'us-ca', 'us-ny', 'us-il', 'us-wa', 'us-ma', 'us-tx',
            'gb-london', 'de-berlin', 'fr-paris', 'sg-singapore', 'ca-toronto'
        ]
