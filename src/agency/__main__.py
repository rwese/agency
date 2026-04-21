#!/usr/bin/env python3
"""
Agency - AI Agent Session Manager

A Python-based tmux session manager for AI agents.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml
from agency.tui.app import run_tui

__version__ = "0.3.0"
VERSION = "0.3.0"

# Paths
AGENCY_DIR = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "agency"
AGENTS_DIR = AGENCY_DIR / "agents"
MANAGERS_DIR = AGENCY_DIR / "managers"
SESSIONS_DIR = AGENCY_DIR / "sessions"

# Local agency directory (in project/git root)
LOCAL_AGENCY_DIR = Path(".agency")
LOCAL_AGENTS_DIR = LOCAL_AGENCY_DIR / "agents"
LOCAL_MANAGERS_DIR = LOCAL_AGENCY_DIR / "managers"
TASKS_FILE = SESSIONS_DIR / "tasks.json"
SESSION_PREFIX = "agency-"
MANAGER_SESSION_PREFIX = "agency-manager-"

# Constants
STOP_TIMEOUT = 30
SHUTDOWN_MESSAGE = (
    "Please wrap up, save your memories to your memory file, then exit gracefully. "
    "Say 'Goodbye' when done."
)

# Wordlist for window name suffixes
WORDS = [
    "swift", "bold", "dark", "warm", "cool", "gray", "neon", "iron", "soft", "loud",
    "wolf", "fox", "bear", "hawk", "owl", "crow", "fish", "deer", "lynx", "crane",
    "frog", "toad", "hare", "mole", "seal", "goat", "jade", "kite", "link", "node",
    "orb", "pipe", "raft", "slug", "tank", "void", "wire", "atom", "base", "byte",
    "cache", "daemon", "ether", "fiber", "graph", "hash", "json", "kernel",
    "lambda", "module", "object", "parse", "query", "root", "socket", "thread",
    "unix", "vector", "worker", "proxy", "relay", "stream", "token",
]


@dataclass
class Agent:
    """Agent configuration."""
    name: str
    personality: Optional[str] = None


@dataclass
class Session:
    """Represents a tmux session with its windows."""
    name: str
    dir: str
    windows: list = field(default_factory=list)


@dataclass
class Task:
    """Represents a delegated task with tracking."""
    task_id: str
    description: str
    status: str  # pending, in_progress, completed, failed
    assigned_to: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[str] = None


def find_git_root(path: Path = Path.cwd()) -> Optional[Path]:
    """Find the git repository root containing the given path."""
    current = path.absolute()
    while current != current.parent:
        if (current / ".git").is_dir():
            return current
        current = current.parent
    return None


def is_interactive() -> bool:
    """Check if running in interactive terminal."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def load_tasks() -> dict[str, Task]:
    """Load tasks from JSON file."""
    if not TASKS_FILE.exists():
        return {}

    with open(TASKS_FILE) as f:
        data = json.load(f)

    return {
        tid: Task(**tdata) for tid, tdata in data.items()
    }


def save_tasks(tasks: dict[str, Task]) -> None:
    """Save tasks to JSON file."""
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        tid: {
            "task_id": t.task_id,
            "description": t.description,
            "status": t.status,
            "assigned_to": t.assigned_to,
            "created_at": t.created_at,
            "completed_at": t.completed_at,
            "result": t.result,
        }
        for tid, t in tasks.items()
    }
    with open(TASKS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def generate_task_id() -> str:
    """Generate a unique task ID (token for requesting party)."""
    import uuid
    return str(uuid.uuid4())[:8].upper()


def log_info(msg: str) -> None:
    print(f"[INFO] {msg}", file=sys.stderr)


def log_error(msg: str) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)


def get_agent_cmd() -> str:
    """Get the agent command to run."""
    return os.environ.get("AGENCY_AGENT_CMD", "pi")


# Tmux socket for isolation - uses separate server from user's tmux
TMUX_SOCKET = "agency"


def tmux(*args: str) -> subprocess.CompletedProcess:
    """Run a tmux command with agency socket."""
    result = subprocess.run(
        ["tmux", "-L", TMUX_SOCKET] + list(args),
        capture_output=True,
        text=True,
    )
    return result


def tmux_or_raise(*args: str) -> None:
    """Run tmux command, raise on error."""
    result = tmux(*args)
    if result.returncode != 0:
        log_error(f"tmux {' '.join(args)} failed: {result.stderr}")
        raise RuntimeError(f"tmux command failed: {result.stderr}")
    return result


def session_exists(session_name: str) -> bool:
    """Check if a tmux session exists."""
    result = tmux("has-session", "-t", session_name)
    return result.returncode == 0


def list_sessions() -> list[str]:
    """List all agency sessions."""
    result = tmux("list-sessions", "-F", "#S")
    if result.returncode != 0:
        return []
    sessions = []
    for line in result.stdout.strip().split("\n"):
        if line.startswith(SESSION_PREFIX):
            sessions.append(line)
    return sessions


def list_windows(session_name: str) -> list[str]:
    """List windows in a session (excluding zsh shell windows)."""
    result = tmux("list-windows", "-t", session_name, "-F", "#W")
    if result.returncode != 0:
        return []
    # Filter out zsh shell windows
    return [w.strip() for w in result.stdout.strip().split("\n") if w.strip() and w.strip() != "zsh"]


def window_exists(session_name: str, window_name: str) -> bool:
    """Check if a window exists in a session."""
    windows = list_windows(session_name)
    return window_name in windows


def make_session_name(work_dir: str) -> str:
    """Create session name from directory basename."""
    basename = Path(work_dir).name
    return f"{SESSION_PREFIX}{basename}"


def make_window_name(agent_name: str, session_name: str) -> str:
    """Create window name, adding suffix if conflict."""
    if window_exists(session_name, agent_name):
        import random
        suffix = random.choice(WORDS)
        return f"{agent_name}-{suffix}"
    return agent_name


def load_agent_config(agent_name: str) -> Optional[dict]:
    """Load agent configuration from YAML."""
    config_path = AGENTS_DIR / f"{agent_name}.yaml"
    if not config_path.exists():
        return None

    with open(config_path) as f:
        return yaml.safe_load(f)


def load_manager_config(manager_name: str) -> Optional[dict]:
    """Load manager configuration from YAML."""
    config_path = MANAGERS_DIR / f"{manager_name}.yaml"
    if not config_path.exists():
        return None

    with open(config_path) as f:
        return yaml.safe_load(f)


def list_available_managers() -> list[str]:
    """List available manager configurations."""
    if not MANAGERS_DIR.exists():
        return []

    managers = []
    for f in MANAGERS_DIR.glob("*.yaml"):
        managers.append(f.stem)
    return sorted(managers)


def create_quiet_settings() -> None:
    """Create .pi/settings.json with quiet startup for agency sessions."""
    pi_dir = SESSIONS_DIR / ".pi"
    pi_dir.mkdir(parents=True, exist_ok=True)
    settings_path = pi_dir / "settings.json"

    # Only create if doesn't exist
    if not settings_path.exists():
        settings = {
            "quietStartup": True,
            "collapseChangelog": True,
            "packages": [],
            "extensions": [],
            "skills": [],
            "prompts": [],
            "themes": []
        }
        with open(settings_path, 'w') as f:
            json.dump(settings, f, indent=2)


def generate_agent_script(
    session_name: str,
    window_name: str,
    agent_cmd: str,
    personality: Optional[str] = None,
) -> Path:
    """Generate and write the agent launch script."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    # Create quiet settings for agent sessions
    create_quiet_settings()

    script_path = SESSIONS_DIR / f"{session_name}-{window_name}.sh"

    agency_dir = Path(__file__).parent.absolute()

    # Build command with --no-context-files for clean persona
    # PI_CODING_AGENT=true signals agent mode
    base_cmd = f'{agent_cmd} --session-dir "{SESSIONS_DIR}" --no-context-files PI_CODING_AGENT=true'
    cmd = f'cd "{agency_dir}" && exec {base_cmd}'
    if personality:
        # Escape personality for shell
        escaped = personality.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("`", "\\`")
        cmd += f' --append-system-prompt "{escaped}"'

    with open(script_path, "w") as f:
        f.write("#!/bin/bash\n")
        f.write(f"{cmd}\n")

    script_path.chmod(0o755)
    return script_path


def send_keys(session_name: str, window_name: str, msg: str) -> None:
    """Send keys to a tmux window."""
    # Use -X to send raw characters
    tmux_or_raise("send-keys", "-t", f"{session_name}:{window_name}", msg, "Enter")


def cmd_init(
    global_init: bool = False,
    local_init: bool = False,
    custom_dir: Optional[str] = None,
    force: bool = False,
) -> None:
    """Initialize agency config directory."""
    interactive = is_interactive()

    # Determine init mode
    if custom_dir:
        local_init = True

    # Check for conflicting flags
    if global_init and local_init:
        log_error("Cannot use --global and --local together")
        sys.exit(1)

    # Auto-detect git root if in git repository and no flags specified
    git_root = find_git_root(Path.cwd())
    has_global_config = AGENCY_DIR.exists()

    # If interactive, show prompts
    if interactive:
        cmd_init_interactive(global_init, local_init, custom_dir, force, git_root, has_global_config)
        return

    # Non-interactive: require explicit flag
    if not global_init and not local_init:
        log_error("Non-interactive mode requires --global or --local flag")
        log_error("Run 'agency init' for interactive setup")
        log_error("Usage: agency init --global  OR  agency init --local")
        if git_root:
            log_info(f"Note: Current directory is inside git repository: {git_root}")
            log_info("Use 'agency init --local' to initialize project-local config")
        sys.exit(1)

    # Execute init based on mode
    if global_init or (not local_init and not custom_dir):
        cmd_init_global(force)

    if local_init or custom_dir:
        cmd_init_local(custom_dir, force)


def cmd_init_interactive(
    global_init: bool,
    local_init: bool,
    custom_dir: Optional[str],
    force: bool,
    git_root: Optional[Path],
    has_global_config: bool,
) -> None:
    """Interactive init with prompts."""
    print("=== Agency Setup ===\n")

    # Step 1: Determine scope
    print("Where should agency config be installed?")
    print("  [1] Global (~/.config/agency/) - Available to all projects")

    if git_root:
        print(f"  [2] Local ({git_root}/.agency/) - Only for this project")
        default_choice = "2"
    else:
        print("  [2] Local - Not available (not in git repository)")
        default_choice = "1"

    # Check for existing configs
    if not has_global_config:
        print("\n  (No existing global config found)")

    if custom_dir:
        print(f"\n  [3] Custom directory: {custom_dir}")
        default_choice = "3"

    # Get user choice
    choice_map = {"1": ("global", False), "2": ("local", True)}
    if custom_dir:
        choice_map["3"] = ("custom", custom_dir)

    choice = input(f"\nChoice [{default_choice}]: ").strip() or default_choice

    if choice == "3" and custom_dir:
        scope_type, is_local = "custom", True
    else:
        scope_type, is_local = choice_map.get(choice, ("global", False))

    # Step 2: Create sample agents?
    create_agents = input("\nCreate sample agent configs? [Y/n]: ").strip().lower() != "n"

    # Step 3: Create sample managers?
    create_managers = input("Create sample manager configs? [Y/n]: ").strip().lower() != "n"

    # Step 4: Check for existing config
    target_dir = None
    if scope_type == "global":
        target_dir = AGENCY_DIR
    elif scope_type == "local" and git_root:
        target_dir = git_root / LOCAL_AGENCY_DIR
    elif scope_type == "custom":
        target_dir = Path(custom_dir) / LOCAL_AGENCY_DIR

    if target_dir and target_dir.exists() and not force:
        print(f"\nWarning: {target_dir} already exists")
        overwrite = input("Overwrite? [y/N]: ").strip().lower() == "y"
        if not overwrite:
            print("Aborted.")
            return
        force = True

    # Execute init
    print()
    if scope_type == "global":
        cmd_init_global(force, create_agents, create_managers)
    else:
        dir_arg = str(target_dir.parent) if target_dir else custom_dir
        cmd_init_local(dir_arg, force, create_agents, create_managers)


def cmd_init_global(force: bool = False, create_agents: bool = True, create_managers: bool = True) -> None:
    """Initialize global config directory."""
    if AGENCY_DIR.exists() and not force:
        log_error(f"Global config already exists at {AGENCY_DIR}")
        log_error("Use --force to overwrite")
        sys.exit(1)

    AGENCY_DIR.mkdir(parents=True, exist_ok=True)
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    MANAGERS_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    if create_agents:
        _create_global_example_agent()

    if create_managers:
        _create_global_example_manager()

    log_info(f"Initialized global config in {AGENCY_DIR}")
    if create_agents:
        log_info(f"Created example agent config: {AGENTS_DIR / 'example.yaml'}")
    if create_managers:
        log_info(f"Created example manager config: {MANAGERS_DIR / 'coordinator.yaml'}")
    log_info("Edit configs and run: agency start-manager coordinator --dir ~/projects")


def _create_global_example_agent() -> None:
    """Create example agent config in global location."""
    example_config = AGENTS_DIR / "example.yaml"
    with open(example_config, "w") as f:
        f.write("""name: example
personality: |
  An example agent personality description.
  Modify this to customize how the agent behaves.
""")


def _create_global_example_manager() -> None:
    """Create example manager config in global location."""
    example_manager = MANAGERS_DIR / "coordinator.yaml"
    with open(example_manager, "w") as f:
        f.write("""name: coordinator
description: |-
  A project coordinator manager. Reviews incoming tasks and delegates
  to specialized agents. Tracks task progress and reports back.
badge: "[MGR]"
badge_color: brightblue
personality: |
  You are a project coordinator for an AI agent team. Your role is to:

  ## Monitoring
  - Use `agency list` to see all active sessions and their agents
  - Track which agents are available and their specialties

  ## Task Management
  - Review incoming tasks not addressed to specific agents
  - Assign tasks to appropriate agents using `agency send <session> <agent> <task>`
  - Generate unique task IDs using the task tracking system

  ## Task IDs
  - When delegating, create a task ID and track it
  - Return task IDs to requesting parties immediately
  - Use `agency tasks` to track task status

  ## Delegation
  - Match tasks to agents based on their personalities/specialties
  - Break large tasks into smaller, delegable pieces
  - Follow up on pending tasks

  ## Communication
  - Report task status to requesting parties
  - Provide clear updates on progress

# Badge options:
# badge: Text prefix shown in tmux window name (e.g., "[MGR]", "⭐")
# badge_color: Color for the tmux status bar:
#   brightblue, brightgreen, brightred, brightyellow, brightmagenta, brightcyan
#   Or standard colors: blue, green, red, yellow, magenta, cyan, white
""")


def cmd_init_local(base_dir: Optional[str] = None, force: bool = False, create_agents: bool = True, create_managers: bool = True) -> None:
    """Initialize local project config in .agency/ directory."""
    if base_dir:
        base_path = Path(base_dir).expanduser().absolute()
    else:
        base_path = Path.cwd()

    # Find git root if not specified
    git_root = find_git_root(base_path)
    if not git_root:
        log_error(f"Not in a git repository: {base_path}")
        log_error("Local init requires being inside a git repository")
        log_error("Use --global for non-git directories")
        sys.exit(1)

    local_dir = git_root / LOCAL_AGENCY_DIR
    local_agents = local_dir / "agents"
    local_managers = local_dir / "managers"

    if local_dir.exists() and not force:
        log_error(f"Local config already exists at {local_dir}")
        log_error("Use --force to overwrite")
        sys.exit(1)

    local_dir.mkdir(parents=True, exist_ok=True)
    local_agents.mkdir(parents=True, exist_ok=True)
    local_managers.mkdir(parents=True, exist_ok=True)

    if create_agents:
        _create_local_example_agent(local_agents)

    if create_managers:
        _create_local_example_manager(local_managers)

    _create_local_readme(local_dir)

    log_info(f"Initialized local config in {local_dir}")
    if create_agents:
        log_info(f"Created example agent config: {local_agents / 'example.yaml'}")
    if create_managers:
        log_info(f"Created example manager config: {local_managers / 'coordinator.yaml'}")
    log_info(f"Created README: {local_dir / 'README.md'}")
    log_info("Edit configs and run: agency start-manager coordinator --dir .")


def _create_local_example_agent(local_agents: Path) -> None:
    """Create example agent config in local directory."""
    example_config = local_agents / "example.yaml"
    with open(example_config, "w") as f:
        f.write("""name: example
personality: |
  An example agent personality for this project.
  Customize this to define your agent's behavior.
""")


def _create_local_example_manager(local_managers: Path) -> None:
    """Create example manager config in local directory."""
    example_manager = local_managers / "coordinator.yaml"
    with open(example_manager, "w") as f:
        f.write("""name: coordinator
description: |
  A project coordinator manager. Reviews tasks and delegates to agents.
badge: "[MGR]"
badge_color: brightblue
personality: |
  You are a project coordinator for this project's AI agent team.

  ## Responsibilities
  - Monitor agency sessions with `agency list`
  - Delegate tasks to appropriate agents
  - Track task IDs and report progress
""")


def _create_local_readme(local_dir: Path) -> None:
    """Create README.md in local agency directory."""
    readme_path = local_dir / "README.md"
    with open(readme_path, "w") as f:
        f.write("""# Agency - Local Configuration

This directory contains project-specific agency configuration.

## Structure

```
.agency/
├── agents/         # Agent configurations
│   └── example.yaml
├── managers/       # Manager configurations
│   └── coordinator.yaml
└── README.md       # This file
```

## Usage

```bash
# Start an agent
agency start example --dir .

# Start the coordinator manager
agency start-manager coordinator --dir .
```

## Notes

- Local configs take precedence over global configs
- This directory should be committed to version control
- See ~/.config/agency/ for global configuration
""")


def cmd_start_manager(manager_name: str, work_dir: str) -> str:
    """Start a manager in its own session."""
    if not manager_name:
        log_error("Manager name required")
        log_error("Usage: agency start-manager <name> --dir <path>")
        sys.exit(1)

    if not work_dir:
        log_error("Working directory required")
        log_error("Usage: agency start-manager <name> --dir <path>")
        sys.exit(1)

    # Expand tildes
    work_dir = os.path.expanduser(work_dir)

    # Create directory if needed
    Path(work_dir).mkdir(parents=True, exist_ok=True)

    # Load config
    config = load_manager_config(manager_name)
    if not config:
        log_error(f"Manager config not found: {MANAGERS_DIR / f'{manager_name}.yaml'}")
        log_error("Run 'agency init' first or create manager config")
        log_error("Use 'agency list-managers' to see available managers")
        sys.exit(1)

    personality = config.get("personality")
    badge = config.get("badge", "[MGR]")
    badge_color = config.get("badge_color", "brightblue")

    # Manager gets its own session (not shared with regular agents)
    session_name = f"{MANAGER_SESSION_PREFIX}{manager_name}"

    # Check if manager already running
    if session_exists(session_name):
        log_error(f"Manager '{manager_name}' already running in session '{session_name}'")
        log_error("Use 'agency attach-manager <name>' to attach")
        sys.exit(1)

    # Apply badge to window name if configured
    window_name = manager_name
    if badge:
        window_name = f"{badge} {manager_name}"

    # Get agent command
    agent_cmd = get_agent_cmd()

    # Generate launch script with manager-specific enhancements
    script_path = generate_manager_script(
        session_name, window_name, agent_cmd, personality, manager_name
    )

    # Create session with window
    tmux_or_raise("new-session", "-d", "-s", session_name, "-c", work_dir)
    tmux_or_raise("new-window", "-d", "-t", session_name, "-n", window_name, "-c", work_dir)

    # Apply manager badge styling if configured
    if badge_color:
        color_map = {
            "brightblue": "blue",
            "brightgreen": "green",
            "brightred": "red",
            "brightyellow": "yellow",
            "brightmagenta": "magenta",
            "brightcyan": "cyan",
            "brightwhite": "white",
            "blue": "blue",
            "green": "green",
            "red": "red",
            "yellow": "yellow",
            "magenta": "magenta",
            "cyan": "cyan",
            "white": "white",
        }
        tmux_color = color_map.get(badge_color, "blue")
        # Set window status style for this window
        tmux("set-window-option", "-t", f"{session_name}:{window_name}",
             "window-status-style", f"fg=black,bg={tmux_color},bold")
        tmux("set-window-option", "-t", f"{session_name}:{window_name}",
             "window-status-current-style", f"fg=black,bg={tmux_color},bold")

    log_info(f"Created manager session '{session_name}' with window '{window_name}'")

    # Send command to run manager
    send_keys(session_name, window_name, str(script_path))

    # Return session:window to stdout
    print(f"{session_name}:{window_name}")


def generate_manager_script(
    session_name: str,
    window_name: str,
    agent_cmd: str,
    personality: Optional[str] = None,
    manager_name: Optional[str] = None,
) -> Path:
    """Generate and write the manager launch script."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    # Create quiet settings for agency sessions
    create_quiet_settings()

    script_path = SESSIONS_DIR / f"{session_name}-{window_name}.sh"

    agency_dir = Path(__file__).parent.absolute()

    # Build command - managers get agency command wrappers
    base_cmd = f'{agent_cmd} --session-dir "{SESSIONS_DIR}" --no-context-files PI_CODING_AGENT=true PI_AGENCY_MANAGER=true'

    if manager_name:
        base_cmd += f' PI_AGENCY_MANAGER_NAME={manager_name}'

    cmd = f'cd "{agency_dir}" && exec {base_cmd}'

    if personality:
        escaped = personality.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("`", "\\`")
        cmd += f' --append-system-prompt "{escaped}"'

    with open(script_path, "w") as f:
        f.write("#!/bin/bash\n")
        f.write(f"{cmd}\n")

    script_path.chmod(0o755)
    return script_path


def cmd_list_managers() -> None:
    """List available manager configurations."""
    managers = list_available_managers()

    if not managers:
        log_info("No manager configs found")
        log_info(f"Create configs in: {MANAGERS_DIR}")
        log_info("Run 'agency init' to create example manager config")
        return

    for mgr in managers:
        config = load_manager_config(mgr)
        desc = config.get("description", "No description") if config else ""
        print(f"{mgr:<20} {desc}")


def cmd_list_manager_sessions() -> None:
    """List running manager sessions."""
    sessions = list_sessions()
    managers_running = [s for s in sessions if s.startswith(MANAGER_SESSION_PREFIX)]

    if not managers_running:
        log_info("No manager sessions running")
        return

    for session in managers_running:
        windows = list_windows(session)
        windows_str = ",".join(windows)
        print(f"{session:<25} [{windows_str}]")


def cmd_attach_manager(manager_name: str) -> None:
    """Attach to a manager session."""
    session_name = f"{MANAGER_SESSION_PREFIX}{manager_name}"

    if not session_exists(session_name):
        log_error(f"Manager session not found: {session_name}")
        log_error("Run 'agency start-manager <name> --dir <path>' first")
        sys.exit(1)

    # Attach to the session
    os.execvp("tmux", ["tmux", "-L", TMUX_SOCKET, "attach-session", "-t", session_name])


def cmd_stop_manager(manager_name: str, force: bool = False) -> None:
    """Stop a manager session."""
    session_name = f"{MANAGER_SESSION_PREFIX}{manager_name}"

    if not session_exists(session_name):
        log_error(f"Manager session not found: {session_name}")
        sys.exit(1)

    # Get the actual window name (may have badge prefix)
    windows = list_windows(session_name)
    # Filter out zsh shell windows to find the manager window
    manager_window = None
    for w in windows:
        # Window name might be "[MGR] manager" or just "manager"
        if w == manager_name or w.endswith(f" {manager_name}") or w.endswith("/zsh"):
            if not w.endswith("/zsh"):
                manager_window = w
                break

    if not manager_window:
        manager_window = manager_name

    log_info(f"Sending shutdown to {session_name}...")
    send_keys(session_name, manager_window, SHUTDOWN_MESSAGE)

    if not force:
        if wait_for_exit(session_name, manager_window, STOP_TIMEOUT):
            log_info(f"{session_name} stopped gracefully")
            return
        log_info(f"{session_name} did not exit gracefully, force killing...")

    tmux_or_raise("kill-session", "-t", session_name)
    log_info(f"{session_name} killed")


def cmd_completions(shell: str) -> None:
    """Output shell completion script."""
    import sys

    # Get the directory containing this script
    agency_dir = Path(__file__).parent.parent.parent
    completion_file = agency_dir / "completions" / shell

    if not completion_file.exists():
        log_error(f"Unknown shell: {shell}")
        log_error("Supported shells: bash, zsh, fish")
        sys.exit(1)

    print(completion_file.read_text())


def generate_task_id(tasks: dict[str, Task]) -> str:
    """Generate next task ID."""
    max_num = 0
    for tid in tasks.keys():
        if tid.startswith("TASK"):
            try:
                num = int(tid[4:])
                max_num = max(max_num, num)
            except ValueError:
                pass
    return f"TASK{max_num + 1:03d}"


def cmd_tasks(action: str, description: Optional[str] = None, task_id: Optional[str] = None,
              status: Optional[str] = None, assignee: Optional[str] = None) -> None:
    """Manage tasks - list, add, update, show, or delete tasks."""
    tasks = load_tasks()

    if action == "list":
        if not tasks:
            log_info("No tasks tracked")
            return

        print("Task ID   Status       Assigned To   Description")
        print("-" * 70)
        for tid, task in sorted(tasks.items()):
            desc = task.description[:40] + "..." if len(task.description) > 40 else task.description
            print(f"{task.task_id:<10} {task.status:<12} {str(task.assigned_to or '-'):<13} {desc}")

    elif action == "add":
        from datetime import datetime
        new_id = task_id or generate_task_id(tasks)
        if new_id in tasks:
            log_error(f"Task already exists: {new_id}")
            sys.exit(1)
        
        new_task = Task(
            task_id=new_id,
            description=description or "New task",
            status="pending",
            assigned_to=assignee,
            created_at=datetime.now().isoformat()
        )
        tasks[new_id] = new_task
        save_tasks(tasks)
        log_info(f"Created task: {new_id}")

    elif action == "update" and task_id:
        if task_id not in tasks:
            log_error(f"Task not found: {task_id}")
            sys.exit(1)
        
        task = tasks[task_id]
        from datetime import datetime
        
        if status:
            if status not in ["pending", "in_progress", "completed", "failed"]:
                log_error(f"Invalid status: {status}")
                sys.exit(1)
            task.status = status
            if status == "completed":
                task.completed_at = datetime.now().isoformat()
            else:
                task.completed_at = None
        
        if assignee is not None:
            task.assigned_to = assignee if assignee else None
        
        save_tasks(tasks)
        log_info(f"Updated task: {task_id}")

    elif action == "show" and task_id:
        if task_id not in tasks:
            log_error(f"Task not found: {task_id}")
            sys.exit(1)

        task = tasks[task_id]
        print(f"Task ID:      {task.task_id}")
        print(f"Status:       {task.status}")
        print(f"Assigned To:  {task.assigned_to or 'Unassigned'}")
        print(f"Created:      {task.created_at or 'Unknown'}")
        print(f"Completed:    {task.completed_at or 'In progress'}")
        print(f"Description:  {task.description}")
        if task.result:
            print(f"Result:       {task.result}")

    elif action == "delete" and task_id:
        if task_id not in tasks:
            log_error(f"Task not found: {task_id}")
            sys.exit(1)
        
        del tasks[task_id]
        save_tasks(tasks)
        log_info(f"Deleted task: {task_id}")


def cmd_start(agent_name: str, work_dir: str) -> str:
    """Start an agent in a session."""
    # Validate
    if not agent_name:
        log_error("Agent name required")
        log_error("Usage: agency start <name> --dir <path>")
        sys.exit(1)

    if not work_dir:
        log_error("Working directory required")
        log_error("Usage: agency start <name> --dir <path>")
        sys.exit(1)

    # Expand tildes
    work_dir = os.path.expanduser(work_dir)

    # Create directory if needed
    Path(work_dir).mkdir(parents=True, exist_ok=True)

    # Load config
    config = load_agent_config(agent_name)
    if not config:
        log_error(f"Config not found: {AGENTS_DIR / f'{agent_name}.yaml'}")
        log_error("Run 'agency init' first or create config")
        sys.exit(1)

    personality = config.get("personality")

    # Generate session and window names
    session_name = make_session_name(work_dir)

    # Check if agent already exists
    if window_exists(session_name, agent_name):
        log_error(f"Agent '{agent_name}' already exists in session '{session_name}'")
        log_error("Use 'agency list' to see running sessions and agents")
        sys.exit(1)

    window_name = make_window_name(agent_name, session_name)

    # Get agent command
    agent_cmd = get_agent_cmd()

    # Generate launch script
    script_path = generate_agent_script(
        session_name, window_name, agent_cmd, personality
    )

    # Create session or add window
    if session_exists(session_name):
        # Session exists - add window
        tmux_or_raise("new-window", "-d", "-t", session_name, "-n", window_name, "-c", work_dir)
        log_info(f"Added window '{window_name}' to session '{session_name}'")
    else:
        # New session
        tmux_or_raise("new-session", "-d", "-s", session_name, "-c", work_dir)
        tmux_or_raise("new-window", "-d", "-t", session_name, "-n", window_name, "-c", work_dir)
        log_info(f"Created session '{session_name}' with window '{window_name}'")

    # Send command to run agent
    send_keys(session_name, window_name, str(script_path))

    # Return session:window to stdout for scripting
    print(f"{session_name}:{window_name}")


def cmd_list() -> None:
    """List all running agency sessions."""
    sessions = list_sessions()

    if not sessions:
        log_info("No agency sessions running")
        return

    for session in sessions:
        windows = list_windows(session)
        windows_str = ",".join(windows)
        print(f"{session:<25} [{windows_str}]")


def cmd_send(session_name: str, target: Optional[str], message: str) -> None:
    """Send a message to an agent."""
    if not session_name or not message:
        log_error("Session and message required")
        log_error("Usage: agency send <session> [agent] <message>")
        sys.exit(1)

    # Parse session:agent syntax
    if ":" in session_name:
        parts = session_name.split(":", 1)
        session_name = parts[0]
        target = parts[1]

    if not session_exists(session_name):
        log_error(f"Session not found: {session_name}")
        sys.exit(1)

    # Determine target window
    if not target:
        windows = list_windows(session_name)
        if len(windows) == 0:
            log_error(f"No windows in session {session_name}")
            sys.exit(1)
        elif len(windows) > 1:
            log_error(f"Multiple windows. Specify: agency send {session_name} <agent> <message>")
            sys.exit(1)
        target = windows[0]

    send_keys(session_name, target, message)
    log_info(f"Sent message to {session_name}:{target}")


def cmd_stop(input_str: str, force: bool = False) -> None:
    """Stop a session or window gracefully."""
    if not input_str:
        log_error("Session required")
        log_error("Usage: agency stop <session>[:agent]")
        sys.exit(1)

    # Parse session:agent
    session_name = input_str
    agent = None
    if ":" in input_str:
        parts = input_str.split(":", 1)
        session_name = parts[0]
        agent = parts[1]

    if not session_exists(session_name):
        log_error(f"Session not found: {session_name}")
        sys.exit(1)

    if agent:
        # Stop specific window
        if not window_exists(session_name, agent):
            log_error(f"Window '{agent}' not found in session '{session_name}'")
            sys.exit(1)

        log_info(f"Sending shutdown to {session_name}:{agent}...")
        send_keys(session_name, agent, SHUTDOWN_MESSAGE)

        if not force:
            # Wait for graceful shutdown with timeout
            if wait_for_exit(session_name, agent, STOP_TIMEOUT):
                log_info(f"{session_name}:{agent} stopped gracefully")
                return
            log_info(f"{session_name}:{agent} did not exit gracefully, force killing...")

        tmux_or_raise("kill-window", "-t", f"{session_name}:{agent}")
        log_info(f"{session_name}:{agent} killed")
    else:
        # Stop entire session - send to all windows
        log_info(f"Sending shutdown to {session_name}...")
        windows = list_windows(session_name)
        for win in windows:
            send_keys(session_name, win, SHUTDOWN_MESSAGE)

        if not force:
            # Wait for all windows to exit
            all_exited = True
            for win in windows:
                if not wait_for_exit(session_name, win, STOP_TIMEOUT):
                    all_exited = False
            if all_exited and not session_exists(session_name):
                log_info(f"{session_name} stopped gracefully")
                return
            log_info("Some windows did not exit gracefully, force killing...")

        tmux_or_raise("kill-session", "-t", session_name)
        log_info(f"{session_name} killed")


def wait_for_exit(session_name: str, window_name: str, timeout: int) -> bool:
    """Wait for a window's process to exit within timeout."""
    # Get the pane PID
    result = tmux("list-panes", "-t", f"{session_name}:{window_name}", "-F", "#{pane_pid}")
    if result.returncode != 0:
        return False

    pane_pid = result.stdout.strip()
    if not pane_pid:
        return False

    # Wait for process to exit
    for _ in range(timeout):
        result = subprocess.run(["ps", "-p", pane_pid], capture_output=True)
        if result.returncode != 0:
            # Process exited
            return True
        time.sleep(1)

    return False


def cmd_kill(input_str: str) -> None:
    """Force kill a session or window."""
    if not input_str:
        log_error("Session required")
        log_error("Usage: agency kill <session>[:agent]")
        sys.exit(1)

    session_name = input_str
    agent = None
    if ":" in input_str:
        parts = input_str.split(":", 1)
        session_name = parts[0]
        agent = parts[1]

    if not session_exists(session_name):
        log_error(f"Session not found: {session_name}")
        sys.exit(1)

    if agent:
        if not window_exists(session_name, agent):
            log_error(f"Window '{agent}' not found in session '{session_name}'")
            sys.exit(1)
        log_info(f"Killing {session_name}:{agent}...")
        tmux_or_raise("kill-window", "-t", f"{session_name}:{agent}")
        log_info(f"Window {session_name}:{agent} killed")
    else:
        log_info(f"Killing {session_name}...")
        tmux_or_raise("kill-session", "-t", session_name)
        log_info(f"Session {session_name} killed")


def cmd_kill_all() -> None:
    """Kill all agency sessions."""
    sessions = list_sessions()

    if not sessions:
        log_info("No agency sessions running")
        return

    count = 0
    for session in sessions:
        tmux("kill-session", "-t", session)
        count += 1

    log_info(f"Killed {count} session(s)")


def cmd_attach(session_name: str, target: Optional[str] = None) -> None:
    """Attach to an agency session."""
    if not session_exists(session_name):
        log_error(f"Session not found: {session_name}")
        sys.exit(1)

    if target:
        if not window_exists(session_name, target):
            log_error(f"Window '{target}' not found in session '{session_name}'")
            sys.exit(1)
        # Select the target window before attaching
        tmux_or_raise("select-window", "-t", f"{session_name}:{target}")

    # Attach to the session - this replaces the current process with tmux
    os.execvp("tmux", ["tmux", "-L", TMUX_SOCKET, "attach-session", "-t", session_name])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Agency - AI Agent Session Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  agency init
  agency start coder --dir ~/projects/myapp
  agency start tester --dir ~/projects/myapp
  agency list
  agency send myapp coder "Fix the bug"
  agency stop myapp:coder
  agency kill-all
"""
    )

    parser.add_argument("--version", action="version", version=f"agency {VERSION}")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # init
    init_parser = subparsers.add_parser("init", help="Initialize agency config",
        description="Create agency config directory with example agent and manager configs.")
    init_parser.add_argument("--global", action="store_true", dest="is_global",
        help="Initialize global config in ~/.config/agency/")
    init_parser.add_argument("--local", action="store_true",
        help="Initialize local project config in .agency/")
    init_parser.add_argument("--dir", default=None,
        help="Custom local directory (implies --local)")
    init_parser.add_argument("--force", action="store_true",
        help="Overwrite existing config")

    # start
    start_parser = subparsers.add_parser("start", help="Start an agent",
        description="Start an agent in a project session. Creates session if needed.")
    start_parser.add_argument("name", help="Agent name (from agent configs)")
    start_parser.add_argument("--dir", required=True, help="Working directory for the agent")

    # start-manager
    start_mgr_parser = subparsers.add_parser("start-manager", help="Start a manager",
        description="Start a manager orchestrator in its own dedicated session.")
    start_mgr_parser.add_argument("name", help="Manager name (from manager configs)")
    start_mgr_parser.add_argument("--dir", required=True, help="Working directory for the manager")

    # list-managers
    subparsers.add_parser("list-managers", help="List manager configs",
        description="List available manager configurations.")

    # list
    subparsers.add_parser("list", help="List running sessions",
        description="List all running agency sessions and their windows.")

    # send
    send_parser = subparsers.add_parser("send", help="Send message to agent",
        description="Send a message to an agent. Use 'session:agent' syntax for multiple windows.")
    send_parser.add_argument("session", help="Session name (use 'session:agent' for specific window)")
    send_parser.add_argument("target", nargs="?", help="Agent name (optional if session has one window)")
    send_parser.add_argument("message", nargs="+", help="Message to send to the agent")

    # stop
    stop_parser = subparsers.add_parser("stop", help="Stop session gracefully",
        description="Stop a session or window gracefully. Sends shutdown, waits 30s.")
    stop_parser.add_argument("session", help="Session or 'session:agent' to stop")

    # kill
    kill_parser = subparsers.add_parser("kill", help="Force kill session",
        description="Force kill a session or window immediately.")
    kill_parser.add_argument("session", help="Session or 'session:agent' to kill")

    # kill-all
    subparsers.add_parser("kill-all", help="Kill all agency sessions",
        description="Force kill all agency sessions. Use 'stop' for graceful shutdown.")

    # attach
    attach_parser = subparsers.add_parser("attach", help="Attach to session",
        description="Attach to an agency tmux session.")
    attach_parser.add_argument("session", help="Session name")
    attach_parser.add_argument("target", nargs="?", help="Window/agent name (optional)")

    # attach-manager
    attach_mgr_parser = subparsers.add_parser("attach-manager", help="Attach to manager",
        description="Attach to a manager session.")
    attach_mgr_parser.add_argument("name", help="Manager name")

    # stop-manager
    stop_mgr_parser = subparsers.add_parser("stop-manager", help="Stop manager gracefully",
        description="Stop a manager session gracefully. Sends shutdown, waits 30s.")
    stop_mgr_parser.add_argument("name", help="Manager name")

    # tasks
    tasks_parser = subparsers.add_parser("tasks", help="Manage tasks",
        description="Manage delegated tasks. Track progress and results.")
    tasks_parser.add_argument("action", choices=["list", "add", "update", "show", "delete"], 
        help="Action: list, add, update, show, delete")
    tasks_parser.add_argument("task_id", nargs="?", help="Task ID (for show/update/delete)")
    tasks_parser.add_argument("-d", "--description", help="Task description (for add)")
    tasks_parser.add_argument("-s", "--status", choices=["pending", "in_progress", "completed", "failed"],
        help="Task status (for update)")
    tasks_parser.add_argument("-a", "--assignee", help="Assign to agent (for add/update)")

    # completions
    comp_parser = subparsers.add_parser("completions", help="Print shell completions",
        description="Print shell completion script. Source or pipe to shell rc file.")
    comp_parser.add_argument("shell", choices=["bash", "zsh", "fish"], help="Shell: bash, zsh, or fish")

    # tui
    subparsers.add_parser("tui", help="Launch TUI",
        description="Launch the terminal user interface for monitoring and managing agents.")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "init":
        cmd_init(
            global_init=args.is_global,
            local_init=args.local,
            custom_dir=args.dir,
            force=args.force,
        )
    elif args.command == "start":
        cmd_start(args.name, args.dir)
    elif args.command == "start-manager":
        cmd_start_manager(args.name, args.dir)
    elif args.command == "list-managers":
        cmd_list_managers()
    elif args.command == "list":
        cmd_list()
    elif args.command == "send":
        # Handle message as multiple args, target is optional
        message = " ".join(args.message)
        cmd_send(args.session, args.target, message)
    elif args.command == "stop":
        cmd_stop(args.session)
    elif args.command == "kill":
        cmd_kill(args.session)
    elif args.command == "kill-all":
        cmd_kill_all()
    elif args.command == "attach":
        cmd_attach(args.session, args.target)
    elif args.command == "attach-manager":
        cmd_attach_manager(args.name)
    elif args.command == "stop-manager":
        cmd_stop_manager(args.name)
    elif args.command == "tasks":
        cmd_tasks(args.action, args.description, args.task_id, args.status, args.assignee)
    elif args.command == "completions":
        cmd_completions(args.shell)
    elif args.command == "tui":
        run_tui()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
