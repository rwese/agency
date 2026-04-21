# Agency - Agent Configuration

## Overview

Simple tmux-based AI agent session manager. Built with uv.

## Installation

```bash
# Install for development
uv pip install -e .

# Run without install
uv run agency <command>
```

## Commands

| Command | Description |
|---------|-------------|
| `agency init` | Create config skeleton in `~/.config/agency/` |
| `agency start <name> --dir <path>` | Start agent in session |
| `agency start-manager <name> --dir <path>` | Start manager (orchestrator) |
| `agency list` | List sessions with windows |
| `agency list-managers` | List available manager roles |
| `agency send <session> <agent> <msg>` | Send message |
| `agency stop <session>[:agent]` | Graceful shutdown |
| `agency stop-manager <name>` | Stop a manager |
| `agency kill <session>[:agent]` | Force kill |
| `agency kill-all` | Kill all agency sessions |
| `agency attach-manager <name>` | Attach to manager session |
| `agency tasks list` | List tracked tasks |
| `agency tasks show <id>` | Show task details |

## Session Model

- **Session** = one per project/directory (`agency-{basename}`)
- **Window** = one per agent
- **Rule** = unique agent names within session

```
agency start coder --dir ~/projects/api  # Creates session "api", window "coder"
agency start tester --dir ~/projects/api # Adds window "tester" to "api"
agency start coder --dir ~/projects/api  # ERROR: coder exists
```

## Configuration

YAML files in `~/.config/agency/agents/`:

```yaml
name: the-dude
personality: |
  Like The Dude from The Big Lebowski. Laid back.
```

YAML files in `~/.config/agency/managers/`:

```yaml
name: coordinator
description: |-
  Reviews tasks and delegates to agents.
badge: "[MGR]"           # Optional: prefix in tmux window name
badge_color: brightblue   # Optional: tmux status bar color
personality: |
  You are a project coordinator. Use `agency list` to monitor sessions.
  Delegate with `agency send <session> <agent> <task>`.
  Track task IDs for requesting parties.
```

**Badge Options:**
- `badge`: Text prefix (e.g., `"[MGR]"`, `"★"`, `"👑"`)
- `badge_color`: tmux color - `brightblue`, `brightgreen`, `brightred`, `brightyellow`, `brightmagenta`, `brightcyan`, `brightwhite`, or standard colors

## Manager Mode

Managers orchestrate agents:
- `start-manager` creates dedicated session (`agency-manager-<name>`)
- Manager monitors all sessions via `agency list`
- Manager delegates to agents via `agency send`
- Task IDs track delegation (return to requesting party)

```bash
# Start a manager
agency start-manager coordinator --dir ~/projects/myapp

# Manager uses CLI to:
# - agency list (see all sessions/agents)
# - agency start coder --dir ~/projects/myapp (create agent)
# - agency send myapp coder "implement X" (delegate)
```

## Development

```bash
# Install in editable mode
uv pip install -e .

# Run tests
uv run pytest

# Or use the test script
./test_agency.sh

# Test with mock agent
AGENCY_AGENT_CMD="python3 mock_agent.py" uv run agency start test --dir /tmp

# Test manager mode
AGENCY_AGENT_CMD="python3 mock_agent.py" uv run agency start-manager coordinator --dir /tmp

# Manual tmux debugging
tmux -L agency list-sessions
tmux -L agency list-windows -t <session>
tmux -L agency capture-pane -t <session>:<window> -p
```

## Testing

- `test_agency.sh` - Integration tests (9 tests)
- `uv run pytest` - Run test suite

## Project Structure

```
agency/
├── src/agency/               # Source package
│   ├── __init__.py          # Package init with version
│   ├── __main__.py          # CLI entry point (agency)
│   ├── generate_agent_script.py  # Agent launch script generator
│   └── mock_agent.py        # Mock pi for testing
├── test_agency.sh           # Integration tests
├── README.md                 # User documentation
├── AGENTS.md                 # This file
├── pyproject.toml            # uv project config
└── ~/.config/agency/        # Config directory
    ├── agents/              # Agent YAML configs
    ├── managers/            # Manager YAML configs
    └── sessions/            # Session scripts, state, tasks.json
```

## Boundaries

**ALWAYS**
- Run tests before committing
- Use `uv run agency` or `agency` (after install)
- Clean up tmux sessions after tests

**USUALLY**
- Test with mock_agent before real pi
- Verify tmux sessions are gone after tests

**NEVER**
- Commit with untested changes
- Leave running tmux sessions
