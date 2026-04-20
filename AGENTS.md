# Agency - Project Agent Configuration

## Overview

Simple tmux-based AI agent session manager. Single bash script, no dependencies beyond tmux/bash.

## Architecture

```
agency/
├── agency              # Main entry point (10KB)
├── agents/             # YAML configs per agent
├── completions/        # Shell completions
├── mock_agent.py       # Test mock for development
└── test_agency.sh      # Test suite (11 tests)
```

## Commands

| Command | Description |
|---------|-------------|
| `agency init` | Create config skeleton in ~/.config/agency/ |
| `agency start <name> [--dir <path>]` | Start agent in tmux |
| `agency send <session> <msg>` | Send message to running session |
| `agency list` | List running sessions |
| `agency stop <session>` | Graceful shutdown (30s timeout) |
| `agency kill <session>` | Force kill session |
| `agency kill-all` | Kill all agency sessions |

## Config Schema

```yaml
name: <agent-name>
memory_file: <path-to-memory-file>
source_dir: <path-to-source-directory>
storage_dir: <path-to-storage-directory>
```

## Session Naming

`{agent}-{word1}-{word2}` e.g., `coder-dark-wolf`

- 59 curated 1-token words
- 3,481 unique combinations
- Set AGENCY_AGENT_CMD env var to override default `pi` command

## Development

```bash
./test_agency.sh          # Run test suite
AGENCY_AGENT_CMD="python3 mock_agent.py" ./agency start test  # Test with mock
shellcheck -S error agency  # Lint check
```

## Quality Gates

- [x] ShellCheck: zero errors
- [x] Tests: 11/11 passing
- [x] .editorconfig: consistent whitespace
