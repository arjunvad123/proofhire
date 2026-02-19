"""
Centralized stealth browser management for LinkedIn automation.

Combines:
- playwright-stealth (context-level wrapper — auto-applies to ALL pages)
- Extra evasion techniques (WebGL, canvas, audio fingerprint randomization)
- Anti-detection Chrome launch args
- Persistent browser profile support
- Proxy integration

This replaces per-page Stealth().apply_stealth_async(page) calls with a
single context-level wrapper that covers every page automatically.
"""

import logging
import random
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from playwright.async_api import (
    async_playwright,
    Playwright,
    Browser,
    BrowserContext,
    Page,
)
from playwright_stealth import Stealth

from .proxy_manager import ProxyManager

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Extra evasion init-scripts (what playwright-extra plugins would provide)
# ---------------------------------------------------------------------------

# These scripts are injected before any page JavaScript runs.

WEBGL_FINGERPRINT_EVASION = """
// Randomize WebGL renderer/vendor strings so fingerprint changes per session
(function() {
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        // UNMASKED_VENDOR_WEBGL
        if (parameter === 37445) {
            return 'Google Inc. (Intel)';
        }
        // UNMASKED_RENDERER_WEBGL
        if (parameter === 37446) {
            return 'ANGLE (Intel, Intel(R) Iris(TM) Plus Graphics 655, OpenGL 4.1)';
        }
        return getParameter.apply(this, arguments);
    };

    // WebGL2 as well
    if (typeof WebGL2RenderingContext !== 'undefined') {
        const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Google Inc. (Intel)';
            }
            if (parameter === 37446) {
                return 'ANGLE (Intel, Intel(R) Iris(TM) Plus Graphics 655, OpenGL 4.1)';
            }
            return getParameter2.apply(this, arguments);
        };
    }
})();
"""

CANVAS_FINGERPRINT_EVASION = """
// Add subtle noise to canvas toDataURL / toBlob to defeat canvas fingerprinting
(function() {
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(type) {
        if (this.width === 0 || this.height === 0) {
            return originalToDataURL.apply(this, arguments);
        }
        const ctx = this.getContext('2d');
        if (ctx) {
            const imageData = ctx.getImageData(0, 0, this.width, this.height);
            const data = imageData.data;
            // Add imperceptible noise to a few pixels
            for (let i = 0; i < Math.min(10, data.length / 4); i++) {
                const idx = Math.floor(Math.random() * (data.length / 4)) * 4;
                data[idx] = data[idx] ^ 1;     // R channel ±1
            }
            ctx.putImageData(imageData, 0, 0);
        }
        return originalToDataURL.apply(this, arguments);
    };
})();
"""

AUDIO_FINGERPRINT_EVASION = """
// Slightly alter AudioContext output to prevent audio fingerprinting
(function() {
    const origGetFloatFrequencyData = AnalyserNode.prototype.getFloatFrequencyData;
    AnalyserNode.prototype.getFloatFrequencyData = function(array) {
        const result = origGetFloatFrequencyData.call(this, array);
        for (let i = 0; i < array.length; i++) {
            array[i] = array[i] + (Math.random() * 0.0001 - 0.00005);
        }
        return result;
    };
})();
"""

CHROME_RUNTIME_EVASION = """
// Make window.chrome look like a real Chrome browser
(function() {
    if (!window.chrome) {
        Object.defineProperty(window, 'chrome', {
            writable: true,
            enumerable: true,
            configurable: false,
            value: {}
        });
    }
    if (!window.chrome.runtime) {
        window.chrome.runtime = {
            PlatformOs: { MAC: 'mac', WIN: 'win', ANDROID: 'android', CROS: 'cros', LINUX: 'linux', OPENBSD: 'openbsd' },
            PlatformArch: { ARM: 'arm', X86_32: 'x86-32', X86_64: 'x86-64', MIPS: 'mips', MIPS64: 'mips64' },
            PlatformNaclArch: { ARM: 'arm', X86_32: 'x86-32', X86_64: 'x86-64', MIPS: 'mips', MIPS64: 'mips64' },
            RequestUpdateCheckStatus: { THROTTLED: 'throttled', NO_UPDATE: 'no_update', UPDATE_AVAILABLE: 'update_available' },
            OnInstalledReason: { INSTALL: 'install', UPDATE: 'update', CHROME_UPDATE: 'chrome_update', SHARED_MODULE_UPDATE: 'shared_module_update' },
            OnRestartRequiredReason: { APP_UPDATE: 'app_update', OS_UPDATE: 'os_update', PERIODIC: 'periodic' },
        };
    }

    // Spoof connection info (hide CDP)
    if (!window.chrome.csi) {
        window.chrome.csi = function() { return {}; };
    }
    if (!window.chrome.loadTimes) {
        window.chrome.loadTimes = function() { return {}; };
    }
})();
"""

PERMISSIONS_EVASION = """
// Override Permissions API to match real browser behavior
(function() {
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = function(parameters) {
        if (parameters.name === 'notifications') {
            return Promise.resolve({ state: Notification.permission });
        }
        return originalQuery.apply(this, arguments);
    };
})();
"""

PLUGINS_EVASION = """
// Ensure navigator.plugins is non-empty (headless has zero plugins)
(function() {
    Object.defineProperty(navigator, 'plugins', {
        get: function() {
            return [
                { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
            ];
        }
    });
    Object.defineProperty(navigator, 'mimeTypes', {
        get: function() {
            return [
                { type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format', enabledPlugin: navigator.plugins[0] },
                { type: 'application/x-google-chrome-pdf', suffixes: 'pdf', description: 'Portable Document Format', enabledPlugin: navigator.plugins[0] }
            ];
        }
    });
})();
"""

HARDWARE_CONCURRENCY_EVASION = """
// Set realistic hardware concurrency (headless often reports 1)
(function() {
    Object.defineProperty(navigator, 'hardwareConcurrency', {
        get: function() { return 8; }
    });
    Object.defineProperty(navigator, 'deviceMemory', {
        get: function() { return 8; }
    });
})();
"""

EXTRA_EVASION_SCRIPTS: List[str] = [
    WEBGL_FINGERPRINT_EVASION,
    CANVAS_FINGERPRINT_EVASION,
    AUDIO_FINGERPRINT_EVASION,
    CHROME_RUNTIME_EVASION,
    PERMISSIONS_EVASION,
    PLUGINS_EVASION,
    HARDWARE_CONCURRENCY_EVASION,
]


# ---------------------------------------------------------------------------
# Anti-detection Chrome launch args
# ---------------------------------------------------------------------------

STEALTH_CHROME_ARGS: List[str] = [
    '--disable-blink-features=AutomationControlled',
    '--disable-dev-shm-usage',
    '--no-sandbox',
    '--disable-infobars',
    '--disable-background-networking',
    '--disable-default-apps',
    '--disable-extensions',
    '--disable-sync',
    '--disable-translate',
    '--metrics-recording-only',
    '--no-first-run',
    '--safebrowsing-disable-auto-update',
    '--password-store=basic',
    '--use-mock-keychain',
    # Prevent "Chrome is being controlled by automated test software" banner
    '--disable-component-update',
    '--disable-domain-reliability',
    '--disable-features=AudioServiceOutOfProcess,IsolateOrigins,site-per-process',
]


# ---------------------------------------------------------------------------
# Realistic user agents (Chrome 122-124, updated for early 2026)
# ---------------------------------------------------------------------------

USER_AGENTS_MAC = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15',
]

USER_AGENTS_WINDOWS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
]

ALL_USER_AGENTS = USER_AGENTS_MAC + USER_AGENTS_WINDOWS


# ---------------------------------------------------------------------------
# Realistic viewport sizes (common monitor resolutions)
# ---------------------------------------------------------------------------

VIEWPORTS = [
    {'width': 1920, 'height': 1080},
    {'width': 1440, 'height': 900},
    {'width': 1536, 'height': 864},
    {'width': 1366, 'height': 768},
    {'width': 2560, 'height': 1440},
]


# ---------------------------------------------------------------------------
# StealthBrowser — the main class
# ---------------------------------------------------------------------------

class StealthBrowser:
    """
    Manages stealth-enhanced Playwright browser instances.

    Uses playwright-stealth context-level wrapping (``Stealth().use_async``)
    so every page created automatically inherits all evasions. On top of that,
    injects the extra evasion scripts that playwright-extra plugins would
    normally provide (WebGL, canvas, audio, chrome.runtime, etc.).

    Usage — simple (non-persistent) context::

        async with StealthBrowser.launch() as sb:
            page = await sb.new_page()
            await page.goto('https://linkedin.com')

    Usage — persistent browser profile::

        async with StealthBrowser.launch_persistent(session_id='abc-123') as sb:
            page = await sb.new_page()
            await page.goto('https://linkedin.com')
    """

    def __init__(
        self,
        playwright: Playwright,
        browser: Optional[Browser],
        context: BrowserContext,
        is_persistent: bool = False,
    ):
        self._playwright = playwright
        self._browser = browser
        self._context = context
        self._is_persistent = is_persistent

    # ---- public helpers ----

    @property
    def context(self) -> BrowserContext:
        """Return the underlying browser context."""
        return self._context

    async def new_page(self) -> Page:
        """Create a new page with extra evasion scripts injected."""
        page = await self._context.new_page()
        # Extra evasion scripts are applied via context-level init scripts,
        # so every page already has them. Nothing extra needed here.
        return page

    async def close(self) -> None:
        """Close browser/context and release resources."""
        try:
            await self._context.close()
        except Exception:
            pass
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass

    # ---- static factory methods (async context managers) ----

    @staticmethod
    @asynccontextmanager
    async def launch(
        headless: bool = False,
        proxy: Optional[Dict[str, str]] = None,
        user_location: Optional[str] = None,
        sticky_session_id: Optional[str] = None,
    ):
        """
        Launch a stealth browser with a fresh (non-persistent) context.

        Args:
            headless: Run headless (False recommended for LinkedIn).
            proxy: Playwright proxy dict ``{server, username, password}``.
            user_location: If set and no proxy given, auto-select a proxy
                           with geo-targeting to match the user's region.
            sticky_session_id: If set, the proxy will always resolve to the
                               same residential IP for this ID (sticky session).

        Yields:
            StealthBrowser instance.
        """
        # Resolve proxy from location if needed
        if not proxy and user_location:
            proxy = ProxyManager().get_proxy_for_location(
                location=user_location,
                sticky_session_id=sticky_session_id,
            )

        if proxy:
            logger.info("Launching browser with proxy: %s", proxy["server"])
        else:
            logger.debug("Launching browser without proxy (direct connection)")

        user_agent = random.choice(ALL_USER_AGENTS)
        viewport = random.choice(VIEWPORTS)

        stealth = Stealth(
            navigator_languages_override=('en-US', 'en'),
        )

        async with stealth.use_async(async_playwright()) as p:
            browser = await p.chromium.launch(
                headless=headless,
                proxy=proxy,
                args=STEALTH_CHROME_ARGS,
            )

            context = await browser.new_context(
                user_agent=user_agent,
                viewport=viewport,
                locale='en-US',
                timezone_id='America/Los_Angeles',
                color_scheme='light',
                # Accept-Language header
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                },
            )

            # Inject extra evasion scripts at the context level
            for script in EXTRA_EVASION_SCRIPTS:
                await context.add_init_script(script)

            sb = StealthBrowser(
                playwright=p,
                browser=browser,
                context=context,
                is_persistent=False,
            )

            try:
                yield sb
            finally:
                await sb.close()

    @staticmethod
    @asynccontextmanager
    async def launch_persistent(
        session_id: str,
        headless: bool = False,
        proxy: Optional[Dict[str, str]] = None,
        user_location: Optional[str] = None,
        profiles_dir: str = './browser_profiles',
    ):
        """
        Launch a stealth browser with a *persistent* browser profile.

        Persistent profiles keep cookies, cache, localStorage etc. between
        runs — exactly like a real user's Chrome.  Each ``session_id`` gets
        its own profile directory.

        The proxy is automatically configured with a sticky session keyed to
        ``session_id`` so the same residential IP is used every time —
        critical for maintaining LinkedIn's device trust.

        Args:
            session_id: Unique session / user identifier.
            headless: Run headless (False recommended for LinkedIn).
            proxy: Playwright proxy dict.
            user_location: If set and no proxy given, auto-select a proxy.
            profiles_dir: Root directory for browser profiles.

        Yields:
            StealthBrowser instance.
        """
        # Resolve proxy from location if needed — always sticky for persistent
        if not proxy and user_location:
            proxy = ProxyManager().get_proxy_for_location(
                location=user_location,
                sticky_session_id=session_id,  # same user → same IP every time
            )

        if proxy:
            logger.info("Launching persistent browser (session=%s) with proxy: %s", session_id, proxy["server"])
        else:
            logger.debug("Launching persistent browser (session=%s) without proxy", session_id)

        user_agent = random.choice(ALL_USER_AGENTS)
        viewport = random.choice(VIEWPORTS)

        # Ensure profile directory exists
        profile_path = Path(profiles_dir) / session_id
        profile_path.mkdir(parents=True, exist_ok=True)

        stealth = Stealth(
            navigator_languages_override=('en-US', 'en'),
        )

        async with stealth.use_async(async_playwright()) as p:
            # launch_persistent_context returns a BrowserContext directly
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(profile_path),
                headless=headless,
                proxy=proxy,
                user_agent=user_agent,
                viewport=viewport,
                locale='en-US',
                timezone_id='America/Los_Angeles',
                color_scheme='light',
                args=STEALTH_CHROME_ARGS,
                # Accept-Language header
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                },
            )

            # Inject extra evasion scripts at the context level
            for script in EXTRA_EVASION_SCRIPTS:
                await context.add_init_script(script)

            sb = StealthBrowser(
                playwright=p,
                browser=None,  # persistent context doesn't have a separate browser
                context=context,
                is_persistent=True,
            )

            try:
                yield sb
            finally:
                await sb.close()
