## agency init improvements — TODO

### Done
- [x] M1.1: Add --context-file CLI option
- [x] M1.2: Add signal handler
- [x] M1.3: Implement checkbox selection
- [x] M2.1: Add custom filepath prompt
- [x] M2.2: Validate paths
- [x] M2.3: Update tests
- [x] M3.1: Update documentation (help text)
- [x] M3.2: Run linter and tests

### Summary
All tasks completed. Features implemented:
- `--context-file` option (repeatable) for direct file path input
- Proper ctrl-c abort with tmux session cleanup
- Interactive checkbox selection (uses rich, falls back to skip in non-TTY)
- Custom filepath prompt after checkbox selection
- Path validation (aborts if file not found)
- Non-interactive mode support (stdin.isatty() check)

### Tests
All init-related tests pass (15/15):
- tests/test_init_context.py: 10 tests
- tests/test_e2e.py::TestInitProject: 5 tests

### Notes
- Other test failures in test_audit.py, test_tasks.py, test_tasks_cli.py are pre-existing
- Not related to init improvements
