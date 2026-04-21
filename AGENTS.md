# Agency - Agent Configuration

## Overview

Simple tmux-based AI agent session manager. Single Python script, no external dependencies beyond tmux.

## Commands

| Command | Description |
|---------|-------------|
| `python3 agency.py init` | Create config skeleton in `~/.config/agency/` |
| `python3 agency.py start <name> --dir <path>` | Start agent in session |
| `python3 agency.py list` | List sessions with windows |
| `python3 agency.py send <session> <agent> <msg>` | Send message |
| `python3 agency.py stop <session>[:agent]` | Graceful shutdown |
| `python3 agency.py kill <session>[:agent]` | Force kill |
| `python3 agency.py kill-all` | Kill all agency sessions |

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

## Development

```bash
# Run tests
./test_agency.sh

# Test with mock agent
AGENCY_AGENT_CMD="python3 mock_agent.py" python3 agency.py start test --dir /tmp

# Manual tmux debugging
tmux list-sessions
tmux list-windows -t <session>
tmux capture-pane -t <session>:<window> -p
```

## Testing

- `test_agency.sh` - Integration tests (9 tests)
- `mock_agent.py` - Mock pi for testing
- `generate_agent_script.py` - Helper for agent launch scripts

## Structure

```
agency/
├── agency.py                   # Main CLI
├── generate_agent_script.py     # Agent script generator
├── mock_agent.py              # Mock agent for testing
├── test_agency.sh             # Test suite
├── README.md                   # User documentation
└── ~/.config/agency/          # Config directory
    ├── agents/                # Agent YAML configs
    └── sessions/              # Session scripts & state
```

## Boundaries

**ALWAYS**
- Run `./test_agency.sh` before committing
- Use `python3 agency.py` not `./agency`
- Clean up tmux sessions after tests

**USUALLY**
- Test with mock_agent before real pi
- Verify tmux sessions are gone after tests

**NEVER**
- Commit with untested changes
- Leave running tmux sessions
