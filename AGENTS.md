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
cd ~/projects/api
agency init

# Start manager + agents
agency start

# Manage tasks (run from project dir)
cd ~/projects/api
agency tasks add -d "Implement auth API"
agency tasks assign swift-bear-a3f2 coder

# Tmux operations
agency tmux list
agency tmux attach

# When done
agency stop agency-api
```

## Commands

### Project Management

| Command | Description |
|---------|-------------|
| `agency init` | Create project + session + `.agency/` |
| `agency start` | Start the agency (manager + all agents) |
| `agency members` | Show all configured members with status |
| `agency stop <session>` | Stop session gracefully |
| `agency kill <session>` | Force kill session |
| `agency resume` | Resume a halted session |
| `agency attach` | Attach to project session (auto-detected) |
| `agency list` | List all agency sessions |

### Tmux Operations

| Command | Description |
|---------|-------------|
| `agency tmux list` | List windows in current project |
| `agency tmux send <window> <text>` | Send keys to window |
| `agency tmux new <name>` | Create new window |
| `agency tmux attach` | Attach to session (new terminal) |
| `agency tmux run <window> <cmd>` | Run command in window |

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
| `AGENCY_AGENT` | Agent name (set for agents) |
| `AGENCY_MANAGER` | Manager name (set for manager) |
| `AGENCY_ROLE` | `MANAGER` or `AGENT` |
| `AGENCY_RESUMING` | `true` on resume |

## Development

```bash
# Install
uv pip install -e .

# Test
./test_agency.sh
uv run pytest

# Lint
uv run ruff check src/
uv run ruff format src/

# Tmux debugging (use project socket)
tmux -L agency-<project> list-windows -t agency-<project>
tmux -L agency-<project> list-sessions

# Test with mock
AGENCY_AGENT_CMD="python3 src/agency/mock_agent.py" \
  agency start --dir /tmp
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
