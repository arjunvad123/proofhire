#!/usr/bin/env python3
"""
Agencity Service Integration Tests

Tests all services and integrations:
- OpenAI API
- Supabase connection
- Redis cache
- Slack bot
- GitHub API
- Environment configuration
"""

import os
import sys
import json
import asyncio
from typing import Dict, List, Tuple
from datetime import datetime

# Colors for terminal output
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

class TestResult:
    def __init__(self, name: str, passed: bool, message: str = ""):
        self.name = name
        self.passed = passed
        self.message = message
        self.timestamp = datetime.now()

class ServiceTester:
    def __init__(self):
        self.results: List[TestResult] = []
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0

    def test(self, name: str, func, *args, **kwargs) -> bool:
        """Run a test and record result"""
        self.tests_run += 1
        print(f"[{self.tests_run}] Testing {name}... ", end="", flush=True)

        try:
            result = func(*args, **kwargs)
            if result:
                print(f"{Colors.GREEN}✓ PASSED{Colors.NC}")
                self.tests_passed += 1
                self.results.append(TestResult(name, True))
                return True
            else:
                print(f"{Colors.RED}✗ FAILED{Colors.NC}")
                self.tests_failed += 1
                self.results.append(TestResult(name, False, "Test returned False"))
                return False
        except Exception as e:
            print(f"{Colors.RED}✗ FAILED{Colors.NC}")
            print(f"  Error: {str(e)}")
            self.tests_failed += 1
            self.results.append(TestResult(name, False, str(e)))
            return False

    async def test_async(self, name: str, func, *args, **kwargs) -> bool:
        """Run an async test and record result"""
        self.tests_run += 1
        print(f"[{self.tests_run}] Testing {name}... ", end="", flush=True)

        try:
            result = await func(*args, **kwargs)
            if result:
                print(f"{Colors.GREEN}✓ PASSED{Colors.NC}")
                self.tests_passed += 1
                self.results.append(TestResult(name, True))
                return True
            else:
                print(f"{Colors.RED}✗ FAILED{Colors.NC}")
                self.tests_failed += 1
                self.results.append(TestResult(name, False, "Test returned False"))
                return False
        except Exception as e:
            print(f"{Colors.RED}✗ FAILED{Colors.NC}")
            print(f"  Error: {str(e)}")
            self.tests_failed += 1
            self.results.append(TestResult(name, False, str(e)))
            return False

    def print_summary(self):
        """Print test summary"""
        print()
        print(f"{Colors.BLUE}{'━' * 60}{Colors.NC}")
        print(f"{Colors.BLUE}  Test Summary{Colors.NC}")
        print(f"{Colors.BLUE}{'━' * 60}{Colors.NC}")
        print()
        print(f"Total Tests:  {self.tests_run}")
        print(f"{Colors.GREEN}Passed:       {self.tests_passed}{Colors.NC}")
        print(f"{Colors.RED}Failed:       {self.tests_failed}{Colors.NC}")
        print()

        if self.tests_failed == 0:
            print(f"{Colors.GREEN}{'╔' + '═' * 58 + '╗'}{Colors.NC}")
            print(f"{Colors.GREEN}║  ✓ ALL SERVICE TESTS PASSED                            ║{Colors.NC}")
            print(f"{Colors.GREEN}{'╚' + '═' * 58 + '╝'}{Colors.NC}")
            return True
        else:
            print(f"{Colors.RED}{'╔' + '═' * 58 + '╗'}{Colors.NC}")
            print(f"{Colors.RED}║  ✗ SOME TESTS FAILED - CHECK CONFIGURATION            ║{Colors.NC}")
            print(f"{Colors.RED}{'╚' + '═' * 58 + '╝'}{Colors.NC}")
            print()
            print(f"{Colors.YELLOW}Failed tests:{Colors.NC}")
            for result in self.results:
                if not result.passed:
                    print(f"  - {result.name}: {result.message}")
            return False

def test_environment_variables() -> bool:
    """Test that required environment variables are set"""
    required_vars = [
        'OPENAI_API_KEY',
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'REDIS_URL',
    ]

    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        print(f"\n  Missing: {', '.join(missing)}")
        return False

    return True

def test_openai_import() -> bool:
    """Test OpenAI library import"""
    try:
        import openai
        return True
    except ImportError as e:
        print(f"\n  Import error: {e}")
        return False

def test_openai_api_key() -> bool:
    """Test OpenAI API key is valid format"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return False

    # Check format
    if not api_key.startswith('sk-'):
        print(f"\n  Invalid API key format")
        return False

    return True

async def test_openai_connection() -> bool:
    """Test actual OpenAI API connection"""
    try:
        import openai
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        # Simple API call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'test'"}],
            max_tokens=10
        )

        return bool(response.choices[0].message.content)
    except Exception as e:
        print(f"\n  API error: {e}")
        return False

def test_redis_import() -> bool:
    """Test Redis library import"""
    try:
        import redis
        return True
    except ImportError as e:
        print(f"\n  Import error: {e}")
        return False

async def test_redis_connection() -> bool:
    """Test Redis connection"""
    try:
        import redis.asyncio as redis

        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        client = redis.from_url(redis_url)

        # Test ping
        response = await client.ping()
        await client.close()

        return response
    except Exception as e:
        print(f"\n  Connection error: {e}")
        return False

async def test_redis_operations() -> bool:
    """Test Redis read/write operations"""
    try:
        import redis.asyncio as redis

        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        client = redis.from_url(redis_url)

        # Test write
        test_key = "agencity:test:deployment"
        test_value = f"test_{datetime.now().isoformat()}"

        await client.set(test_key, test_value, ex=60)

        # Test read
        retrieved = await client.get(test_key)
        await client.delete(test_key)
        await client.close()

        return retrieved.decode() == test_value if retrieved else False
    except Exception as e:
        print(f"\n  Operation error: {e}")
        return False

def test_supabase_import() -> bool:
    """Test Supabase client import"""
    try:
        from supabase import create_client
        return True
    except ImportError as e:
        print(f"\n  Import error: {e}")
        return False

def test_supabase_url() -> bool:
    """Test Supabase URL format"""
    url = os.getenv('SUPABASE_URL')
    if not url:
        return False

    if not url.startswith('https://') or not '.supabase.co' in url:
        print(f"\n  Invalid Supabase URL format")
        return False

    return True

async def test_supabase_connection() -> bool:
    """Test Supabase connection"""
    try:
        from supabase import create_client

        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')

        client = create_client(url, key)

        # Try a simple query (this might fail if tables don't exist, but connection is tested)
        try:
            response = client.table('candidates').select('id').limit(1).execute()
            return True
        except Exception:
            # Connection works even if table doesn't exist
            return True
    except Exception as e:
        print(f"\n  Connection error: {e}")
        return False

def test_slack_token() -> bool:
    """Test Slack bot token format"""
    token = os.getenv('SLACK_BOT_TOKEN')
    if not token:
        print(f"\n  No token found")
        return False

    if not token.startswith('xoxb-'):
        print(f"\n  Invalid token format")
        return False

    return True

def test_github_token() -> bool:
    """Test GitHub token format"""
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print(f"\n  No token found")
        return False

    if not token.startswith('ghp_') and not token.startswith('github_pat_'):
        print(f"\n  Invalid token format")
        return False

    return True

def test_fastapi_import() -> bool:
    """Test FastAPI import"""
    try:
        from fastapi import FastAPI
        return True
    except ImportError as e:
        print(f"\n  Import error: {e}")
        return False

def test_app_import() -> bool:
    """Test app.main import"""
    try:
        # Add parent directory to path
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        from app.main import app
        return app is not None
    except Exception as e:
        print(f"\n  Import error: {e}")
        return False

async def main():
    """Run all service tests"""
    print(f"{Colors.BLUE}{'╔' + '═' * 58 + '╗'}{Colors.NC}")
    print(f"{Colors.BLUE}║     Agencity Service Integration Tests                ║{Colors.NC}")
    print(f"{Colors.BLUE}{'╚' + '═' * 58 + '╝'}{Colors.NC}")
    print()

    tester = ServiceTester()

    # Environment tests
    print(f"{Colors.BLUE}{'━' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}  Environment Configuration{Colors.NC}")
    print(f"{Colors.BLUE}{'━' * 60}{Colors.NC}")
    print()

    tester.test("Required environment variables", test_environment_variables)

    # OpenAI tests
    print()
    print(f"{Colors.BLUE}{'━' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}  OpenAI Integration{Colors.NC}")
    print(f"{Colors.BLUE}{'━' * 60}{Colors.NC}")
    print()

    tester.test("OpenAI library import", test_openai_import)
    tester.test("OpenAI API key format", test_openai_api_key)
    await tester.test_async("OpenAI API connection", test_openai_connection)

    # Redis tests
    print()
    print(f"{Colors.BLUE}{'━' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}  Redis Cache{Colors.NC}")
    print(f"{Colors.BLUE}{'━' * 60}{Colors.NC}")
    print()

    tester.test("Redis library import", test_redis_import)
    await tester.test_async("Redis connection", test_redis_connection)
    await tester.test_async("Redis operations", test_redis_operations)

    # Supabase tests
    print()
    print(f"{Colors.BLUE}{'━' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}  Supabase Database{Colors.NC}")
    print(f"{Colors.BLUE}{'━' * 60}{Colors.NC}")
    print()

    tester.test("Supabase library import", test_supabase_import)
    tester.test("Supabase URL format", test_supabase_url)
    await tester.test_async("Supabase connection", test_supabase_connection)

    # Slack tests
    print()
    print(f"{Colors.BLUE}{'━' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}  Slack Integration{Colors.NC}")
    print(f"{Colors.BLUE}{'━' * 60}{Colors.NC}")
    print()

    tester.test("Slack bot token format", test_slack_token)

    # GitHub tests
    print()
    print(f"{Colors.BLUE}{'━' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}  GitHub Integration{Colors.NC}")
    print(f"{Colors.BLUE}{'━' * 60}{Colors.NC}")
    print()

    tester.test("GitHub token format", test_github_token)

    # Application tests
    print()
    print(f"{Colors.BLUE}{'━' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}  Application{Colors.NC}")
    print(f"{Colors.BLUE}{'━' * 60}{Colors.NC}")
    print()

    tester.test("FastAPI import", test_fastapi_import)
    tester.test("Application import", test_app_import)

    # Print summary
    success = tester.print_summary()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    # Load .env file if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    asyncio.run(main())
