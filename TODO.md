# Agency Python Rewrite - TODO

## Status: Complete ✅

---

## Completed Tasks

### Stage 1: Core Rewrite

- [x] **1.1** Python CLI framework - argparse with subcommands
- [x] **1.2** Session management - Create/list/destroy tmux sessions
- [x] **1.3** Window management - Add/remove agent windows per session
- [x] **1.4** Agent spawning - Start pi/mock with proper args
- [x] **1.5** Message sending - Send messages to specific windows

### Stage 2: Agent Lifecycle

- [x] **2.1** Graceful shutdown - Send message to agents
- [x] **2.2** Agent deduplication - Prevent duplicate agents per session
- [x] **2.3** Config loading - Read agent YAML configs

### Stage 3: Testing

- [x] **3.1** Test suite - bash integration tests
- [x] **3.2** Mock agent - Proper mocking of pi

### Stage 4: Polish

- [ ] **4.1** Shell completions - bash/zsh/fish
- [ ] **4.2** Documentation - README with examples
- [x] **4.3** AGENTS.md update

---

## Completion Criteria

- [x] `agency start coder --dir ~/api` creates session `api` with window `coder`
- [x] `agency start tester --dir ~/api` adds window `tester` to session `api`
- [x] `agency start coder --dir ~/api` errors if agent exists in session
- [x] `agency list` shows `api [coder, tester]`
- [x] `agency send api coder "hi"` sends to correct window
- [x] All pytest tests pass (9/9)
