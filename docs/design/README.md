# Agency v2.0 Design Documents

## Overview

This directory contains the complete design specification for Agency v2.0.

## Documents

### [v2.0-index.md](v2.0-index.md)
**Start here.** Overview, quick reference, and links to all documents.

### [v2.0-entities.md](v2.0-entities.md)
Core entities and relationships:
- Project, Manager, Agent, Task definitions
- Entity diagrams
- Task state machine
- File structure

### [v2.0-cli.md](v2.0-cli.md)
Complete CLI reference:
- All commands with flags
- Examples for each command
- Exit codes
- Error output format

### [v2.0-schemas.md](v2.0-schemas.md)
Data model schemas:
- `tasks.json` v2 schema
- `task.json` and `result.json`
- YAML config schemas
- Task ID generation
- Locking strategy

### [v2.0-workflows.md](v2.0-workflows.md)
Detailed workflows:
- Project creation
- Task lifecycle diagrams
- Manager approval flow
- Shutdown and halt/resume
- Template system

### [v2.0-requirements.md](v2.0-requirements.md)
Requirements specification (source of truth):
- Goals and principles
- Core requirements
- Task lifecycle rules
- Heartbeat processing
- Notification rules
- Dos and don'ts
- Edge cases

## Reading Order

1. Start with `v2.0-index.md`
2. Read `v2.0-entities.md` for conceptual model
3. Reference `v2.0-cli.md` for commands
4. Use `v2.0-schemas.md` for implementation
5. Reference `v2.0-workflows.md` for behavior
6. **Critical**: Read `v2.0-requirements.md` for operational rules (heartbeat, notifications, dos/don'ts)

## Status

| Document | Status |
|----------|--------|
| v2.0-index.md | ✓ Complete |
| v2.0-entities.md | ✓ Complete |
| v2.0-cli.md | ✓ Complete |
| v2.0-schemas.md | ✓ Complete |
| v2.0-workflows.md | ✓ Complete |
| v2.0-requirements.md | ✓ Complete |

## Related Documents

- [AGENTS.md](../../AGENTS.md) - Developer-focused overview
- [CHANGELOG.md](../../CHANGELOG.md) - Version history
- [templates/](../../templates/) - Bundled templates (basic, api, fullstack)
