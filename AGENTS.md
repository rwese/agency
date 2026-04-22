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

> **Role Requirements**: Commands are filtered by `AGENCY_ROLE`:
> - **No role** (default): Full command set
> - **MANAGER**: All commands except `templates` and `completions`
> - **AGENT**: Tasks agent command only

### Project Management

| Command | Role | Description |
|---------|------|-------------|
| `agency init` | any | Create project + session + `.agency/` |
| `agency templates` | none | List available project templates |
| `agency start` | any | Start the agency (manager + all agents) |
| `agency members` | any | Show all configured members with status |
| `agency stop <session>` | any | Stop session gracefully |
| `agency kill <session>` | any | Force kill session |
| `agency resume` | any | Resume a halted session |
| `agency attach` | any | Attach to project session (auto-detected) |
| `agency list` | any | List all agency sessions |

### Tmux Operations

| Command | Role | Description |
|---------|------|-------------|
| `agency tmux list` | any | List windows in current project |
| `agency tmux send <window> <text>` | any | Send keys to window |
| `agency tmux new <name>` | any | Create new window |
| `agency tmux attach` | any | Attach to session (new terminal) |
| `agency tmux run <window> <cmd>` | any | Run command in window |

### Task Management

| Command | Role | Description |
|---------|------|-------------|
| `agency tasks list` | any | List active tasks (Markdown) |
| `agency tasks add -d <desc>` | any | Create task |
| `agency tasks show <id>` | any | Show task details |
| `agency tasks assign <id> <agent>` | any | Assign to agent |
| `agency tasks complete <id> --result <text>` | any | Complete task |
| `agency tasks update <id> [--status] [--priority]` | any | Update task |
| `agency tasks delete <id>` | any | Delete task |
| `agency tasks history` | any | List completed tasks |

### Audit Trail

SQLite-based audit logging for all agency operations.

| Command | Role | Description |
|---------|------|-------------|
| `agency audit list` | any | List audit events |
| `agency audit list --type task` | any | Filter by event type (cli, task, session, agent) |
| `agency audit list --task <id>` | any | Filter by task ID |
| `agency audit stats` | any | Show audit statistics |
| `agency audit export` | any | Export events to JSON |
| `agency audit export --format csv` | any | Export to CSV |
| `agency audit clear` | any | Preview old events |
| `agency audit clear --force` | any | Delete events older than 30 days |

**Event Types:**
- `cli` - CLI command invocations
- `task` - Task lifecycle (create, assign, update, complete, approve, reject, delete)
- `session` - Session events (start, stop)
- `agent` - Agent activity (start, heartbeat)

**Storage:** `.agency/audit.db` (SQLite)

## File Structure

```
<project-root>/
├── .agency/
│   ├── config.yaml           # Project settings
│   ├── manager.yaml          # Manager personality
│   ├── agents.yaml           # Agent registry
│   ├── tasks.json            # Active tasks
│   ├── audit.db              # Audit trail (SQLite)
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

## Template Injection

Personality files and context files support dynamic placeholders that are processed before injection.

### Syntax

```
${{file:path}}      → Read file at path, inject contents
${{shell:cmd}}       → Execute command, inject stdout
```

### Examples

**Include a common file:**
```yaml
personality: |
  # Base personality
  You are a helpful developer.

  ${{file:./common-knowledge.md}}
```

**Include shell output:**
```yaml
personality: |
  Current project info:
  ${{shell:git remote -v}}
```

**Custom delimiters:**

For files containing `${{...}}` syntax (e.g., code with template literals), use custom delimiters via config:

```yaml
template_delimiter: "{{...}}"
```

This changes the pattern to `{{file:path}}` / `{{shell:cmd}}`.

### Behavior

- **File paths**: Relative paths resolved from `.agency/` directory
- **Shell commands**: Run fresh every time (no caching), 60s timeout
- **Errors**: Warnings logged to console, placeholder replaced with empty string on error
- **Nesting**: Not supported (processed once only)

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
