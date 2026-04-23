---
title: Agency v2.0 Specification
version: 2.0.0
schemas:
  base_url: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas
  files:
    - config.json
    - manager.json
    - agent.json
    - agents.json
    - task.json
    - tasks_store.json
    - result.json
    - pending_task.json
    - notification.json
    - notifications_store.json
    - slots_available.json
    - halted.json
---

# Agency v2.0 - Specification

> **Purpose**: This document is the **single source of truth** for Agency's data structures. Schemas are embedded below and also available as standalone JSON files in `src/agency/schemas/`.

---

## Table of Contents

1. [Entities](#1-entities)
2. [Task Lifecycle](#2-task-lifecycle)
3. [File Structure](#3-file-structure)
4. [Schemas](#4-schemas)
5. [Configuration](#5-configuration)
6. [Communication](#6-communication)

---

## 1. Entities

### 1.1 Entity Overview

| Entity | Cardinality | Description |
|--------|-----------|-------------|
| **Project** | 1 | tmux session + `.agency/` directory |
| **Manager** | 1 per project | Orchestrator at window index 0 |
| **Agent** | N per project | Workers at window index 1+ |
| **Task** | N | Units of work with lifecycle states |

### 1.2 Entity Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│  PROJECT                                                          │
│  ├── tmux session: agency-<project-name>                        │
│  ├── tmux socket: agency-<project-name>                        │
│  └── Directory: <project-root>/.agency/                        │
└─────────────────────────────┬───────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│    MANAGER      │  │     AGENT       │  │     AGENT       │
│  (window: 0)    │  │  (window: 1+)   │  │  (window: 2+)   │
│  [MGR] name     │  │  name           │  │  name           │
└────────┬────────┘  └────────┬────────┘  └─────────────────┘
         │                     │
         │ 1:N                 │ 1:1
         ▼                     ▼
┌─────────────────┐  ┌─────────────────┐
│     TASK        │  │     TASK        │
│   (queue)       │  │  (in_progress)  │
└─────────────────┘  └─────────────────┘
```

---

## 2. Task Lifecycle

### 2.1 Status States

| Status | Description | Who Sets It |
|--------|-------------|-------------|
| `pending` | Awaiting assignment | `TaskStore.add_task()`, `clear_agent_info()` |
| `in_progress` | Agent actively working | `TaskStore.pickup_task()` |
| `pending_approval` | Awaiting review | `TaskStore.complete_task()` |
| `completed` | Approved by reviewer | `TaskStore.approve_task()` |
| `failed` | Rejected; may retry | `TaskStore.reject_task()` |

### 2.2 State Diagram

```
                    ┌───────────────────────────────────────┐
                    │                                       │
                    ▼                                       │
┌──────────┐     ┌──────────────┐     ┌──────────────────┐│
│ pending  │────►│ in_progress  │────►│ pending_approval  │──┘
└──────────┘     └──────────────┘     └────────┬─────────┘
    ▲                                          │
    │         ┌──────────┐         ┌───────────┴───────┐
    │         │  failed  │◄────────│   completed       │
    └─────────┤          │         └───────────────────┘
              └──────────┘
```

### 2.3 Priority Levels

| Priority | Value | Description |
|----------|-------|-------------|
| `low` | 0 | Default priority |
| `normal` | 1 | Standard priority |
| `high` | 2 | Urgent priority |

---

## 3. File Structure

```
<project-root>/
├── .agency/
│   ├── config.yaml           # Project configuration
│   ├── manager.yaml          # Manager personality + settings
│   ├── agents.yaml           # Agent registry
│   ├── .halted               # Halt marker (optional)
│   ├── .resuming             # Resume context (optional)
│   ├── var/
│   │   ├── tasks.json       # Task registry (source of truth)
│   │   ├── notifications.json # Notification history
│   │   ├── audit.db         # SQLite audit log
│   │   └── tasks/
│   │       └── <task_id>/
│   │           ├── task.json    # Full task definition
│   │           └── result.json  # Completion result
│   ├── pending/
│   │   └── <task_id>.json    # Pending approval (full task + result)
│   │   └── <task_id>.rejected # Rejection reason (if rejected)
│   ├── signals/
│   │   └── slots-available.json # Task slot tracking
│   ├── run/
│   │   └── .heartbeat-{name}.pid # Heartbeat PID files
│   └── agents/
│       └── <name>.yaml       # Individual agent configs
```

---

## 4. Schemas

### 4.1 Configuration Schemas

#### config.json

Project configuration stored at `.agency/config.yaml`.

```json
--8<-- "src/agency/schemas/config.json"
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `project` | string | ✅ | - | Project name |
| `shell` | enum | No | bash | Shell for agents |
| `parallel_limit` | integer | No | 2 | Max parallel tasks |
| `audit_enabled` | boolean | No | true | Enable audit logging |

#### manager.json

Manager configuration stored at `.agency/manager.yaml`.

```json
--8<-- "src/agency/schemas/manager.json"
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | ✅ | coordinator | Window title |
| `personality` | string | ✅ | - | System prompt |
| `poll_interval` | integer | No | 30 | Heartbeat seconds |
| `auto_approve` | boolean | No | false | Auto-approve tasks |

#### agent.json

Individual agent configuration stored at `.agency/agents/<name>.yaml`.

```json
--8<-- "src/agency/schemas/agent.json"
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Agent identifier |
| `personality` | string | No | Agent prompt |

#### agents.json

Agent registry stored at `.agency/agents.yaml`.

```json
--8<-- "src/agency/schemas/agents.json"
```

---

### 4.2 Task Schemas

#### task.json

Represents a unit of work.

```json
--8<-- "src/agency/schemas/task.json"
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `task_id` | string | ✅ | Unique ID (word-word-hex) |
| `description` | string | ✅ | Human-readable description |
| `status` | enum | ✅ | Current state |
| `priority` | enum | ✅ | low/normal/high |
| `assigned_to` | string\|null | ✅ | Agent name |
| `created_at` | datetime | ✅ | ISO8601 timestamp |
| `started_at` | datetime\|null | No | When work began |
| `completed_at` | datetime\|null | No | When completed |
| `agent_info` | object\|null | No | PID + session for crash detection |
| `reviewer_assigned` | string\|null | No | Reviewer handling this |

#### tasks_store.json

Root task registry stored at `.agency/var/tasks.json`.

```json
--8<-- "src/agency/schemas/tasks_store.json"
```

#### result.json

Completion result stored at `.agency/var/tasks/<id>/result.json`.

```json
--8<-- "src/agency/schemas/result.json"
```

#### pending_task.json

Task awaiting approval stored at `.agency/var/pending/<id>.json`.

```json
--8<-- "src/agency/schemas/pending_task.json"
```

---

### 4.3 System Schemas

#### notification.json

A single notification event.

```json
--8<-- "src/agency/schemas/notification.json"
```

#### notifications_store.json

Notification history stored at `.agency/var/notifications.json`.

```json
--8<-- "src/agency/schemas/notifications_store.json"
```

#### slots_available.json

Task slot tracking stored at `.agency/signals/slots-available.json`.

```json
--8<-- "src/agency/schemas/slots_available.json"
```

#### halted.json

Halt state marker stored at `.agency/.halted`.

```json
--8<-- "src/agency/schemas/halted.json"
```

---

## 5. Configuration

### 5.1 Example config.yaml

```yaml
$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/config.json
project: my-api
shell: bash
parallel_limit: 3
audit_enabled: true
```

### 5.2 Example manager.yaml

```yaml
$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/manager.json
name: coordinator
personality: |
  You are the project coordinator.

  ## Task Management
  - agency tasks list  # See pending
  - agency tasks assign <id> <agent>  # Assign
  - agency tasks add -d "..."  # Create

poll_interval: 30
auto_approve: false
```

### 5.3 Example agents.yaml

```yaml
$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/agents.json
agents:
  - name: coder
    config: agents/coder.yaml
  - name: tester
    config: agents/tester.yaml
```

---

## 6. Communication

### 6.1 Communication Channels

| Channel | Protocol | Purpose |
|---------|----------|---------|
| **pi-inject socket** | Unix socket + JSON | Send messages to pi |
| **pi-status socket** | Unix socket + JSON | Query pi state |
| **tmux** | send-keys | Terminal control |
| **File system** | JSON/YAML | Persistent state |

### 6.2 Notification Delivery Chain

```
1. LOG to var/notifications.json
2. WRITE to var/system_hint.txt
3. TRY pi-inject socket (validate path first!)
4. FALLBACK tmux send-keys
```

### 6.3 Cross-Project Isolation

| Mechanism | Protection |
|-----------|------------|
| tmux socket `agency-<project>` | Session isolation |
| Socket path validation vs `AGENCY_DIR` | Prevent cross-project injection |
| Project-local `.agency/` | State isolation |

---

## Appendix A: Environment Variables

| Variable | Role | Description |
|----------|------|-------------|
| `AGENCY_DIR` | Both | Path to `.agency/` directory |
| `AGENCY_ROLE` | Both | `MANAGER` or `AGENT` |
| `AGENCY_AGENT` | Agent | Agent name |
| `AGENCY_MANAGER` | Manager | Manager name |
| `AGENCY_SOCKET` | Both | Tmux socket name |
| `AGENCY_POLL_INTERVAL` | Both | Heartbeat poll seconds |
| `AGENCY_PING_INTERVAL` | Agent | Idle ping seconds |
| `AGENCY_PARALLEL_LIMIT` | Manager | Max concurrent tasks |
| `PI_INJECTOR_SOCKET` | Both | pi-inject Unix socket |
| `PI_STATUS_SOCKET` | Both | pi-status Unix socket |

---

## Appendix B: Audit Events

| Event | When | Logged By |
|-------|------|----------|
| `task_create` | Task added | `TaskStore.add_task()` |
| `task_assign` | Task assigned | `TaskStore.assign_task()` |
| `task_pickup` | Agent starts | `TaskStore.pickup_task()` |
| `task_complete` | Agent completes | `TaskStore.complete_task()` |
| `task_approve` | Manager approves | `TaskStore.approve_task()` |
| `task_reject` | Manager rejects | `TaskStore.reject_task()` |
| `crash_detected` | Agent dies | `heartbeat.check_stale_tasks()` |
| `agent_start` | Agent created | `session.start_agent_window()` |

---

*Document Version: 2.0.0*
*Last Updated: 2024-04-23*
*Schema Version: 2*
