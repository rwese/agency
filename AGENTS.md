# Agency v2.0 - Agent Configuration

Tmux-based AI agent orchestration with project-centric model.

## Architecture

```
agency-<project>                    # tmux session + socket
├── [MGR] coordinator              # Manager (index 0)
├── coder                           # Agent (index 1+)
└── tester                          # Agent
```

**Relationships:**
- Project 1:1 Manager
- Project 1:N Agents  
- Manager 1:N Tasks
- Agent 1:1 Task (active)

## Quick Start

```bash
# Create project
agency init-project --dir ~/projects/api --start-manager coordinator

# Add agents
agency start coder --dir ~/projects/api
agency start tester --dir ~/projects/api

# Manage tasks
agency tasks add -d "Implement auth API"
agency tasks assign swift-bear-a3f2 coder

# Attach and work
agency attach api
```

## Commands

### Project Management

| Command | Description |
|---------|-------------|
| `agency init-project --dir <path>` | Create project + session + `.agency/` |
| `agency start <name> --dir <path>` | Start agent in project |
| `agency stop <session>` | Shutdown session gracefully |
| `agency resume <session>` | Resume from halt |
| `agency attach <session>` | Attach to session |
| `agency list` | List sessions |

### Task Management

| Command | Description |
|---------|-------------|
| `agency tasks list` | List active tasks (Markdown) |
| `agency tasks add -d <desc>` | Create task |
| `agency tasks show <id>` | Show task details |
| `agency tasks assign <id> <agent>` | Assign to agent |
| `agency tasks complete <id> --result <text>` | Complete task |
| `agency tasks update <id> [--status] [--priority]` | Update task |
| `agency tasks delete <id>` | Delete task |
| `agency tasks history` | List completed tasks |

## File Structure

```
<project-root>/
├── .agency/
│   ├── config.yaml           # Project settings
│   ├── manager.yaml          # Manager personality
│   ├── agents.yaml           # Agent registry
│   ├── tasks.json            # Active tasks
│   ├── .halted              # Halt marker
│   ├── agents/
│   │   ├── coder.yaml
│   │   └── coder/
│   │       └── personality.md
│   ├── tasks/
│   │   └── <task_id>/
│   │       ├── task.json
│   │       └── result.json
│   └── pending/
│       └── <task_id>.json
├── src/
└── ...
```

## Configuration

### config.yaml

```yaml
project: api
shell: bash
template_url: https://github.com/rwese/agency-templates
```

### manager.yaml

```yaml
personality: |
  You are the project coordinator.

  ## Task Management
  - agency tasks list  # See pending
  - agency tasks assign <id> <agent>  # Assign
  - agency tasks add -d "..."  # Create

poll_interval: 30
auto_approve: false
```

### agents.yaml

```yaml
agents:
  - name: coder
    config: agents/coder.yaml
  - name: tester
    config: agents/tester.yaml
```

### agents/<name>.yaml

```yaml
name: coder
personality: personality.md
```

## Task Lifecycle

```
pending → in_progress → pending_approval → completed
                     ↓
                  failed (on reject)
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AGENCY_PROJECT` | Project name |
| `AGENCY_DIR` | Path to `.agency/` |
| `AGENCY_AGENT` | Agent name |
| `AGENCY_MANAGER` | Manager name |
| `PI_CODING_AGENT` | `true` for agents |
| `PI_AGENCY_MANAGER` | `true` for manager |
| `PI_AGENCY_RESUMING` | `true` on resume |

## Development

```bash
# Install
uv pip install -e .

# Test
./test_agency.sh
uv run pytest

# Lint
uvx ruff check src/
uvx ruff format src/

# Debug tmux
tmux -L agency-api list-sessions
tmux -L agency-api list-windows -t <session>

# Test with mock
AGENCY_AGENT_CMD="python3 src/agency/mock_agent.py" \
  uv run agency start coder --dir /tmp
```

## Design Documents

See `docs/design/` for complete specification:
- `v2.0-index.md` - Overview
- `v2.0-entities.md` - Entity relationships
- `v2.0-cli.md` - CLI reference
- `v2.0-schemas.md` - Data schemas
- `v2.0-workflows.md` - Workflows

## Boundaries

**ALWAYS**
- Run `./test_agency.sh` before committing
- Use `uv run agency` or `agency` (after install)

**NEVER**
- Commit with untested changes
- Leave running tmux sessions
- Store secrets in `.agency/`
