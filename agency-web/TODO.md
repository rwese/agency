# agency-web Planning

## Tasks

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Create PRD with user stories | [x] | v1.1 with teams, GitHub, webhooks |
| 2 | Define API endpoints outline | [x] | Full REST API spec |
| 3 | Define data model sketch | [x] | SQLite schema with FTS |
| 4 | Define UI wireframes (text) | [x] | 8 pages |
| 5 | Clarify requirements via questions | [x] | Teams, GitHub sync, Slack, etc. |

## Requirements Summary (from clarifications)

### Additional Features
- [x] Teams (group users, team-scoped epics/tasks)
- [x] Tags/labels on epics and tasks
- [x] External ID (GitHub issue references)
- [x] Full-text search
- [x] Custom dashboard widgets
- [x] GitHub bidirectional sync (auto-create from issues, reference commits/PRs)
- [x] Slack notifications via webhooks (task created, status, assigned, comment)
- [x] Webhooks for all CRUD events
- [x] Activity logging (audit trail)
- [x] Usage metrics
- [x] Health endpoint

### Constraints
- [x] On-premise only (no cloud)
- [x] Self-contained (no external auth)
- [x] Single binary deployment
- [x] Mobile-first UI
- [x] Screen reader optimized (WCAG 2.1 AA)

### Design
- [x] Custom branding (logo, colors)
- [x] Light/dark mode support

## Status

**Completed:** All planning documents ready for handoff
