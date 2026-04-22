# Implementation TODO - Session-Centric to Task-Centric Refactor

## Overview

Refactor Agency to use tasks as the canonical source of truth, removing session state complexity.

### Goals
- Tasks track agent work (PID, session ID, status)
- Crash detection via process existence check
- Agent session persistence for review/restart flow
- Per-agent parallelism (parallel_limit per agent)

---

## Tasks

### Phase 1: Task Model Update

- [x] 1.1: Add `agent_info` field to Task dataclass
  - `session_id: str | None`
  - `pid: int | None`
  - `started_at: str | None`
- [x] 1.2: Update `_pickup_task()` or new method to store agent info when agent picks up work
- [x] 1.3: Add method `clear_agent_info(task_id)` to revert crashed tasks
- [x] 1.4: Update JSON serialization/deserialization
- [x] 1.5: Add `rejection_reason` and `review_notes` fields
- [x] 1.6: Add helper methods (get_agent_busy_count, get_in_progress_tasks, etc.)
- [x] 1.7: Add process_exists() and check_stale_tasks() functions

### Phase 2: pi-status Extension

- [x] 2.1: Extend pi-status to return session info
  - Add `currentTask` and `currentTaskId` to status/health response
  - Add `set_task` and `clear_task` commands
- [x] 2.2: Update pi-status schema/docs
- [x] 2.3: Build pi-status extension

### Phase 3: Heartbeat Refactor

- [x] 3.1: Update heartbeat to include PID in notifications
- [x] 3.2: Add crash detection loop
  - Check `process_exists(pid)` for in_progress tasks
  - Revert to pending if crashed
- [x] 3.3: Add `check_stale_tasks()` function

### Phase 4: Manager Orchestration

- [x] 4.1: Implement `should_start_agent(agent)` check
  - Check available slots (parallel_limit - busy_count)
  - Check unblocked tasks available
- [x] 4.2: Create orchestrator module (`orchestrator.py`)
  - `Orchestrator` class for agent lifecycle management
  - `assign_tasks_to_agents()` for task distribution
  - `start_agents_for_work()` for on-demand agent starting
- [x] 4.3: Implement `manager_heartbeat_v2()` with orchestration
  - Crash detection + task assignment + agent starting
- [x] 4.4: Update heartbeat status notifications

### Phase 5: Review Flow

- [ ] 5.1: Create reviewer agent config template
- [ ] 5.2: Implement `start_reviewer(task)` in manager
- [ ] 5.3: Reviewer receives fresh context + task info
- [ ] 5.4: Approve/reject commands for reviewer

### Phase 5: Review Flow

- [x] 5.1: Create reviewer.py module
- [x] 5.2: Implement `start_reviewer(task)` function
- [x] 5.3: Reviewer prompt with fresh context + task info
- [x] 5.4: `handle_rejection()` for rejection flow

### Phase 6: Restart on Rejection

- [x] 6.1: Add `restart_agent_for_fix()` function
- [x] 6.2: Store session_id in task when picked up
- [x] 6.3: Implement rejection → restart flow
- [x] 6.4: `inject_fix_to_running_agent()` for live agents
- [x] 6.5: `start_fresh_agent()` for crashed agents

### Phase 7: Stop Modes

- [x] 7.1: Graceful stop (finish current, wrap-up, exit) - already implemented
- [x] 7.2: Immediate stop (interrupt, wrap-up, exit) - already implemented
- [x] 7.3: Force stop (kill immediately) - already implemented

### Phase 8: Cleanup

- [ ] 8.1: Remove session "running" state tracking
- [ ] 8.2: Remove window state tracking
- [ ] 8.3: Remove `.halted` marker file logic
- [ ] 8.4: Update documentation
- [ ] 8.5: Update CHANGELOG

---

## Done

### Summary
- [x] Design discussion completed
- [x] Task model defined
- [x] pi-status extension interface defined
- [x] Review flow designed
- [x] Restart flow designed

---

## Notes

- **Session persistence**: pi session IDs stored in task
- **Crash detection**: PID check in heartbeat
- **Reviewer**: Separate agent with fresh context
- **Parallelism**: Per-agent limit in config
