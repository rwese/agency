# Agency - Demo Projects Status

## Completed Demos

| Demo | Status | Notes |
|------|--------|-------|
| **Log Parser v3** | ✅ Complete | Auto-approval via TaskStore works |
| **URL Shortener** | ✅ Complete | Backend + Frontend agents worked |
| **Bookmarks Vault** | ⬜ Next | Web app demo |
| **Secret Scanner** | ⬜ Planned | CLI tool demo |

## Known Issues

1. **Manager heartbeat not detecting new pending_approval** - The auto-approval only works on first poll after task is marked. New pending_approval tasks may not be detected until next poll cycle.

2. **Manager shows "No tasks assigned"** - When there are pending_approval tasks but no unassigned tasks, the manager doesn't auto-approve.

## Fix Needed

The heartbeat should check for pending_approval tasks **every poll cycle**, not just when the count changes.

## Demo Results

### URL Shortener
- **Backend (FastAPI):** ✅ Created with SQLite
  - POST /links, GET /{code}, GET /{code}/stats, DELETE /{code}
  - Tested and working
- **Frontend (HTML/JS):** ✅ Created web UI
  - Form, copy button, stats display
  - Ready to use when backend is running

### Log Parser
- CLI tool with click
- Grep command with regex support
- Multiple output formats
