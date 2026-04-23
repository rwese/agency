# Demo Project 06: API Rate Limiter Middleware

**Type:** Library/Middleware
**Complexity:** Medium-High
**Purpose:** Test middleware patterns, concurrency, distributed state

## Overview

A rate limiting middleware library for Python web frameworks (Flask, FastAPI, Starlette) with multiple backend support.

## Features

- [ ] Token bucket algorithm implementation
- [ ] Sliding window algorithm implementation
- [ ] In-memory storage backend
- [ ] Redis storage backend (for distributed)
- [ ] Per-IP limiting
- [ ] Per-user limiting (via API key)
- [ ] Custom limits per endpoint
- [ ] Rate limit headers in response (X-RateLimit-*)
- [ ] Whitelist/blacklist support
- [ ] Framework adapters (Flask, FastAPI, Starlette)

## Tech Stack

- **Language:** Python
- **Dependencies:** `redis` (optional), web framework of choice

## Usage Example

```python
from fastapi import FastAPI
from rate_limiter import RateLimiter, RedisBackend

app = FastAPI()
limiter = RateLimiter(backend=RedisBackend("redis://localhost"))

@app.get("/api/users")
@limiter.limit(requests=100, window=60)  # 100 req/min
async def get_users():
    return {"users": [...]}
```

## CLI/Script Interface

```bash
# Test rate limiter
rate-limit-test --url http://localhost:8000/api --requests 150 --concurrency 10

# Benchmark
rate-limit-bench --duration 60 --rate 100
```

## Test Cases

| ID | Test | Description |
|----|------|-------------|
| TC01 | Token bucket | 100 requests in window, 101 fails |
| TC02 | Sliding window | Window boundary correct |
| TC03 | Redis backend | Distributed limiting works |
| TC04 | Per-IP | Different IPs get separate limits |
| TC05 | Per-user | API keys tracked separately |
| TC06 | Headers | X-RateLimit-* headers present |
| TC07 | Retry-After | Retry-After header on 429 |
| TC08 | Concurrent | Thread-safe implementation |

## Task Breakdown

1. Implement token bucket algorithm
2. Implement sliding window algorithm
3. Create in-memory storage backend
4. Create Redis storage backend
5. Build middleware adapter base
6. Implement Flask adapter
7. Implement FastAPI/Starlette adapter
8. Add rate limit headers
9. Add whitelist/blacklist
10. Write unit tests for algorithms
11. Write integration tests with frameworks
12. Create e2e test report

## Success Criteria

- Token bucket correctly limits requests
- Redis backend works across multiple processes
- Headers present on all responses
- 429 returned when limit exceeded
- Thread-safe under concurrent load
