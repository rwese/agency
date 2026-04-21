# E2E Test: Todo CLI Application

This directory contains the end-to-end integration test for agency.

## Test Scenario

**Goal:** Verify that agency can orchestrate multiple agents to complete a task.

**Task:** Create a simple CLI todo application

**Agents:**
- **coordinator** (manager): Orchestrates task delegation
- **coder**: Implements the todo CLI
- **tester**: Writes and runs tests

## Test Workflow

```
1. Initialize local agency in e2e directory
2. Start coordinator manager
3. Coordinator assigns task to coder
4. Coder creates todo.py
5. Coordinator assigns test task to tester
6. Tester creates and runs pytest tests
7. Verify final state: todo.py + tests pass
```

## Running the Test

```bash
# Option 1: Use just recipe
just test-e2e

# Option 2: Manual
cd e2e/test-todo-app
agency init --local
agency start-manager coordinator --dir .
agency attach-manager coordinator
```

## Expected Results

### Success
- `todo.py` exists with working CLI
- `test_todo.py` exists with passing tests
- All agents communicate and complete tasks

### Failure Indicators
- Agent doesn't respond to messages
- Task not completed
- Tests fail
- Manager doesn't delegate properly

## Configuration Files

```
e2e/test-todo-app/
├── agents/
│   ├── coder.yaml       # Coder agent prompt
│   └── tester.yaml      # Tester agent prompt
├── managers/
│   └── coordinator.yaml # Manager prompt with protocol
└── README.md            # This file
```
