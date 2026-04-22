# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-04-22

### Added

#### Task Dependencies
- **Dependency field**: Tasks can depend on other tasks via `depends_on`
- **Dependency management**: `tasks depends <id> [--add|--remove|--set] <deps...>`
- **Blocking logic**: Tasks blocked until all dependencies are completed
- **Circular detection**: Prevents circular dependency chains
- **Agent filtering**: Agents only see unblocked tasks
- **Manager visibility**: `--include-blocked` flag to see all tasks

## [2.0.0] - 2026-04-21

### Added

#### Project-Centric Model
- **Single project session**: All entities (manager + agents) in one tmux session
- **Per-project sockets**: `tmux -L agency-<project>` for isolation
- **Local config**: `.agency/` directory at git root, version controlled

#### Task System v2
- **Word-based task IDs**: `swift-bear-a3f2` format using eff.org wordlist
- **Versioned schema**: `tasks.json` v2 with explicit schema version
- **Task directories**: `.agency/tasks/<id>/task.json` + `result.json`
- **Pending workflow**: Manager approval for task completions
- **Rejection flow**: Agent revises and resubmits rejected tasks
- **Priority levels**: `low`, `normal`, `high`
- **Agent task filtering**: Auto-filters to agent's tasks when `AGENCY_AGENT` is set

#### Template System
- **GitHub templates**: Download from any GitHub repository
- **Template caching**: `~/.cache/agency/templates/`
- **Subdirectory support**: `--template https://github.com/user/repo/tree/main/.agency-templates/basic`
- **Refresh flag**: `--refresh` to bypass cache

#### Halt/Resume
- **Halt detection**: `.halted` file + session/window rename
- **Graceful resume**: Manager restarts with `AGENCY_RESUMING=true`
- **Pending preservation**: Incomplete tasks preserved across resume

#### Manager Capabilities
- **Task broker**: Creates, assigns, and reviews tasks
- **Health monitoring**: Polls for agent status
- **Approval workflow**: Reviews pending completions
- **Configurable polling**: `poll_interval` in `manager.yaml`

### Changed

#### CLI Overhaul
- **`init-project` replaces `init`**: Creates session + `.agency/` in one command
- **`start` for all**: Both agents and managers started via `start`
- **`stop` handles all**: Single command stops entire session
- **Markdown output**: Tasks listed in Markdown format
- **JSON errors**: `--json` flag for machine-readable errors

#### Configuration
- **YAML configs**: `config.yaml`, `manager.yaml`, `agents.yaml`
- **Personality files**: `personality.md` referenced from config
- **Extended schemas**: Configurable poll intervals, auto-approve, max retries

#### Task Lifecycle
- **Atomic moves**: `os.rename()` for pending completions
- **File locking**: `filelock.FileLock` for `tasks.json`
- **Result artifacts**: `{files, diff, summary}` in result.json

### Removed

- **TUI**: Terminal UI removed, CLI only
- **Global config**: No `~/.config/agency/` for project configs
- **Legacy session model**: No separate `agency-manager-*` sessions
- **Numeric task IDs**: `TASK001` replaced with word-based IDs
- **`init --global`**: Templates in cache instead
- **`init --local`**: Replaced by `init-project`
- **`stop-manager`**: Integrated into `stop`

### Fixed

- **Race conditions**: Atomic file operations for pending completions
- **Agent discovery**: Config-based registry instead of tmux polling
- **Session isolation**: Per-project tmux sockets

### Dependencies

- Added: `filelock>=3.13.0`
- Added: `requests>=2.31.0`
- Added: `rich>=13.0.0`
- Removed: `textual>=8.2.4` (TUI)

---

## [0.3.0] - 2024

### Added
- TUI for monitoring sessions and tasks
- Task tracking with JSON persistence
- Shell completions for bash, zsh, fish
- Manager sessions with badge styling
- Mock agent for testing

### Changed
- Session naming: `agency-<project>` pattern
- Window naming with word suffixes
- `stop` with graceful shutdown timeout

---

## [0.2.0] - 2024

### Added
- Agent configuration in YAML
- Manager configuration with personality
- `init --local` for project configs
- `init --global` for shared configs

### Changed
- Session model: Separate sessions per project
- Agent startup: Configurable personality

---

## [0.1.0] - 2024

### Added
- Initial release
- Basic tmux session management
- Agent start/stop/list
- Message passing via tmux send-keys
