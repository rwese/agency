# agency-web API Specification

**Version:** 1.1  
**Date:** 2026-04-22  
**Status:** Draft  

---

## Overview

RESTful API for agency-web ticketing system.  
Base URL: `/api/v1`

### Authentication
- Session-based auth for web users
- API key header for automations: `Authorization: Bearer <api_key>`

### Response Format
All responses follow this structure:
```json
{
  "data": { ... } | [ ... ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100
  },
  "error": null
}
```

Error responses:
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

---

## Endpoints

### Authentication

#### POST /auth/login
Login with credentials.

**Request:**
```json
{
  "username": "alice",
  "password": "secret123"
}
```

**Response (200):**
```json
{
  "data": {
    "user": { "id": "uuid", "username": "alice", "role": "member" },
    "token": "jwt_token_here"
  }
}
```

---

#### POST /auth/logout
Logout current session.

**Response (200):**
```json
{ "data": { "success": true } }
```

---

#### GET /auth/me
Get current authenticated user.

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "username": "alice",
    "email": "alice@example.com",
    "role": "member",
    "teams": [{ "id": "uuid", "name": "Backend" }],
    "created_at": "2026-01-15T10:30:00Z"
  }
}
```

---

#### POST /auth/apikey
Generate API key for automation user. (Admin only)

**Request:**
```json
{
  "username": "ci-bot",
  "name": "GitHub Actions Bot",
  "team_ids": ["uuid"]
}
```

**Response (201):**
```json
{
  "data": {
    "api_key": "agw_sk_abc123...",
    "user_id": "uuid",
    "name": "GitHub Actions Bot",
    "created_at": "2026-04-22T12:00:00Z"
  }
}
```
> ⚠️ API key shown only once. Store securely.

---

### Teams

#### GET /teams
List teams current user belongs to.

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Backend",
      "description": "Backend team",
      "member_count": 4
    }
  ],
  "meta": { "page": 1, "per_page": 20, "total": 2 }
}
```

---

#### POST /teams
Create new team. (Admin only)

**Request:**
```json
{
  "name": "Frontend",
  "description": "Frontend development team"
}
```

**Response (201):** Created team object.

---

#### GET /teams/{id}
Get team details with members.

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "name": "Backend",
    "description": "...",
    "members": [
      { "id": "uuid", "username": "alice", "role": "member" },
      { "id": "uuid", "username": "bob", "role": "member" }
    ],
    "created_at": "2026-04-01T10:00:00Z"
  }
}
```

---

#### PUT /teams/{id}
Update team.

**Request:**
```json
{
  "name": "Backend Team",
  "description": "Updated description"
}
```

**Response (200):** Updated team object.

---

#### DELETE /teams/{id}
Delete team. (Admin only)

**Response (204):** No content.

---

#### POST /teams/{id}/members
Add member to team.

**Request:**
```json
{
  "user_id": "uuid"
}
```

**Response (201):**
```json
{ "data": { "success": true } }
```

---

#### DELETE /teams/{id}/members/{user_id}
Remove member from team.

**Response (204):** No content.

---

### Users

#### GET /users
List all users. (Admin only)

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| page | int | 1 | Page number |
| per_page | int | 20 | Items per page |
| role | string | - | Filter by role |
| team_id | uuid | - | Filter by team |

**Response (200):**
```json
{
  "data": [
    { "id": "uuid", "username": "alice", "email": "...", "role": "member", "teams": ["Backend"] },
    { "id": "uuid", "username": "bob", "email": "...", "role": "viewer", "teams": ["Frontend"] }
  ],
  "meta": { "page": 1, "per_page": 20, "total": 2 }
}
```

---

#### POST /users
Create new user. (Admin only)

**Request:**
```json
{
  "username": "carol",
  "email": "carol@example.com",
  "password": "secure_password",
  "role": "member",
  "team_ids": ["uuid"]
}
```

**Response (201):**
```json
{
  "data": {
    "id": "uuid",
    "username": "carol",
    "email": "carol@example.com",
    "role": "member",
    "teams": ["Backend"],
    "created_at": "2026-04-22T12:00:00Z"
  }
}
```

---

#### GET /users/{id}
Get user by ID.

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "username": "alice",
    "email": "alice@example.com",
    "role": "member",
    "teams": [{ "id": "uuid", "name": "Backend" }],
    "created_at": "2026-01-15T10:30:00Z"
  }
}
```

---

#### PUT /users/{id}
Update user. (Admin only, or self for limited fields)

**Request:**
```json
{
  "email": "newemail@example.com",
  "role": "admin",
  "team_ids": ["uuid1", "uuid2"]
}
```

**Response (200):** Updated user object.

---

#### DELETE /users/{id}
Delete user. (Admin only)

**Response (204):** No content.

---

### Epics

#### GET /epics
List all epics (team-scoped for current user).

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| page | int | 1 | Page number |
| per_page | int | 20 | Items per page |
| status | string | - | Filter: open, in_progress, review, blocked, done |
| team_id | uuid | - | Filter by team |
| tag | string | - | Filter by tag |
| created_by | uuid | - | Filter by creator |

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "title": "User Authentication",
      "description": "Implement login system",
      "status": "in_progress",
      "tags": ["security", "auth"],
      "team": { "id": "uuid", "name": "Backend" },
      "task_count": 5,
      "completed_task_count": 2,
      "created_at": "2026-01-20T09:00:00Z",
      "updated_at": "2026-04-20T14:30:00Z",
      "created_by": { "id": "uuid", "username": "alice" }
    }
  ],
  "meta": { "page": 1, "per_page": 20, "total": 10 }
}
```

---

#### POST /epics
Create new epic.

**Request:**
```json
{
  "title": "User Authentication",
  "description": "Implement login and session management",
  "status": "open",
  "tags": ["security"],
  "team_id": "uuid"
}
```

**Response (201):** Created epic object.

---

#### GET /epics/search?q=
Full-text search across epics.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| q | string | Search query |
| page | int | Page number |
| per_page | int | Items per page |

**Response (200):** List of matching epics with relevance score.

---

#### GET /epics/{id}
Get epic with tasks.

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "title": "User Authentication",
    "description": "...",
    "status": "in_progress",
    "tags": ["security"],
    "team": { "id": "uuid", "name": "Backend" },
    "created_at": "...",
    "updated_at": "...",
    "created_by": { "id": "uuid", "username": "alice" },
    "tasks": [
      {
        "id": "uuid",
        "title": "Design login form",
        "status": "done",
        "priority": "high",
        "tags": ["ui"],
        "assignee": { "id": "uuid", "username": "bob" }
      }
    ]
  }
}
```

---

#### PUT /epics/{id}
Update epic.

**Request:**
```json
{
  "title": "Updated Title",
  "status": "done",
  "tags": ["security", "done"]
}
```

**Response (200):** Updated epic object.

---

#### DELETE /epics/{id}
Delete epic. Also deletes all child tasks. (Admin only)

**Response (204):** No content.

---

### Tasks

#### GET /tasks
List all tasks (with filters).

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| page | int | 1 | Page number |
| per_page | int | 20 | Items per page |
| status | string | - | Filter by status |
| priority | string | - | Filter: low, medium, high, critical |
| epic_id | uuid | - | Filter by epic |
| team_id | uuid | - | Filter by team |
| assignee_id | uuid | - | Filter by assignee |
| tag | string | - | Filter by tag |
| external_id | string | - | Filter by GitHub reference |
| created_by | uuid | - | Filter by creator |

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "title": "Implement login form",
      "description": "...",
      "status": "in_progress",
      "priority": "high",
      "tags": ["ui", "auth"],
      "external_id": "github:owner/repo#123",
      "created_at": "...",
      "updated_at": "...",
      "epic": { "id": "uuid", "title": "User Authentication" },
      "team": { "id": "uuid", "name": "Backend" },
      "assignee": { "id": "uuid", "username": "bob" },
      "created_by": { "id": "uuid", "username": "alice" },
      "attachment_count": 2,
      "comment_count": 5,
      "github_ref_count": 1
    }
  ],
  "meta": { "page": 1, "per_page": 20, "total": 50 }
}
```

---

#### POST /tasks
Create new task.

**Request:**
```json
{
  "title": "Implement login form",
  "description": "Create HTML form with email/password fields",
  "status": "open",
  "priority": "high",
  "tags": ["ui"],
  "external_id": "github:owner/repo#123",
  "epic_id": "uuid",
  "assignee_id": "uuid"
}
```

**Response (201):** Created task object.

---

#### GET /tasks/search?q=
Full-text search across tasks.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| q | string | Search query |
| page | int | Page number |
| per_page | int | Items per page |

**Response (200):** List of matching tasks with relevance score.

---

#### GET /tasks/{id}
Get task with comments, attachments, and GitHub refs.

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "title": "Implement login form",
    "description": "...",
    "status": "in_progress",
    "priority": "high",
    "tags": ["ui"],
    "external_id": "github:owner/repo#123",
    "created_at": "...",
    "updated_at": "...",
    "epic": { "id": "uuid", "title": "User Authentication" },
    "team": { "id": "uuid", "name": "Backend" },
    "assignee": { "id": "uuid", "username": "bob" },
    "created_by": { "id": "uuid", "username": "alice" },
    "comments": [...],
    "attachments": [...],
    "github_refs": [
      {
        "id": "uuid",
        "ref_type": "pull_request",
        "ref_id": "PR #456",
        "url": "https://github.com/owner/repo/pull/456",
        "created_at": "..."
      }
    ]
  }
}
```

---

#### PUT /tasks/{id}
Update task.

**Request:**
```json
{
  "status": "done",
  "assignee_id": "uuid",
  "tags": ["ui", "done"]
}
```

**Response (200):** Updated task object.

---

#### DELETE /tasks/{id}
Delete task and its comments/attachments. (Admin or creator)

**Response (204):** No content.

---

### GitHub Integration

#### GET /tasks/{id}/github-refs
List GitHub references for a task.

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "ref_type": "commit",
      "ref_id": "abc123def",
      "url": "https://github.com/owner/repo/commit/abc123def",
      "created_at": "2026-04-22T12:00:00Z"
    },
    {
      "id": "uuid",
      "ref_type": "pull_request",
      "ref_id": "PR #456",
      "url": "https://github.com/owner/repo/pull/456",
      "created_at": "2026-04-22T12:00:00Z"
    }
  ]
}
```

---

#### POST /tasks/{id}/github-refs
Add GitHub reference to task.

**Request:**
```json
{
  "ref_type": "pull_request",
  "ref_id": "PR #456",
  "url": "https://github.com/owner/repo/pull/456"
}
```

**Response (201):** Created GitHub ref object.

---

#### POST /github/sync-issue
Sync a GitHub issue (webhook receiver from GitHub).

**Request:**
```json
{
  "action": "opened",
  "issue": {
    "number": 123,
    "title": "Bug: Login broken",
    "body": "...",
    "state": "open",
    "html_url": "https://github.com/owner/repo/issues/123"
  },
  "repository": {
    "full_name": "owner/repo"
  }
}
```

**Response (200):**
```json
{
  "data": {
    "task_id": "uuid",
    "synced": true,
    "action": "created"
  }
}
```

---

#### DELETE /github-refs/{id}
Remove GitHub reference.

**Response (204):** No content.

---

### Comments

#### GET /tasks/{id}/comments
List comments for a task.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| page | int | 1 | Page number |
| per_page | int | 50 | Items per page |

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "content": "This looks good!",
      "created_at": "2026-04-22T10:00:00Z",
      "updated_at": "2026-04-22T10:00:00Z",
      "author": { "id": "uuid", "username": "alice" }
    }
  ],
  "meta": { "page": 1, "per_page": 50, "total": 1 }
}
```

---

#### POST /tasks/{id}/comments
Add comment to task.

**Request:**
```json
{
  "content": "Updated the design based on feedback"
}
```

**Response (201):** Created comment object.

---

#### PUT /comments/{id}
Update comment. (Author only)

**Request:**
```json
{
  "content": "Updated content"
}
```

**Response (200):** Updated comment object.

---

#### DELETE /comments/{id}
Delete comment. (Admin, or comment author)

**Response (204):** No content.

---

### Attachments

#### GET /tasks/{id}/attachments
List attachments for a task.

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "filename": "build.log",
      "content_type": "text/plain",
      "size_bytes": 15000,
      "uploaded_at": "2026-04-22T12:00:00Z",
      "uploaded_by": { "id": "uuid", "username": "ci-bot" }
    }
  ]
}
```

---

#### POST /tasks/{id}/attachments
Upload attachment to task.

**Request:** `multipart/form-data`
```
file: <binary data>
```

**Response (201):**
```json
{
  "data": {
    "id": "uuid",
    "filename": "screenshot.png",
    "content_type": "image/png",
    "size_bytes": 120000,
    "storage_path": "/attachments/uuid/screenshot.png",
    "uploaded_at": "2026-04-22T12:00:00Z",
    "uploaded_by": { "id": "uuid", "username": "alice" }
  }
}
```

---

#### GET /attachments/{id}
Download attachment.

**Response:** Binary file with appropriate `Content-Type` header.

---

#### DELETE /attachments/{id}
Delete attachment. (Admin, uploader, or task creator)

**Response (204):** No content.

---

### Webhooks

#### GET /webhooks
List webhooks. (Admin only)

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Slack Notifications",
      "url": "https://hooks.slack.com/...",
      "events": ["task.created", "task.status_changed", "comment.created"],
      "active": true,
      "created_at": "2026-04-01T10:00:00Z"
    }
  ]
}
```

---

#### POST /webhooks
Create webhook.

**Request:**
```json
{
  "name": "Slack Notifications",
  "url": "https://hooks.slack.com/...",
  "events": ["task.created", "task.status_changed", "task.assigned", "comment.created"],
  "secret": "webhook_secret_for_signing"
}
```

**Response (201):** Created webhook object.

---

#### GET /webhooks/{id}
Get webhook details.

**Response (200):** Webhook object with stats.

---

#### PUT /webhooks/{id}
Update webhook.

**Request:**
```json
{
  "url": "https://new-url.com/webhook",
  "events": ["task.created", "epic.status_changed"],
  "active": false
}
```

**Response (200):** Updated webhook object.

---

#### DELETE /webhooks/{id}
Delete webhook.

**Response (204):** No content.

---

#### POST /webhooks/{id}/test
Send test event.

**Response (200):**
```json
{
  "data": {
    "success": true,
    "status_code": 200,
    "response_time_ms": 150
  }
}
```

---

### Admin

#### GET /admin/metrics
Get usage metrics. (Admin only)

**Response (200):**
```json
{
  "data": {
    "total_users": 10,
    "total_teams": 3,
    "total_epics": 25,
    "total_tasks": 150,
    "total_attachments": 500,
    "active_users_7d": 8,
    "tasks_created_7d": 12,
    "tasks_completed_7d": 8
  }
}
```

---

#### GET /admin/activity
Get activity logs.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| page | int | 1 | Page number |
| per_page | int | 50 | Items per page |
| entity_type | string | - | Filter: epic, task, comment, attachment |
| actor_id | uuid | - | Filter by user |
| action | string | - | Filter by action type |

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "action": "task.status_changed",
      "entity_type": "task",
      "entity_id": "uuid",
      "actor": { "id": "uuid", "username": "alice" },
      "payload": {
        "before": { "status": "in_progress" },
        "after": { "status": "done" }
      },
      "created_at": "2026-04-22T14:30:00Z"
    }
  ],
  "meta": { "page": 1, "per_page": 50, "total": 1000 }
}
```

---

#### GET /health
Health check endpoint.

**Response (200):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 86400,
  "database": "connected"
}
```

---

## Status Values

### Epic/Task Status
| Value | Description |
|-------|-------------|
| `open` | Not started |
| `in_progress` | Work underway |
| `review` | In review/testing |
| `blocked` | Waiting on external dependency |
| `done` | Completed |

### Task Priority
| Value | Description |
|-------|-------------|
| `low` | Nice to have |
| `medium` | Normal priority |
| `high` | Important |
| `critical` | Urgent, blocking |

### User Roles
| Value | Description |
|-------|-------------|
| `admin` | Full access |
| `member` | Create/edit within team, view all accessible |
| `viewer` | Read-only access |
| `automation` | API-only, limited permissions |

### GitHub Ref Types
| Value | Description |
|-------|-------------|
| `commit` | Git commit reference |
| `pull_request` | GitHub PR reference |
| `issue` | GitHub issue reference |

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Not authenticated |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 400 | Invalid input |
| `CONFLICT` | 409 | Resource conflict (e.g., duplicate username) |
| `PAYLOAD_TOO_LARGE` | 413 | Attachment too large |
| `INTERNAL_ERROR` | 500 | Server error |

---

## Webhook Payload Format

All webhook deliveries:
```json
{
  "event": "task.created",
  "timestamp": "2026-04-22T12:00:00Z",
  "data": { ... },
  "signature": "sha256=abc123..."
}
```

Signature verification:
```
HMAC-SHA256(secret, payload) = signature
```
