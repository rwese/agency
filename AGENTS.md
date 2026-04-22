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
agency session start

# Manage tasks (run from project dir)
cd ~/projects/api
agency tasks add -d "Implement auth API"
agency tasks assign swift-bear-a3f2 coder

# Session operations
agency session list
agency session windows list
agency session attach

# When done
agency session stop
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

### Session Management

| Command | Role | Description |
|---------|------|-------------|
| `agency session start` | any | Start the session (manager + all agents) |
| `agency session stop [session]` | any | Stop session gracefully |
| `agency session kill [session]` | any | Force kill session |
| `agency session resume` | any | Resume a halted session |
| `agency session attach` | any | Attach to project session |
| `agency session list` | any | List all agency sessions |
| `agency session members` | any | Show all configured members with status |

### Session Windows

| Command | Role | Description |
|---------|------|-------------|
| `agency session windows list` | any | List windows in current session |
| `agency session windows send <window> <text>` | any | Send keys to window |
| `agency session windows new <name>` | any | Create new window |
| `agency session windows run <window> <cmd>` | any | Run command in window |



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

### Heartbeat Commands

Background processes that monitor tasks and notify agents of available work.
Role determined by `AGENCY_ROLE` env var, agent name from `AGENCY_AGENT`.

| Command | Description |
|---------|-------------|
| `AGENCY_ROLE=manager agency heartbeat start` | Start manager heartbeat |
| `AGENCY_ROLE=agent AGENCY_AGENT=<name> agency heartbeat start` | Start agent heartbeat |
| `agency heartbeat stop` | Stop heartbeats |
| `agency heartbeat status` | Show heartbeat status |
| `agency heartbeat logs` | View own heartbeat logs |

**Behavior:**
- Manager heartbeat notifies coordinator of unassigned tasks (only when nothing in progress)
- Agent heartbeat notifies agent of assigned tasks (only when no task in progress)

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
│   ├── manager.yaml           # Manager personality
│   ├── agents.yaml            # Agent registry
│   ├── tasks.json             # Active tasks
│   ├── audit.db               # Audit trail (SQLite)
│   ├── notifications.json     # Heartbeat notifications
│   ├── .halted               # Halt marker
│   ├── .heartbeat-*.pid       # Heartbeat PID files
│   ├── .heartbeat-*.log       # Heartbeat log files
│   ├── pi/
│   │   └── extensions/        # pi extensions (self-contained)
│   │       ├── pi-inject/
│   │       ├── pi-status/
│   │       └── no-frills/
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

All config files include `$schema` directives for IDE validation and autocompletion.

### config.yaml

```yaml
$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/config.json
project: api
shell: bash
template_url: https://github.com/rwese/agency-templates
audit_enabled: true  # Set to false to disable audit logging
```

### manager.yaml

```yaml
$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/manager.json
name: coordinator
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
$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/agents.json
agents:
  - name: coder
    config: agents/coder.yaml
  - name: tester
    config: agents/tester.yaml
```

### agents/<name>.yaml

```yaml
$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/agent.json
name: coder
personality: |
  You are the coder agent.
```

## YAML Schemas

Agency config files use JSON Schema for validation and autocompletion.

### IDE Setup

**VS Code:** Install the "YAML Language Support" by Red Hat extension. The `$schema` directive in each file enables validation automatically.

**JetBrains IDEs:** Native YAML support with schema detection from `$schema` directive.

### Available Schemas

| Schema | File | URL |
|--------|------|-----|
| config | `.agency/config.yaml` | `schemas/config.json` |
| manager | `.agency/manager.yaml` | `schemas/manager.json` |
| agents | `.agency/agents.yaml` | `schemas/agents.json` |
| agent | `.agency/agents/<name>.yaml` | `schemas/agent.json` |

### Validation

Config files are validated on load. Invalid configs log warnings but continue with defaults.

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

### Lazy Agent Spawning

Agents are spawned **only when work is assigned to them**. This reduces overhead by only running agents when needed.

**Spawning rules:**
1. Task must be **assigned** to an agent
2. Agent must **not already be running**
3. Agent must have **available slot** (capacity < parallel_limit)

**Slot coordination:**
- Tracked in `.agency/signals/slots-available.json`
- When task completes → slot released → waiting agents notified
- Uses file-based signaling for efficient waiting

### Automated Review

When a task reaches `pending_approval`, the manager heartbeat automatically:
1. Detects orphaned tasks (no reviewer assigned)
2. Spawns a reviewer agent for each pending task
3. Tracks `reviewer_assigned` field in task
4. Auto-recovers if reviewer crashes

## File Structure

```
<project-root>/
├── .agency/
│   ├── config.yaml           # Project settings
│   ├── manager.yaml           # Manager personality
│   ├── agents.yaml            # Agent registry
│   ├── tasks.json             # Active tasks
│   ├── audit.db               # Audit trail (SQLite)
│   ├── notifications.json     # Heartbeat notifications
│   ├── signals/              # Slot coordination
│   │   └── slots-available.json
│   ├── .halted               # Halt marker
│   ├── .heartbeat-*.pid       # Heartbeat PID files
│   ├── .heartbeat-*.log       # Heartbeat log files
│   ├── pi/
│   │   └── extensions/        # pi extensions (self-contained)
│   │       ├── pi-inject/
│   │       ├── pi-status/
│   │       └── no-frills/
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

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AGENCY_PROJECT` | Project name |
| `AGENCY_DIR` | Path to `.agency/` |
| `AGENCY_AGENT` | Agent name (set for agents) |
| `AGENCY_MANAGER` | Manager name (set for manager) |
| `AGENCY_ROLE` | `MANAGER` or `AGENT` |
| `AGENCY_RESUMING` | `true` on resume |

## pi Extensions

Bundled extensions are **automatically copied** to each project's `.agency/pi/extensions/` during `agency init`. Agency is self-contained - no global installation required.

| Extension | Description |
|-----------|-------------|
| `pi-status` | Status bar for tmux windows |
| `pi-inject` | Message injection via Unix socket |
| `no-frills` | Hide/modify TUI decorations |

### Info

```bash
# Show extensions location for current project
just pi-extensions-info
```

### Manual Override (optional)

If needed, override extension paths via environment variables:

| Variable | Description |
|----------|-------------|
| `AGENCY_PI_INJECT_EXT` | Path to pi-inject extension |
| `AGENCY_PI_STATUS_EXT` | Path to pi-status extension |
| `AGENCY_PI_NOFILLS_EXT` | Path to no-frills extension |

### no-frills Commands

| Command | Description |
|---------|-------------|
| `/deco` | Interactive settings UI |
| `/deco tools [full\|borderless\|minimal]` | Tool box style |
| `/deco thinking [on\|off]` | Toggle thinking blocks |
| `/deco working [on\|off]` | Toggle working indicator |
| `/deco footer [on\|off]` | Toggle footer |
| `/deco header [on\|off]` | Toggle header |

### no-frills Environment Variables

| Variable | Values | Description |
|----------|--------|-------------|
| `PI_NOFILLS_TOOLS` | `full`, `borderless`, `minimal` | Tool box style |
| `PI_NOFILLS_THINKING` | `1`, `0`, `true`, `false` | Hide thinking |
| `PI_NOFILLS_WORKING` | `1`, `0`, `true`, `false` | Hide spinner |
| `PI_NOFILLS_FOOTER` | `1`, `0`, `true`, `false` | Hide footer |
| `PI_NOFILLS_HEADER` | `1`, `0`, `true`, `false` | Hide header |

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
