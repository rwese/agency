# agency-web PRD

**Version:** 1.0  
**Date:** 2026-04-22  
**Status:** Draft  

---

## 1. Problem Statement

The agency team needs visibility into ongoing work items without relying on external services. We need a lightweight ticketing system to track Epics and Tasks, allow stakeholders to view progress, enable automations to interact programmatically, and store related files and artifacts.

---

## 2. User Personas

### P1: Internal Team Member
- Full access to all features
- Creates, updates, and closes epics and tasks
- Attaches files, adds comments
- Manages project state

### P2: External Stakeholder
- Read-only or limited access
- Views epics and task status
- Views attached files
- May submit requests (future)

### P3: Automation System
- API-only access
- Creates tasks/epics programmatically
- Updates status based on CI/CD events
- Attaches build logs/artifacts

---

## 3. Entity Model

### Epic
- **Purpose:** High-level initiative or goal
- **Fields:**
  - `id` (UUID)
  - `title` (string, required)
  - `description` (text, optional)
  - `status` (enum: open, in_progress, review, blocked, done)
  - `created_at` (timestamp)
  - `updated_at` (timestamp)
  - `created_by` (user FK)
  - `tasks` (relation to Task[])

### Task
- **Purpose:** Individual work item within an Epic
- **Fields:**
  - `id` (UUID)
  - `title` (string, required)
  - `description` (text, optional)
  - `status` (enum: open, in_progress, review, blocked, done)
  - `priority` (enum: low, medium, high, critical)
  - `assignee` (user FK, optional)
  - `epic_id` (Epic FK, required)
  - `created_at` (timestamp)
  - `updated_at` (timestamp)
  - `created_by` (user FK)
  - `comments` (relation to Comment[])
  - `attachments` (relation to Attachment[])

### Attachment
- **Purpose:** File associated with a Task
- **Fields:**
  - `id` (UUID)
  - `filename` (string)
  - `content_type` (string, MIME type)
  - `size_bytes` (integer)
  - `storage_path` (string, internal path)
  - `task_id` (Task FK)
  - `uploaded_at` (timestamp)
  - `uploaded_by` (user FK)

### Comment
- **Purpose:** Discussion on a Task
- **Fields:**
  - `id` (UUID)
  - `content` (text)
  - `task_id` (Task FK)
  - `author` (user FK)
  - `created_at` (timestamp)

### User
- **Purpose:** System user
- **Fields:**
  - `id` (UUID)
  - `username` (string, unique)
  - `email` (string)
  - `role` (enum: admin, member, viewer, automation)
  - `created_at` (timestamp)
  - `api_key_hash` (string, optional, for automation users)

---

## 4. User Stories

### Authentication & Authorization

| ID | Story | Priority |
|----|-------|----------|
| AUTH-01 | As a team member, I want to log in with credentials so I can access my account | must |
| AUTH-02 | As an automation, I want to authenticate via API key so I can interact programmatically | must |
| AUTH-03 | As an admin, I want to manage user accounts so I can control access | must |
| AUTH-04 | As a viewer, I want read-only access so I can monitor progress without making changes | should |

### Epic Management

| ID | Story | Priority |
|----|-------|----------|
| EPIC-01 | As a team member, I want to create an epic with title and description so I can define initiatives | must |
| EPIC-02 | As a team member, I want to update epic status so I can track progress | must |
| EPIC-03 | As a team member, I want to view all epics in a list so I can see the big picture | must |
| EPIC-04 | As a team member, I want to view epic details with its tasks so I can understand scope | must |
| EPIC-05 | As a viewer, I want to view epics so I can stay informed | should |

### Task Management

| ID | Story | Priority |
|----|-------|----------|
| TASK-01 | As a team member, I want to create a task within an epic so I can break down work | must |
| TASK-02 | As a team member, I want to update task status and priority so I can track work | must |
| TASK-03 | As a team member, I want to assign a task to a team member so responsibilities are clear | must |
| TASK-04 | As a team member, I want to view my assigned tasks so I know what to work on | must |
| TASK-05 | As a team member, I want to filter tasks by status, epic, or assignee so I can find items | must |
| TASK-06 | As an automation, I want to create tasks via API so CI/CD can log work | must |
| TASK-07 | As an automation, I want to update task status via API so build status reflects work | must |

### Comments & Collaboration

| ID | Story | Priority |
|----|-------|----------|
| COMMENT-01 | As a team member, I want to add comments to a task so I can discuss work | must |
| COMMENT-02 | As a team member, I want to view comment history on a task so I can understand context | must |
| COMMENT-03 | As a viewer, I want to read comments so I can follow discussions | should |

### File Attachments

| ID | Story | Priority |
|----|-------|----------|
| FILE-01 | As a team member, I want to attach files to a task so I can share artifacts | must |
| FILE-02 | As a team member, I want to download attachments so I can access files | must |
| FILE-03 | As an automation, I want to attach build logs so failures are documented | must |
| FILE-04 | As a viewer, I want to view/download attachments so I can access shared files | should |
| FILE-05 | As an admin, I want to limit attachment size so storage is controlled | should |

### Dashboard & Views

| ID | Story | Priority |
|----|-------|----------|
| DASH-01 | As a team member, I want a dashboard showing my tasks so I see my workload | should |
| DASH-02 | As a team member, I want a Kanban board view so I can visualize workflow | could |
| DASH-03 | As a team member, I want to see epic progress so I can track milestones | should |

---

## 5. API Contract (Draft)

### Authentication
```
POST   /api/auth/login          # User login
POST   /api/auth/logout         # User logout
GET    /api/auth/me             # Current user info
```

### Users
```
GET    /api/users               # List users (admin)
POST   /api/users               # Create user (admin)
GET    /api/users/{id}          # Get user
PUT    /api/users/{id}          # Update user (admin)
DELETE /api/users/{id}          # Delete user (admin)
```

### Epics
```
GET    /api/epics               # List epics
POST   /api/epics               # Create epic
GET    /api/epics/{id}          # Get epic with tasks
PUT    /api/epics/{id}          # Update epic
DELETE /api/epics/{id}          # Delete epic
```

### Tasks
```
GET    /api/tasks               # List tasks (with filters)
POST   /api/tasks               # Create task
GET    /api/tasks/{id}          # Get task with comments/attachments
PUT    /api/tasks/{id}          # Update task
DELETE /api/tasks/{id}          # Delete task
```

### Comments
```
GET    /api/tasks/{id}/comments # List comments for task
POST   /api/tasks/{id}/comments # Add comment
DELETE /api/comments/{id}       # Delete comment
```

### Attachments
```
GET    /api/tasks/{id}/attachments     # List attachments
POST   /api/tasks/{id}/attachments     # Upload attachment
GET    /api/attachments/{id}           # Download attachment
DELETE /api/attachments/{id}           # Delete attachment
```

### Automation
```
POST   /api/auth/apikey         # Generate API key (admin)
```

---

## 6. File Storage

### Requirements
- Store files on local filesystem or cloud storage
- Support images (PNG, JPG, GIF, WebP)
- Support documents (PDF, MD, TXT)
- Support build artifacts (LOG, JSON, ZIP, TAR.GZ)
- Maximum file size: TBD (suggest 50MB default)

### Storage Structure
```
/storage/
  └── attachments/
      └── {task_id}/
          └── {attachment_id}_{filename}
```

### Metadata
- All file metadata stored in database
- Original filename preserved
- MIME type detected/stored
- SHA256 checksum for integrity (optional)

---

## 7. Non-Functional Requirements

### Scale
- ≤10 concurrent users
- ≤1000 total issues (epics + tasks)
- ≤10,000 attachments (estimated)

### Performance
- Page load < 2s for typical views
- API response < 500ms for CRUD operations
- File upload < 30s for 50MB

### Security
- Authentication required for write operations
- Role-based access control (RBAC)
- API key auth for automation
- Input validation and sanitization

### Data
- SQLite for lightweight deployment (recommended)
- Automatic backup strategy (TBD)
- No sensitive data in logs

---

## 8. Out of Scope (v1)

- Sub-tasks within tasks
- Time tracking
- Notifications/email
- Custom fields
- Integrations (GitHub, Slack)
- Multi-project support
- Mobile app

---

## 9. Future Considerations

- SSO/OAuth integration
- Webhook support for external notifications
- Search functionality
- Export/import data
- Activity audit log
- Markdown rendering in descriptions/comments

---

## 10. Open Questions

| # | Question | Status |
|---|----------|--------|
| 1 | Authentication method (credentials only, or OAuth)? | Open |
| 2 | Hosting environment (local, VPS, cloud)? | Open |
| 3 | Storage backend (local filesystem, S3-compatible)? | Open |
| 4 | Maximum attachment size? | Open |
| 5 | Need for email notifications? | Open |
