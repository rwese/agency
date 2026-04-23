# Demo Project 14: URL Shortener (Microservices + Docker)

**Type:** Microservices with Docker Compose
**Complexity:** High
**Purpose:** Test Docker, microservices, Redis, PostgreSQL, API gateway

## Overview

A production-ready URL shortener with API, worker, and Redis cache, all containerized.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│   Nginx    │────▶│   API       │
│             │     │  (Gateway) │     │   Service   │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                    ┌─────────────┐             │
                    │   Redis     │◀────────────┤
                    │  (Cache)   │             │
                    └─────────────┘             │
                                               │
                    ┌─────────────┐             │
                    │ PostgreSQL  │◀────────────┘
                    │  (Storage) │
                    └─────────────┘
```

## Services

### 1. API Service
- REST API for URL management
- Handles create, get, delete operations
- Caches short URLs in Redis
- Written in Python/FastAPI

### 2. Redirect Service
- High-performance redirect handler
- Serves static HTML redirects
- Reads from Redis cache
- Can fall back to PostgreSQL
- Written in Go for performance

### 3. Nginx Gateway
- Routes requests to services
- Handles HTTPS termination
- Rate limiting
- Static file serving

## Features

- [ ] Create short URL (POST /urls)
- [ ] Get original URL (GET /{short_code})
- [ ] Redirect to original URL (GET /r/{short_code})
- [ ] Delete short URL (DELETE /urls/{id})
- [ ] View stats (GET /urls/{id}/stats)
- [ ] Click analytics
- [ ] Custom short codes
- [ ] URL expiration
- [ ] Rate limiting
- [ ] Health check endpoints

## Tech Stack

- **API:** Python + FastAPI
- **Cache:** Redis
- **Database:** PostgreSQL
- **Gateway:** Nginx
- **Worker:** Python (for analytics)
- **Container:** Docker Compose

## Data Model

### PostgreSQL

```sql
-- urls table
CREATE TABLE urls (
  id SERIAL PRIMARY KEY,
  short_code VARCHAR(20) UNIQUE NOT NULL,
  original_url TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP,
  is_active BOOLEAN DEFAULT true,
  created_by VARCHAR(100)
);

-- clicks table (analytics)
CREATE TABLE clicks (
  id SERIAL PRIMARY KEY,
  url_id INTEGER REFERENCES urls(id),
  clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  referrer TEXT,
  user_agent TEXT,
  ip_address INET
);
```

### Redis Cache

```
url:{short_code} -> original_url (TTL: 1 hour)
clicks:{short_code} -> click_count
```

## API Endpoints

```bash
# Create short URL
POST /api/v1/urls
{"url": "https://example.com/very/long/path", "custom_code": "my-link"}

# Get URL info
GET /api/v1/urls/{short_code}

# Delete URL
DELETE /api/v1/urls/{short_code}

# Get stats
GET /api/v1/urls/{short_code}/stats

# Health check
GET /health
GET /health/ready
```

## Docker Configuration

### docker-compose.yml

```yaml
version: '3.8'
services:
  api:
    build: ./api
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/urls
      - REDIS_URL=redis://cache:6379
    depends_on:
      - db
      - cache

  redirect:
    build: ./redirect
    ports: ["8080:8080"]
    environment:
      - REDIS_URL=redis://cache:6379
      - POSTGRES_URL=postgresql://user:pass@db:5432/urls
    depends_on:
      - cache
      - db

  nginx:
    image: nginx:alpine
    ports: ["80:80"]
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - api
      - redirect

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=urls
    volumes:
      - postgres_data:/var/lib/postgresql/data

  cache:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

## Test Cases

| ID | Test | Description |
|----|------|-------------|
| TC01 | Create URL | Short code returned |
| TC02 | Redirect | 302 to original |
| TC03 | Custom code | User-defined code works |
| TC04 | Expiration | Expired URL returns 410 |
| TC05 | Stats | Click count increments |
| TC06 | Rate limit | 429 after limit |
| TC07 | Health check | All services healthy |
| TC08 | Cache hit | Redis served correctly |
| TC09 | Cache miss | DB queried, cached |
| TC10 | Delete | URL no longer accessible |

## Task Breakdown

1. Setup Docker Compose structure
2. Create API service (FastAPI)
3. Setup PostgreSQL schema
4. Implement URL CRUD in API
5. Add Redis caching layer
6. Create redirect service (Go)
7. Configure Nginx gateway
8. Add health check endpoints
9. Implement rate limiting
10. Add click tracking/analytics
11. Write Docker tests
12. Write integration tests
13. Create e2e test report

## Success Criteria

- All services start with `docker-compose up`
- API creates short URLs correctly
- Redirects work (302 to original)
- Redis caches short URLs
- Click analytics are tracked
- Health endpoints return 200
- Rate limiting works
- Nginx routes correctly
- Tests pass in containers
