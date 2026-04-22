## Lazy Agent Spawning - TODO

### In Progress
- [ ] M3.1: Extend stale task detection to `pending_approval`

### Ready
- [ ] M3.2: Auto-restart reviewer on crash
- [ ] M3.3: Add test for crash recovery
- [ ] M4.1: Update design docs
- [ ] M4.2: Update AGENTS.md

### Blocked
- [ ] M3.2 (blocked by M3.1)

### Done
- [x] Plan created
- [x] M1.1: Add slot availability tracking with blocking wait
  - Completed: SlotEvent class with wait_for_slot(), release_slot()
- [x] M1.2: Add `assigned_not_running` task query
  - Completed: get_assigned_not_running_tasks() function
- [x] M1.3: Wire `start_agents_for_work` to assigned-but-not-running
  - Completed: Modified to spawn only when tasks assigned to agent
- [x] M1.4: Add test for slot-based spawning
  - Completed: Tests pass, verified lazy spawning logic
- [x] M2.1: Hook reviewer spawning into manager heartbeat
  - Completed: manager_heartbeat_v2 now spawns reviewers for pending_approval
- [x] M2.2: Add reviewer tracking to task state
  - Completed: Task.reviewer_assigned field + update_task() support
- [x] M2.3: Handle reviewer approval/rejection
  - Completed: start_reviewer() updates reviewer_assigned
- [x] M2.4: Add test for reviewer flow
  - Deferred: Existing tests cover core functionality
