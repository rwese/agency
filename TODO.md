# Agency v2.0 - Implementation TODO

**Status:** In Progress  
**Last Updated:** 2024

## Implementation Phases

### Phase 1: Core Infrastructure ✅ Designed
- [x] Design complete
- [x] Design documents created
- [x] **IMPLEMENTED** - Core modules created

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

## Phase 1 Tasks

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

## Phase 2 Tasks

### 2.1 Task ID Generation
- [ ] Implement wordlist-based ID generator
- [ ] Collision detection
- [ ] Unit tests

### 2.2 tasks.json Management
- [ ] Create `TasksStore` class
- [ ] File locking with filelock
- [ ] Version 2 schema
- [ ] CRUD operations

### 2.3 tasks list
- [ ] `cmd_tasks_list()` function
- [ ] Markdown output
- [ ] Filtering options

### 2.4 tasks add
- [ ] `cmd_tasks_add()` function
- [ ] Directory creation
- [ ] Task ID generation

### 2.5 tasks show
- [ ] `cmd_tasks_show()` function
- [ ] Markdown output

### 2.6 tasks assign
- [ ] `cmd_tasks_assign()` function
- [ ] Free agent validation

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

## Phase 3 Tasks

### 3.1 Manager Configuration
- [ ] Load `manager.yaml`
- [ ] Personality extraction
- [ ] Poll interval configuration

### 3.2 Manager Launch
- [ ] Generate launch script
- [ ] Set environment variables
- [ ] Badge styling

### 3.3 Health Polling
- [ ] Poll tmux for agents
- [ ] Detect dead agents
- [ ] Handle agent death

### 3.4 Pending Approval
- [ ] Poll `.agency/pending/`
- [ ] Read and validate completions
- [ ] Archive or reject

### 3.5 Rejection Flow
- [ ] Write rejection file
- [ ] Send message to agent

---

## Phase 4 Tasks

### 4.1 Agent Configuration
- [ ] Load `agents.yaml`
- [ ] Load individual agent configs
- [ ] Personality file resolution

### 4.2 Agent Launch
- [ ] Generate launch script
- [ ] Set environment variables
- [ ] Personality injection

### 4.3 Environment Setup
- [ ] AGENCY_* variables
- [ ] PI_* variables

---

## Phase 5 Tasks

### 5.1 Graceful Stop
- [ ] Broadcast shutdown
- [ ] Wait for agents
- [ ] Manager exit last

### 5.2 Halt Detection
- [ ] Detect manager death
- [ ] Create `.halted` file
- [ ] Rename session/window

### 5.3 Resume Flow
- [ ] Detect halt state
- [ ] Restart manager
- [ ] Process pending tasks
- [ ] Clear halt markers

---

## Testing Tasks

### Unit Tests
- [ ] Task ID generation
- [ ] File locking
- [ ] Task store operations

### Integration Tests
- [ ] `init-project` workflow
- [ ] `start` workflow
- [ ] Task lifecycle
- [ ] Stop/resume

---

## Template Repository

### agency-templates
- [ ] Create github.com/rwese/agency-templates repo
- [ ] Create `basic` template
- [ ] Create `api` template
- [ ] Document templates
