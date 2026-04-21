# Agency - Completed ✅

## All Tasks Done

- [x] Research pi arguments for quiet startup
- [x] Research pi arguments for proper persona bootstrapping  
- [x] Validate lifecycle and shutdown
- [x] Add `attach` command to enter agency tmux session
- [x] Add manager role system with `start-manager` command
- [x] Add `managers/` directory for manager configurations
- [x] Add task tracking system with `tasks` command
- [x] Add manager-specific CLI commands (attach-manager, stop-manager, list-managers)
- [x] Add configurable manager badges (badge, badge_color) for tmux visibility
- [x] Convert to uv pyproject.toml structure

---

## What Was Implemented

### 1. Quiet Startup
- Creates `~/.config/agency/sessions/.pi/settings.json` with:
  - `quietStartup: true`
  - `collapseChangelog: true`
  - Empty packages/extensions/skills/prompts/themes
- Note: pi looks for settings in CWD, not session-dir

### 2. Persona Bootstrapping
- Uses `--no-context-files` to skip AGENTS.md/CLAUDE.md
- Uses `--append-system-prompt` with personality text
- Sets `PI_CODING_AGENT=true` for agent mode

### 3. Lifecycle & Shutdown
- `stop` sends shutdown message, waits up to 30s
- Falls back to force kill if agent doesn't exit
- `kill` force kills immediately

### 4. Attach Command
- `agency attach <session>` - attach to session
- `agency attach <session> <agent>` - attach and switch to window
- Uses `tmux attach-session -t session`

### 5. Manager Role System

#### New Directories
- `~/.config/agency/managers/` - Manager YAML configs

#### New Commands
| Command | Description |
|---------|-------------|
| `start-manager <name> --dir <path>` | Start manager in dedicated session |
| `list-managers` | List available manager configs |
| `attach-manager <name>` | Attach to manager session |
| `stop-manager <name>` | Stop a manager gracefully |
| `tasks list` | List all tracked tasks |
| `tasks show <id>` | Show task details |

#### Session Types
- **Project sessions**: `agency-<project>` - shared by agents
- **Manager sessions**: `agency-manager-<name>` - dedicated to orchestration

#### Manager Capabilities
- Monitor all sessions via `agency list`
- Create agents via `agency start <name> --dir <path>`
- Delegate tasks via `agency send <session> <agent> <task>`
- Track task IDs for requesting parties
- Task data stored in `~/.config/agency/sessions/tasks.json`

#### Environment Variables for Managers
- `PI_AGENCY_MANAGER=true` - Signals manager mode
- `PI_AGENCY_MANAGER_NAME=<name>` - Manager's configured name

#### Manager Badges
- Configurable `badge` field adds prefix to tmux window name (e.g., `"[MGR]"`, `"★"`)
- Configurable `badge_color` sets tmux status bar highlighting (brightblue default)
- Makes managers easily identifiable in tmux window list and status bar

### 6. uv Packaging
- `pyproject.toml` with hatchling build backend
- Entry point: `agency = "agency.__main__:main"`
- `justfile` for common development commands
- `.gitignore` for venv and build artifacts
- `src/agency/` package structure
