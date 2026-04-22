# agency-web Data Model

**Version:** 1.0  
**Date:** 2026-04-22  
**Status:** Draft  

---

## Entity Relationship Diagram

```
┌──────────┐       ┌──────────┐       ┌──────────┐
│   User   │       │   Epic   │       │  Task    │
├──────────┤       ├──────────┤       ├──────────┤
│ id (PK)  │───┐   │ id (PK)  │───┐   │ id (PK)  │
│ username │   │   │ title    │   │   │ title    │
│ email    │   │   │ desc     │   └───│ epic_id  │
│ role     │   │   │ status   │       │ status   │
│ api_key  │   │   │ created  │       │ priority │
└──────────┘   │   │ updated  │       │ assignee │
               │   │ created_by   │   │ created  │
               │   └──────────┘       │ updated  │
               │                       │ created_by   │
               │                       └──────────┘
               │                              │
               │   ┌──────────────┐           │
               │   │   Comment    │           │
               │   ├──────────────┤           │
               └───│ id (PK)      │           │
                   │ content       │           │
                   │ task_id (FK)  │───────────┘
                   │ author (FK)   │
                   │ created       │
                   └──────────────┘
                          
                   ┌──────────────┐
                   │ Attachment   │
                   ├──────────────┤
                   │ id (PK)      │
                   │ filename     │
                   │ content_type │
                   │ size_bytes   │
                   │ storage_path │
                   │ task_id (FK) │
                   │ uploaded_by  │
                   │ uploaded     │
                   └──────────────┘
```

---

## Tables

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
- `idx_users_api_key_hash` ON api_key_hash (for API auth lookup)

---

### epics

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| title | VARCHAR(255) | NOT NULL | Epic title |
| description | TEXT | NULL | Detailed description |
| status | ENUM | NOT NULL, DEFAULT 'open' | open, in_progress, review, blocked, done |
| created_by | UUID | FK → users.id | Creator |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes:**
- `idx_epics_status` ON status
- `idx_epics_created_by` ON created_by

---

### tasks

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| title | VARCHAR(255) | NOT NULL | Task title |
| description | TEXT | NULL | Detailed description |
| status | ENUM | NOT NULL, DEFAULT 'open' | open, in_progress, review, blocked, done |
| priority | ENUM | NOT NULL, DEFAULT 'medium' | low, medium, high, critical |
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

**Foreign Keys:**
- `fk_tasks_epic` ON epic_id → epics(id) ON DELETE CASCADE
- `fk_tasks_assignee` ON assignee_id → users(id) ON DELETE SET NULL
- `fk_tasks_creator` ON created_by → users(id)

---

### comments

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| content | TEXT | NOT NULL | Comment text |
| task_id | UUID | FK → tasks.id, NOT NULL | Parent task |
| author_id | UUID | FK → users.id | Comment author |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |

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

---

## Suggested Schema (SQLite)

```sql
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

-- Epics
CREATE TABLE epics (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    created_by TEXT NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_epics_status ON epics(status);
CREATE INDEX idx_epics_created_by ON epics(created_by);

-- Tasks
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    priority TEXT NOT NULL DEFAULT 'medium',
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

-- Comments
CREATE TABLE comments (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    author_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL
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
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    uploaded_by TEXT REFERENCES users(id) ON DELETE SET NULL,
    uploaded_at TEXT NOT NULL
);

CREATE INDEX idx_attachments_task_id ON attachments(task_id);
CREATE INDEX idx_attachments_storage_path ON attachments(storage_path);
```

---

## Storage

### File Storage Structure
```
/storage/
└── attachments/
    └── {task_id}/
        └── {attachment_id}_{original_filename}
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
5. **Cascade Delete**: Deleting epic cascades to tasks, comments, attachments
6. **Soft Delete**: Consider adding `deleted_at` for soft delete (future enhancement)
