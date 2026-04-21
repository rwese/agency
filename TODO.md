# TODO: Add Usage Examples to Agency CLI Help

## Tasks

- [x] 1. Add role-based epilog functions to `__main__.py`
- [x] 2. Apply epilog to CLI group based on AGENCY_ROLE
- [x] 3. Test help output for DEFAULT role
- [x] 4. Test help output for MANAGER role
- [x] 5. Test help output for AGENT role
- [x] 6. Run tests to ensure no regressions

## Status

✓ Completed: 2026-04-21

## Summary

Added role-based usage examples to `agency --help`:

- **Default (interactive)**: Quick start, task management, session management
- **MANAGER**: Coordinator workflow, monitoring sessions
- **AGENT**: Task workflow (list, show, update, complete)

All relevant tests pass. Lint clean.
