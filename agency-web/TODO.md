# agency-web Planning

## Tasks

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Create PRD with user stories | [x] | v1.2 complete |
| 2 | Define API endpoints outline | [x] | Full REST API spec |
| 3 | Define data model sketch | [x] | SQLite schema with FTS |
| 4 | Define UI wireframes (text) | [x] | 8 pages |
| 5 | Clarify requirements via questions | [x] | Complete |

## Requirements Summary

### Entities
- Team, User, Epic, Task, Comment, Attachment
- GitHubRef, Webhook, ActivityLog, GitHubAppConfig

### Features
- [x] Teams (group users, team-scoped epics/tasks)
- [x] Tags/labels on epics and tasks
- [x] External ID (GitHub issue references)
- [x] Full-text search
- [x] Dashboard widgets (my tasks, epic progress, activity)
- [x] Kanban board (by status columns)
- [x] GitHub App bidirectional sync
- [x] Slack notifications via webhooks
- [x] Webhook system for all CRUD events
- [x] Activity logging with configurable retention
- [x] Admin metrics dashboard
- [x] Health endpoint
- [x] Bulk task actions
- [x] Inline editing
- [x] Keyboard shortcuts (J/K/N)
- [x] Magic link email invites
- [x] Configurable blocked file types
- [x] Full database backup/export
- [x] Auto-migrations (configurable)
- [x] JSON structured logging

### Constraints
- [x] On-premise only
- [x] Self-contained (no external auth)
- [x] Single binary (Go)
- [x] Docker containerized (GHCR)
- [x] Mobile-first UI
- [x] Screen reader optimized (WCAG AA)
- [x] Custom branding via CSS variables
- [x] Full markdown support

### Tech Decisions (from clarifications)
- Session auth: Implementation-defined
- Real-time: Implementation-defined (polling or WebSocket)
- File blocking: Configurable blocklist
- GitHub: GitHub App, configured repo list
- User invites: Magic links
- Kanban: By status columns
- Dashboard: Simple counts, no charts

## Status

**Completed:** All planning documents ready for handoff
