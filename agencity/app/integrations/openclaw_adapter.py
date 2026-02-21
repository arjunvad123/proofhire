"""
OpenClaw Adapter - Abstraction layer for OpenClaw integration.

This module isolates Agencity from OpenClaw's internal changes.
When OpenClaw updates, only this adapter needs to change.

Key Principles:
1. Define YOUR interface, not OpenClaw's
2. Handle version differences internally
3. Provide fallbacks for missing features
4. Test the adapter, not OpenClaw directly
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol

logger = logging.getLogger(__name__)


# ── Your Interface (Stable) ────────────────────────────────────────────────

class OpenClawGatewayInterface(Protocol):
    """
    Your stable interface for OpenClaw operations.
    
    This interface doesn't change when OpenClaw updates.
    Only the implementation (OpenClawAdapter) changes.
    """
    
    async def send_message(self, channel: str, message: str) -> None:
        """Send a message via any channel (Slack, WhatsApp, etc.)."""
        ...
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call an Agencity tool through OpenClaw."""
        ...
    
    async def search_memory(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search semantic memory for past conversations."""
        ...
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and health."""
        ...


# ── Adapter Implementation (Version-Specific) ───────────────────────────────

class OpenClawAdapter:
    """
    Adapter that wraps OpenClaw's actual implementation.
    
    When OpenClaw changes, only this class needs updating.
    Your Agencity code continues to work unchanged.
    """
    
    def __init__(self, openclaw_version: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize adapter for specific OpenClaw version.
        
        Args:
            openclaw_version: OpenClaw version (e.g., "1.2.3")
            config: OpenClaw configuration
        """
        self.version = openclaw_version
        self.config = config or {}
        self._gateway = None
        self._init_for_version(openclaw_version)
    
    def _init_for_version(self, version: str) -> None:
        """Handle version-specific initialization."""
        major, minor, patch = self._parse_version(version)
        
        try:
            if major == 1 and minor <= 2:
                # OpenClaw 1.0.x - 1.2.x API
                self._init_v1_api(version)
            elif major == 1 and minor >= 3:
                # OpenClaw 1.3.x+ API (may have changed)
                self._init_v1_3_api(version)
            elif major >= 2:
                # OpenClaw 2.0.x+ API (likely breaking changes)
                self._init_v2_api(version)
            else:
                raise ValueError(f"Unsupported OpenClaw version: {version}")
        except ImportError as e:
            logger.error(f"Failed to import OpenClaw {version}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize OpenClaw {version}: {e}")
            raise
    
    def _parse_version(self, version: str) -> tuple[int, int, int]:
        """Parse version string into (major, minor, patch)."""
        parts = version.lstrip('v').split('.')
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    
    def _init_v1_api(self, version: str) -> None:
        """Initialize for OpenClaw 1.0.x - 1.2.x."""
        # Example - adjust based on actual OpenClaw API
        try:
            from openclaw import Gateway  # type: ignore
            
            self._gateway = Gateway(
                port=self.config.get('port', 18789),
                config_path=self.config.get('config_path')
            )
            logger.info(f"Initialized OpenClaw v1 API ({version})")
        except ImportError:
            # Fallback if OpenClaw not installed
            logger.warning("OpenClaw not installed, using mock adapter")
            self._gateway = MockGateway()
    
    def _init_v1_3_api(self, version: str) -> None:
        """Initialize for OpenClaw 1.3.x+ (may have API changes)."""
        # Handle API changes in 1.3.x
        try:
            from openclaw.v1_3 import GatewayV13  # type: ignore
            
            # New API might have different constructor
            self._gateway = GatewayV13(
                port=self.config.get('port', 18789),
                config=self.config  # Different parameter name
            )
            logger.info(f"Initialized OpenClaw v1.3 API ({version})")
        except ImportError:
            # Try fallback to v1 API
            logger.warning(f"OpenClaw 1.3+ not available, falling back to v1")
            self._init_v1_api("1.2.0")
    
    def _init_v2_api(self, version: str) -> None:
        """Initialize for OpenClaw 2.0.x+ (likely breaking changes)."""
        # Major version changes often have breaking API changes
        try:
            from openclaw.v2 import GatewayV2  # type: ignore
            
            # Completely different API structure
            self._gateway = GatewayV2.create(
                config=self.config,
                version=version
            )
            logger.info(f"Initialized OpenClaw v2 API ({version})")
        except ImportError:
            raise ValueError(
                f"OpenClaw 2.0+ requires migration. "
                f"See migration guide for version {version}"
            )
    
    # ── Public Interface (Stable) ─────────────────────────────────────────
    
    async def send_message(self, channel: str, message: str) -> None:
        """
        Send message - handles API differences across versions.
        
        Your Agencity code calls this method, which handles
        version-specific OpenClaw API differences internally.
        """
        try:
            # Version-specific implementation
            if self.version.startswith("1.0") or self.version.startswith("1.1") or self.version.startswith("1.2"):
                # OpenClaw 1.0.x - 1.2.x API
                await self._gateway.send(channel=channel, text=message)
            elif self.version.startswith("1.3"):
                # OpenClaw 1.3.x API (might have changed)
                await self._gateway.post_message(channel_id=channel, content=message)
            elif self.version.startswith("2."):
                # OpenClaw 2.0.x API (likely different)
                await self._gateway.send_message(
                    target=channel,
                    message=message
                )
            else:
                raise ValueError(f"Unsupported version for send_message: {self.version}")
        except Exception as e:
            logger.error(f"Failed to send message via OpenClaw {self.version}: {e}")
            raise
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call tool - abstracts OpenClaw's tool calling.
        
        Your Agencity tools are registered with OpenClaw.
        This method handles version differences in tool calling.
        """
        try:
            # Version-specific tool calling
            if self.version.startswith("1."):
                # OpenClaw 1.x API
                result = await self._gateway.call_tool(
                    name=tool_name,
                    parameters=params
                )
            elif self.version.startswith("2."):
                # OpenClaw 2.x API (might use different method)
                result = await self._gateway.invoke_tool(
                    tool=tool_name,
                    args=params
                )
            else:
                raise ValueError(f"Unsupported version for call_tool: {self.version}")
            
            return result
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name} via OpenClaw {self.version}: {e}")
            raise
    
    async def search_memory(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search semantic memory - handles version differences."""
        try:
            if self.version.startswith("1."):
                # OpenClaw 1.x memory API
                results = await self._gateway.memory.search(query, limit=limit)
            elif self.version.startswith("2."):
                # OpenClaw 2.x memory API (might be different)
                results = await self._gateway.search_memory(query=query, max_results=limit)
            else:
                raise ValueError(f"Unsupported version for search_memory: {self.version}")
            
            return results
        except Exception as e:
            logger.error(f"Failed to search memory via OpenClaw {self.version}: {e}")
            return []  # Graceful degradation
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status - handles version differences."""
        try:
            if self.version.startswith("1."):
                status = await self._gateway.get_status()
            elif self.version.startswith("2."):
                status = await self._gateway.health_check()
            else:
                status = {"status": "unknown", "version": self.version}
            
            return status
        except Exception as e:
            logger.error(f"Failed to get status via OpenClaw {self.version}: {e}")
            return {"status": "error", "error": str(e)}


# ── Mock Implementation (For Testing) ──────────────────────────────────────

class MockGateway:
    """Mock gateway for testing when OpenClaw is not installed."""
    
    async def send(self, channel: str, text: str) -> None:
        logger.info(f"[MOCK] Sending to {channel}: {text}")
    
    async def call_tool(self, name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[MOCK] Calling tool {name} with {parameters}")
        return {"result": "mock_response"}
    
    async def memory_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        logger.info(f"[MOCK] Searching memory: {query}")
        return []
    
    async def get_status(self) -> Dict[str, Any]:
        return {"status": "mock", "version": "mock"}


# ── Factory Function ────────────────────────────────────────────────────────

def create_openclaw_adapter(
    version: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> OpenClawAdapter:
    """
    Factory function to create OpenClaw adapter.
    
    Automatically detects OpenClaw version if not specified.
    """
    if version is None:
        # Try to detect installed version
        try:
            import openclaw  # type: ignore
            version = getattr(openclaw, '__version__', '1.0.0')
        except ImportError:
            logger.warning("OpenClaw not installed, using mock adapter")
            version = "1.0.0"  # Default to mock
    
    return OpenClawAdapter(version=version, config=config)
