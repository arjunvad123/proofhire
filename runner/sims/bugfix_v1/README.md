# Bug Fix Challenge: Rate Limiter

## Overview

This simulation tests your ability to diagnose and fix a bug in a rate limiting module.

## The Problem

The `RateLimiter` class in `app/rate_limiter.py` has a bug that allows clients to make one more request than the configured limit.

For example, with `max_requests=3`, clients can actually make 4 requests before being blocked.

## Your Task

1. **Find the Bug**: Examine the code and identify the root cause
2. **Fix the Bug**: Modify the code to correctly enforce the rate limit
3. **Add a Test**: Write a regression test that would catch this bug
4. **Document Your Approach**: Write up how you identified and fixed the issue

## Running Tests

```bash
pytest tests/ -v
```

Currently, `test_blocks_requests_over_limit` fails due to the bug.

## Expected Outcome

- All tests pass
- The rate limiter correctly blocks the (max_requests + 1)th request
- Your fix doesn't break any other functionality

## Time Limit

60 minutes
