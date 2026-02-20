#!/usr/bin/env python3
"""
Test Decodo (formerly SmartProxy) configuration and connectivity.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.services.linkedin.proxy_manager import ProxyManager


async def main():
    print("=" * 60)
    print("🔍 Testing Decodo Proxy Configuration")
    print("=" * 60)
    print()

    # Initialize proxy manager
    pm = ProxyManager()

    # Check configuration
    print("📋 Configuration Check:")
    print(f"   Provider: {pm.provider or '(not set)'}")
    print(f"   Has Username: {'✅ Yes' if pm.username else '❌ No'}")
    print(f"   Has Password: {'✅ Yes' if pm.password else '❌ No'}")
    print(f"   Is Configured: {'✅ Yes' if pm.is_configured else '❌ No'}")
    print()

    if not pm.is_configured:
        print("❌ Proxy not configured!")
        print()
        print("Please set in your .env file:")
        print("  PROXY_PROVIDER=smartproxy")
        print("  PROXY_USERNAME=your-username")
        print("  PROXY_PASSWORD=your-password")
        sys.exit(1)

    print("✅ Proxy is configured!")
    print("✅ Using Username/Password authentication")
    print()

    # Test proxy URL generation
    print("🔧 Testing Proxy URL Generation:")
    test_locations = [
        ("San Francisco, CA", "test_user_123"),
        ("London, UK", "test_user_456"),
        (None, "test_user_789"),
    ]

    for location, user_id in test_locations:
        proxy = pm.get_proxy_for_location(location, sticky_session_id=user_id)
        if proxy:
            print(f"   Location: {location or 'default'}")
            print(f"   Server: {proxy['server']}")
            print(f"   Username: {proxy['username'][:60]}...")
            print(f"   Password: {'***' if proxy['password'] else '(empty)'}")
            print()

    # Test health check
    print("🌐 Testing Proxy Connectivity:")
    print("   This will make a real HTTP request through the proxy...")
    print()

    proxy = pm.get_proxy_for_location("San Francisco, CA", "health_check_test")
    print(f"   Testing with proxy URL format...")
    print(f"   Server: {proxy['server']}")
    print(f"   Username length: {len(proxy['username'])} chars")
    print(f"   Password: {'(set)' if proxy.get('password') else '(empty)'}")
    print()

    health = await pm.check_proxy_health(proxy)

    if health["ok"]:
        print("✅ Proxy connection successful!")
        print(f"   Exit IP: {health['ip']}")
        print(f"   Country: {health['country']}")
        print(f"   Latency: {health['latency_ms']}ms")
        print()
        print("🎉 All tests passed! Your proxy is working correctly.")
    else:
        print("❌ Proxy connection failed!")
        error_msg = health.get('error', 'Unknown error')
        print(f"   Error: {error_msg if error_msg else '(Empty error - check network/credentials)'}")
        print()
        print("Troubleshooting:")
        print("  1. Check your username/password credentials in .env")
        print("  2. Verify your Decodo account has active balance")
        print("  3. Check firewall/network restrictions")
        print("  4. Try the Decodo dashboard to verify credentials")
        print("  5. Verify username/password format matches Decodo requirements")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
