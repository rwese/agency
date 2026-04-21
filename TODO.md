# Agency v2.0 - Implementation TODO

**Status:** Stage 2: Completions COMPLETE
**Last Updated:** 2024-04-21

## Current Stage

### Stage 1: Approval CLI

- [x] Add `tasks approve` command
- [x] Add `tasks reject` command
- [x] Add `tasks reopen` command
- [x] Add `tasks history` command

### Stage 2: Completions (DONE)

- [x] Convert `__main__.py` to Click
- [x] Enable Click shell completions
- [x] Test with bash/zsh/fish

### Stage 3: Integration Tests (Pending)

- [ ] Set up pytest-tmux fixture
- [ ] Test full workflow
- [ ] Add GitHub Actions

---

## Task Details

### 1.1 tasks approve
- [x] Add `cmd_approve()` function
- [x] Wire up argparse subcommand
- [x] Test: verify task status → completed

### 1.2 tasks reject
- [x] Add `cmd_reject()` function
- [x] Wire up argparse subcommand
- [x] Test: verify task status → failed, rejection file created

### 1.3 tasks reopen
- [x] Add `cmd_reopen()` function
- [x] Wire up argparse subcommand
- [x] Test: verify task status → pending

### 1.4 tasks history
- [x] Verify existing implementation works
- [x] Add filtering options if needed
- [x] Test: verify output format
