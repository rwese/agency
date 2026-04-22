# agency-web Data Model

**Version:** 1.1  
**Date:** 2026-04-22  
**Status:** Draft  

---

## Entity Relationship Diagram

```
┌──────────┐       ┌──────────┐       ┌──────────┐
│   Team   │──┐    │   Epic   │       │  Task    │
├──────────┤  │    ├──────────┤       ├──────────┤
│ id (PK)  │  │    │ id (PK)  │───┐   │ id (PK)  │
│ name     │  │    │ title    │   │   │ title    │
│ desc     │  │    │ desc     │   │   │ desc     │
│ created  │  │    │ status   │   │   │ status   │
└──────────┘  │    │ tags     │   │   │ priority │
             │    │ team_id  │───┘   │ tags     │
             │    │ created_by   │   │ external_id   │
             │    └──────────┘       │ epic_id  │
             │                        │ assignee_id   │
             │                        │ created_by   │
             │                        │ created  │
             │                        │ updated  │
             │                        └──────────┘
             │                              │
┌──────────┐ │    ┌──────────────┐           │
│   User   │─┘    │   Comment    │           │
├──────────┤      ├──────────────┤           │
│ id (PK)  │      │ id (PK)      │           │
│ username │──────│ content      │           │
│ email    │      │ task_id (FK) │───────────┘
│ password │      │ author_id    │
│ role     │      │ created      │
│ api_key  │      │ updated      │
└──────────┘      └──────────────┘
                          
      ┌──────────────┐      ┌──────────────┐
      │ Attachment   │      │ GitHubRef    │
      ├──────────────┤      ├──────────────┤
      │ id (PK)      │      │ id (PK)      │
      │ filename     │      │ ref_type     │
      │ content_type │      │ ref_id       │
      │ size_bytes   │      │ url          │
      │ storage_path │      │ task_id (FK) │
      │ task_id (FK) │      │ created      │
      │ uploaded_by  │      └──────────────┘
      │ uploaded     │
      └──────────────┘

┌──────────────┐      ┌──────────────┐
│   Webhook    │      │ ActivityLog  │
├──────────────┤      ├──────────────┤
│ id (PK)      │      │ id (PK)      │
│ name         │      │ action       │
│ url          │      │ entity_type  │
│ events       │      │ entity_id    │
│ secret       │      │ actor_id     │
│ active       │      │ payload      │
│ created_by   │      │ created      │
│ created      │      └──────────────┘
└──────────────┘

User ◄──────────► Team  (many-to-many via user_teams)
```

---

## Tables

### teams

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| name | VARCHAR(100) | UNIQUE, NOT NULL | Team name |
| description | TEXT | NULL | Team description |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes:**
- `idx_teams_name` ON name

---

### users

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| username | VARCHAR(50) | UNIQUE, NOT NULL | Login username |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Email address |
| password_hash | VARCHAR(255) | NULL | Hashed password (NULL for API-only) |
| role | ENUM | NOT NULL, DEFAULT 'member' | admin, member, viewer, automation |
| api_key_hash | VARCHAR(255) | NULL | Hashed API key (for automation users) |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes:**
- `idx_users_username` ON username
- `idx_users_api_key_hash` ON api_key_hash

**Relationships:**
- Many-to-many with teams via `user_teams`

---

### user_teams (junction table)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| user_id | UUID | PK, FK → users.id | User reference |
| team_id | UUID | PK, FK → teams.id | Team reference |
| joined_at | TIMESTAMP | NOT NULL | When user joined team |

**Primary Key:** (user_id, team_id)

---

### epics

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| title | VARCHAR(255) | NOT NULL | Epic title |
| description | TEXT | NULL | Detailed description (markdown) |
| status | ENUM | NOT NULL, DEFAULT 'open' | open, in_progress, review, blocked, done |
| tags | TEXT | NULL | JSON array of tags |
| team_id | UUID | FK → teams.id, NOT NULL | Owning team |
| created_by | UUID | FK → users.id | Creator |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes:**
- `idx_epics_status` ON status
- `idx_epics_team_id` ON team_id
- `idx_epics_created_by` ON created_by

**Foreign Keys:**
- `fk_epics_team` ON team_id → teams(id)
- `fk_epics_creator` ON created_by → users(id)

---

### tasks

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| title | VARCHAR(255) | NOT NULL | Task title |
| description | TEXT | NULL | Detailed description (markdown) |
| status | ENUM | NOT NULL, DEFAULT 'open' | open, in_progress, review, blocked, done |
| priority | ENUM | NOT NULL, DEFAULT 'medium' | low, medium, high, critical |
| tags | TEXT | NULL | JSON array of tags |
| external_id | VARCHAR(255) | NULL | External reference (e.g., "github:owner/repo#123") |
| epic_id | UUID | FK → epics.id, NOT NULL | Parent epic |
| assignee_id | UUID | FK → users.id, NULL | Assigned user |
| created_by | UUID | FK → users.id | Creator |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes:**
- `idx_tasks_status` ON status
- `idx_tasks_priority` ON priority
- `idx_tasks_epic_id` ON epic_id
- `idx_tasks_assignee_id` ON assignee_id
- `idx_tasks_created_by` ON created_by
- `idx_tasks_external_id` ON external_id
- `idx_tasks_tags` ON tags (for JSON search)

**Foreign Keys:**
- `fk_tasks_epic` ON epic_id → epics(id) ON DELETE CASCADE
- `fk_tasks_assignee` ON assignee_id → users(id) ON DELETE SET NULL
- `fk_tasks_creator` ON created_by → users(id)

---

### github_refs

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| ref_type | ENUM | NOT NULL | commit, pull_request, issue |
| ref_id | VARCHAR(255) | NOT NULL | Reference ID (commit hash, PR number, etc.) |
| url | VARCHAR(512) | NOT NULL | Full GitHub URL |
| task_id | UUID | FK → tasks.id, NOT NULL | Parent task |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |

**Indexes:**
- `idx_github_refs_task_id` ON task_id
- `idx_github_refs_ref_id` ON ref_id
- UNIQUE(task_id, ref_type, ref_id)

**Foreign Keys:**
- `fk_github_refs_task` ON task_id → tasks(id) ON DELETE CASCADE

---

### comments

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| content | TEXT | NOT NULL | Comment text (markdown) |
| task_id | UUID | FK → tasks.id, NOT NULL | Parent task |
| author_id | UUID | FK → users.id | Comment author |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes:**
- `idx_comments_task_id` ON task_id
- `idx_comments_author_id` ON author_id

**Foreign Keys:**
- `fk_comments_task` ON task_id → tasks(id) ON DELETE CASCADE
- `fk_comments_author` ON author_id → users(id) ON DELETE SET NULL

---

### attachments

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| filename | VARCHAR(255) | NOT NULL | Original filename |
| content_type | VARCHAR(100) | NOT NULL | MIME type |
| size_bytes | INTEGER | NOT NULL | File size |
| storage_path | VARCHAR(512) | NOT NULL, UNIQUE | Internal file path |
| checksum | VARCHAR(64) | NULL | SHA256 checksum |
| task_id | UUID | FK → tasks.id, NOT NULL | Parent task |
| uploaded_by | UUID | FK → users.id | Uploader |
| uploaded_at | TIMESTAMP | NOT NULL | Upload timestamp |

**Indexes:**
- `idx_attachments_task_id` ON task_id
- `idx_attachments_storage_path` ON storage_path

**Foreign Keys:**
- `fk_attachments_task` ON task_id → tasks(id) ON DELETE CASCADE
- `fk_attachments_uploader` ON uploaded_by → users(id) ON DELETE SET NULL

---

### webhooks

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| name | VARCHAR(100) | NOT NULL | Webhook name |
| url | VARCHAR(512) | NOT NULL | Target URL |
| events | TEXT | NOT NULL | JSON array of event types |
| secret | VARCHAR(255) | NOT NULL | HMAC signing secret |
| active | BOOLEAN | NOT NULL, DEFAULT TRUE | Is active |
| created_by | UUID | FK → users.id | Creator |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes:**
- `idx_webhooks_active` ON active

**Foreign Keys:**
- `fk_webhooks_creator` ON created_by → users(id)

---

### activity_logs

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| action | VARCHAR(50) | NOT NULL | Action identifier (e.g., "task.created") |
| entity_type | VARCHAR(20) | NOT NULL | Entity type (epic, task, comment, attachment) |
| entity_id | UUID | NOT NULL | Entity ID |
| actor_id | UUID | FK → users.id, NULL | User who performed action (NULL for API) |
| payload | TEXT | NULL | JSON with before/after values |
| created_at | TIMESTAMP | NOT NULL | When action occurred |

**Indexes:**
- `idx_activity_entity` ON (entity_type, entity_id)
- `idx_activity_actor` ON actor_id
- `idx_activity_action` ON action
- `idx_activity_created` ON created_at

**Foreign Keys:**
- `fk_activity_actor` ON actor_id → users(id) ON DELETE SET NULL

---

## Enum Definitions

### user_role
```sql
CREATE TYPE user_role AS ENUM ('admin', 'member', 'viewer', 'automation');
```

### entity_status
```sql
CREATE TYPE entity_status AS ENUM ('open', 'in_progress', 'review', 'blocked', 'done');
```

### task_priority
```sql
CREATE TYPE task_priority AS ENUM ('low', 'medium', 'high', 'critical');
```

### github_ref_type
```sql
CREATE TYPE github_ref_type AS ENUM ('commit', 'pull_request', 'issue');
```

---

## Suggested Schema (SQLite)

```sql
-- Teams
CREATE TABLE teams (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_teams_name ON teams(name);

-- Users
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    role TEXT NOT NULL DEFAULT 'member',
    api_key_hash TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_api_key_hash ON users(api_key_hash);

-- User-Team membership
CREATE TABLE user_teams (
    user_id TEXT NOT NULL REFERENCES users(id),
    team_id TEXT NOT NULL REFERENCES teams(id),
    joined_at TEXT NOT NULL,
    PRIMARY KEY (user_id, team_id)
);

-- Epics
CREATE TABLE epics (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    tags TEXT,
    team_id TEXT NOT NULL REFERENCES teams(id),
    created_by TEXT NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_epics_status ON epics(status);
CREATE INDEX idx_epics_team_id ON epics(team_id);
CREATE INDEX idx_epics_created_by ON epics(created_by);

-- Tasks
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    priority TEXT NOT NULL DEFAULT 'medium',
    tags TEXT,
    external_id TEXT,
    epic_id TEXT NOT NULL REFERENCES epics(id) ON DELETE CASCADE,
    assignee_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    created_by TEXT NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_epic_id ON tasks(epic_id);
CREATE INDEX idx_tasks_assignee_id ON tasks(assignee_id);
CREATE INDEX idx_tasks_created_by ON tasks(created_by);
CREATE INDEX idx_tasks_external_id ON tasks(external_id);

-- GitHub References
CREATE TABLE github_refs (
    id TEXT PRIMARY KEY,
    ref_type TEXT NOT NULL,
    ref_id TEXT NOT NULL,
    url TEXT NOT NULL,
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    UNIQUE(task_id, ref_type, ref_id)
);

CREATE INDEX idx_github_refs_task_id ON github_refs(task_id);
CREATE INDEX idx_github_refs_ref_id ON github_refs(ref_id);

-- Comments
CREATE TABLE comments (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    author_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_comments_task_id ON comments(task_id);
CREATE INDEX idx_comments_author_id ON comments(author_id);

-- Attachments
CREATE TABLE attachments (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    storage_path TEXT UNIQUE NOT NULL,
    checksum TEXT,
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    uploaded_by TEXT REFERENCES users(id) ON DELETE SET NULL,
    uploaded_at TEXT NOT NULL
);

CREATE INDEX idx_attachments_task_id ON attachments(task_id);
CREATE INDEX idx_attachments_storage_path ON attachments(storage_path);

-- Webhooks
CREATE TABLE webhooks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    events TEXT NOT NULL,
    secret TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_by TEXT NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_webhooks_active ON webhooks(active);

-- Activity Logs
CREATE TABLE activity_logs (
    id TEXT PRIMARY KEY,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    actor_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    payload TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX idx_activity_entity ON activity_logs(entity_type, entity_id);
CREATE INDEX idx_activity_actor ON activity_logs(actor_id);
CREATE INDEX idx_activity_action ON activity_logs(action);
CREATE INDEX idx_activity_created ON activity_logs(created_at);
```

---

## Full-Text Search

SQLite FTS5 virtual table for search:

```sql
-- Create FTS5 virtual table
CREATE VIRTUAL TABLE epics_fts USING fts5(
    title,
    description,
    content='epics',
    content_rowid='rowid'
);

CREATE VIRTUAL TABLE tasks_fts USING fts5(
    title,
    description,
    content='tasks',
    content_rowid='rowid'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER epics_ai AFTER INSERT ON epics BEGIN
    INSERT INTO epics_fts(rowid, title, description) VALUES (NEW.rowid, NEW.title, NEW.description);
END;

CREATE TRIGGER epics_ad AFTER DELETE ON epics BEGIN
    INSERT INTO epics_fts(epics_fts, rowid, title, description) VALUES('delete', OLD.rowid, OLD.title, OLD.description);
END;

CREATE TRIGGER epics_au AFTER UPDATE ON epics BEGIN
    INSERT INTO epics_fts(epics_fts, rowid, title, description) VALUES('delete', OLD.rowid, OLD.title, OLD.description);
    INSERT INTO epics_fts(rowid, title, description) VALUES (NEW.rowid, NEW.title, NEW.description);
END;
```

---

## Storage

### File Storage Structure
```
/storage/
└── attachments/
    └── {task_id}/
        └── {attachment_id}_{sanitized_filename}
```

### Example
```
/storage/attachments/
├── a1b2c3d4-...
│   └── e5f6g7h8_screenshot.png
└── i9j0k1l2-...
    └── m3n4o5p6_build.log.gz
```

---

## Notes

1. **UUIDs**: Use UUIDv4 for all primary keys
2. **Timestamps**: Store as ISO 8601 strings in SQLite (e.g., `2026-04-22T12:00:00Z`)
3. **Password Hashing**: Use bcrypt or argon2
4. **API Keys**: Store hashed; show plaintext once on creation
5. **Cascade Delete**: 
   - Deleting epic cascades to tasks, comments, attachments, github_refs
   - Deleting team does NOT cascade (epics need reassignment first)
6. **Tags Storage**: JSON array stored as TEXT, query with JSON functions
7. **Activity Logging**: Log all write operations asynchronously
8. **Soft Delete**: Consider adding `deleted_at` for soft delete (future enhancement)
