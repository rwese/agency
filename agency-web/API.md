# agency-web API Specification

**Version:** 1.0  
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
    "token": "session_token_here"
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
  "name": "GitHub Actions Bot"
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

### Users

#### GET /users
List all users. (Admin only)

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| page | int | 1 | Page number |
| per_page | int | 20 | Items per page |
| role | string | - | Filter by role |

**Response (200):**
```json
{
  "data": [
    { "id": "uuid", "username": "alice", "email": "...", "role": "member" },
    { "id": "uuid", "username": "bob", "email": "...", "role": "viewer" }
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
  "role": "member"
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
  "role": "admin"
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
List all epics.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| page | int | 1 | Page number |
| per_page | int | 20 | Items per page |
| status | string | - | Filter: open, in_progress, review, blocked, done |
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
  "status": "open"
}
```

**Response (201):** Created epic object.

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
    "created_at": "...",
    "updated_at": "...",
    "created_by": { "id": "uuid", "username": "alice" },
    "tasks": [
      {
        "id": "uuid",
        "title": "Design login form",
        "status": "done",
        "priority": "high",
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
  "status": "done"
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
List all tasks.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| page | int | 1 | Page number |
| per_page | int | 20 | Items per page |
| status | string | - | Filter by status |
| priority | string | - | Filter: low, medium, high, critical |
| epic_id | uuid | - | Filter by epic |
| assignee_id | uuid | - | Filter by assignee |
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
      "created_at": "...",
      "updated_at": "...",
      "epic": { "id": "uuid", "title": "User Authentication" },
      "assignee": { "id": "uuid", "username": "bob" },
      "created_by": { "id": "uuid", "username": "alice" },
      "attachment_count": 2,
      "comment_count": 5
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
  "epic_id": "uuid",
  "assignee_id": "uuid"
}
```

**Response (201):** Created task object.

---

#### GET /tasks/{id}
Get task with comments and attachments.

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "title": "Implement login form",
    "description": "...",
    "status": "in_progress",
    "priority": "high",
    "created_at": "...",
    "updated_at": "...",
    "epic": { "id": "uuid", "title": "User Authentication" },
    "assignee": { "id": "uuid", "username": "bob" },
    "created_by": { "id": "uuid", "username": "alice" },
    "comments": [
      {
        "id": "uuid",
        "content": "Started working on this",
        "created_at": "...",
        "author": { "id": "uuid", "username": "bob" }
      }
    ],
    "attachments": [
      {
        "id": "uuid",
        "filename": "mockup.png",
        "content_type": "image/png",
        "size_bytes": 45000,
        "uploaded_at": "..."
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
  "assignee_id": "uuid"
}
```

**Response (200):** Updated task object.

---

#### DELETE /tasks/{id}
Delete task and its comments/attachments. (Admin or creator)

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
| `member` | Create/edit own items, view all |
| `viewer` | Read-only access |
| `automation` | API-only, limited permissions |

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
