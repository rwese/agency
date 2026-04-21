"""TUI-specific commands for agent management."""

import os
import subprocess
from pathlib import Path

import yaml


# Constants from main module (duplicated to avoid circular imports)
TMUX_SOCKET = "agency"
SESSION_PREFIX = "agency-"
MANAGER_PREFIX = "agency-manager-"
AGENCY_DIR = Path.home() / ".config" / "agency"
AGENTS_DIR = AGENCY_DIR / "agents"
SESSIONS_DIR = AGENCY_DIR / "sessions"

# Shutdown message for graceful stop
SHUTDOWN_MESSAGE = (
    "Please wrap up, save your memories to your memory file, then exit gracefully. "
    "Say 'Goodbye' when done."
)
STOP_TIMEOUT = 30

WORDS = [
    "swift", "bold", "dark", "warm", "cool", "gray", "neon", "iron", "soft", "loud",
    "wolf", "fox", "bear", "hawk", "owl", "crow", "fish", "deer", "lynx", "crane",
]


def tmux(*args: str) -> subprocess.CompletedProcess:
    """Run a tmux command with agency socket."""
    result = subprocess.run(
        ["tmux", "-L", TMUX_SOCKET] + list(args),
        capture_output=True,
        text=True,
    )
    return result


def tmux_or_raise(*args: str) -> subprocess.CompletedProcess:
    """Run tmux command, raise on error."""
    result = tmux(*args)
    if result.returncode != 0:
        raise RuntimeError(f"tmux {' '.join(args)} failed: {result.stderr}")
    return result


def session_exists(session_name: str) -> bool:
    """Check if a tmux session exists."""
    result = tmux("has-session", "-t", session_name)
    return result.returncode == 0


def window_exists(session_name: str, window_name: str) -> bool:
    """Check if a window exists in a session."""
    result = tmux("list-windows", "-t", session_name, "-F", "#W")
    if result.returncode != 0:
        return False
    windows = [w.strip() for w in result.stdout.strip().split("\n") if w.strip()]
    return window_name in windows


def list_windows(session_name: str) -> list[str]:
    """List windows in a session."""
    result = tmux("list-windows", "-t", session_name, "-F", "#W")
    if result.returncode != 0:
        return []
    return [w.strip() for w in result.stdout.strip().split("\n") if w.strip() and w.strip() != "zsh"]


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


def load_agent_config(agent_name: str) -> dict | None:
    """Load agent configuration from YAML."""
    config_path = AGENTS_DIR / f"{agent_name}.yaml"
    if not config_path.exists():
        return None
    with open(config_path) as f:
        return yaml.safe_load(f)


def get_agent_cmd() -> str:
    """Get the agent command to run."""
    return os.environ.get("AGENCY_AGENT_CMD", "pi")


def send_keys(session_name: str, window_name: str, msg: str) -> None:
    """Send keys to a tmux window."""
    tmux("send-keys", "-t", f"{session_name}:{window_name}", msg, "Enter")


def generate_agent_script(
    session_name: str,
    window_name: str,
    agent_cmd: str,
    personality: str | None = None,
) -> Path:
    """Generate and write the agent launch script."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    # Create quiet settings for agent sessions
    pi_dir = SESSIONS_DIR / ".pi"
    pi_dir.mkdir(parents=True, exist_ok=True)
    settings_path = pi_dir / "settings.json"

    if not settings_path.exists():
        import json
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

    script_path = SESSIONS_DIR / f"{session_name}-{window_name}.sh"

    agency_dir = Path(__file__).parent.parent.absolute()

    # Build command with --no-context-files for clean persona
    base_cmd = f'{agent_cmd} --session-dir "{SESSIONS_DIR}" --no-context-files PI_CODING_AGENT=true'
    cmd = f'cd "{agency_dir}" && exec {base_cmd}'
    if personality:
        escaped = personality.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("`", "\\`")
        cmd += f' --append-system-prompt "{escaped}"'

    with open(script_path, "w") as f:
        f.write("#!/bin/bash\n")
        f.write(f"{cmd}\n")

    script_path.chmod(0o755)
    return script_path


def wait_for_exit(session_name: str, window_name: str, timeout: int) -> bool:
    """Wait for a window's process to exit within timeout."""
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
            return True
        import time
        time.sleep(1)

    return False


def start_agent(agent_name: str, work_dir: str) -> str:
    """Start an agent in a session."""
    # Expand tildes
    work_dir = os.path.expanduser(work_dir)

    # Create directory if needed
    Path(work_dir).mkdir(parents=True, exist_ok=True)

    # Load config
    config = load_agent_config(agent_name)
    if not config:
        raise ValueError(f"Config not found: {AGENTS_DIR / f'{agent_name}.yaml'}")

    personality = config.get("personality")

    # Generate session and window names
    session_name = make_session_name(work_dir)

    # Check if agent already exists
    if window_exists(session_name, agent_name):
        raise ValueError(f"Agent '{agent_name}' already exists in session '{session_name}'")

    window_name = make_window_name(agent_name, session_name)

    # Get agent command
    agent_cmd = get_agent_cmd()

    # Generate launch script
    script_path = generate_agent_script(
        session_name, window_name, agent_cmd, personality
    )

    # Create session or add window
    if session_exists(session_name):
        tmux_or_raise("new-window", "-d", "-t", session_name, "-n", window_name, "-c", work_dir)
    else:
        tmux_or_raise("new-session", "-d", "-s", session_name, "-c", work_dir)
        tmux_or_raise("new-window", "-d", "-t", session_name, "-n", window_name, "-c", work_dir)

    # Send command to run agent
    send_keys(session_name, window_name, str(script_path))

    return f"{session_name}:{window_name}"


def stop_agent(session_name: str, agent: str, force: bool = False) -> None:
    """Stop an agent gracefully."""
    if not session_exists(session_name):
        raise ValueError(f"Session not found: {session_name}")

    if not window_exists(session_name, agent):
        raise ValueError(f"Window '{agent}' not found in session '{session_name}'")

    # Send shutdown message
    send_keys(session_name, agent, SHUTDOWN_MESSAGE)

    if not force:
        if wait_for_exit(session_name, agent, STOP_TIMEOUT):
            return
        # Fall through to kill if graceful shutdown failed

    tmux_or_raise("kill-window", "-t", f"{session_name}:{agent}")
