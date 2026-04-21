# Agency Testing Guide

## Overview

This document covers testing strategies for agency, including unit tests, integration tests, and end-to-end tests.

## Test Types

### 1. Integration Tests (`test_agency.sh`)

Quick validation of core functionality.

```bash
./test_agency.sh
```

**Covers:**
- `init --global` / `init --local`
- `start` agent
- `list` sessions
- `send` messages
- `stop` / `kill` sessions
- Shell completions

### 2. End-to-End Tests (`just e2e-*`)

Full workflow validation with real agents.

```bash
# Initialize test directory
just e2e-test-init

# Start coordinator
just e2e-test-start

# Attach to manager (interactive)
just e2e-test-attach

# Verify results
just e2e-test-verify

# Clean up
just e2e-test-clean
```

## E2E Test Scenario

**Task:** Create a simple CLI todo application

**Agents:**
- `coordinator` - Manager that orchestrates
- `coder` - Implements the todo CLI
- `tester` - Writes and runs tests

**Expected Output:**
- `e2e/test-todo-app/todo.py` - Working CLI
- `e2e/test-todo-app/test_todo.py` - Passing tests

## Debugging E2E Tests

### Check Session Status
```bash
just e2e-test-status
# or
agency list
```

### View Agent Output
```bash
# Attach to session with specific agent
agency attach e2e-test <agent>
```

### Common Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| Agent not responding | Manager waits forever | Check if pi started correctly |
| Task not completed | Missing files | Verify personality prompt loaded |
| Communication broken | No `DONE` response | Check message delivery |
| Tests fail | pytest errors | Run manually: `cd e2e/test-todo-app && pytest` |

### Manual Intervention

If agents get stuck:

```bash
# Send message directly
agency send agency-manager-coordinator coordinator "Status?"

# Stop gracefully
agency stop-manager coordinator

# Force kill
agency kill-manager coordinator
```

## Blind Spots to Monitor

1. **Pi startup timing** - Does agent initialize before receiving messages?
2. **Session directory** - Do agents share or isolate state?
3. **Personality injection** - Does `--append-system-prompt` work correctly?
4. **Message delivery** - Are messages received in order?
5. **Error propagation** - Do agent failures bubble up?

## Test Artifacts

```
agency/
├── test_agency.sh           # Integration test runner
├── e2e/
│   └── test-todo-app/       # E2E test scenario
│       ├── agents/          # Agent configs
│       ├── managers/        # Manager configs
│       └── README.md        # Test documentation
└── TESTING.md               # This file
```

## CI/CD Integration

Run tests in CI:

```bash
#!/bin/bash
set -e

# Install
uv pip install -e .

# Run integration tests
./test_agency.sh

# Run e2e test (optional, may need manual interaction)
# just e2e-test-init
# just e2e-test-start
# ...
```
