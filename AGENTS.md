# Agency - Agent Configuration

Simple tmux-based AI agent session manager. Built with uv.

## Quick Start

```bash
# Install
uv pip install -e .

# Initialize config
agency init

# Start an agent
agency start coder --dir ~/projects/myapp

# List sessions
agency list
```

## Commands

| Command | Description |
|---------|-------------|
| `agency init [--global\|--local]` | Interactive init (or specify scope) |
| `agency start <name> --dir <path>` | Start agent in project session |
| `agency start-manager <name> --dir <path>` | Start manager (orchestrator) |
| `agency list` | List sessions and windows |
| `agency list-managers` | List available manager configs |
| `agency send <session> [agent] <msg>` | Send message to agent |
| `agency attach <session> [agent]` | Attach to tmux session |
| `agency attach-manager <name>` | Attach to manager session |
| `agency stop <session>[:agent]` | Stop gracefully (30s timeout) |
| `agency stop-manager <name>` | Stop a manager gracefully |
| `agency tui` | Launch terminal user interface |
| `agency kill-all` | Kill all agency sessions |
| `agency tasks list\|show <id>` | Manage tracked tasks |

## Session Model

```
agency-        # Project session (shared by agents)
agency-manager- # Manager session (dedicated)
```

```
agency start coder --dir ~/projects/api   # Creates session "api", window "coder"
agency start tester --dir ~/projects/api  # Adds window "tester" to session "api"
agency start coder --dir ~/projects/api  # ERROR: coder exists
```

## Configuration

### Init Options

```bash
# Interactive (prompts for scope, agents, managers)
agency init

# Non-interactive global init
agency init --global

# Local project init (in git root's .agency/)
agency init --local

# Custom directory (implies --local)
agency init --dir ~/projects/myapp

# Overwrite existing
agency init --global --force
```

### Local Configuration

Projects can have `.agency/` directory with local configs:

```
.agency/
├── agents/         # Project-specific agents
├── managers/       # Project-specific managers
└── README.md
```

Benefits:
- **Version controlled**: Share agent setup with team
- **Self-contained**: Clone and run agents immediately
- **Portable**: Works across machines

### Global Configuration

**Agents**: `~/.config/agency/agents/<name>.yaml`
```yaml
name: coder
personality: |
  You are a senior Python developer.
```

**Managers**: `~/.config/agency/managers/<name>.yaml`
```yaml
name: coordinator
description: Reviews tasks and delegates to agents.
badge: "[MGR]"           # Optional: tmux window prefix
badge_color: brightblue  # Optional: tmux status color
personality: |
  You are a project coordinator...
```

## Development

```bash
# Install
uv pip install -e .

# Test
./test_agency.sh
uv run pytest

# Debug tmux
tmux -L agency list-sessions
tmux -L agency list-windows -t <session>

# Test with mock agent
AGENCY_AGENT_CMD="python3 src/agency/mock_agent.py" uv run agency start test --dir /tmp
AGENCY_AGENT_CMD="python3 src/agency/mock_agent.py" uv run agency start-manager coordinator --dir /tmp
```

**Just recipes:**
```bash
just install     # Install package
just test       # Run tests
just lint       # Run ruff
just clean      # Clean build artifacts
just reset      # Reset ~/.config/agency
```

## Project Structure

```
agency/
├── src/agency/
│   ├── __init__.py
│   ├── __main__.py      # CLI entry (agency)
│   ├── generate_agent_script.py
│   ├── mock_agent.py
│   └── agents/          # Example configs
├── test_agency.sh
├── pyproject.toml
├── justfile
└── README.md
```

## Boundaries

**ALWAYS**
- Run `./test_agency.sh` before committing
- Use `uv run agency` or `agency` (after install)

**USUALLY**
- Test with mock_agent before real pi
- Verify tmux sessions are gone after tests

**NEVER**
- Commit with untested changes
- Leave running tmux sessions
