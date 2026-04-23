---
name: agency
description: "Orchestrate AI agent sessions for project work. Use when: (1) initializing a new project with agency init, (2) starting/stopping multi-agent sessions, (3) assigning tasks with agency tasks add/assign, (4) monitoring session health, or (5) coordinating manager + coder workflows."
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
- **Creating custom agencies**: See [creating-agencies.md](references/creating-agencies.md)
- **Full docs**: [README](../../README.md), [design docs](../../docs/design/)

## Templates

| Template | Use Case | Agents |
|----------|----------|--------|
| `basic` | Single developer | manager + coder |
| `solo` | Personal projects, minimal | manager + developer |
| `api` | Backend + frontend | manager + backend + frontend |
| `fullstack` | Full application | manager + backend + frontend + devops |
| `team` | Small team | manager + coder + reviewer + tester |

## Agent Personalities

Pre-built personality templates available in `assets/personalities/`:

| Personality | Purpose |
|-------------|---------|
| [coder.md](assets/personalities/coder.md) | Backend/API development |
| [reviewer.md](assets/personalities/reviewer.md) | Code review and quality |
| [devops.md](assets/personalities/devops.md) | Infrastructure and deployment |
| [tester.md](assets/personalities/tester.md) | QA and test coverage |
| [architect.md](assets/personalities/architect.md) | System design and decisions |

**Usage:** Copy a personality file to `agents/<name>/personality.md` and reference it in your `agents.yaml`.
