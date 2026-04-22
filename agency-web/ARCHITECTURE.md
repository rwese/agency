# agency-web Architecture

**Version:** 1.0  
**Date:** 2026-04-22  
**Status:** Draft  

---

## 1. System Overview

agency-web is a lightweight, self-hosted ticketing system for managing Epics and Tasks. It provides a RESTful API, a responsive web UI, GitHub integration, and webhook support for external automation.

### Design Principles

1. **Self-contained**: No external auth providers, databases, or storage dependencies
2. **On-premise deployment**: Single Docker container for easy deployment
3. **API-first**: All features accessible via REST API
4. **Accessibility**: WCAG 2.1 AA compliant, screen reader optimized
5. **Mobile-first**: Responsive design with keyboard shortcuts

### Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Backend | Hono + TypeScript | Lightweight, fast, edge-ready |
| Database | SQLite + Prisma | Single-file, zero-config, auto-migrations |
| Frontend | React + Vite + Tailwind | Fast DX, small bundle, utility-first CSS |
| Container | Docker | Single container deployment to GHCR |

---

## 2. System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        agency-web                                │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Frontend   │    │    API       │    │   Worker     │      │
│  │   (React)    │    │   (Hono)     │    │   (Jobs)     │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                  │                    │              │
│         └──────────────────┼────────────────────┘              │
│                            │                                   │
│                   ┌────────┴────────┐                         │
│                   │   Business     │                         │
│                   │    Logic        │                         │
│                   └────────┬────────┘                         │
│                            │                                   │
│         ┌──────────────────┼──────────────────┐              │
│         │                  │                  │              │
│  ┌──────┴──────┐   ┌───────┴──────┐   ┌──────┴──────┐        │
│  │  Database   │   │   Storage    │   │  Webhooks   │        │
│  │  (SQLite)   │   │  (Files)     │   │  (HTTP)     │        │
│  └─────────────┘   └──────────────┘   └─────────────┘        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
agency-web/
├── backend/                      # Hono API server
│   ├── src/
│   │   ├── index.ts              # Entry point
│   │   ├── routes/               # API route handlers
│   │   │   ├── auth.ts
│   │   │   ├── teams.ts
│   │   │   ├── users.ts
│   │   │   ├── epics.ts
│   │   │   ├── tasks.ts
│   │   │   ├── comments.ts
│   │   │   ├── attachments.ts
│   │   │   ├── webhooks.ts
│   │   │   └── admin.ts
│   │   ├── services/            # Business logic
│   │   │   ├── auth.service.ts
│   │   │   ├── github.service.ts
│   │   │   └── webhook.service.ts
│   │   ├── middleware/           # Hono middleware
│   │   │   ├── auth.middleware.ts
│   │   │   ├── error.middleware.ts
│   │   │   └── logger.middleware.ts
│   │   └── lib/                  # Utilities
│   │       ├── db.ts             # Prisma client
│   │       └── storage.ts        # File storage utilities
│   └── prisma/
│       └── schema.prisma         # Database schema
├── frontend/                     # React SPA
│   ├── src/
│   │   ├── main.tsx              # Entry point
│   │   ├── App.tsx               # Root component
│   │   ├── components/           # Reusable UI components
│   │   │   ├── ui/               # Base components
│   │   │   ├── layout/           # Layout components
│   │   │   └── features/         # Feature components
│   │   ├── pages/                # Page components
│   │   ├── hooks/                # Custom React hooks
│   │   ├── services/             # API client
│   │   ├── stores/               # State management
│   │   └── styles/               # Global styles
│   └── index.html
├── storage/                      # File attachment storage
│   └── attachments/
├── docker-compose.yml            # Local development
├── Dockerfile                    # Production image
└── .github/
    └── workflows/
        └── ci.yml               # GitHub Actions CI/CD
```

---

## 3. Data Architecture

### Entity Relationship Diagram

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│    Team       │────────▶│    Epic      │──┐      │    Task      │
├──────────────┤         ├──────────────┤  │      ├──────────────┤
│ id (PK)      │         │ id (PK)      │  │      │ id (PK)      │
│ name         │         │ title        │  │      │ title        │
│ description  │         │ description  │  │      │ description  │
│ created_at   │         │ status       │  │      │ status       │
└──────────────┘         │ tags         │  │      │ priority     │
       │                 │ team_id (FK) │  │      │ tags         │
       │                 │ created_by   │  │      │ external_id  │
       │                 └──────────────┘  │      │ epic_id (FK) │
       │                                    │      │ assignee_id  │
┌──────────────┐         ┌──────────────┐  │      │ created_by   │
│    User      │◀────────│   Comment    │◀─┘      └──────────────┘
├──────────────┤         ├──────────────┤                 │
│ id (PK)      │         │ id (PK)      │          ┌───────┴───────┐
│ username     │────────▶│ content      │          │               │
│ email        │         │ task_id (FK) │◀─────────│  GitHubRef    │
│ password_hash│         │ author_id    │          ├───────────────┤
│ role         │         └──────────────┘          │ ref_type      │
│ api_key_hash │                                       │ ref_id        │
└──────────────┘                                       │ url           │
       │                                               │ task_id (FK)  │
       │                 ┌──────────────┐              └───────────────┘
       │                 │ Attachment   │
       │                 ├──────────────┤
       │                 │ id (PK)      │
       │                 │ filename     │
       │                 │ content_type │
       │                 │ size_bytes   │
       │                 │ storage_path │
       │                 │ task_id (FK) │
       │                 │ uploaded_by  │
       │                 └──────────────┘

       ┌──────────────┐         ┌──────────────┐
       │   Webhook     │         │ ActivityLog  │
       ├──────────────┤         ├──────────────┤
       │ id (PK)       │         │ id (PK)      │
       │ name          │         │ action       │
       │ url           │         │ entity_type  │
       │ events        │         │ entity_id    │
       │ secret        │         │ actor_id     │
       │ active        │         │ payload      │
       │ created_by    │         └──────────────┘
       └──────────────┘

User ◄──────────────► Team  (many-to-many via user_teams)
```

### Data Model Details

See [DATA_MODEL.md](./DATA_MODEL.md) for complete table definitions, indexes, and constraints.

### Key Design Decisions

1. **UUID Primary Keys**: All entities use UUIDv4 for distributed-friendly IDs
2. **Soft Delete**: Future enhancement via `deleted_at` field
3. **JSON Tags**: Stored as TEXT with JSON functions for flexibility
4. **Cascade Delete**: Epic deletion cascades to Tasks, Comments, Attachments
5. **No Cascade for Teams**: Epics require explicit reassignment before team deletion

---

## 4. API Architecture

### API Design Principles

1. **RESTful**: Resource-based URLs with proper HTTP verbs
2. **Consistent Response Format**: All responses follow `{data, meta, error}` structure
3. **Pagination**: Cursor-based for lists with `page`/`per_page` parameters
4. **Versioning**: `/api/v1` prefix for future-proofing
5. **Filtering**: Query parameters for list filtering

### Authentication Flow

```
┌─────────┐         ┌─────────┐         ┌─────────┐
│ Client  │         │   API   │         │  DB     │
└────┬────┘         └────┬────┘         └────┬────┘
     │                   │                   │
     │  POST /auth/login │                   │
     │  {username, password}                 │
     │───────────────────▶│                   │
     │                   │  Verify password │
     │                   │─────────────────▶│
     │                   │◀─────────────────│
     │                   │  Return user     │
     │  {token, user}    │                   │
     │◀──────────────────│                   │
     │                   │                   │
     │  GET /api/tasks  │                   │
     │  Authorization: Bearer <token>        │
     │──────────────────▶│                   │
     │                   │  Validate token  │
     │                   │─────────────────▶│
     │  {data: [...]}    │                   │
     │◀──────────────────│                   │
```

### Authentication Methods

| Method | Use Case | Header |
|--------|----------|--------|
| Session | Web UI users | Cookie-based |
| API Key | Automation systems | `Authorization: Bearer <api_key>` |

### API Key Flow (Automation)

```
1. Admin creates automation user via POST /auth/apikey
2. System generates secure API key: agw_sk_xxx
3. Key is shown once and must be stored securely (hashed in DB)
4. Automation includes key in Authorization header
5. System validates key and extracts user identity
```

### Error Handling

All errors return consistent structure:

```json
{
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Title is required",
    "details": { "field": "title" }
  }
}
```

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Not authenticated |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 400 | Invalid input |
| `CONFLICT` | 409 | Duplicate resource |
| `PAYLOAD_TOO_LARGE` | 413 | File too large |
| `INTERNAL_ERROR` | 500 | Server error |

---

## 5. Security Architecture

### Authentication & Authorization

```
┌─────────────────────────────────────────────────────────────┐
│                    Authorization Matrix                     │
├──────────────┬─────────┬─────────┬─────────┬───────────────┤
│   Resource   │  Admin  │ Member  │ Viewer  │  Automation   │
├──────────────┼─────────┼─────────┼─────────┼───────────────┤
│ Teams        │ CRUD    │ List    │ List    │ None          │
│ Users        │ CRUD    │ Read    │ Read    │ None          │
│ Epics        │ CRUD    │ CRUD    │ Read    │ Create        │
│ Tasks        │ CRUD    │ CRUD    │ Read    │ CRUD          │
│ Comments     │ CRUD    │ CRUD    │ Read    │ Create        │
│ Attachments  │ CRUD    │ CRUD    │ Read    │ Create        │
│ Webhooks     │ CRUD    │ None    | None    | None          │
│ Admin APIs   │ CRUD    | None    | None    | None          │
└──────────────┴─────────┴─────────┴─────────┴───────────────┘
```

### Password Security

- Algorithm: bcrypt (cost factor 12)
- Minimum password length: 8 characters
- No password strength requirements (self-hosted, team discretion)

### API Rate Limiting

| Tier | Limit | Scope |
|------|-------|-------|
| Authenticated users | 1000 req/min | Per user |
| API keys | 100 req/min | Per key |
| Anonymous | 20 req/min | Per IP |

### Webhook Security

```
┌──────────────┐    HMAC-SHA256     ┌──────────────┐
│   agency-web │──────────────────▶│   External   │
│              │  payload + secret  │   System     │
└──────────────┘                    └──────────────┘

Signature header: X-Agency-Signature: sha256=abc123...
```

---

## 6. Storage Architecture

### File Storage

```
/storage/
└── attachments/
    └── {task_id}/
        └── {attachment_id}_{sanitized_filename}
```

### Storage Rules

1. **Local filesystem only**: No S3 or cloud storage
2. **Maximum file size**: 50MB (configurable)
3. **Filename sanitization**: Remove special characters, truncate if needed
4. **UUID collision prevention**: Use UUID for both task and attachment IDs

### Blocked File Types (Default)

```
.exe, .dmg, .sh, .bat, .cmd, .ps1, .vbs, .scr
```

### Integrity Verification

- SHA256 checksum stored with each attachment
- Checksum calculated on upload
- Optional verification on download

---

## 7. Integration Architecture

### GitHub Integration

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   GitHub    │ Webhook │  agency-web │  API    │  GitHub     │
│ Repository  │────────▶│             │────────▶│  API        │
└─────────────┘         └─────────────┘         └─────────────┘
```

#### Inbound Events (GitHub → agency-web)

| Event | Action |
|-------|--------|
| Issue opened | Create task with `external_id` |
| Issue closed | Set linked task to `done` |
| PR opened | Link PR to task (via `T-{id}` reference) |
| PR merged | Move linked task to `review` or `done` |
| Commit referenced | Create `GitHubRef` |

#### Outbound Events (agency-web → GitHub)

| Event | Action |
|-------|--------|
| Task created | Post comment on linked issue |
| Task status changed | Post comment on linked issue |
| Task assigned | Post comment on linked issue |
| Comment added | Post comment on linked issue |

#### Reference Patterns

```
Closes owner/repo#123      # GitHub native
Fixes T-456                # agency-web task reference
Related to T-789           # agency-web task reference
```

### Webhook System

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  agency-web │ Delivery│   External  │         │   System    │
│   Event     │────────▶│   Endpoint  │────────▶│   Logic     │
└─────────────┘         └─────────────┘         └─────────────┘
```

#### Supported Events

| Category | Events |
|----------|--------|
| Epic | `epic.created`, `epic.updated`, `epic.deleted`, `epic.status_changed` |
| Task | `task.created`, `task.updated`, `task.deleted`, `task.status_changed`, `task.assigned` |
| Comment | `comment.created`, `comment.deleted` |
| Attachment | `attachment.uploaded`, `attachment.deleted` |

---

## 8. Frontend Architecture

### Component Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                        App Shell                            │
│  ┌─────────┐  ┌─────────────────────────────────────────┐  │
│  │ Sidebar │  │              Main Content                │  │
│  │         │  │  ┌─────────────────────────────────────┐  │  │
│  │ • Logo  │  │  │           Page Header                │  │  │
│  │ • Nav   │  │  ├─────────────────────────────────────┤  │  │
│  │ • Teams │  │  │                                      │  │  │
│  │ • User  │  │  │           Page Content               │  │  │
│  │         │  │  │                                      │  │  │
│  └─────────┘  │  └─────────────────────────────────────┘  │  │
│               └─────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Page Structure

| Route | Page | Description |
|-------|------|-------------|
| `/` | Dashboard | Assigned tasks, team progress, recent activity |
| `/epics` | Epic List | All epics with filters |
| `/epics/:id` | Epic Detail | Epic with child tasks |
| `/tasks` | Task List | All tasks with filters |
| `/tasks/:id` | Task Detail | Task with comments, attachments, GitHub refs |
| `/teams` | Team List | Teams user belongs to |
| `/settings` | Settings | User preferences |

### State Management

- **Server State**: React Query for API data fetching and caching
- **UI State**: React useState/useReducer for local state
- **URL State**: Search params for filters and pagination

### Responsive Breakpoints

| Breakpoint | Width | Layout |
|------------|-------|--------|
| Mobile | < 640px | Bottom nav, stacked content |
| Tablet | 640-1024px | Collapsible sidebar |
| Desktop | > 1024px | Persistent sidebar |

---

## 9. Deployment Architecture

### Container Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Container                         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   Hono Server                       │    │
│  │   ┌───────────┐  ┌───────────┐  ┌───────────┐     │    │
│  │   │   API     │  │  Static   │  │   WS      │     │    │
│  │   │  /api/*   │  │   /       │  │  /ws      │     │    │
│  │   └───────────┘  └───────────┘  └───────────┘     │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                   │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────┐    │
│  │   SQLite   │  │  Storage   │  │   React SPA       │    │
│  │ /data/*.db │  │ /storage/* │  │   (built assets)   │    │
│  └────────────┘  └────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AGENCY_DB_PATH` | Yes | `./data/agency.db` | SQLite database path |
| `AGENCY_PORT` | No | `8080` | Server port |
| `AGENCY_SECRET_KEY` | Yes | - | JWT signing key |
| `AGENCY_ADMIN_EMAIL` | First run | - | Initial admin email |
| `AGENCY_ADMIN_PASSWORD` | First run | Auto-generate | Initial admin password |
| `AGENCY_AUTO_UPGRADE` | No | `false` | Auto-apply migrations |

### Health Check

```
GET /health
Response: { "status": "healthy", "version": "1.0.0", "database": "connected" }
```

---

## 10. Development Architecture

### Local Development

```bash
# Start all services
docker-compose up -d

# Backend: http://localhost:3000
# Frontend: http://localhost:5173 (Vite dev server)
# API: http://localhost:3000/api/v1
```

### CI/CD Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Push/PR   │───▶│    Build    │───▶│    Test     │───▶│   Deploy    │
│             │    │  Docker     │    │  Lint/Type │    │   to GHCR   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### GitHub Actions Workflows

| Workflow | Trigger | Actions |
|----------|---------|---------|
| `ci.yml` | Push/PR | Lint, Type check, Test, Build |

---

## 11. Performance Considerations

### Database

- **Indexes**: All foreign keys and frequently queried columns indexed
- **Pagination**: Required for list endpoints (default 20 items)
- **Full-text search**: SQLite FTS5 for title/description search

### API

- **Response caching**: ETag headers for GET requests
- **Compression**: Gzip for JSON responses
- **Rate limiting**: Per-user and per-API-key limits

### Frontend

- **Code splitting**: Route-based lazy loading
- **Optimistic updates**: Immediate UI feedback
- **Polling**: For real-time updates (WebSocket optional future enhancement)

---

## 12. Observability

### Logging

- **Format**: JSON structured logs
- **Levels**: debug, info, warn, error
- **Fields**: timestamp, level, message, requestId, userId, duration

### Metrics (Admin)

- Total users/teams/epics/tasks
- Active users (7-day)
- Tasks created/completed (7-day)
- Storage usage

### Activity Logs

- All write operations logged
- Audit trail with before/after values
- Configurable retention period

---

## 13. Future Considerations

| Feature | Priority | Notes |
|---------|----------|-------|
| Dark mode | Should | CSS variable-based theming |
| WebSocket updates | Could | Real-time sync |
| SSO/OAuth | Could | Future integration |
| Sub-tasks | Won't | Out of scope v1 |
| Time tracking | Won't | Out of scope v1 |

---

## 14. Related Documents

- [PRD.md](./PRD.md) - Product requirements
- [API.md](./API.md) - API specification
- [DATA_MODEL.md](./DATA_MODEL.md) - Database schema
- [UI_WIREFRAMES.md](./UI_WIREFRAMES.md) - UI layouts
- [TODO.md](./TODO.md) - Implementation tasks
