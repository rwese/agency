# Agency

> Simple tmux-based AI agent session manager.

A lightweight bash script that manages AI agent sessions in tmux, providing persistent memory and simple CLI commands.

## Features

- **Persistent Memory**: Each agent maintains a memory file across sessions
- **Simple CLI**: Start, send messages, list, stop, and kill agents
- **Graceful Shutdown**: Agents receive shutdown prompts to save state before exit
- **Session Management**: Named sessions with timestamps for easy tracking
- **No Dependencies**: Just needs `tmux` and `bash`

## Installation

```bash
# Clone or copy to ~/.local/bin/
cp agency ~/.local/bin/
chmod +x ~/.local/bin/agency

# Source completions (add to ~/.bashrc or ~/.zshrc)
source /path/to/completions/bash
```

## Configuration

Initialize the config directory:

```bash
agency init
```

This creates `~/.config/agency/agents/` with an example config.

### Agent Config (`~/.config/agency/agents/<name>.yaml`)

```yaml
name: coder
memory_file: ~/.agency/memory/coder.md
source_dir: ~/.agency/agents/coder
storage_dir: ~/.agency/storage/coder
working_dir: ~/projects/myapp
```

## Usage

```bash
# Initialize (first time only)
agency init

# Start an agent
agency start coder
agency start coder --dir ~/projects/myapp

# Send a message to a running agent
agency send coder dark-wolf "Fix the authentication bug"

# List running sessions
agency list

# Graceful shutdown (sends shutdown prompt, waits up to 30s)
agency stop coder dark-wolf

# Force kill
agency kill coder dark-wolf
agency kill-all
```

## Commands

| Command | Description |
|---------|-------------|
| `agency init` | Create config skeleton |
| `agency start <name> [--dir <path>]` | Start agent in tmux |
| `agency send <session> <msg>` | Send message to session |
| `agency list` | List running sessions |
| `agency stop <session>` | Graceful shutdown (30s timeout) |
| `agency kill <session>` | Force kill session |
| `agency kill-all` | Kill all agency sessions |

## Session Names

Sessions are named: `{prefix}{agent-name}-{word1}-{word2}`

Example: `agency-coder-dark-wolf`

- Prefix: `agency-`
- Agent name: from config
- Word pair: high-entropy 1-token words (59 words, 3481 combinations)

## Requirements

- `tmux` >= 1.8
- `bash` >= 4.0
- Optional: `yq` for YAML config parsing

## License

MIT
