---
name: agency
description: Orchestrate AI agent sessions for project work. Use when: (1) initializing a new project with agency init, (2) starting/stopping multi-agent sessions, (3) assigning tasks with agency tasks add/assign, (4) monitoring session health, or (5) coordinating manager + coder workflows.
---

# Agency

AI agent orchestration with project-centric model.


## Quick Start

```bash
# Initialize project
agency init --dir ~/projects/myproject --template basic

# Start session
agency session start

# Attach to interact
agency session attach
# Detach: Ctrl+B D
```

## Core Workflows

### New Project

```bash
cd ~/projects
agency init --dir myproject --template api
agency session start
agency session attach
```

### Manager Assigns Tasks

```bash
# In manager window
agency tasks add -d "Implement user auth"
agency tasks assign task-001 coder
agency tasks list
```

### Agent Completes Task

```bash
# In agent window
agency tasks list
# Work on task...
agency tasks complete task-001 --result "Done!"
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Session not found | `agency session list` + verify `.agency/` exists |
| Attach wrong session | `Ctrl+B D` to detach, then `agency session attach` |
| Agent not responding | `agency heartbeat status` / `agency heartbeat start --role manager` |

## Reference

- **CLI commands**: See [commands.md](references/commands.md)
- **Config schemas**: See [config.md](references/config.md)
- **Full docs**: [README](../../README.md), [design docs](../../docs/design/)
