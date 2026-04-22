# Full-Stack TypeScript Template

Production-ready full-stack web application template with Hono, React, and Kubernetes.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Hono + TypeScript |
| ORM | Prisma |
| Security | Arcjet (rate limiting) |
| Frontend | React 18 + Vite |
| State | React Query + Zustand |
| Styling | Tailwind CSS |
| Database | PostgreSQL |
| Cache | Redis |
| Container | Docker + Kubernetes |

## Agents

This template is designed for use with [Agency](https://github.com/rwese/agency) - a multi-agent orchestration tool.

### Agent Roles

| Agent | Responsibilities |
|-------|-----------------|
| **backend** | API routes, Prisma models, business logic |
| **frontend** | React components, pages, API integration |
| **devops** | Docker, Kubernetes, CI/CD pipelines |
| **architect** | System design, patterns, ADRs |
| **security** | Auth, vulnerabilities, compliance |
| **qa** | Tests, automation, quality gates |

## Quick Start

### 1. Initialize Project

```bash
# Create new project from template
agency init-project --dir ~/projects/myapp --template https://github.com/rwese/agency-templates/tree/main/fullstack-ts

cd ~/projects/myapp
```

### 2. Start Development

```bash
# With Docker Compose
docker compose up

# Or start agents
agency start
```

### 3. Environment Setup

Copy `.env.example` files and configure:

```bash
# backend
cp backend/.env.example backend/.env

# frontend
cp frontend/.env.example frontend/.env
```

## Project Structure

```
fullstack-ts/
├── .agency/              # Agency configuration
│   ├── config.yaml       # Project settings
│   ├── manager.yaml      # Coordinator personality
│   ├── agents.yaml       # Agent definitions
│   └── agents/           # Individual agent configs
├── backend/              # Hono API
│   ├── src/
│   ├── prisma/          # Database schema
│   └── Dockerfile
├── frontend/             # React app
│   ├── src/
│   └── Dockerfile
├── k8s/                  # Kubernetes manifests
├── docker-compose.yml    # Local development
└── .github/workflows/    # CI/CD
```

## Development

### Backend

```bash
cd backend
pnpm install
pnpm dev          # Start dev server
pnpm build        # Production build
pnpm test         # Run tests
pnpm db:push      # Push schema
pnpm db:migrate   # Run migrations
pnpm db:studio    # Prisma Studio
```

### Frontend

```bash
cd frontend
pnpm install
pnpm dev          # Start dev server
pnpm build        # Production build
pnpm test         # Run tests
pnpm lint         # ESLint
pnpm typecheck    # TypeScript check
```

### E2E Tests

```bash
npx playwright test
```

## Deployment

### Local (Docker Compose)

```bash
docker compose up -d
```

### Kubernetes

```bash
# Apply manifests
kubectl apply -k k8s/

# Update images (after CI/CD)
kubectl set image deployment/api api=registry.yourdomain.com/fullstack/api:$SHA
kubectl set image deployment/frontend frontend=registry.yourdomain.com/fullstack/frontend:$SHA
```

## CI/CD

- **CI**: Runs on every PR - linting, type check, tests, security scan
- **Deploy**: Runs on merge to main - builds images, deploys to staging, then production

### Required Secrets

```
REGISTRY_USER      # Container registry username
REGISTRY_TOKEN     # Container registry token
```

## Quality Gates

| Check | Tool | Threshold |
|-------|------|-----------|
| TypeScript | tsc | 0 errors |
| ESLint | eslint | 0 errors |
| Unit Tests | vitest | 80% coverage |
| E2E Tests | playwright | 100% critical paths |
| Security | trivy | 0 critical vulns |

## License

MIT
