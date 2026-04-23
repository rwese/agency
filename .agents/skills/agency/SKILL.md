---
name: agency
description: Setup and run Agency for AI agent orchestration. Use when initializing a new project, starting/stopping sessions, managing tasks, or working with tmux-based multi-agent workflows.
---

# Agency Skill

Agency is a tmux-based AI agent orchestration tool. Use this skill when setting up Agency for a project or managing agent sessions.

## Installation

```bash
# 1. Install agency CLI
cd ~/Repos/github.com/rwese/agency && uv pip install -e .

# 2. Install this skill for AI agents
agency skill install ~/.pi/agent/skills/
# Result: ~/.pi/agent/skills/agency/SKILL.md

# 3. Verify
agency --version
```

## Quick Start

```bash
# List available templates
agency templates

# Initialize project
agency init --dir ~/projects/myproject --template basic

# Start session
agency session start

# Attach
agency session attach
```

## Core Commands

### Project Initialization

| Command | Description |
|---------|-------------|
| `agency templates` | List available templates |
| `agency init --dir <path>` | Create project with basic template |
| `agency init --dir <path> --template api` | Use specific template |
| `agency init --dir <path> --template fullstack` | Use fullstack template |
| `agency init --dir <path> --force` | Overwrite existing |

### Session Management

| Command | Description |
|---------|-------------|
| `agency session start` | Start manager + all agents |
| `agency session stop` | Stop gracefully (Ctrl+C to abort) |
| `agency session attach` | Attach to session tmux |
| `agency session list` | List running sessions |
| `agency session members` | Show manager + agents status |

### Task Management

| Command | Description |
|---------|-------------|
| `agency tasks add -d "..."` | Create task |
| `agency tasks list` | List tasks |
| `agency tasks show <id>` | Show task details |
| `agency tasks assign <id> <agent>` | Assign to agent |
| `agency tasks complete <id> --result "..."` | Mark complete |
| `agency tasks history` | Show completed tasks |

### Session Window Operations

| Command | Description |
|---------|-------------|
| `agency session windows list` | List windows |
| `agency session windows send <win> <text>` | Send keys |
| `agency session windows run <win> <cmd>` | Run command |

## Templates

### Available Templates

| Template | Use Case |
|----------|----------|
| `basic` | Single coder agent (default) |
| `api` | Backend + frontend agents |
| `fullstack` | Backend + frontend + devops |

### Custom Templates

```bash
# From GitHub
agency init --dir ~/projects/myproject \
  --template https://github.com/user/repo/tree/main/my-template
```

## Workflow Examples

### New Project Setup

```bash
# Create and start
cd ~/projects
agency init --dir myproject --template api
agency session start
agency session attach

# Inside session, use Ctrl+B then D to detach
```

### Manager Assigns Tasks

```bash
# In manager window
agency tasks list
agency tasks add -d "Implement user auth"
agency tasks assign task-001 coder

# Monitor
agency tasks list
```

### Agent Completes Task

```bash
# In coder window
agency tasks list
# Work on task...
agency tasks complete task-001 --result "Done!"
```

## tmux Keybindings (when attached)

| Binding | Action |
|---------|--------|
| `Ctrl+B D` | Detach from session |
| `Ctrl+B 0` | Switch to window 0 (manager) |
| `Ctrl+B 1` | Switch to window 1 |
| `Ctrl+B 2` | Switch to window 2 |
| `Ctrl+B L` | Last window |
| `Ctrl+B :` | Command mode |

## File Structure

```
project/
├── .agency/
│   ├── config.yaml         # Project settings
│   ├── manager.yaml        # Manager personality
│   ├── agents.yaml         # Agent registry
│   ├── tasks/              # Task data
│   └── agents/             # Agent configs
└── src/                    # Project code
```

## Troubleshooting

### Session Not Found

```bash
# Check for running sessions
agency session list

# Verify .agency/ exists
ls -la .agency/
```

### Attach to Wrong Session

```bash
# Detach first (Ctrl+B D)
# Then attach to correct project
agency session attach
```

### Agent Not Responding

```bash
# Check heartbeat status
agency heartbeat status

# Restart heartbeat
agency heartbeat stop
agency heartbeat start --role manager
```

## Configuration

### config.yaml

```yaml
project: myproject
shell: bash
parallel_limit: 3
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `AGENCY_DIR` | Path to `.agency/` |
| `AGENCY_AGENT` | Current agent name |
| `AGENCY_ROLE` | MANAGER or AGENT |

## See Also

- [Agency README](../../README.md)
- [Design Docs](../../docs/design/)
