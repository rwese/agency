## Manager Review Bypass — Fix Plan

### Problem Analysis

The task went `pending` → `completed` without:
1. Status change to `in_progress`
2. Status change to `pending_approval`
3. Manager review

### Root Causes Identified

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 1 | Developer bypassed `pending_approval` status | `tasks complete` called directly | No review step |
| 2 | Developer used wrong commands | Tried `agency tasks-agent` instead of `agency tasks` | Task status never updated |
| 3 | Task ID injection with spaces | pi-inject passed args with spaces | `b j e c t` instead of `bect` |
| 4 | Manager not polling for completions | Developer marked complete, no notification | Manager didn't see it |

### Fixes Needed

#### 1. Enforce `pending_approval` Status Transition

The task should go: `pending` → `in_progress` → `pending_approval` → `completed`

Current: Developer calls `complete` → goes directly to `completed`
Fix: Developer calls `complete` → goes to `pending_approval`, then manager approves → `completed`

#### 2. Better Command Guidance

Developer tried `agency tasks-agent complete` but the command is `agency tasks complete`
Also: Developer didn't mark task as `in_progress` first

Fix: Add clear workflow instructions in personality

#### 3. Task ID Quoting in pi-inject

The task ID had spaces when passed via pi-inject socket.
Need to ensure proper escaping of arguments.

### In Progress

- [ ] Fix 1: Enforce pending_approval before completed
- [ ] Fix 2: Update developer personality with correct commands
- [ ] Fix 3: Investigate pi-inject task ID quoting

### Done

- [ ] None yet

---

## Demo Retries

After fixing the issues, retry building demo projects:

- [ ] **Log Parser v2** - Retry after workflow fixes (log-parser was bypassed, needs review flow)
- [ ] **URL Shortener** - Next demo
- [ ] **Bookmarks Vault** - Next demo
- [ ] **Secret Scanner** - Final demo

---

## Session Review Information

After a session ends, review session logs in `.agency/var/`:

```bash
# Session artifacts location
ls .agency/var/
├── audit.db          # Audit log of all actions
├── notifications.json # All notifications sent
├── tasks.json        # Final task state
└── tasks/            # Per-task details
    └── <task-id>/
        ├── task.json     # Task data
        ├── result.json   # Completion result
        └── pending_approval.json  # Review data (if any)

# Review notification history
cat .agency/var/notifications.json | jq .

# Review audit trail
sqlite3 .agency/var/audit.db "SELECT * FROM events ORDER BY timestamp DESC LIMIT 50;"

# Review task state
cat .agency/var/tasks.json | jq '.tasks | to_entries[] | select(.value.status == \"completed\")'
```

---

## User Goal

Fix the manager review bypass issue where tasks skip the approval workflow.
