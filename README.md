# Agency - AI Agent Session Manager

A Python-based tmux session manager for AI agents. Each agent runs in its own tmux window within a project-based session.

## Quick Start

```bash
# Install with uv
uv pip install -e .

# Or run directly without install
uv run agency --help

# Initialize config
agency init

# Create an agent config
cat > ~/.config/agency/agents/myagent.yaml <<EOF
name: myagent
personality: |
  Your agent's personality description
EOF

# Start an agent
agency start myagent --dir ~/projects/myapp

# List running agents
agency list

# Send a message
agency send myapp myagent "Hello!"

# Stop gracefully
agency stop myapp:myagent

# Kill all sessions
agency kill-all
```

## Installation

### Using uv (recommended)

```bash
# Install in editable mode for development
uv pip install -e .

# Install for production use
uv pip install .
```

### Using pip

```bash
pip install .
```

### Run without installing

```bash
uv run agency <command>
```

## Session Model

- **Session** = One per project/directory (based on directory basename)
- **Window** = One per agent
- **Rule**: Unique agent names within a session

Example:
```bash
agency start coder --dir ~/projects/api     # Creates session "api", window "coder"
agency start tester --dir ~/projects/api     # Adds window "tester" to session "api"
agency start coder --dir ~/projects/api     # ERROR: "coder" already exists
```

## Manager Mode

Managers are specialized agents that orchestrate other agents. They:
- Monitor all agency sessions and agents
- Review incoming tasks and delegate to appropriate agents
- Track task IDs for requesting parties
- Coordinate multi-agent workflows

```bash
# List available managers
agency list-managers

# Start a manager (creates dedicated session)
agency start-manager coordinator --dir ~/projects/myapp

# List manager sessions
agency list

# Attach to a manager
agency attach-manager coordinator

# Stop a manager
agency stop-manager coordinator
```

### Manager Responsibilities

When a manager receives a task not addressed to a specific agent:
1. Assigns a task ID (returned to requesting party)
2. Delegates to appropriate agent using `agency send`
3. Tracks task status
4. Reports back when complete

## Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize config directory (creates agents/ and managers/) |
| `start <name> --dir <path>` | Start agent in project session |
| `start-manager <name> --dir <path>` | Start manager in dedicated session |
| `list` | List all running sessions and windows |
| `list-managers` | List available manager configurations |
| `send <session> [agent] <msg>` | Send message to agent |
| `attach <session> [agent]` | Attach to tmux session |
| `attach-manager <name>` | Attach to manager session |
| `stop <session>[:agent]` | Stop gracefully (30s timeout) |
| `stop-manager <name>` | Stop a manager gracefully |
| `kill <session>[:agent]` | Force kill immediately |
| `kill-all` | Kill all agency sessions |
| `tasks list` | List all tracked tasks |
| `tasks show <task_id>` | Show task details |
| `completions <shell>` | Print shell completion script (bash/zsh/fish) |

## Configuration

### Agent Configs
Stored in `~/.config/agency/agents/`:

```yaml
name: myagent
personality: |
  Your personality description.
  Can be multi-line.
```

### Manager Configs
Stored in `~/.config/agency/managers/`:

```yaml
name: coordinator
description: |
  A project coordinator that reviews tasks and delegates to agents.
badge: "[MGR]"           # Optional: prefix in tmux window name
badge_color: brightblue  # Optional: tmux status bar color
personality: |
  You are a project coordinator. Your role is to:
  - Monitor all agency sessions with `agency list`
  - Delegate tasks to appropriate agents
  - Track task IDs for requesting parties
  - Report task status back to stakeholders
```

**Badge Options:**
- `badge`: Text prefix shown in tmux window name (e.g., `"[MGR]"`, `"★"`, `"👑"`)
- `badge_color`: Color for tmux status bar highlighting:
  - Bright: `brightblue`, `brightgreen`, `brightred`, `brightyellow`, `brightmagenta`, `brightcyan`, `brightwhite`
  - Standard: `blue`, `green`, `red`, `yellow`, `magenta`, `cyan`, `white`

### Task Tracking
Tasks are stored in `~/.config/agency/sessions/tasks.json`:

```json
{
  "A1B2C3D4": {
    "task_id": "A1B2C3D4",
    "description": "Implement user auth",
    "status": "in_progress",
    "assigned_to": "coder",
    "created_at": "2024-01-15T10:30:00",
    "completed_at": null,
    "result": null
  }
}
```

## Environment Variables

- `AGENCY_AGENT_CMD` - Override the agent command (default: `pi`)
- `XDG_CONFIG_HOME` - Config directory (default: `~/.config`)

## Agent Configuration

Agents are automatically configured for clean operation:

- **Quiet startup**: `~/.config/agency/sessions/.pi/settings.json` with `quietStartup: true`
- **Clean persona**: Uses `--no-context-files` to skip AGENTS.md/CLAUDE.md loading
- **Session isolation**: Each agent stores session data in `~/.config/agency/sessions/`
- **Manager mode**: Sets `PI_AGENCY_MANAGER=true` for manager agents

## Project Structure

```
agency/
├── src/agency/            # Source package
│   ├── __init__.py       # Package init with version
│   ├── __main__.py       # CLI entry point
│   ├── generate_agent_script.py  # Script generator
│   ├── mock_agent.py     # Mock for testing
│   └── agents/           # Example agent configs
├── README.md
├── AGENTS.md             # Developer documentation
├── pyproject.toml        # uv/pip project config
├── test_agency.sh        # Integration tests
└── completions/          # Shell completions
```

## Shell Completions

Smart shell completions for bash, zsh, and fish.

### Quick Install

```bash
# Print and install bash completions
agency completions bash >> ~/.bashrc

# Print and install zsh completions
agency completions zsh >> ~/.zshrc

# Print and install fish completions
agency completions fish > ~/.config/fish/completions/agency.fish
```

### Manual Install

#### Bash

```bash
# Source in .bashrc or .profile
source /path/to/agency/completions/bash

# Or install system-wide
sudo cp completions/bash /usr/local/etc/bash_completion.d/agency
```

### Zsh

```bash
# Add to .zshrc
fpath=(~/path/to/agency/completions/zsh $fpath)
autoload -Uz _agency
compdef _agency agency

# Or copy completion file
cp completions/zsh ~/.config/zsh/completions/_agency
```

### Fish

```bash
# Copy completion file
cp completions/fish ~/.config/fish/completions/agency.fish
```

### Just Recipes

```bash
just completions-bash     # Install bash completions
just completions-zsh      # Install zsh completions  
just completions-fish     # Install fish completions
just completions          # Install all
```

## Testing

```bash
# Run test suite
uv run pytest

# Or use the test script
./test_agency.sh
```

## Architecture

- `agency/__main__.py` - Main CLI and session management
- `agency/generate_agent_script.py` - Helper for agent launch scripts
- `agency/mock_agent.py` - Mock agent for testing

## Session Types

| Prefix | Type | Purpose |
|--------|------|---------|
| `agency-` | Project | Shared by multiple agents working on same project |
| `agency-manager-` | Manager | Dedicated session for orchestration/coordination |
