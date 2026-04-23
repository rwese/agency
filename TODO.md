## Lazy Agent Spawning - TODO

### Done

- [x] Plan created
- [x] M1.1: Add slot availability tracking with blocking wait
- [x] M1.2: Add `assigned_not_running` task query
- [x] M1.3: Wire `start_agents_for_work` to assigned-but-not-running
- [x] M1.4: Add test for slot-based spawning
- [x] M2.1: Hook reviewer spawning into manager heartbeat
- [x] M2.2: Add reviewer tracking to task state
- [x] M2.3: Handle reviewer approval/rejection
- [x] M3.1: Extend stale task detection to `pending_approval`
- [x] M3.2: Auto-restart reviewer on crash
- [x] M4.1: Update design docs
- [x] M4.2: Update AGENTS.md

### Deferred (low priority)

- M2.4: Add test for reviewer flow
- M3.3: Add test for crash recovery

---

## Template Integration (2026-04-23)

Integrated `agency-templates` repo into `agency` repo as `templates/` directory.

### Done

- [x] Create `templates/` directory
- [x] Copy templates (basic, api, fullstack)
- [x] Update `TemplateManager` to prefer local templates
- [x] Fix cache key to include subdir
- [x] Update `list_templates` command
- [x] Update documentation
- [x] Delete agency-templates repo
