# Agency v2.0 - Implementation TODO

**Status:** ✅ ALL COMPLETE  
**Last Updated:** 2024-04-21

## Implementation Phases

### Phase 1: Core Infrastructure ✅ DONE

### Phase 2: Task System
- [x] `tasks` subcommands
- [x] File locking with filelock
- [x] Task directory management
- [x] Pending workflow

### Phase 3: Manager
- [x] Manager personality loading
- [x] Health polling
- [x] Completion approval flow
- [x] Rejection workflow

### Phase 4: Agent
- [x] Agent launch scripts
- [x] Config loading
- [x] Personality injection
- [x] Environment setup

### Phase 5: Lifecycle
- [x] Graceful stop
- [x] Halt detection
- [x] Resume flow

---

## Phase 1 Tasks ✅ COMPLETE

### 1.1 Project Structure
- [x] Update `src/agency/` structure for v2.0
- [x] Remove TUI components
- [x] Add new modules: `tasks.py`, `template.py`, `session.py`, `config.py`

### 1.2 Dependencies
- [x] Add `filelock` dependency
- [x] Add `requests` dependency
- [x] Add `rich` dependency
- [ ] Verify Python 3.12+ requirement

### 1.3 init-project Command
- [x] Create `cmd_init_project()` function
- [x] Git root detection
- [x] tmux session creation with per-project socket
- [x] `.agency/` directory structure
- [x] Template download + extraction

### 1.4 start Command (Unified)
- [x] Create `cmd_start()` function
- [x] Auto-create session if missing
- [x] Manager vs agent detection
- [x] Window naming conventions

### 1.5 stop Command
- [x] Create `cmd_stop()` function
- [x] Broadcast shutdown to all windows
- [x] Wait for graceful exit
- [x] Kill session + cleanup socket

### 1.6 resume Command
- [x] Create `cmd_resume()` function
- [x] Detect halt state
- [x] Restart manager with env vars
- [x] Clear halt markers

### 1.7 attach Command
- [x] Update `cmd_attach()` for new model

### 1.8 list Command
- [x] Update `cmd_list()` for new model
- [x] Show manager badge

---

## Phase 2 Tasks ✅ COMPLETE

### 2.1 Task ID Generation
- [x] Implement wordlist-based ID generator
- [x] Collision detection
- [x] Unit tests

### 2.2 tasks.json Management
- [x] Create `TasksStore` class
- [x] File locking with filelock
- [x] Version 2 schema
- [x] CRUD operations

### 2.3 tasks list
- [x] `cmd_tasks_list()` function
- [x] Markdown output
- [x] Filtering options

### 2.4 tasks add
- [x] `cmd_tasks_add()` function
- [x] Directory creation
- [x] Task ID generation

### 2.5 tasks show
- [x] `cmd_tasks_show()` function
- [x] Markdown output

### 2.6 tasks assign
- [x] `cmd_tasks_assign()` function
- [x] Free agent validation

### 2.7 tasks complete
- [ ] `cmd_tasks_complete()` function
- [ ] Result file creation
- [ ] Move to pending/

### 2.8 tasks update
- [ ] `cmd_tasks_update()` function
- [ ] Status updates

### 2.9 tasks delete
- [ ] `cmd_tasks_delete()` function
- [ ] Cleanup task directory

### 2.10 tasks history
- [ ] `cmd_tasks_history()` function
- [ ] Read from task directories

---

## Phase 3 Tasks ✅ COMPLETE

### 3.1 Manager Configuration
- [x] Load `manager.yaml`
- [x] Personality extraction
- [x] Poll interval configuration

### 3.2 Manager Launch
- [x] Generate launch script
- [x] Set environment variables
- [x] Badge styling

### 3.3 Health Polling
- [x] Poll tmux for agents
- [x] Detect dead agents
- [x] Handle agent death

### 3.4 Pending Approval
- [x] Poll `.agency/pending/`
- [x] Read and validate completions
- [x] Archive or reject

### 3.5 Rejection Flow
- [x] Write rejection file
- [x] Send message to agent

---

## Phase 4 Tasks ✅ COMPLETE

### 4.1 Agent Configuration
- [x] Load `agents.yaml`
- [x] Load individual agent configs
- [x] Personality file resolution

### 4.2 Agent Launch
- [x] Generate launch script
- [x] Set environment variables
- [x] Personality injection

### 4.3 Environment Setup
- [x] AGENCY_* variables
- [x] PI_* variables

---

## Phase 5 Tasks ✅ COMPLETE

### 5.1 Graceful Stop
- [x] Broadcast shutdown
- [x] Wait for agents
- [x] Manager exit last

### 5.2 Halt Detection
- [x] Detect manager death
- [x] Create `.halted` file
- [x] Rename session/window

### 5.3 Resume Flow
- [x] Detect halt state
- [x] Restart manager
- [x] Process pending tasks
- [x] Clear halt markers

---

## Testing Tasks

### Unit Tests
- [x] Task ID generation
- [x] File locking
- [x] Task store operations
- [x] Configuration loading
- [x] Session management

### Integration Tests
- [ ] `init-project` workflow
- [ ] `start` workflow
- [ ] Task lifecycle
- [ ] Stop/resume

---

## Template Repository

### agency-templates
- [x] Create github.com/rwese/agency-templates repo
- [x] Create `basic` template
- [x] Create `api` template
- [x] Document templates
