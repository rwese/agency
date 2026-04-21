# Agency - AI Agent Session Manager

A Python-based tmux session manager for AI agents. Each agent runs in its own tmux window within a project-based session.

## Quick Start

```bash
# Initialize config
python3 agency.py init

# Create an agent config
cat > ~/.config/agency/agents/myagent.yaml <<EOF
name: myagent
personality: |
  Your agent's personality description
EOF

# Start an agent
python3 agency.py start myagent --dir ~/projects/myapp

# List running agents
python3 agency.py list

# Send a message
python3 agency.py send myapp myagent "Hello!"

# Stop gracefully
python3 agency.py stop myapp:myagent

# Kill session
python3 agency.py kill-all
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

## Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize config directory |
| `start <name> --dir <path>` | Start agent in session |
| `list` | List all sessions and windows |
| `send <session> [agent] <msg>` | Send message to agent |
| `attach <session> [agent]` | Attach to tmux session |
| `stop <session>[:agent]` | Stop gracefully (30s timeout) |
| `kill <session>[:agent]` | Force kill immediately |
| `kill-all` | Kill all agency sessions |

## Configuration

Agent configs are stored in `~/.config/agency/agents/`:

```yaml
name: myagent
personality: |
  Your personality description.
  Can be multi-line.
```

## Environment Variables

- `AGENCY_AGENT_CMD` - Override the agent command (default: `pi`)
- `XDG_CONFIG_HOME` - Config directory (default: `~/.config`)

## Agent Configuration

Agents are automatically configured for clean operation:

- **Quiet startup**: `~/.config/agency/sessions/.pi/settings.json` with `quietStartup: true`
- **Clean persona**: Uses `--no-context-files` to skip AGENTS.md/CLAUDE.md loading
- **Session isolation**: Each agent stores session data in `~/.config/agency/sessions/`

## Installation

```bash
# Run directly
python3 agency.py --help

# Or symlink
ln -s $(pwd)/agency.py /usr/local/bin/agency
chmod +x agency.py
```

## Testing

```bash
./test_agency.sh
```

## Architecture

- `agency.py` - Main CLI and session management
- `generate_agent_script.py` - Helper for agent launch scripts
- `mock_agent.py` - Mock agent for testing
