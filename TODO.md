# Agency - Known Issues and Fixes

## Completed Fixes

| # | Issue | Fix | Status |
|---|-------|-----|--------|
| 1 | Developer bypassed `pending_approval` status | Added status transition validation | ✅ |
| 2 | Developer used wrong commands | Updated personality with correct workflow | ✅ |
| 3 | Task ID injection with spaces | Documented as tmux behavior | ✅ |
| 4 | Manager didn't auto-review | Updated manager personality + v2 heartbeat | ✅ |
| 5 | Manager heartbeat v1 not auto-assigning | Switched to v2 heartbeat with `assign_tasks_to_agents()` | ✅ |
| 6 | Auto-approval only on count change | Check every cycle for pending tasks | ✅ |

## Known Issues

1. **Heartbeat v2 may not be running** - Need to verify heartbeat process starts correctly
2. **Auto-assignment may not be working** - Tasks created but not assigned to agents

## Demo Projects Status

| Demo | Status |
|------|--------|
| **Log Parser** | ✅ Complete |
| **URL Shortener** | ✅ Complete (backend + frontend) |
| **Bookmarks Vault** | ⏳ In progress - testing auto-assignment |
| **Secret Scanner** | ⬜ Pending |

## Testing Needed

Verify that:
1. Heartbeat v2 starts and runs for each session
2. Tasks are auto-assigned by manager heartbeat
3. Tasks are auto-approved by manager heartbeat

## Commands to Test

```bash
# Check heartbeat is running
ps aux | grep heartbeat | grep <project>

# Check task assignment
agency tasks list
```
