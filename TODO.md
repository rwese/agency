# Agency - Known Issues and Fixes

## Completed Fixes

| # | Issue | Fix | Status |
|---|-------|-----|--------|
| 1 | Developer bypassed `pending_approval` status | Added status transition validation | ✅ |
| 2 | Developer used wrong commands | Updated personality with correct workflow | ✅ |
| 3 | Task ID injection with spaces | tmux behavior, core fix prevents bypass | ✅ |
| 4 | Manager didn't auto-review pending tasks | Updated manager personality to auto-review | ✅ |

## Demo Results

### Log Parser v2 - ✅ SUCCESS

- Task marked for approval (pending_approval)
- Manager detected pending task
- Manager offered to review
- Manager reviewed and approved

**Note:** Manual approval was needed because manager asked for confirmation. Fixed by updating manager personality.

### Log Parser v1 - ❌ FAILED

- Developer bypassed review workflow
- Task went directly to completed
- No manager review

## Demo Projects

Ready for testing:

- [ ] **URL Shortener** - API service
- [ ] **Bookmarks Vault** - Web app
- [ ] **Secret Scanner** - CLI tool

## Session Review

After sessions, check `.agency/var/` for:

```bash
cat .agency/var/notifications.json | jq .
sqlite3 .agency/var/audit.db "SELECT * FROM events ORDER BY ts DESC LIMIT 50;"
```
