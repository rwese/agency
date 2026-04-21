"""
Agency v2.0 - Session Management

Handles tmux session operations with per-project sockets.
"""

import os
import subprocess
from pathlib import Path

# Constants
SESSION_PREFIX = "agency-"
MANAGER_PREFIX = "[MGR] "
HALTED_SUFFIX = "-HALTED"
SHUTDOWN_MESSAGE = "Please wrap up, save your work, then exit gracefully. Say 'Goodbye' when done."

# Default context files to discover
DEFAULT_CONTEXT_FILES = ["AGENTS.md", "CLAUDE.md", ".claude.md"]


def discover_context_files(work_dir: Path, git_root: Path) -> list[Path]:
    """Discover context files from work_dir up to git_root.

    Args:
        work_dir: Starting directory
        git_root: Git repository root (stop here)

    Returns:
        List of discovered context file paths
    """
    context_files = []
    current = work_dir.absolute()

    while current != current.parent and current != git_root:
        for filename in DEFAULT_CONTEXT_FILES:
            file_path = current / filename
            if file_path.is_file() and file_path not in context_files:
                context_files.append(file_path)
        current = current.parent

    return context_files


def format_context_args(context_files: list[Path]) -> str:
    """Format context files as --append-system-prompt arguments.

    Args:
        context_files: List of file paths

    Returns:
        Command line arguments for append-system-prompt
    """
    if not context_files:
        return ""
    args = []
    for f in context_files:
        # Use process substitution for file contents
        args.append(f'--append-system-prompt "<({f})"')
    return " ".join(args)


# Base personality injected into all agents (always included)
BASE_PERSONALITY = """You are running in an Agency v2.0 tmux session.

## Environment
- **tmux session**: `{session_name}` (socket: `{socket_name}`)
- **Working directory**: `{work_dir}`
- **Agency dir**: `{agency_dir}`

## Agency Commands (run from project directory)

### Session Info
```bash
agency members                       # List session members with status
agency list                         # List all agency sessions
agency tmux list                    # List windows in this session
agency attach                       # Attach to this session
```

## Windows in this session
- **Manager**: `[MGR] coordinator` (or custom name)
- **Agents**: `coder`, `developer`, etc.

## Communication Protocol
- Check `agency members` to see who's online
- Use `agency tmux list` to see current windows and their status
"""

# Manager-specific base additions
MANAGER_BASE_ADDITION = """

## Task Management Commands
```bash
agency tasks list                    # List pending tasks
agency tasks add -d "description"    # Create task
agency tasks show <id>              # View task details
agency tasks assign <id> <agent>    # Assign to agent
agency tasks complete <id> --result "..."  # Approve completed task
agency tasks reject <id> --reason "..."  # Reject with reason
agency tasks update <id> --status <status>  # Update task status
```

## Coordinator Workflow
After each response, ALWAYS check `agency tasks list` to see if work needs assignment.

When tasks are unassigned:
1. Assign to available agents using `agency tasks assign <id> <agent>`
2. Distribute work evenly across agents

When tasks are pending approval:
1. Review with `agency tasks show <id>`
2. Approve or reject with `agency tasks approve/reject <id>`
"""

# Agent-specific base additions
AGENT_BASE_ADDITION = """

## Task Workflow
**After completing any action, always check `agency tasks list` for new work.**

If you have an assigned task:
1. View it: `agency tasks show <id>`
2. Mark in_progress: `agency tasks update <id> --status in_progress`
3. Work on it
4. Complete: `agency tasks complete <id> --result "..."`

**ONE TASK AT A TIME** - finish current task before starting another.
"""


class SessionManager:
    """Manages a tmux session with dedicated socket."""

    def __init__(self, session_name: str, socket_name: str | None = None):
        self.session_name = session_name
        self.socket_name = socket_name or session_name

    def _tmux(self, *args: str) -> subprocess.CompletedProcess:
        """Run a tmux command with the session's socket."""
        result = subprocess.run(
            ["tmux", "-L", self.socket_name] + list(args),
            capture_output=True,
            text=True,
        )
        return result

    def session_exists(self) -> bool:
        """Check if session exists."""
        result = self._tmux("has-session", "-t", self.session_name)
        return result.returncode == 0

    def window_exists(self, window_name: str) -> bool:
        """Check if window exists in session."""
        windows = self.list_windows()
        return window_name in windows or f"{MANAGER_PREFIX}{window_name}" in windows

    def manager_exists(self) -> bool:
        """Check if manager window exists."""
        windows = self.list_windows()
        return any(w.startswith(MANAGER_PREFIX) for w in windows)

    def list_windows(self) -> list[str]:
        """List all windows in session."""
        result = self._tmux("list-windows", "-t", self.session_name, "-F", "#W")
        if result.returncode != 0:
            return []
        return [w.strip() for w in result.stdout.strip().split("\n") if w.strip() and w not in ("zsh", "tmux")]

    def send_keys(self, window_name: str, msg: str) -> None:
        """Send keys to a window."""
        self._tmux("send-keys", "-t", f"{self.session_name}:{window_name}", msg, "Enter")

    def broadcast_shutdown(self) -> None:
        """Send shutdown message to all windows."""
        windows = self.list_windows()
        for window in windows:
            self.send_keys(window, SHUTDOWN_MESSAGE)

    def kill_window(self, window_name: str) -> None:
        """Kill a specific window."""
        self._tmux("kill-window", "-t", f"{self.session_name}:{window_name}")

    def kill_session(self) -> None:
        """Kill the entire session."""
        self._tmux("kill-session", "-t", self.session_name)

    def rename_session(self, new_name: str) -> None:
        """Rename the session."""
        self._tmux("rename-session", "-t", self.session_name, new_name)

    def rename_window(self, window_name: str, new_name: str) -> None:
        """Rename a window."""
        self._tmux("rename-window", "-t", f"{self.session_name}:{window_name}", new_name)

    def cleanup_socket(self) -> None:
        """Remove the tmux socket file."""
        socket_path = Path.home() / ".tmux" / self.socket_name
        if socket_path.exists():
            socket_path.unlink()

        # Also check other possible locations
        socket_path2 = Path("/tmp") / f"tmux-{os.getuid()}" / self.socket_name
        if socket_path2.exists():
            socket_path2.unlink()

    def wait_for_exit(self, window_name: str, timeout: int = 30) -> bool:
        """Wait for a window's process to exit."""
        import time

        # Get pane PID
        result = self._tmux("list-panes", "-t", f"{self.session_name}:{window_name}", "-F", "#{pane_pid}")
        if result.returncode != 0:
            return False

        pane_pid = result.stdout.strip()
        if not pane_pid:
            return False

        # Wait for process to exit
        for _ in range(timeout):
            proc_result = subprocess.run(["ps", "-p", pane_pid], capture_output=True)
            if proc_result.returncode != 0:
                return True
            time.sleep(1)

        return False


def create_project_session(
    session_name: str,
    socket_name: str,
    work_dir: Path,
    initial_window_name: str | None = None,
) -> None:
    """Create a new project session with named initial window.

    Args:
        session_name: Name of the tmux session
        socket_name: Name of the tmux socket
        work_dir: Working directory for the session
        initial_window_name: Name for the initial window (default: session_name)
    """
    window_name = initial_window_name or session_name

    result = subprocess.run(
        [
            "tmux",
            "-f", "/dev/null",
            "-L",
            socket_name,
            "new-session",
            "-d",
            "-s",
            session_name,
            "-n",
            window_name,
            "-c",
            str(work_dir),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to create session: {result.stderr}")


def start_manager_window(
    session_name: str,
    socket_name: str,
    manager_name: str,
    agency_dir: Path,
    work_dir: Path,
) -> None:
    """Start a manager window in the session."""
    # Create window at next available index
    window_name = f"{MANAGER_PREFIX}{manager_name}"

    result = subprocess.run(
        [
            "tmux",
            "-L",
            socket_name,
            "new-window",
            "-d",
            "-t",
            f"{session_name}:",  # Colon to explicitly target session
            "-n",
            window_name,
            "-c",
            str(work_dir),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to create manager window: {result.stderr}")

    # Apply badge color to window
    subprocess.run(
        [
            "tmux",
            "-L",
            socket_name,
            "set-window-option",
            "-t",
            f"{session_name}:{window_name}",
            "window-status-style",
            "fg=black,bg=blue,bold",
        ],
        capture_output=True,
    )
    subprocess.run(
        [
            "tmux",
            "-L",
            socket_name,
            "set-window-option",
            "-t",
            f"{session_name}:{window_name}",
            "window-status-current-style",
            "fg=black,bg=blue,bold",
        ],
        capture_output=True,
    )

    # Generate and execute launch script
    script_path = _generate_manager_launch_script(session_name, socket_name, manager_name, agency_dir, work_dir)

    # Send command to window
    subprocess.run(
        [
            "tmux",
            "-L",
            socket_name,
            "send-keys",
            "-t",
            f"{session_name}:{window_name}",
            str(script_path),
            "Enter",
        ],
        capture_output=True,
    )


def start_agent_window(
    session_name: str,
    socket_name: str,
    agent_name: str,
    agency_dir: Path,
    work_dir: Path,
) -> None:
    """Start an agent window in the session."""
    # Create window at next available index

    result = subprocess.run(
        [
            "tmux",
            "-L",
            socket_name,
            "new-window",
            "-d",
            "-t",
            f"{session_name}:",  # Colon to explicitly target session
            "-n",
            agent_name,
            "-c",
            str(work_dir),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to create agent window: {result.stderr}")

    # Generate and execute launch script
    script_path = _generate_agent_launch_script(session_name, socket_name, agent_name, agency_dir, work_dir)

    # Send command to window
    subprocess.run(
        [
            "tmux",
            "-L",
            socket_name,
            "send-keys",
            "-t",
            f"{session_name}:{agent_name}",
            str(script_path),
            "Enter",
        ],
        capture_output=True,
    )


def _escape_prompt(s: str) -> str:
    """Escape string for shell prompt injection."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("`", "\\`")


def _generate_manager_launch_script(
    session_name: str,
    socket_name: str,
    manager_name: str,
    agency_dir: Path,
    work_dir: Path,
) -> Path:
    """Generate the manager launch script."""
    from agency.config import load_agency_config

    scripts_dir = agency_dir / ".scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    script_path = scripts_dir / f"manager-{manager_name}.sh"

    # Get manager personality from config (user additions)
    manager_config_path = agency_dir / "manager.yaml"
    user_personality = ""

    if manager_config_path.exists():
        import yaml

        config = yaml.safe_load(manager_config_path.read_text())
        user_personality = config.get("personality", "")

    # Build full personality: base + manager additions + user
    full_personality = (
        BASE_PERSONALITY.format(
            session_name=session_name,
            socket_name=socket_name,
            work_dir=work_dir,
            agency_dir=agency_dir,
        )
        + MANAGER_BASE_ADDITION
        + ("\n\n## Who am i\n" + user_personality if user_personality else "")
    )

    escaped = _escape_prompt(full_personality)
    personality_args = f' --append-system-prompt "{escaped}"'

    # Discover context files from work_dir to git_root
    agency_config = load_agency_config(agency_dir)
    context_files = discover_context_files(work_dir, work_dir)  # Use work_dir as git_root for now

    # Add custom context files from config if specified
    if agency_config.additional_context_files:
        for cf in agency_config.additional_context_files:
            # Substitute AGENCY_* vars and expand ~ and ${HOME}
            cf_expanded = (
                cf.replace("${AGENCY_DIR}", str(agency_dir))
                .replace("${AGENCY_WORKDIR}", str(work_dir))
                .replace("${AGENCY_PROJECT}", session_name)
                .replace("${HOME}", str(Path.home()))
            )
            # Expand ~ (after substituting other vars)
            cf_expanded = os.path.expanduser(cf_expanded)

            cf_path = Path(cf_expanded)
            # Absolute paths used directly, relative paths resolved from work_dir
            if cf_path.is_absolute():
                if cf_path.exists():
                    context_files.append(cf_path)
                else:
                    print(f"[WARN] Context file not found: {cf_expanded}")
            else:
                # Relative path - resolve from work_dir
                abs_path = work_dir / cf_path
                if abs_path.exists():
                    context_files.append(abs_path)
                else:
                    print(f"[WARN] Context file not found: {abs_path}")

    context_args = format_context_args(context_files)

    # Get agent command
    agent_cmd = os.environ.get("AGENCY_AGENT_CMD", "pi")

    # Get poll interval and chunk size from config
    poll_interval = 30
    chunk_size = 1
    if manager_config_path.exists():
        import yaml
        config = yaml.safe_load(manager_config_path.read_text())
        poll_interval = config.get("poll_interval", 30)
        chunk_size = config.get("chunk_size", 1)

    # Get pi-inject extension path
    inject_extension = os.environ.get(
        "AGENCY_PI_INJECT_EXT",
        str(Path.home() / ".pi" / "agent" / "extensions" / "pi-inject" / "extensions")
    )

    # Import heartbeat module for path
    from agency import heartbeat as heartbeat_module
    heartbeat_path = Path(heartbeat_module.__file__).parent / "heartbeat.py"

    # Build command with heartbeat in background
    # Use unique socket path per member
    injector_socket = f"{agency_dir}/injector-{manager_name}.sock"
    cmd = (
        f'cd "{work_dir}" && '
        f"rm -f \"{injector_socket}\" && "
        # Start heartbeat in background with all env vars
        f"env "
        f"AGENCY_ROLE=MANAGER "
        f"AGENCY_DIR=\"{agency_dir}\" "
        f"AGENCY_MANAGER={manager_name} "
        f"AGENCY_SOCKET={socket_name} "
        f"AGENCY_POLL_INTERVAL={poll_interval} "
        f"AGENCY_CHUNK_SIZE={chunk_size} "
        f"PI_INJECTOR_SOCKET=\"{injector_socket}\" "
        f"python3 {heartbeat_path} > /dev/null 2>&1 & "
        # Give heartbeat a moment to start
        f"sleep 1 && "
        # Use env to ensure all vars are passed to pi
        f"env "
        f"AGENCY_ROLE=MANAGER "
        f"AGENCY_PROJECT={session_name} "
        f"AGENCY_DIR=\"{agency_dir}\" "
        f"AGENCY_WORKDIR=\"{work_dir}\" "
        f"AGENCY_MANAGER={manager_name} "
        f"AGENCY_SOCKET={socket_name} "
        f"AGENCY_POLL_INTERVAL={poll_interval} "
        f"AGENCY_CHUNK_SIZE={chunk_size} "
        f"PI_INJECTOR_SOCKET=\"{injector_socket}\" "
        f"{agent_cmd} "
        f'-e "{inject_extension}" '
        f'--session-dir "{agency_dir}" '
        f"--no-context-files "
        f"{context_args}"
        f"{personality_args} "
    )

    script_path.write_text(f"#!/bin/bash\n{cmd}\n")
    script_path.chmod(0o755)

    return script_path


def _generate_agent_launch_script(
    session_name: str,
    socket_name: str,
    agent_name: str,
    agency_dir: Path,
    work_dir: Path,
) -> Path:
    """Generate the agent launch script."""
    from agency.config import load_agency_config

    scripts_dir = agency_dir / ".scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    script_path = scripts_dir / f"agent-{agent_name}.sh"

    # Get agent personality from config (user additions)
    agent_config_path = agency_dir / "agents" / f"{agent_name}.yaml"
    user_personality = ""

    if agent_config_path.exists():
        import yaml

        config = yaml.safe_load(agent_config_path.read_text())

        # Check for personality file reference
        personality_ref = config.get("personality", "")
        if personality_ref and personality_ref.endswith(".md"):
            personality_file = agent_config_path.parent / personality_ref
            if personality_file.exists():
                user_personality = personality_file.read_text()
        elif personality_ref:
            user_personality = personality_ref

    # Build full personality: base + agent additions + user
    full_personality = (
        BASE_PERSONALITY.format(
            session_name=session_name,
            socket_name=socket_name,
            work_dir=work_dir,
            agency_dir=agency_dir,
        )
        + AGENT_BASE_ADDITION
        + ("\n\n## Custom Personality\n" + user_personality if user_personality else "")
    )

    escaped = _escape_prompt(full_personality)
    personality_args = f' --append-system-prompt "{escaped}"'

    # Discover context files from work_dir to git_root
    agency_config = load_agency_config(agency_dir)
    context_files = discover_context_files(work_dir, work_dir)

    # Add custom context files from config if specified
    if agency_config.additional_context_files:
        for cf in agency_config.additional_context_files:
            # Substitute AGENCY_* vars
            cf_expanded = (
                cf.replace("${AGENCY_DIR}", str(agency_dir))
                .replace("${AGENCY_WORKDIR}", str(work_dir))
                .replace("${AGENCY_PROJECT}", session_name)
            )
            cf_path = Path(cf_expanded)
            # Absolute paths used directly, relative paths resolved from work_dir
            if cf_path.is_absolute():
                if cf_path.exists():
                    context_files.append(cf_path)
                else:
                    print(f"[WARN] Context file not found: {cf_expanded}")
            else:
                # Relative path - resolve from work_dir
                abs_path = work_dir / cf_path
                if abs_path.exists():
                    context_files.append(abs_path)
                else:
                    print(f"[WARN] Context file not found: {abs_path}")

    context_args = format_context_args(context_files)

    # Get agent command
    agent_cmd = os.environ.get("AGENCY_AGENT_CMD", "pi")

    # Get pi-inject extension path
    inject_extension = os.environ.get(
        "AGENCY_PI_INJECT_EXT",
        str(Path.home() / ".pi" / "agent" / "extensions" / "pi-inject" / "extensions")
    )

    # Import heartbeat module for path
    from agency import heartbeat as heartbeat_module
    heartbeat_path = Path(heartbeat_module.__file__).parent / "heartbeat.py"

    # Build command with heartbeat in background
    # Use unique socket path per member
    injector_socket = f"{agency_dir}/injector-{agent_name}.sock"
    cmd = (
        f'cd "{work_dir}" && '
        f"rm -f \"{injector_socket}\" && "
        # Start heartbeat in background with all env vars
        f"env "
        f"AGENCY_ROLE=AGENT "
        f"AGENCY_DIR=\"{agency_dir}\" "
        f"AGENCY_AGENT={agent_name} "
        f"AGENCY_SOCKET={socket_name} "
        f"PI_INJECTOR_SOCKET=\"{injector_socket}\" "
        f"python3 {heartbeat_path} > /dev/null 2>&1 & "
        # Give heartbeat a moment to start
        f"sleep 1 && "
        # Use env to ensure all vars are passed to pi
        f"env "
        f"AGENCY_ROLE=AGENT "
        f"AGENCY_PROJECT={session_name} "
        f"AGENCY_DIR=\"{agency_dir}\" "
        f"AGENCY_WORKDIR=\"{work_dir}\" "
        f"AGENCY_AGENT={agent_name} "
        f"AGENCY_SOCKET={socket_name} "
        f"PI_INJECTOR_SOCKET=\"{injector_socket}\" "
        f"{agent_cmd} "
        f'-e "{inject_extension}" '
        f'--session-dir "{agency_dir}" '
        f"--no-context-files "
        f"{personality_args} "
        f"{context_args}"
    )

    script_path.write_text(f"#!/bin/bash\n{cmd}\n")
    script_path.chmod(0o755)

    return script_path


def resume_halted_session(
    session_name: str,
    socket_name: str,
    agency_dir: Path,
    work_dir: Path,
) -> bool:
    """Resume a halted session."""
    sm = SessionManager(session_name, socket_name)

    # Check if session is halted
    if session_name.endswith(HALTED_SUFFIX):
        # Remove HALTED suffix
        new_name = session_name[: -len(HALTED_SUFFIX)]
        sm.rename_session(new_name)
        session_name = new_name

    # Rename manager window if needed
    windows = sm.list_windows()
    for window in windows:
        if window.startswith("[HALTED]"):
            new_name = window.replace("[HALTED]", "[MGR]")
            sm.rename_window(window, new_name)
            break

    # Restart manager
    manager_config_path = agency_dir / "manager.yaml"
    if manager_config_path.exists():
        import yaml

        _config = yaml.safe_load(manager_config_path.read_text())

        # Send resume signal to manager
        for window in windows:
            if window.startswith("[MGR]") or window.startswith("[HALTED]"):
                sm.send_keys(window, "# RESUMED")
                break

    return True


def list_agency_sessions() -> list[dict]:
    """List all agency sessions across all sockets."""
    import subprocess

    sessions = []
    tmux_sockets_dir = Path("/tmp") / f"tmux-{os.getuid()}"

    # Discover all agency sockets
    agency_sockets = []
    if tmux_sockets_dir.exists():
        for socket_file in tmux_sockets_dir.iterdir():
            if socket_file.is_socket() and socket_file.name.startswith(SESSION_PREFIX):
                agency_sockets.append(socket_file.name)

    # Check each socket for sessions
    for socket_name in agency_sockets:
        result = subprocess.run(
            ["tmux", "-L", socket_name, "list-sessions", "-F", "#S"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    session_name = line.strip()
                    sm = SessionManager(session_name, socket_name)
                    windows = []

                    for w in sm.list_windows():
                        is_manager = w.startswith(MANAGER_PREFIX)
                        clean_name = w.replace(MANAGER_PREFIX, "")
                        windows.append(
                            {
                                "name": clean_name,
                                "is_manager": is_manager,
                            }
                        )

                    sessions.append(
                        {
                            "name": session_name,
                            "windows": windows,
                        }
                    )

    return sessions
