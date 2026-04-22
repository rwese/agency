"""
Agency v2.0 - Session Management

Handles tmux session operations with per-project sockets.
"""

import os
import subprocess
from pathlib import Path

# Lazy import for audit to avoid circular imports
_audit_store = None


def _get_audit_store(agency_dir: Path | None = None):
    """Get audit store lazily if audit is enabled in config."""
    global _audit_store
    if _audit_store is None and agency_dir:
        try:
            from agency.audit import AuditStore
            from agency.config import load_agency_config

            config = load_agency_config(agency_dir)
            if config.audit_enabled:
                _audit_store = AuditStore(agency_dir)
            else:
                _audit_store = False
        except Exception:
            _audit_store = False
    return _audit_store if _audit_store else None


# Constants
SESSION_PREFIX = "agency-"
MANAGER_PREFIX = "[MGR] "
HALTED_SUFFIX = "-HALTED"
SHUTDOWN_MESSAGE = "Please wrap up, save your work, then exit gracefully. Say 'Goodbye' when done."
WRAPUP_MESSAGE = """Please perform cleanup: (1) Save all work, (2) Update pending tasks with remaining work status using 'agency tasks-agent update <task-id> --status pending --result incomplete: <what remains>', (3) Say 'Goodbye' in your response, then exit."""

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
## Your Role
You are a specialized agent. Your job is to WORK on assigned tasks, not just report status.

## Task Workflow (EXACT STEPS)

### When you start OR when idle:

1. **Check your work queue:**
   ```bash
   agency tasks-agent my-work
   ```
   This shows your tasks in priority order: in_progress → pending → pending_approval

2. **For each pending task:**
   a. View: `agency tasks-agent show <task-id>`
   b. Mark in_progress: `agency tasks-agent update <task-id> --status in_progress`
   c. **DO THE WORK** - create files, write code, etc.
   d. Mark complete: `agency tasks-agent complete <task-id> --result "<what you did>"`

3. **After completing, check for more work:**
   ```bash
   agency tasks-agent my-work
   ```

### Critical Rules:
- **DO NOT** just list tasks - WORK on them immediately
- **DO NOT** say "I'll do X later" - do it NOW
- **DO NOT** wait for permission - complete the task and mark it done
- **When idle**, check `agency tasks-agent my-work` for work

## Coordinator Tasks
If assigned a coordinator task (like reviewing docs):
1. Complete the work as instructed
2. Mark complete: `agency tasks-agent complete <id> --result "<summary>"`

## Working Directory
All work happens in the project directory. Use `cd` to navigate.
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

    def send_keys(self, window_name: str, msg: str, enter: bool = True) -> None:
        """Send keys to a window."""
        if enter:
            self._tmux("send-keys", "-t", f"{self.session_name}:{window_name}", msg, "Enter")
        else:
            self._tmux("send-keys", "-t", f"{self.session_name}:{window_name}", msg)

    def send_escape(self, window_name: str) -> None:
        """Send Escape key to a window to cancel any ongoing operation."""
        self._tmux("send-keys", "-t", f"{self.session_name}:{window_name}", "Escape")

    def broadcast_shutdown(self) -> None:
        """Send shutdown message to all windows."""
        windows = self.list_windows()
        for window in windows:
            self.send_keys(window, SHUTDOWN_MESSAGE)

    def broadcast_escape(self) -> None:
        """Send Escape key to all windows to cancel ongoing operations."""
        windows = self.list_windows()
        for window in windows:
            self.send_escape(window)

    def broadcast_wrapup(self) -> None:
        """Send wrapup message to all windows asking for cleanup and task updates."""
        windows = self.list_windows()
        for window in windows:
            self.send_keys(window, WRAPUP_MESSAGE)

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

    def switch_to_window(self, window_name: str) -> None:
        """Switch to a window (set as current)."""
        self._tmux("select-window", "-t", f"{self.session_name}:{window_name}")

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

    # Instance variable to track pane state for idle detection
    _idle_tracker: dict[str, dict] = {}  # window_name -> {stable_since, last_hash, last_check}

    def get_pane_content_hash(self, window_name: str) -> str | None:
        """Get a hash of the visible pane content (current screen only, not scrollback).

        Returns content hash or None if unavailable.
        This captures just the current visible lines, ignoring scrollback history.
        """
        import hashlib

        # Get current visible pane content (not scrollback)
        result = self._tmux("capture-pane", "-p", "-t", f"{self.session_name}:{window_name}")
        if result.returncode != 0:
            return None

        # Normalize: remove trailing whitespace, hash the content
        content = result.stdout.rstrip()
        if not content:
            return None

        hash_val = hashlib.md5(content.encode("utf-8", errors="ignore")).hexdigest()
        return hash_val

    def is_window_idle(self, window_name: str, idle_seconds: int = 120) -> bool:
        """Check if window pane has been showing the same content for idle_seconds.

        Returns True only if the pane content has been stable (unchanged) for
        the full idle_seconds period. This means the agent is truly idle,
        not just between commands.

        An agent is considered IDLE when:
        - The same pane content has been displayed for idle_seconds

        An agent is WORKING when:
        - Pane content changes frequently (output, progress, etc.)
        - Any change resets the idle timer

        Args:
            window_name: Name of the window
            idle_seconds: Seconds of stable content required (default: 120)

        Returns:
            True if pane content stable for idle_seconds, False otherwise
        """
        import time

        current_hash = self.get_pane_content_hash(window_name)
        if current_hash is None:
            return False

        current_time = int(time.time())

        if window_name not in self._idle_tracker:
            # First check - initialize with current state
            self._idle_tracker[window_name] = {
                "stable_since": current_time,
                "last_hash": current_hash,
                "last_check": current_time,
            }
            return False  # Can't be idle on first check

        tracker = self._idle_tracker[window_name]

        if current_hash != tracker["last_hash"]:
            # Content changed - reset stable timer
            tracker["stable_since"] = current_time
            tracker["last_hash"] = current_hash
            tracker["last_check"] = current_time
            return False

        # Same content - check if stable long enough
        tracker["last_check"] = current_time
        return (current_time - tracker["stable_since"]) >= idle_seconds

    def get_idle_windows(self, idle_seconds: int = 120) -> list[str]:
        """Get list of windows that have been idle for specified seconds.

        Args:
            idle_seconds: Number of seconds of inactivity required

        Returns:
            List of window names that are idle
        """
        idle_windows = []
        for window in self.list_windows():
            if self.is_window_idle(window, idle_seconds):
                idle_windows.append(window)
        return idle_windows


def create_project_session(
    session_name: str,
    socket_name: str,
    work_dir: Path,
) -> None:
    """Create a new project session (no initial window).

    The manager will be created as window:0.

    Args:
        session_name: Name of the tmux session
        socket_name: Name of the tmux socket
        work_dir: Working directory for the session
    """
    result = subprocess.run(
        [
            "tmux",
            "-f",
            "/dev/null",
            "-L",
            socket_name,
            "new-session",
            "-d",
            "-s",
            session_name,
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
    """Start a manager window in the session as window:0 and switch to it."""
    window_name = f"{MANAGER_PREFIX}{manager_name}"

    # Rename window:0 to manager name (session was created with a default window)
    subprocess.run(
        [
            "tmux",
            "-L",
            socket_name,
            "rename-window",
            "-t",
            f"{session_name}:0",
            window_name,
        ],
        capture_output=True,
    )

    # Set the working directory for window:0
    subprocess.run(
        [
            "tmux",
            "-L",
            socket_name,
            "send-keys",
            "-t",
            f"{session_name}:{window_name}",
            f"cd {work_dir}",
            "Enter",
        ],
        capture_output=True,
    )

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

    # Switch to manager window (make it the current window)
    subprocess.run(
        [
            "tmux",
            "-L",
            socket_name,
            "select-window",
            "-t",
            f"{session_name}:{window_name}",
        ],
        capture_output=True,
    )

    # Audit log
    audit = _get_audit_store(agency_dir)
    if audit:
        audit.log_agent(
            action="start",
            agency_role="manager",
            details={
                "session": session_name,
                "manager_name": manager_name,
                "work_dir": str(work_dir),
            },
        )

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

    # Audit log
    audit = _get_audit_store(agency_dir)
    if audit:
        audit.log_agent(
            action="start",
            agency_role="manager",
            details={
                "session": session_name,
                "manager_name": manager_name,
                "work_dir": str(work_dir),
            },
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

    # Audit log
    audit = _get_audit_store(agency_dir)
    if audit:
        audit.log_agent(
            action="start",
            agency_role="agent",
            details={
                "session": session_name,
                "agent_name": agent_name,
                "work_dir": str(work_dir),
            },
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

    scripts_dir = agency_dir / "run" / ".scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    script_path = scripts_dir / f"manager-{manager_name}.sh"

    # Load agency config first (needed for template delimiter)
    agency_config = load_agency_config(agency_dir)

    # Get manager personality from config (user additions)
    manager_config_path = agency_dir / "manager.yaml"
    user_personality = ""

    if manager_config_path.exists():
        import yaml

        config = yaml.safe_load(manager_config_path.read_text())
        user_personality = config.get("personality", "")

    # Process template injection for user personality
    from agency.template_inject import InjectionOptions, TemplateInjector, process_string

    inj_options = InjectionOptions(base_dir=agency_dir)
    if agency_config.template_delimiter:
        # Parse "{{...}}" format
        parts = agency_config.template_delimiter.split("...")
        if len(parts) == 2:
            injector = TemplateInjector.with_delimiters(parts[0], parts[1], inj_options)
            inj_result = injector.process(user_personality)
        else:
            inj_result = process_string(user_personality, base_dir=agency_dir)
    else:
        inj_result = process_string(user_personality, base_dir=agency_dir)
    user_personality = inj_result.content
    for err in inj_result.errors:
        print(err, flush=True)

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
    context_files = discover_context_files(work_dir, work_dir)  # Use work_dir as git_root for now

    # Add custom context files from config if specified
    if agency_config.additional_context_files:
        from agency.template_inject import process_file

        # Counter for unique temp file names
        context_idx = 0
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
            # Resolve absolute/relative paths
            if not cf_path.is_absolute():
                cf_path = work_dir / cf_path

            if not cf_path.exists():
                print(f"[WARN] Context file not found: {cf_expanded}", flush=True)
                continue

            # Process template injection and write to temp file
            inj_result = process_file(cf_path)
            for err in inj_result.errors:
                print(err, flush=True)

            # Write processed content to temp file in scripts_dir
            temp_path = scripts_dir / f"_context_{context_idx}_{cf_path.name}"
            temp_path.write_text(inj_result.content, encoding="utf-8")
            context_files.append(temp_path)
            context_idx += 1

    context_args = format_context_args(context_files)

    # Get agent command
    agent_cmd = os.environ.get("AGENCY_AGENT_CMD", "pi")

    # Get poll interval and chunk size from manager config
    poll_interval = 30
    chunk_size = 1
    if manager_config_path.exists():
        import yaml

        config = yaml.safe_load(manager_config_path.read_text())
        poll_interval = config.get("poll_interval", 30)
        chunk_size = config.get("chunk_size", 1)

    # Get parallel limit from agency config
    parallel_limit = agency_config.parallel_limit

    # Get pi session directory (default: .agency/pi/sessions/)
    pi_session_dir = os.environ.get("AGENCY_PI_SESSION_DIR", str(agency_dir / "pi" / "sessions"))

    # Get pi extensions from project-local .agency/pi/extensions/ (self-contained)
    # pi-inject and pi-status have extensions/ subdirectory; no-frills is at root
    inject_extension = os.environ.get(
        "AGENCY_PI_INJECT_EXT", str(agency_dir / "pi" / "extensions" / "pi-inject" / "extensions")
    )

    status_extension = os.environ.get(
        "AGENCY_PI_STATUS_EXT", str(agency_dir / "pi" / "extensions" / "pi-status" / "extensions")
    )

    nofrills_extension = os.environ.get("AGENCY_PI_NOFILLS_EXT", str(agency_dir / "pi" / "extensions" / "no-frills"))

    # Import heartbeat module for path
    from agency import heartbeat as heartbeat_module

    heartbeat_path = Path(heartbeat_module.__file__).parent / "heartbeat.py"

    # Build command with heartbeat in background
    # Use unique socket path per member
    injector_socket = f"{agency_dir}/run/injector-{manager_name}.sock"
    status_socket = f"{agency_dir}/run/status-{manager_name}.sock"

    # Build parallel limit env var
    parallel_limit_env = f"AGENCY_PARALLEL_LIMIT={parallel_limit} " if parallel_limit else ""

    # No-frills env vars for minimal UI (hide decorations)
    nofrills_env = (
        "PI_NOFILLS_TOOLS=minimal PI_NOFILLS_THINKING=1 PI_NOFILLS_WORKING=1 PI_NOFILLS_FOOTER=1 PI_NOFILLS_HEADER=1 "
    )

    cmd = (
        f'cd "{work_dir}" && '
        f'rm -f "{injector_socket}" && '
        # Start heartbeat in background with all env vars
        f"env "
        f"AGENCY_ROLE=MANAGER "
        f'AGENCY_DIR="{agency_dir}" '
        f"AGENCY_MANAGER={manager_name} "
        f"AGENCY_SOCKET={socket_name} "
        f"AGENCY_POLL_INTERVAL={poll_interval} "
        f"AGENCY_CHUNK_SIZE={chunk_size} "
        f"{parallel_limit_env}"
        f'PI_INJECTOR_SOCKET="{injector_socket}" '
        f'PI_STATUS_SOCKET="{status_socket}" '
        f"python3 {heartbeat_path} > /dev/null 2>&1 & "
        # Give heartbeat a moment to start
        f"sleep 1 && "
        # Use env to ensure all vars are passed to pi
        f"env "
        f"AGENCY_ROLE=MANAGER "
        f"AGENCY_PROJECT={session_name} "
        f'AGENCY_DIR="{agency_dir}" '
        f'AGENCY_WORKDIR="{work_dir}" '
        f"AGENCY_MANAGER={manager_name} "
        f"AGENCY_SOCKET={socket_name} "
        f"AGENCY_POLL_INTERVAL={poll_interval} "
        f"AGENCY_CHUNK_SIZE={chunk_size} "
        f"{parallel_limit_env}"
        f'PI_INJECTOR_SOCKET="{injector_socket}" '
        f'PI_STATUS_SOCKET="{status_socket}" '
        f"{nofrills_env}"
        f"{agent_cmd} "
        f'-e "{inject_extension}" '
        f'-e "{status_extension}" '
        f'-e "{nofrills_extension}" '
        f"--no-extensions "
        f"--no-themes "
        f"--offline "
        f'--session-dir "{pi_session_dir}" '
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

    scripts_dir = agency_dir / "run" / ".scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    script_path = scripts_dir / f"agent-{agent_name}.sh"

    # Load agency config first (needed for template delimiter)
    agency_config = load_agency_config(agency_dir)

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

    # Process template injection for user personality
    from agency.template_inject import InjectionOptions, TemplateInjector, process_string

    inj_options = InjectionOptions(base_dir=agency_dir)
    if agency_config.template_delimiter:
        # Parse "{{...}}" format
        parts = agency_config.template_delimiter.split("...")
        if len(parts) == 2:
            injector = TemplateInjector.with_delimiters(parts[0], parts[1], inj_options)
            inj_result = injector.process(user_personality)
        else:
            inj_result = process_string(user_personality, base_dir=agency_dir)
    else:
        inj_result = process_string(user_personality, base_dir=agency_dir)
    user_personality = inj_result.content
    for err in inj_result.errors:
        print(err, flush=True)

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
    context_files = discover_context_files(work_dir, work_dir)

    # Add custom context files from config if specified
    if agency_config.additional_context_files:
        from agency.template_inject import process_file

        # Counter for unique temp file names
        context_idx = 0
        for cf in agency_config.additional_context_files:
            # Substitute AGENCY_* vars
            cf_expanded = (
                cf.replace("${AGENCY_DIR}", str(agency_dir))
                .replace("${AGENCY_WORKDIR}", str(work_dir))
                .replace("${AGENCY_PROJECT}", session_name)
            )
            cf_path = Path(cf_expanded)
            # Resolve absolute/relative paths
            if not cf_path.is_absolute():
                cf_path = work_dir / cf_path

            if not cf_path.exists():
                print(f"[WARN] Context file not found: {cf_expanded}", flush=True)
                continue

            # Process template injection and write to temp file
            inj_result = process_file(cf_path)
            for err in inj_result.errors:
                print(err, flush=True)

            # Write processed content to temp file in scripts_dir
            temp_path = scripts_dir / f"_context_{context_idx}_{cf_path.name}"
            temp_path.write_text(inj_result.content, encoding="utf-8")
            context_files.append(temp_path)
            context_idx += 1

    context_args = format_context_args(context_files)

    # Get agent command
    agent_cmd = os.environ.get("AGENCY_AGENT_CMD", "pi")

    # Get pi extensions from project-local .agency/pi/extensions/ (self-contained)
    # pi-inject and pi-status have extensions/ subdirectory; no-frills is at root
    inject_extension = os.environ.get(
        "AGENCY_PI_INJECT_EXT", str(agency_dir / "pi" / "extensions" / "pi-inject" / "extensions")
    )

    status_extension = os.environ.get(
        "AGENCY_PI_STATUS_EXT", str(agency_dir / "pi" / "extensions" / "pi-status" / "extensions")
    )

    nofrills_extension = os.environ.get("AGENCY_PI_NOFILLS_EXT", str(agency_dir / "pi" / "extensions" / "no-frills"))

    # Import heartbeat module for path
    from agency import heartbeat as heartbeat_module

    heartbeat_path = Path(heartbeat_module.__file__).parent / "heartbeat.py"

    # Build command with heartbeat in background
    # Use unique socket path per member
    injector_socket = f"{agency_dir}/run/injector-{agent_name}.sock"
    status_socket = f"{agency_dir}/run/status-{agent_name}.sock"

    # Get poll and ping intervals from manager config
    poll_interval = 30
    ping_interval = 120
    manager_config_path = agency_dir / "manager.yaml"
    if manager_config_path.exists():
        import yaml

        config = yaml.safe_load(manager_config_path.read_text())
        poll_interval = config.get("poll_interval", 30)
        ping_interval = config.get("ping_interval", 120)

    # Get pi session directory (default: .agency/pi/sessions/)
    pi_session_dir = os.environ.get("AGENCY_PI_SESSION_DIR", str(agency_dir / "pi" / "sessions"))

    # No-frills env vars for minimal UI (hide decorations)
    nofrills_env = (
        "PI_NOFILLS_TOOLS=minimal PI_NOFILLS_THINKING=1 PI_NOFILLS_WORKING=1 PI_NOFILLS_FOOTER=1 PI_NOFILLS_HEADER=1 "
    )

    # Build pi command with explicit extension and no global extensions/themes
    pi_cmd = (
        f"{agent_cmd} "
        f'-e "{inject_extension}" '
        f'-e "{status_extension}" '
        f'-e "{nofrills_extension}" '
        f"--no-extensions "
        f"--no-themes "
        f"--offline "
        f'--session-dir "{pi_session_dir}" '
        f"--no-context-files "
        f"{personality_args} "
        f"{context_args}"
    )

    cmd = (
        f'cd "{work_dir}" && '
        f'rm -f "{injector_socket}" && '
        # Start heartbeat in background with all env vars
        f"env "
        f"AGENCY_ROLE=AGENT "
        f'AGENCY_DIR="{agency_dir}" '
        f"AGENCY_AGENT={agent_name} "
        f"AGENCY_SOCKET={socket_name} "
        f"AGENCY_POLL_INTERVAL={poll_interval} "
        f"AGENCY_PING_INTERVAL={ping_interval} "
        f'PI_INJECTOR_SOCKET="{injector_socket}" '
        f'PI_STATUS_SOCKET="{status_socket}" '
        f"python3 {heartbeat_path} > /dev/null 2>&1 & "
        # Give heartbeat a moment to start
        f"sleep 1 && "
        # Use env to ensure all vars are passed to pi
        f"env "
        f"AGENCY_ROLE=AGENT "
        f"AGENCY_PROJECT={session_name} "
        f'AGENCY_DIR="{agency_dir}" '
        f'AGENCY_WORKDIR="{work_dir}" '
        f"AGENCY_AGENT={agent_name} "
        f"AGENCY_SOCKET={socket_name} "
        f'PI_INJECTOR_SOCKET="{injector_socket}" '
        f'PI_STATUS_SOCKET="{status_socket}" '
        f"{nofrills_env}"
        f"{pi_cmd}"
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
