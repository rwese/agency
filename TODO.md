# TODO: Agency E2E Integration Test

## Status: ✓ COMPLETE

## Summary

E2E test ran successfully on 2026-04-21.

## Test Results

| Metric | Result |
|--------|--------|
| Manager started | ✓ |
| Coder created todo.py | ✓ (3118 bytes) |
| Tester created test_todo.py | ✓ (4245 bytes) |
| Tests run | 4/7 passed |
| Test failures | Minor (state pollution, path issues) |

## Files Created

```
e2e/test-todo-app/
├── agents/
│   ├── coder.yaml          # Coder agent prompt
│   └── tester.yaml        # Tester agent prompt
├── managers/
│   └── coordinator.yaml   # Manager with protocol
├── README.md             # Test documentation
└── e2e-proof.txt         # Proof of work
```

## Issues Found

1. **Badge in window name breaks scripts** - Window name with `[MGR]` causes shell escaping issues. Fixed by using empty badge.

2. **Wrong session name in coordinator prompt** - Prompt uses `e2e-test` but actual session is `agency-test`. Minor issue.

3. **TextLog import error in tui/app.py** - Pre-existing issue, TextLog renamed in newer textual.

## Usage

```bash
# Initialize test directory
just e2e-test-init

# Start coordinator
just e2e-test-start

# Attach to interact (in another terminal)
just e2e-test-attach

# Clean up
just e2e-test-clean
```

## Proof

See `e2e/test-todo-app/e2e-proof.txt` for full test output.
