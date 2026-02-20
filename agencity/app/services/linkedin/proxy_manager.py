"""
Residential proxy management for LinkedIn automation.

Handles:
- Proxy pool management with Decodo (formerly SmartProxy) and BrightData
- Location-based geo-targeting (country/state)
- Sticky sessions — same user_id always gets same IP
- Proxy health checking
- Graceful fallback when no proxy is configured

Proxy credentials are read from environment variables via app.config:
    PROXY_PROVIDER   — "smartproxy" (Decodo) or "brightdata"
    PROXY_USERNAME   — Username for proxy authentication
    PROXY_PASSWORD   — Password for proxy authentication
"""

import hashlib
import logging
import random
from typing import Optional, Dict, List

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Provider-specific constants
# ---------------------------------------------------------------------------

# Decodo (formerly SmartProxy) residential endpoints
# Note: Endpoints remain the same after rebrand - no setup changes needed
# Port 7000 is standard, but port 10000 works on more networks
SMARTPROXY_HOST = "gate.smartproxy.com"
SMARTPROXY_PORT = 10000  # Changed from 7000 - port 10000 has better network compatibility

# BrightData (Luminati) residential endpoints
BRIGHTDATA_HOST = "brd.superproxy.io"
BRIGHTDATA_PORT = 22225


class ProxyManager:
    """Manages residential proxy pool for LinkedIn automation."""

    # Mapping of free-text locations to ISO country codes
    LOCATION_TO_COUNTRY: Dict[str, str] = {
        # United States
        "san francisco": "us",
        "california": "us",
        "los angeles": "us",
        "new york": "us",
        "chicago": "us",
        "seattle": "us",
        "boston": "us",
        "austin": "us",
        "miami": "us",
        "denver": "us",
        "portland": "us",
        "atlanta": "us",
        "dallas": "us",
        "houston": "us",
        "phoenix": "us",
        "philadelphia": "us",
        "washington": "us",
        # International
        "london": "gb",
        "manchester": "gb",
        "berlin": "de",
        "munich": "de",
        "paris": "fr",
        "singapore": "sg",
        "toronto": "ca",
        "vancouver": "ca",
        "sydney": "au",
        "melbourne": "au",
        "tokyo": "jp",
        "mumbai": "in",
        "bangalore": "in",
        "amsterdam": "nl",
        "dublin": "ie",
        "zurich": "ch",
        "stockholm": "se",
        "oslo": "no",
        "copenhagen": "dk",
        "helsinki": "fi",
        "madrid": "es",
        "barcelona": "es",
        "rome": "it",
        "milan": "it",
        "sao paulo": "br",
        "tel aviv": "il",
        "dubai": "ae",
        "seoul": "kr",
    }

    # Country-name fallbacks
    COUNTRY_NAME_TO_CODE: Dict[str, str] = {
        "united states": "us",
        "united kingdom": "gb",
        "uk": "gb",
        "canada": "ca",
        "germany": "de",
        "france": "fr",
        "australia": "au",
        "japan": "jp",
        "india": "in",
        "netherlands": "nl",
        "ireland": "ie",
        "switzerland": "ch",
        "sweden": "se",
        "norway": "no",
        "denmark": "dk",
        "finland": "fi",
        "spain": "es",
        "italy": "it",
        "brazil": "br",
        "israel": "il",
        "south korea": "kr",
        "singapore": "sg",
        "uae": "ae",
    }

    # US state code detection (from location strings like "San Francisco, CA")
    US_STATE_CODES = {
        "al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga",
        "hi", "id", "il", "in", "ia", "ks", "ky", "la", "me", "md",
        "ma", "mi", "mn", "ms", "mo", "mt", "ne", "nv", "nh", "nj",
        "nm", "ny", "nc", "nd", "oh", "ok", "or", "pa", "ri", "sc",
        "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv", "wi", "wy",
    }

    def __init__(self):
        """Initialize proxy manager from settings."""
        self.provider: str = (settings.proxy_provider or "").strip().lower()
        self.username: str = (settings.proxy_username or "").strip()
        self.password: str = (settings.proxy_password or "").strip()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def is_configured(self) -> bool:
        """Return True if proxy credentials are present."""
        if not self.provider:
            return False
        # Decodo (SmartProxy) uses username/password authentication
        if self.provider == "smartproxy":
            return bool(self.username and self.password)
        # BrightData requires username/password
        return bool(self.username and self.password)

    def get_proxy_for_location(
        self,
        location: Optional[str] = None,
        sticky_session_id: Optional[str] = None,
    ) -> Optional[Dict[str, str]]:
        """
        Get a Playwright-compatible proxy dict for a given location.

        Args:
            location: Free-text location (e.g. "San Francisco, CA").
                      Used for geo-targeting so the exit IP is near the user.
            sticky_session_id: If provided, the same session ID will always
                               resolve to the **same** residential IP.
                               Critical for persistent browser profiles so
                               LinkedIn doesn't see a different IP each run.

        Returns:
            ``{"server": ..., "username": ..., "password": ...}`` for
            Playwright, or ``None`` if no proxy is configured.
        """
        if not self.is_configured:
            logger.debug("No proxy configured — connecting directly")
            return None

        country = self._resolve_country(location)
        us_state = self._resolve_us_state(location) if country == "us" else None

        # Build provider-specific username with session/geo params
        if self.provider == "smartproxy":
            full_username = self._smartproxy_username(country, us_state, sticky_session_id)
            server = f"http://{SMARTPROXY_HOST}:{SMARTPROXY_PORT}"
            # Decodo uses username/password authentication
            proxy_password = self.password
        elif self.provider == "brightdata":
            full_username = self._brightdata_username(country, us_state, sticky_session_id)
            server = f"http://{BRIGHTDATA_HOST}:{BRIGHTDATA_PORT}"
            proxy_password = self.password
        else:
            logger.warning(f"Unknown proxy provider '{self.provider}', falling back to smartproxy format")
            full_username = self._smartproxy_username(country, us_state, sticky_session_id)
            server = f"http://{SMARTPROXY_HOST}:{SMARTPROXY_PORT}"
            proxy_password = self.password

        proxy = {
            "server": server,
            "username": full_username,
            "password": proxy_password,
        }

        logger.info(
            "Proxy configured: provider=%s country=%s state=%s sticky=%s",
            self.provider,
            country,
            us_state or "any",
            bool(sticky_session_id),
        )
        return proxy

    def get_scraper_proxy(
        self,
        proxy_location: str,
        sticky_session_id: Optional[str] = None,
    ) -> Optional[Dict[str, str]]:
        """
        Get proxy for a scraper account using a region code directly.

        Args:
            proxy_location: Country code (e.g. 'us', 'gb', 'de').
            sticky_session_id: Optional session ID for IP stickiness.

        Returns:
            Proxy config dict for Playwright, or None.
        """
        if not self.is_configured:
            return None

        if self.provider == "smartproxy":
            full_username = self._smartproxy_username(proxy_location, None, sticky_session_id)
            server = f"http://{SMARTPROXY_HOST}:{SMARTPROXY_PORT}"
            # Decodo uses username/password authentication
            proxy_password = self.password
        elif self.provider == "brightdata":
            full_username = self._brightdata_username(proxy_location, None, sticky_session_id)
            server = f"http://{BRIGHTDATA_HOST}:{BRIGHTDATA_PORT}"
            proxy_password = self.password
        else:
            full_username = self._smartproxy_username(proxy_location, None, sticky_session_id)
            server = f"http://{SMARTPROXY_HOST}:{SMARTPROXY_PORT}"
            proxy_password = self.api_key if self.api_key else self.password

        return {
            "server": server,
            "username": full_username,
            "password": proxy_password,
        }

    async def check_proxy_health(self, proxy: Dict[str, str], retries: int = 3) -> Dict[str, any]:
        """
        Test proxy connectivity and return diagnostic info.

        Args:
            proxy: Playwright-format proxy dict {server, username, password}.
            retries: Number of retry attempts (residential proxies can be flaky).

        Returns:
            {"ok": bool, "ip": str|None, "country": str|None, "latency_ms": int|None, "error": str|None}
        """
        import time

        result = {
            "ok": False,
            "ip": None,
            "country": None,
            "latency_ms": None,
            "error": None,
        }

        # Build proxy URL in format: http://username:password@host:port
        # Note: Do NOT URL-encode credentials - httpx handles this internally
        proxy_host = proxy['server'].replace('http://', '').replace('https://', '')
        if proxy.get('password'):
            proxy_url = f"http://{proxy['username']}:{proxy['password']}@{proxy_host}"
        else:
            proxy_url = f"http://{proxy['username']}@{proxy_host}"

        last_error = None
        for attempt in range(retries):
            try:
                start = time.monotonic()
                # httpx uses 'proxy' parameter, not 'proxies'
                async with httpx.AsyncClient(
                    proxy=proxy_url,
                    timeout=20.0,
                ) as client:
                    resp = await client.get("https://ipinfo.io/json")
                    elapsed = time.monotonic() - start

                    if resp.status_code == 200:
                        data = resp.json()
                        result["ok"] = True
                        result["ip"] = data.get("ip")
                        result["country"] = data.get("country")
                        result["latency_ms"] = int(elapsed * 1000)
                        logger.info(
                            "Proxy health OK: ip=%s country=%s latency=%dms",
                            result["ip"], result["country"], result["latency_ms"],
                        )
                        return result
                    else:
                        last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
            except httpx.ConnectTimeout:
                last_error = "Connection timeout - proxy server unreachable or credentials invalid"
                logger.warning("Proxy health check attempt %d failed: Connection timeout", attempt + 1)
            except httpx.ProxyError as exc:
                last_error = f"Proxy error: {str(exc)}"
                logger.warning("Proxy health check attempt %d failed: Proxy error - %s", attempt + 1, exc)
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {str(exc)}"
                logger.warning("Proxy health check attempt %d failed: %s", attempt + 1, exc)

            # Wait before retry (residential proxies can be temporarily unavailable)
            if attempt < retries - 1:
                import asyncio
                await asyncio.sleep(1)

        result["error"] = last_error
        return result

    def get_available_regions(self) -> List[str]:
        """Get sorted list of supported country codes."""
        codes = set(self.LOCATION_TO_COUNTRY.values())
        return sorted(codes)

    # ------------------------------------------------------------------
    # Provider-specific username builders
    # ------------------------------------------------------------------

    def _smartproxy_username(
        self,
        country: str,
        us_state: Optional[str],
        sticky_session_id: Optional[str],
    ) -> str:
        """
        Build Decodo (formerly SmartProxy) username with geo-targeting and sticky session.

        Decodo uses username/password authentication.

        Username format:
            user-{base_username}-country-{cc}[-session-{id}]

        Note: State-level targeting (-state-XX) requires a premium plan.
        Session IDs are supported for sticky sessions.

        Docs: https://decodo.com (formerly smartproxy.com)
        """
        # Decodo uses username as the base identifier
        if not self.username:
            raise ValueError("Decodo requires PROXY_USERNAME to be set")
        base = f"user-{self.username}"

        parts = [base, f"country-{country}"]

        # Note: State-level targeting disabled - requires premium Decodo plan
        # If you have a premium plan, uncomment the following:
        # if us_state:
        #     parts.append(f"state-{us_state}")

        if sticky_session_id:
            # Deterministic 8-char session key derived from the user's ID
            session_key = self._derive_session_key(sticky_session_id)
            parts.append(f"session-{session_key}")
        else:
            # Random session per request (rotating IP)
            parts.append(f"session-{random.randint(1_000_000, 9_999_999)}")

        return "-".join(parts)

    def _brightdata_username(
        self,
        country: str,
        us_state: Optional[str],
        sticky_session_id: Optional[str],
    ) -> str:
        """
        Build BrightData (Luminati) username with geo-targeting and sticky session.

        BrightData format:
            brd-customer-{customer_id}-zone-{zone}-country-{cc}[-state-{st}][-session-{id}]

        The base username should be: {customer_id}-zone-{zone}
        (e.g. "c_abc123-zone-residential")

        Docs: https://docs.brightdata.com/api-reference/proxy/parameters
        """
        parts = [f"brd-customer-{self.username}", f"country-{country}"]

        if us_state:
            parts.append(f"state-{us_state}")

        if sticky_session_id:
            session_key = self._derive_session_key(sticky_session_id)
            parts.append(f"session-{session_key}")
        else:
            parts.append(f"session-{random.randint(1_000_000, 9_999_999)}")

        return "-".join(parts)

    # ------------------------------------------------------------------
    # Location resolution helpers
    # ------------------------------------------------------------------

    def _resolve_country(self, location: Optional[str]) -> str:
        """Resolve a free-text location to a 2-letter country code."""
        if not location:
            return "us"

        loc = location.lower().strip()

        # 1) Check city-level mapping
        for city, code in self.LOCATION_TO_COUNTRY.items():
            if city in loc:
                return code

        # 2) Check country-name mapping
        for name, code in self.COUNTRY_NAME_TO_CODE.items():
            if name in loc:
                return code

        # 3) Check if the location string itself is a 2-letter code
        parts = [p.strip() for p in loc.replace(",", " ").split()]
        for p in parts:
            if len(p) == 2 and p.isalpha():
                # Could be a US state code or country code
                if p in self.COUNTRY_NAME_TO_CODE.values():
                    return p

        return "us"  # default fallback

    def _resolve_us_state(self, location: Optional[str]) -> Optional[str]:
        """Extract a US state code from a location string like 'San Francisco, CA'."""
        if not location:
            return None

        parts = [p.strip().lower() for p in location.replace(",", " ").split()]
        for p in parts:
            if len(p) == 2 and p in self.US_STATE_CODES:
                return p

        return None

    @staticmethod
    def _derive_session_key(session_id: str) -> str:
        """
        Derive a deterministic 8-char session key from a session ID.

        This ensures the same user_id always maps to the same proxy IP
        (sticky session), which is critical for persistent browser profiles
        so LinkedIn sees a stable IP across runs.
        """
        digest = hashlib.sha256(session_id.encode()).hexdigest()
        return digest[:8]
