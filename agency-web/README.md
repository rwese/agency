# agency-web

A lightweight, self-hosted ticketing system for tracking Epics and Tasks. Built with [Agency](https://github.com/rwese/agency) multi-agent orchestration in mind.

## Features

- **Epics & Tasks** — Organize work into high-level initiatives with granular task breakdowns
- **Kanban Board** — Visual workflow management with drag-and-drop status transitions
- **Comments** — Threaded discussions with full Markdown support
- **File Attachments** — Attach and share artifacts with configurable storage limits
- **Webhooks** — HTTP callbacks for external integrations (Slack, Jenkins, etc.)
- **GitHub Integration** — Sync with GitHub Issues, PRs, and commits
- **Full-Text Search** — Quickly find any epic, task, or comment
- **REST API** — Programmatic access for automation and CI/CD pipelines
- **Activity Logs** — Complete audit trail of all changes
- **Admin Dashboard** — Usage metrics, storage stats, and system management
- **Mobile-First Design** — Responsive UI optimized for all devices
- **Accessibility** — WCAG 2.1 AA compliant with keyboard navigation

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Hono + TypeScript |
| ORM | Prisma |
| Database | SQLite |
| Frontend | React 18 + Vite |
| State | React Query + Zustand |
| Styling | Tailwind CSS |
| Auth | Self-contained (no external providers) |
| Container | Docker + Kubernetes |

## Quick Start

### Docker Compose (Local Development)

```bash
# Clone the repository
git clone https://github.com/rwese/agency/agency-web.git
cd agency-web

# Start the application
docker compose up

# Access at http://localhost:8080
```

### Environment Setup

Copy `.env.example` files and configure:

```bash
# backend
cp backend/.env.example backend/.env

# frontend
cp frontend/.env.example frontend/.env
```

#### Required Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AGENCY_DB_PATH` | SQLite database path | Yes |
| `AGENCY_SECRET_KEY` | JWT signing key / encryption | Yes |
| `AGENCY_ADMIN_EMAIL` | First admin email | On first run |
| `AGENCY_ADMIN_PASSWORD` | First admin password | On first run (auto-generated if not set) |
| `AGENCY_AUTO_UPGRADE` | Auto-migrate database | No (default: false) |

## Project Structure

```
agency-web/
├── .agency/              # Agency configuration
│   ├── config.yaml       # Project settings
│   ├── manager.yaml      # Coordinator personality
│   ├── agents.yaml       # Agent definitions
│   └── agents/           # Individual agent configs
├── backend/              # Hono API
│   ├── src/
│   │   ├── routes/       # API routes
│   │   ├── services/     # Business logic
│   │   └── middleware/   # Auth, logging, etc.
│   ├── prisma/          # Database schema
│   └── Dockerfile
├── frontend/             # React app
│   ├── src/
│   │   ├── components/   # UI components
│   │   ├── pages/       # Route pages
│   │   └── hooks/       # Custom hooks
│   └── Dockerfile
├── k8s/                  # Kubernetes manifests
├── docker-compose.yml    # Local development
├── .github/workflows/    # CI/CD
└── docs/                 # Documentation
```

## Development

### Prerequisites

- Node.js 20+
- pnpm 8+
- Docker & Docker Compose (for local dev)

### Backend

```bash
cd backend
pnpm install
pnpm dev          # Start dev server
pnpm build       # Production build
pnpm test        # Run tests
pnpm db:push     # Push schema
pnpm db:migrate  # Run migrations
pnpm db:studio   # Prisma Studio
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

## API Documentation

### Authentication
```
POST   /api/auth/login          # User login
POST   /api/auth/logout         # User logout
GET    /api/auth/me             # Current user info
POST   /api/auth/apikey         # Generate API key (admin)
POST   /api/auth/invite         # Send magic link invite (admin)
```

### Teams
```
GET    /api/teams               # List teams
POST   /api/teams               # Create team (admin)
GET    /api/teams/{id}          # Get team
PUT    /api/teams/{id}          # Update team
DELETE /api/teams/{id}          # Delete team (admin)
POST   /api/teams/{id}/members  # Add member
DELETE /api/teams/{id}/members/{user_id}  # Remove member
```

### Epics
```
GET    /api/epics               # List epics (team-scoped)
POST   /api/epics               # Create epic
GET    /api/epics/{id}          # Get epic with tasks
PUT    /api/epics/{id}          # Update epic
DELETE /api/epics/{id}          # Delete epic
GET    /api/epics/search?q=     # Full-text search
```

### Tasks
```
GET    /api/tasks               # List tasks (with filters)
POST   /api/tasks               # Create task
GET    /api/tasks/{id}          # Get task with comments/attachments
PUT    /api/tasks/{id}          # Update task
DELETE /api/tasks/{id}          # Delete task
POST   /api/tasks/bulk-update   # Bulk update status/assignee
GET    /api/tasks/search?q=     # Full-text search
```

### Comments
```
GET    /api/tasks/{id}/comments # List comments
POST   /api/tasks/{id}/comments # Add comment
PUT    /api/comments/{id}       # Update comment
DELETE /api/comments/{id}       # Delete comment
```

### Attachments
```
GET    /api/tasks/{id}/attachments     # List attachments
POST   /api/tasks/{id}/attachments     # Upload attachment
GET    /api/attachments/{id}           # Download attachment
DELETE /api/attachments/{id}           # Delete attachment
```

### GitHub Integration
```
GET    /api/tasks/{id}/github-refs     # List GitHub refs
POST   /api/tasks/{id}/github-refs     # Add GitHub ref
POST   /api/github/sync                # Sync webhook receiver
GET    /api/github/config              # Get GitHub App config
PUT    /api/github/config              # Update GitHub App config
```

### Webhooks
```
GET    /api/webhooks            # List webhooks
POST   /api/webhooks            # Create webhook
PUT    /api/webhooks/{id}       # Update webhook
DELETE /api/webhooks/{id}       # Delete webhook
POST   /api/webhooks/{id}/test  # Send test event
```

### Admin
```
GET    /api/admin/metrics        # Usage metrics
GET    /api/admin/activity       # Activity logs
GET    /api/admin/storage        # Storage usage
GET    /api/health              # Health check
POST   /api/admin/backup         # Trigger full backup
```

See [API.md](API.md) for complete API documentation.

## Deployment

### Docker Compose (Production)

```bash
docker compose -f docker-compose.yml up -d
```

### Kubernetes

```bash
# Apply manifests
kubectl apply -k k8s/

# Update images (after CI/CD)
kubectl set image deployment/api api=registry.yourdomain.com/agency/api:$SHA
kubectl set image deployment/frontend frontend=registry.yourdomain.com/agency/frontend:$SHA
```

### Container Registry

Images are published to GHCR (GitHub Container Registry):
- `ghcr.io/rwese/agency-web/api`
- `ghcr.io/rwese/agency-web/frontend`

## CI/CD

GitHub Actions workflows handle:
- **CI**: Linting, type checking, tests, security scans
- **Deploy**: Build images, deploy to staging on merge to main

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

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for system design details.

See [DATA_MODEL.md](DATA_MODEL.md) for entity relationships.

## Documentation

| Document | Description |
|----------|-------------|
| [PRD.md](PRD.md) | Product requirements and user stories |
| [API.md](API.md) | API contract documentation |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture |
| [DATA_MODEL.md](DATA_MODEL.md) | Data model details |
| [TEST_PLAN.md](TEST_PLAN.md) | Testing strategy |

## Contributing

1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/your-username/agency-web.git`
3. **Create a branch**: `git checkout -b feature/my-feature`
4. **Make changes** and commit using conventional commits
5. **Push** to your fork: `git push origin feature/my-feature`
6. **Open a Pull Request** against `main`

### Coding Standards

- TypeScript strict mode enabled
- ESLint + Prettier for code formatting
- Conventional Commits for changelog automation
- Tests required for new features

## License

MIT
