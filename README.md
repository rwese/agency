# Agency - AI Agent Session Manager

A tmux-based multi-agent orchestration tool for AI-driven development workflows.

## Quick Start

```bash
# Install
uv pip install -e .

# Create a project with a manager
agency init-project --dir ~/projects/api --start-manager coordinator

# Start agents
agency start developer --dir ~/projects/api

# Manage tasks
agency tasks add -d "Implement authentication"
agency tasks assign swift-bear-a3f2 developer
agency tasks list

# Attach and work
agency attach api
```

## Architecture

```
agency-api                    # tmux session + socket
├── [MGR] coordinator       # Manager (orchestrator)
├── developer                # Agent
└── tester                  # Agent
```

**Relationships:**
- Project 1:1 Manager
- Project 1:N Agents
- Manager 1:N Tasks
- Agent 1:1 Task (active)

## Installation

```bash
# Using uv (recommended)
uv pip install -e .

# Or run without installing
uv run agency <command>
```

## Commands

### Project Management

| Command | Description |
|---------|-------------|
| `agency init-project --dir <path>` | Create project + session + `.agency/` |
| `agency start <name> --dir <path>` | Start agent or manager |
| `agency stop <session>` | Shutdown gracefully |
| `agency resume <session>` | Resume from halt |
| `agency attach <session>` | Attach to session |
| `agency list` | List sessions |

### Task Management

| Command | Description |
|---------|-------------|
| `agency tasks list` | List active tasks |
| `agency tasks add -d <desc>` | Create task |
| `agency tasks show <id>` | Show task details |
| `agency tasks assign <id> <agent>` | Assign to agent |
| `agency tasks complete <id> --result <text>` | Complete task |
| `agency tasks history` | Show completed tasks |

## File Structure

```
project/
├── .agency/
│   ├── config.yaml           # Project settings
│   ├── manager.yaml          # Manager personality
│   ├── agents.yaml           # Agent registry
│   ├── tasks.json            # Active tasks
│   ├── agents/
│   │   └── developer.yaml
│   ├── tasks/
│   │   └── <task_id>/
│   │       ├── task.json
│   │       └── result.json
│   └── pending/
│       └── <task_id>.json
└── src/
```

## Task Lifecycle

```
pending → in_progress → pending_approval → completed
                     ↓
                  failed (on reject)
```

## Templates

Use templates for quick project setup:

```bash
# Basic template (default)
agency init-project --dir ~/projects/api

# API template
agency init-project --dir ~/projects/api \
  --template https://github.com/rwese/agency-templates/tree/main/api

# Custom template
agency init-project --dir ~/projects/app \
  --template https://github.com/user/repo
```

## Configuration

### config.yaml

```yaml
project: api
shell: bash
```

### manager.yaml

```yaml
personality: |
  You are the project coordinator.

  ## Task Management
  - agency tasks list
  - agency tasks assign <id> <agent>

poll_interval: 30
auto_approve: false
```

### agents.yaml

```yaml
agents:
  - name: developer
    config: agents/developer.yaml
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AGENCY_PROJECT` | Project name |
| `AGENCY_DIR` | Path to `.agency/` |
| `AGENCY_AGENT` | Agent name |
| `AGENCY_MANAGER` | Manager name |
| `PI_CODING_AGENT` | Set for agents |
| `PI_AGENCY_MANAGER` | Set for manager |

## Testing

```bash
# Run tests
uv run pytest

# Lint
uvx ruff check src/

# Format
uvx ruff format src/
```

## Project Structure

```
agency/
├── src/agency/
│   ├── __init__.py
│   ├── __main__.py       # CLI entry
│   ├── session.py         # Session management
│   ├── tasks.py           # Task store
│   ├── tasks_cli.py       # Task CLI
│   ├── template.py        # Template download
│   └── config.py          # Config loading
├── tests/
│   ├── test_tasks.py
│   ├── test_session.py
│   └── test_config.py
├── docs/design/           # Design documents
└── pyproject.toml
```

## Design Documents

See `docs/design/` for complete specification:
- [v2.0-index.md](docs/design/v2.0-index.md) - Overview
- [v2.0-entities.md](docs/design/v2.0-entities.md) - Entities
- [v2.0-cli.md](docs/design/v2.0-cli.md) - CLI reference
- [v2.0-schemas.md](docs/design/v2.0-schemas.md) - Data schemas
- [v2.0-workflows.md](docs/design/v2.0-workflows.md) - Workflows
