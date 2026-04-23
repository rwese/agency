# Agency CLI Reference

## Templates

| Command | Description |
|---------|-------------|
| `agency templates` | List available templates |
| `agency init --dir <path>` | Create project with basic template |
| `agency init --dir <path> --template api` | Use specific template |
| `agency init --dir <path> --template fullstack` | Use fullstack template |
| `agency init --dir <path> --force` | Overwrite existing |
| `agency init --template https://github.com/user/repo/tree/main/my-template` | From GitHub |

## Session Management

| Command | Description |
|---------|-------------|
| `agency session start` | Start manager + all agents |
| `agency session stop` | Stop gracefully |
| `agency session attach` | Attach to session tmux |
| `agency session list` | List running sessions |
| `agency session members` | Show manager + agents status |
| `agency session windows list` | List windows |
| `agency session windows send <win> <text>` | Send keys |
| `agency session windows run <win> <cmd>` | Run command |

## Task Management

| Command | Description |
|---------|-------------|
| `agency tasks add -d "..."` | Create task |
| `agency tasks list` | List tasks |
| `agency tasks show <id>` | Show task details |
| `agency tasks assign <id> <agent>` | Assign to agent |
| `agency tasks complete <id> --result "..."` | Mark complete |
| `agency tasks history` | Show completed tasks |

## Heartbeat

| Command | Description |
|---------|-------------|
| `agency heartbeat status` | Check heartbeat status |
| `agency heartbeat start --role manager` | Start as manager |
| `agency heartbeat stop` | Stop heartbeat |

## tmux Keybindings (when attached)

| Binding | Action |
|---------|--------|
| `Ctrl+B D` | Detach from session |
| `Ctrl+B 0` | Switch to window 0 (manager) |
| `Ctrl+B 1` | Switch to window 1 |
| `Ctrl+B 2` | Switch to window 2 |
| `Ctrl+B L` | Last window |
| `Ctrl+B :` | Command mode |

## Available Templates

| Template | Use Case |
|----------|----------|
| `basic` | Single coder agent (default) |
| `api` | Backend + frontend agents |
| `fullstack` | Backend + frontend + devops |
