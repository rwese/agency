# Agency - Project Agent Configuration

## Overview

Simple tmux-based AI agent session manager. Single bash script, no dependencies beyond tmux/bash.

## Architecture

```
agency/
├── agency              # Main entry point
├── agents/            # YAML configs per agent
└── completions/       # Shell completions
```

## Commands

| Command | Description |
|---------|-------------|
| `agency init` | Create config skeleton in ~/.agency/ |
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

`{agent-name}-{timestamp}` e.g., `coder-20260420-1430`

## Quality Gates

- [x] ShellCheck: zero errors
- [x] shfmt: consistent formatting
- [x] .editorconfig: consistent whitespace
