#!/usr/bin/env python3
"""
Agency - AI Agent Session Manager

A Python-based tmux session manager for AI agents.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

VERSION = "0.2.0"

# Paths
AGENCY_DIR = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "agency"
AGENTS_DIR = AGENCY_DIR / "agents"
SESSIONS_DIR = AGENCY_DIR / "sessions"
SESSION_PREFIX = "agency-"

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


def cmd_init() -> None:
    """Initialize agency config directory."""
    AGENCY_DIR.mkdir(parents=True, exist_ok=True)
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    example_config = AGENTS_DIR / "example.yaml"
    with open(example_config, "w") as f:
        f.write("""name: example
personality: |
  An example agent personality description.
  Modify this to customize how the agent behaves.
""")
    
    log_info(f"Initialized agency config in {AGENCY_DIR}")
    log_info(f"Created example config: {example_config}")
    log_info("Edit the config and run: agency start example --dir ~/projects")


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
            log_info(f"Some windows did not exit gracefully, force killing...")
        
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
    subparsers.add_parser("init", help="Initialize agency config")
    
    # start
    start_parser = subparsers.add_parser("start", help="Start an agent")
    start_parser.add_argument("name", help="Agent name")
    start_parser.add_argument("--dir", required=True, help="Working directory")
    
    # list
    subparsers.add_parser("list", help="List running sessions")
    
    # send
    send_parser = subparsers.add_parser("send", help="Send message to agent")
    send_parser.add_argument("session", help="Session name")
    send_parser.add_argument("target", nargs="?", help="Agent name (optional if single window)")
    send_parser.add_argument("message", nargs="+", help="Message to send")
    
    # stop
    stop_parser = subparsers.add_parser("stop", help="Stop session gracefully")
    stop_parser.add_argument("session", help="Session[:agent]")
    
    # kill
    kill_parser = subparsers.add_parser("kill", help="Force kill session")
    kill_parser.add_argument("session", help="Session[:agent]")
    
    # kill-all
    subparsers.add_parser("kill-all", help="Kill all agency sessions")
    
    # attach
    attach_parser = subparsers.add_parser("attach", help="Attach to an agency session")
    attach_parser.add_argument("session", help="Session name")
    attach_parser.add_argument("target", nargs="?", help="Agent/window name (optional)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "init":
        cmd_init()
    elif args.command == "start":
        cmd_start(args.name, args.dir)
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
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
