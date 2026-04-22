# agency-web PRD

**Version:** 1.2  
**Date:** 2026-04-22  
**Status:** Draft  

---

## 1. Problem Statement

The agency team needs visibility into ongoing work items without relying on external services. We need a lightweight ticketing system to track Epics and Tasks, allow stakeholders to view progress, enable automations to interact programmatically, and store related files and artifacts.

**Key Constraints:**
- On-premise deployment only (no cloud dependency)
- Self-contained stack (no external auth providers)
- Single binary for easy deployment (containerized)
- Mobile-first UI
- Screen reader optimized (WCAG 2.1 AA)

---

## 2. User Personas

### P1: Internal Team Member
- Full access to features within their team
- Creates, updates, and closes epics and tasks
- Attaches files, adds comments
- Manages project state
- Views dashboard with assigned tasks and team progress

### P2: External Stakeholder
- Read-only or limited access
- Views team-specific epics and task status
- Views attached files
- May submit requests (future)

### P3: Automation System
- API-only access
- Creates tasks/epics programmatically
- Updates status based on CI/CD events
- Attaches build logs/artifacts
- Syncs with GitHub (issues, PRs, commits)

### P4: Admin
- Manages teams and user membership
- Configures webhooks
- Manages blocked file types
- Views usage metrics and logs
- Manages GitHub App integration
- Configures GitHub repo sync list

---

## 3. Entity Model

### Team
- **Purpose:** Group users and ownership for epics/tasks
- **Fields:**
  - `id` (UUID)
  - `name` (string, required)
  - `description` (text)
  - `created_at` (timestamp)
  - `members` (relation to User[])

### Epic
- **Purpose:** High-level initiative or goal
- **Fields:**
  - `id` (UUID)
  - `title` (string, required)
  - `description` (text, markdown)
  - `status` (enum: open, in_progress, review, blocked, done)
  - `tags` (string[], for categorization)
  - `team_id` (Team FK, required)
  - `created_by` (user FK)
  - `created_at` (timestamp)
  - `updated_at` (timestamp)
  - `tasks` (relation to Task[])

### Task
- **Purpose:** Individual work item within an Epic
- **Fields:**
  - `id` (UUID)
  - `title` (string, required)
  - `description` (text, markdown)
  - `status` (enum: open, in_progress, review, blocked, done)
  - `priority` (enum: low, medium, high, critical)
  - `tags` (string[])
  - `external_id` (string, e.g., "github:org/repo#123")
  - `epic_id` (Epic FK, required)
  - `assignee_id` (user FK, optional)
  - `created_by` (user FK)
  - `created_at` (timestamp)
  - `updated_at` (timestamp)
  - `comments` (relation to Comment[])
  - `attachments` (relation to Attachment[])
  - `github_refs` (relation to GitHubRef[])

### GitHubRef
- **Purpose:** Link to GitHub commits, PRs, issues
- **Fields:**
  - `id` (UUID)
  - `ref_type` (enum: commit, pull_request, issue)
  - `ref_id` (string, e.g., "abc123" or "PR #456")
  - `url` (string, full GitHub URL)
  - `task_id` (Task FK)
  - `created_at` (timestamp)

### Attachment
- **Purpose:** File associated with a Task
- **Fields:**
  - `id` (UUID)
  - `filename` (string)
  - `content_type` (string, MIME type)
  - `size_bytes` (integer)
  - `storage_path` (string, internal path)
  - `checksum` (string, SHA256)
  - `task_id` (Task FK)
  - `uploaded_by` (user FK)
  - `uploaded_at` (timestamp)

### Comment
- **Purpose:** Discussion on a Task
- **Fields:**
  - `id` (UUID)
  - `content` (text, markdown)
  - `task_id` (Task FK)
  - `author` (user FK)
  - `created_at` (timestamp)
  - `updated_at` (timestamp)

### User
- **Purpose:** System user
- **Fields:**
  - `id` (UUID)
  - `username` (string, unique)
  - `email` (string)
  - `password_hash` (string)
  - `role` (enum: admin, member, viewer, automation)
  - `api_key_hash` (string, optional)
  - `teams` (relation to Team[])
  - `created_at` (timestamp)
  - `updated_at` (timestamp)

### Webhook
- **Purpose:** HTTP callbacks for external integrations
- **Fields:**
  - `id` (UUID)
  - `name` (string)
  - `url` (string)
  - `events` (string[], events to trigger)
  - `secret` (string, for signature verification)
  - `active` (boolean)
  - `created_by` (user FK)
  - `created_at` (timestamp)

### ActivityLog
- **Purpose:** Audit trail of all actions
- **Fields:**
  - `id` (UUID)
  - `action` (string, e.g., "task.created", "epic.status_changed")
  - `entity_type` (string, e.g., "task", "epic")
  - `entity_id` (UUID)
  - `actor_id` (user FK, optional for API)
  - `payload` (JSON, before/after values)
  - `created_at` (timestamp)

### GitHubAppConfig
- **Purpose:** GitHub App configuration
- **Fields:**
  - `id` (UUID)
  - `app_id` (string)
  - `app_name` (string)
  - `installation_id` (string)
  - `repositories` (string[], configured repo list)
  - `webhook_secret` (string)
  - `private_key` (text, encrypted)
  - `created_at` (timestamp)

---

## 4. User Stories

### Authentication & Authorization

| ID | Story | Priority |
|----|-------|----------|
| AUTH-01 | As a team member, I want to log in with credentials so I can access my account | must |
| AUTH-02 | As an automation, I want to authenticate via API key so I can interact programmatically | must |
| AUTH-03 | As an admin, I want to manage user accounts so I can control access | must |
| AUTH-04 | As a viewer, I want read-only access so I can monitor progress without making changes | should |
| AUTH-05 | As a system, I want all auth to be self-contained so we don't depend on external providers | must |
| AUTH-06 | As an admin, I want to invite users via magic link so they can self-register | must |
| AUTH-07 | As a system, I want the first admin to be created via environment variables on first run | must |

### Team Management

| ID | Story | Priority |
|----|-------|----------|
| TEAM-01 | As an admin, I want to create teams so I can organize users | must |
| TEAM-02 | As an admin, I want to add/remove members from teams so access is controlled | must |
| TEAM-03 | As a team member, I want to see my team's epics and tasks so I know what's relevant | must |
| TEAM-04 | As a user, I want to be on multiple teams so I can collaborate across projects | must |

### Epic Management

| ID | Story | Priority |
|----|-------|----------|
| EPIC-01 | As a team member, I want to create an epic with title, description, and tags so I can define initiatives | must |
| EPIC-02 | As a team member, I want to update epic status so I can track progress | must |
| EPIC-03 | As a team member, I want to view all epics in a list so I can see the big picture | must |
| EPIC-04 | As a team member, I want to view epic details with its tasks so I can understand scope | must |
| EPIC-05 | As a viewer, I want to view epics so I can stay informed | should |
| EPIC-06 | As a team member, I want to filter epics by tag so I can find related work | should |

### Task Management

| ID | Story | Priority |
|----|-------|----------|
| TASK-01 | As a team member, I want to create a task within an epic so I can break down work | must |
| TASK-02 | As a team member, I want to update task status and priority so I can track work | must |
| TASK-03 | As a team member, I want to assign a task to a team member so responsibilities are clear | must |
| TASK-04 | As a team member, I want to view my assigned tasks so I know what to work on | must |
| TASK-05 | As a team member, I want to filter tasks by status, epic, assignee, or tag so I can find items | must |
| TASK-06 | As a team member, I want to search tasks by text so I can find items quickly | must |
| TASK-07 | As a team member, I want to link an external ID (GitHub issue) to a task so I can track cross-system references | must |
| TASK-08 | As an automation, I want to create tasks via API so CI/CD can log work | must |
| TASK-09 | As an automation, I want to update task status via API so build status reflects work | must |
| TASK-10 | As a team member, I want to add tags to tasks so I can categorize work | must |
| TASK-11 | As a team member, I want bulk actions so I can update multiple tasks at once | must |
| TASK-12 | As a team member, I want inline editing so I can quickly update without modals | must |

### Comments & Collaboration

| ID | Story | Priority |
|----|-------|----------|
| COMMENT-01 | As a team member, I want to add comments to a task so I can discuss work | must |
| COMMENT-02 | As a team member, I want to view comment history on a task so I can understand context | must |
| COMMENT-03 | As a viewer, I want to read comments so I can follow discussions | should |
| COMMENT-04 | As a team member, I want to edit/delete my own comments so I can correct mistakes | should |

### File Attachments

| ID | Story | Priority |
|----|-------|----------|
| FILE-01 | As a team member, I want to attach files to a task so I can share artifacts | must |
| FILE-02 | As a team member, I want to download attachments so I can access files | must |
| FILE-03 | As an automation, I want to attach build logs so failures are documented | must |
| FILE-04 | As a viewer, I want to view/download attachments so I can access shared files | should |
| FILE-05 | As an admin, I want to limit attachment size so storage is controlled | must |
| FILE-06 | As an admin, I want to configure blocked file types so security is maintained | must |

### Dashboard & Views

| ID | Story | Priority |
|----|-------|----------|
| DASH-01 | As a team member, I want a dashboard showing my assigned tasks so I see my workload | must |
| DASH-02 | As a team member, I want a dashboard showing team epic progress so I track milestones | must |
| DASH-03 | As a team member, I want a dashboard showing recent activity so I stay informed | must |
| DASH-04 | As a team member, I want a Kanban board view by status so I can visualize workflow | should |
| DASH-05 | As a team member, I want full-text search so I can find any item quickly | must |
| DASH-06 | As a team member, I want keyboard shortcuts (J/K navigation, N for new) so I can work efficiently | must |

### GitHub Integration

| ID | Story | Priority |
|----|-------|----------|
| GH-01 | As an admin, I want to configure GitHub App integration so the system can sync with GitHub | must |
| GH-02 | As an admin, I want to specify which repos to sync so I control scope | must |
| GH-03 | As a system, I want to auto-create tasks from GitHub issues so work is synchronized | must |
| GH-04 | As a system, I want to update task status when GitHub issue is closed so status reflects reality | must |
| GH-05 | As a system, I want to link PRs to tasks when PRs reference tasks so code is connected to work | must |
| GH-06 | As a system, I want to move tasks to review/done when PR is merged so progress is tracked | must |
| GH-07 | As a system, I want to post comments on GitHub issues when task changes so stakeholders are notified | must |

### Notifications & Webhooks

| ID | Story | Priority |
|----|-------|----------|
| WH-01 | As an admin, I want to configure webhooks so external systems receive updates | must |
| WH-02 | As an external system, I want to receive webhook events for all CRUD operations so I can react to changes | must |
| WH-03 | As an external system, I want webhook payloads signed so I can verify authenticity | must |
| WH-04 | As an admin, I want to configure one global Slack channel for notifications so the team is informed | should |
| WH-05 | As a system, I want to trigger Slack notifications for task created, status changes, assignments, and comments | should |

### Admin & Observability

| ID | Story | Priority |
|----|-------|----------|
| ADMIN-01 | As an admin, I want to view usage metrics so I understand system activity | must |
| ADMIN-02 | As an admin, I want activity logs so I can audit changes | must |
| ADMIN-03 | As an admin, I want a health endpoint so load balancers can check status | must |
| ADMIN-04 | As an admin, I want to manage webhooks so integrations work | must |
| ADMIN-05 | As an admin, I want to view user counts (active/inactive) so I understand usage | must |
| ADMIN-06 | As an admin, I want to view task stats by status and priority so I understand workload | must |
| ADMIN-07 | As an admin, I want to view storage usage so I monitor capacity | must |
| ADMIN-08 | As an admin, I want to view API usage and rate limit metrics so I monitor system health | must |
| ADMIN-09 | As an admin, I want configurable activity log retention so I manage storage | must |
| ADMIN-10 | As an admin, I want to export full database backup so I can restore if needed | must |

---

## 5. API Contract (Draft)

### Authentication
```
POST   /api/auth/login          # User login
POST   /api/auth/logout         # User logout
GET    /api/auth/me             # Current user info
POST   /api/auth/apikey         # Generate API key (admin)
POST   /api/auth/invite         # Send magic link invite (admin)
POST   /api/auth/register       # Register via magic link
```

### Teams
```
GET    /api/teams               # List teams
POST   /api/teams               # Create team (admin)
GET    /api/teams/{id}          # Get team
PUT    /api/teams/{id}         # Update team (admin)
DELETE /api/teams/{id}         # Delete team (admin)
POST   /api/teams/{id}/members  # Add member
DELETE /api/teams/{id}/members/{user_id}  # Remove member
```

### Users
```
GET    /api/users               # List users (admin)
POST   /api/users               # Create user (admin)
GET    /api/users/{id}         # Get user
PUT    /api/users/{id}         # Update user (admin)
DELETE /api/users/{id}         # Delete user (admin)
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

### GitHub
```
GET    /api/tasks/{id}/github-refs    # List GitHub refs
POST   /api/tasks/{id}/github-refs   # Add GitHub ref
DELETE /api/github-refs/{id}         # Remove GitHub ref
POST   /api/github/sync               # Sync webhook receiver
GET    /api/github/config             # Get GitHub App config (admin)
PUT    /api/github/config             # Update GitHub App config (admin)
POST   /api/github/repos              # Add repo to sync list (admin)
DELETE /api/github/repos/{name}      # Remove repo from sync (admin)
```

### Comments
```
GET    /api/tasks/{id}/comments # List comments for task
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

### Webhooks
```
GET    /api/webhooks              # List webhooks
POST   /api/webhooks              # Create webhook
GET    /api/webhooks/{id}         # Get webhook
PUT    /api/webhooks/{id}         # Update webhook
DELETE /api/webhooks/{id}         # Delete webhook
POST   /api/webhooks/{id}/test    # Send test event
```

### Admin
```
GET    /api/admin/metrics         # Usage metrics
GET    /api/admin/activity        # Activity logs
GET    /api/admin/activity/export  # Export activity logs
PUT    /api/admin/activity/retention  # Set retention period
GET    /api/admin/storage         # Storage usage stats
GET    /api/admin/settings        # System settings
PUT    /api/admin/settings        # Update settings
GET    /api/admin/blocked-types   # Get blocked file types
PUT    /api/admin/blocked-types   # Update blocked file types
POST   /api/admin/backup          # Trigger full backup
GET    /api/health                # Health check
```

---

## 6. Webhook Events

| Event | Trigger | Payload |
|-------|---------|---------|
| `epic.created` | New epic created | Epic object |
| `epic.updated` | Epic fields changed | Epic object, changes |
| `epic.deleted` | Epic deleted | Epic ID |
| `epic.status_changed` | Epic status changed | Epic ID, old/new status |
| `task.created` | New task created | Task object |
| `task.updated` | Task fields changed | Task object, changes |
| `task.deleted` | Task deleted | Task ID |
| `task.status_changed` | Task status changed | Task ID, old/new status |
| `task.assigned` | Task assigned | Task ID, assignee |
| `comment.created` | New comment | Comment object |
| `comment.deleted` | Comment deleted | Comment ID |
| `attachment.uploaded` | File uploaded | Attachment object |
| `attachment.deleted` | File deleted | Attachment ID |

### Webhook Payload Format
```json
{
  "event": "task.created",
  "timestamp": "2026-04-22T12:00:00Z",
  "data": { ... },
  "signature": "sha256=..."
}
```

### Slack Notification Format (via webhook)
```
[#channel] Task "Implement login" was created by alice
Epic: User Authentication | Status: Open | Priority: High
→ View in agency-web
```

---

## 7. GitHub Integration

### GitHub App Setup
1. Admin installs GitHub App on organization
2. Admin configures app credentials in agency-web
3. Admin specifies which repositories to sync
4. Agency-web receives webhook events from GitHub

### Sync Behavior

**Inbound (GitHub → agency-web):**
| GitHub Event | agency-web Action |
|--------------|------------------|
| Issue opened | Create task with `external_id` |
| Issue closed | Set linked task to `done` |
| PR opened | Link PR to task (via `T-{id}` in title/body) |
| PR merged | Move linked task to `review` or `done` |
| Commit referenced | Create `GitHubRef` for commit |

**Outbound (agency-web → GitHub):**
| agency-web Action | GitHub Action |
|-------------------|---------------|
| Task created | Post comment on linked issue |
| Task status changed | Post comment on linked issue |
| Task assigned | Post comment on linked issue |
| Comment added | Post comment on linked issue |

### Reference Format
```
# In commit message or PR description:
Closes owner/repo#123
Fixes T-456
Related to T-789
```

### Configuration
```yaml
github:
  app_id: "123456"
  installation_id: "987654"
  repositories:
    - "org/repo1"
    - "org/repo2"
  webhook_secret: "..."
```

---

## 8. File Storage

### Requirements
- Store files on local filesystem (no S3/cloud dependency)
- Support all common file types
- Maximum file size: 50MB (configurable)
- Configurable blocked file types (e.g., executables)

### Storage Structure
```
/storage/
  └── attachments/
      └── {task_id}/
          └── {attachment_id}_{sanitized_filename}
```

### Metadata
- All file metadata stored in database
- Original filename preserved (sanitized)
- MIME type detected/stored
- SHA256 checksum for integrity

### Blocked Types (Default)
```
.exe, .dmg, .sh, .bat, .cmd, .ps1, .vbs, .scr
```

---

## 9. Branding & Theme

### CSS Variables
Full theme customization via CSS variables:

```css
:root {
  /* Brand colors */
  --color-primary: #3b82f6;
  --color-primary-hover: #2563eb;
  --color-secondary: #64748b;
  
  /* Background */
  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --bg-tertiary: #f1f5f9;
  
  /* Text */
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-muted: #94a3b8;
  
  /* Status colors */
  --status-open: #64748b;
  --status-progress: #3b82f6;
  --status-review: #f59e0b;
  --status-blocked: #ef4444;
  --status-done: #22c55e;
  
  /* Logo */
  --logo-url: url('/static/logo.png');
  --logo-height: 40px;
}
```

### Logo Requirements
- Default: SVG logo placeholder
- Configurable via CSS variable
- Support for custom favicon

---

## 10. UI/UX

### Responsive Breakpoints
| Breakpoint | Layout |
|------------|--------|
| < 640px | Mobile: Bottom nav, full-width content |
| 640-1024px | Tablet: Collapsible sidebar |
| > 1024px | Desktop: Sidebar + Content |

### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| `n` | New task/epic (context-aware) |
| `j` | Next item |
| `k` | Previous item |
| `Enter` | Open selected item |
| `e` | Edit selected item |
| `Escape` | Cancel/close |
| `/` | Focus search |
| `?` | Show keyboard shortcuts |

### Markdown Support
Full markdown in descriptions and comments:
- Bold, italic, strikethrough
- Headers (h1-h4)
- Lists (ordered, unordered, task lists)
- Code blocks with syntax highlighting
- Links and images
- Tables
- Blockquotes

---

## 11. Non-Functional Requirements

### Scale
- ≤10 concurrent users
- ≤1000 total issues (epics + tasks)
- ≤10,000 attachments (estimated)
- Single instance per deployment

### Performance
- Page load < 2s for typical views
- API response < 500ms for CRUD operations
- File upload < 30s for 50MB
- Full-text search < 1s
- Real-time updates via polling or WebSocket

### Security
- Password hashing: bcrypt/argon2
- Session/auth: Implementation-defined (JWT or sessions)
- API key auth: Bearer token
- Rate limits: 100 req/min for API keys
- Webhook signatures: HMAC-SHA256
- Input validation and sanitization
- No external auth dependencies

### Accessibility
- WCAG 2.1 AA compliance
- Screen reader optimized
- Keyboard navigation
- Mobile-first responsive design
- High contrast mode support

### Logging
- JSON structured logging
- Request/response logging
- Error logging with stack traces
- Configurable log levels

### Deployment

**Environment Variables:**
| Variable | Description | Required |
|----------|-------------|----------|
| `AGENCY_DB_PATH` | SQLite database path | Yes |
| `AGENCY_PORT` | Server port | No (default: 8080) |
| `AGENCY_SECRET_KEY` | JWT signing key / encryption | Yes |
| `AGENCY_SMTP_HOST` | SMTP server for email | No |
| `AGENCY_SMTP_PORT` | SMTP port | No |
| `AGENCY_SMTP_USER` | SMTP username | No |
| `AGENCY_SMTP_PASSWORD` | SMTP password | No |
| `AGENCY_ADMIN_EMAIL` | First admin email | On first run |
| `AGENCY_ADMIN_PASSWORD` | First admin password | On first run (auto-generate if not set) |
| `AGENCY_AUTO_UPGRADE` | Auto-migrate database | No (default: false) |

**First Run Behavior:**
1. Check if admin exists
2. If not, use `AGENCY_ADMIN_EMAIL` + `AGENCY_ADMIN_PASSWORD`
3. If password not set, auto-generate and log to container stdout
4. If `AGENCY_AUTO_UPGRADE=false` and migrations needed, throw error

### Database
- SQLite with auto-migrations
- Migration required: fail fast unless `AGENCY_AUTO_UPGRADE=true`

### Docker
- Image published to GHCR (GitHub Container Registry)
- Single container deployment
- Health check endpoint for orchestration

### Data
- Configurable activity log retention
- Admin can export full database backup
- Indefinite data retention by default

---

## 12. Out of Scope (v1)

- Sub-tasks within tasks
- Time tracking
- Custom fields (beyond tags)
- Multiple isolated workspaces
- Native mobile app
- SSO/OAuth integration
- Built-in email notifications (relay via webhooks)

---

## 13. Future Considerations

- SSO/OAuth integration
- Multi-instance support
- Mobile native app
- Time tracking
- Custom fields
- Dark mode
- Drag-drop task ordering within epic
- Keyboard shortcut customization
