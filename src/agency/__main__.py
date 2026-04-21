#!/usr/bin/env python3
"""
Agency v2.0 - AI Agent Session Manager

A tmux-based multi-agent orchestration tool.
"""

import argparse
import sys
from pathlib import Path

from agency import __version__
from agency.session import SessionManager
from agency.template import TemplateManager

VERSION = __version__


def find_agency_dir(path: Path = Path.cwd()) -> Path | None:
    """Find .agency/ directory by walking up from path."""
    current = path.absolute()
    while current != current.parent:
        if (current / ".agency").is_dir():
            return current / ".agency"
        current = current.parent
    return None


def cmd_init_project(args: argparse.Namespace) -> int:
    """Create a new project with session and .agency/ directory."""
    from agency.session import create_project_session

    work_dir = Path(args.dir).expanduser().absolute()

    if not work_dir.exists():
        work_dir.mkdir(parents=True, exist_ok=True)

    # Find git root
    git_root = find_git_root(work_dir)
    if not git_root:
        print("[ERROR] Not in a git repository", file=sys.stderr)
        print("[ERROR] Agency requires a git repository", file=sys.stderr)
        return 1

    agency_dir = git_root / ".agency"

    # Check if session already exists
    project_name = work_dir.name
    session_name = f"agency-{project_name}"
    sm = SessionManager(session_name)

    if sm.session_exists():
        if args.force:
            sm.kill_session()
        else:
            print(f"[ERROR] Session '{session_name}' already exists", file=sys.stderr)
            print("[ERROR] Use --force to overwrite", file=sys.stderr)
            return 1

    # Download template if specified
    template_url = args.template or "https://github.com/rwese/agency-templates"

    if template_url:
        tm = TemplateManager(
            template_url, cache_dir=Path.home() / ".cache" / "agency" / "templates"
        )
        template_path = tm.get_template(args.template_subdir or "basic", refresh=args.refresh)
        if template_path:
            print(f"[INFO] Using template from {template_url}")
            # Copy template to agency_dir
            _copy_template_to_agency(template_path, agency_dir)
        else:
            print(
                "[WARN] Could not download template, creating default structure", file=sys.stderr
            )
            _create_default_agency_structure(agency_dir)
    else:
        _create_default_agency_structure(agency_dir)

    # Create tmux session with socket
    socket_name = f"agency-{project_name}"
    create_project_session(session_name, socket_name, work_dir)

    print(f"[INFO] Created project session: {session_name}")
    print(f"[INFO] .agency/ created at: {agency_dir}")

    # Start manager if specified
    if args.start_manager:
        from agency.session import start_manager_window

        start_manager_window(session_name, socket_name, args.start_manager, agency_dir, work_dir)
        print(f"[INFO] Started manager: [MGR] {args.start_manager}")

    return 0


def _copy_template_to_agency(template_path: Path, agency_dir: Path) -> None:
    """Copy template files to .agency/ directory."""
    import shutil

    agency_dir.mkdir(parents=True, exist_ok=True)

    # Copy all files from template
    for item in template_path.rglob("*"):
        if item.is_file():
            rel_path = item.relative_to(template_path)
            dest = agency_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest)


def _create_default_agency_structure(agency_dir: Path) -> None:
    """Create default .agency/ directory structure."""

    agency_dir.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    (agency_dir / "agents").mkdir(exist_ok=True)
    (agency_dir / "tasks").mkdir(exist_ok=True)
    (agency_dir / "pending").mkdir(exist_ok=True)
    (agency_dir / ".scripts").mkdir(exist_ok=True)

    # Create default config.yaml
    config_path = agency_dir / "config.yaml"
    if not config_path.exists():
        config_path.write_text("""project: default
shell: bash
""")

    # Create default agents.yaml
    agents_path = agency_dir / "agents.yaml"
    if not agents_path.exists():
        agents_path.write_text("""agents: []
""")

    # Create default README.md
    readme_path = agency_dir / "README.md"
    if not readme_path.exists():
        readme_path.write_text("""# Agency Project

This project uses Agency for AI agent orchestration.

## Commands

```bash
# Start an agent
agency start <name> --dir .

# List tasks
agency tasks list

# Add a task
agency tasks add -d "Task description"
```
""")


def cmd_start(args: argparse.Namespace) -> int:
    """Start an agent or manager in the project session."""
    from agency.session import SessionManager, start_agent_window, start_manager_window

    name = args.name
    work_dir = Path(args.dir).expanduser().absolute()

    # Find git root
    git_root = find_git_root(work_dir)
    if not git_root:
        print("[ERROR] Not in a git repository", file=sys.stderr)
        return 1

    agency_dir = git_root / ".agency"
    if not agency_dir.exists():
        print(f"[ERROR] No .agency/ found in {git_root}", file=sys.stderr)
        print("[ERROR] Run 'agency init-project --dir <path>' first", file=sys.stderr)
        return 1

    project_name = work_dir.name
    session_name = f"agency-{project_name}"
    socket_name = f"agency-{project_name}"

    sm = SessionManager(session_name, socket_name=socket_name)

    # Create session if it doesn't exist
    if not sm.session_exists():
        print(f"[INFO] Creating new session: {session_name}")
        from agency.session import create_project_session

        create_project_session(session_name, socket_name, work_dir)

    # Check if it's a manager
    is_manager = (
        args.manager
        or (agency_dir / "manager.yaml").exists()
        and name == _get_manager_name(agency_dir)
    )

    if is_manager:
        # Check if manager already exists
        if sm.manager_exists():
            print("[ERROR] Manager already exists in session", file=sys.stderr)
            return 1
        start_manager_window(session_name, socket_name, name, agency_dir, work_dir)
        print(f"[INFO] Started manager: [MGR] {name}")
    else:
        # Check if agent config exists
        config_path = agency_dir / "agents" / f"{name}.yaml"
        if not config_path.exists():
            print(f"[ERROR] Agent config not found: {config_path}", file=sys.stderr)
            return 1

        # Check if agent already running
        if sm.window_exists(name):
            print(f"[INFO] Agent '{name}' already running, attaching...", file=sys.stderr)
        else:
            start_agent_window(session_name, socket_name, name, agency_dir, work_dir)
            print(f"[INFO] Started agent: {name}")

    return 0


def _get_manager_name(agency_dir: Path) -> str | None:
    """Get manager name from agency config."""
    # TODO: Implement when config loading is ready
    return None


def cmd_stop(args: argparse.Namespace) -> int:
    """Stop a session gracefully."""
    from agency.session import SessionManager

    session_name = args.session
    if not session_name.startswith("agency-"):
        session_name = f"agency-{session_name}"

    socket_name = session_name  # Same as session name for v2

    sm = SessionManager(session_name, socket_name=socket_name)

    if not sm.session_exists():
        print(f"[ERROR] Session not found: {session_name}", file=sys.stderr)
        return 1

    # Broadcast shutdown to all windows
    sm.broadcast_shutdown()

    # Wait for graceful exit
    import time

    timeout = args.timeout or 60
    interval = 2

    for _ in range(timeout // interval):
        time.sleep(interval)
        if not sm.session_exists():
            print("[INFO] Session stopped gracefully")
            # Clean up socket
            sm.cleanup_socket()
            return 0

    # Force kill
    print("[WARN] Graceful shutdown timed out, force killing...")
    sm.kill_session()
    sm.cleanup_socket()
    print("[INFO] Session killed")

    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    """Resume a halted session."""
    from agency.session import resume_halted_session

    session_name = args.session
    if not session_name.startswith("agency-"):
        session_name = f"agency-{session_name}"

    socket_name = session_name

    # Find agency dir
    work_dir = _find_work_dir_for_session(session_name)
    if not work_dir:
        print(f"[ERROR] Could not find project directory for {session_name}", file=sys.stderr)
        return 1

    agency_dir = work_dir / ".agency"
    halted_file = agency_dir / ".halted"

    if not halted_file.exists():
        print("[WARN] No halt marker found. Session may not be halted.")

    # Resume session
    if resume_halted_session(session_name, socket_name, agency_dir, work_dir):
        print(f"[INFO] Resumed session: {session_name}")
        return 0
    else:
        print("[ERROR] Failed to resume session", file=sys.stderr)
        return 1


def _find_work_dir_for_session(session_name: str) -> Path | None:
    """Find the working directory for a session by searching common locations."""
    # TODO: Implement session registry or metadata
    # For now, this is a placeholder
    return None


def cmd_attach(args: argparse.Namespace) -> int:
    """Attach to a session."""
    import os

    session_name = args.session
    if not session_name.startswith("agency-"):
        session_name = f"agency-{session_name}"

    socket_name = session_name

    # Use tmux attach
    os.execvp("tmux", ["tmux", "-L", socket_name, "attach-session", "-t", session_name])


def cmd_list(args: argparse.Namespace) -> int:
    """List all agency sessions."""
    from agency.session import list_agency_sessions

    sessions = list_agency_sessions()

    if not sessions:
        print("[INFO] No agency sessions running")
        return 0

    for session in sessions:
        print(f"{session['name']}")
        for window in session.get("windows", []):
            is_manager = window.get("is_manager", False)
            prefix = "  [MGR] " if is_manager else "  "
            print(f"{prefix}{window['name']}")

    return 0


def cmd_tasks(args: argparse.Namespace) -> int:
    """Task management commands."""
    from agency.tasks.cli import handle_tasks_command

    # Find agency dir
    agency_dir = find_agency_dir()
    if not agency_dir:
        print("[ERROR] No .agency/ found", file=sys.stderr)
        print("[ERROR] Run 'agency init-project --dir <path>' first", file=sys.stderr)
        return 1

    return handle_tasks_command(args, agency_dir)


def cmd_version(args: argparse.Namespace) -> int:
    """Show version."""
    print(f"agency {VERSION}")
    return 0


def find_git_root(path: Path = Path.cwd()) -> Path | None:
    """Find the git repository root containing the given path."""
    current = path.absolute()
    while current != current.parent:
        if (current / ".git").is_dir():
            return current
        current = current.parent
    return None


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        description="Agency - AI Agent Session Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--version", action="version", version=f"agency {VERSION}")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # init-project
    init_parser = subparsers.add_parser("init-project", help="Create a new project")
    init_parser.add_argument("--dir", required=True, help="Project directory")
    init_parser.add_argument("--template", help="Template repository URL")
    init_parser.add_argument("--template-subdir", help="Template subdirectory")
    init_parser.add_argument("--start-manager", help="Start manager on init")
    init_parser.add_argument("--force", action="store_true", help="Overwrite existing")
    init_parser.add_argument("--refresh", action="store_true", help="Bypass template cache")

    # start
    start_parser = subparsers.add_parser("start", help="Start an agent or manager")
    start_parser.add_argument("name", help="Agent or manager name")
    start_parser.add_argument("--dir", required=True, help="Project directory")
    start_parser.add_argument("--manager", action="store_true", help="Start as manager")

    # stop
    stop_parser = subparsers.add_parser("stop", help="Stop a session")
    stop_parser.add_argument("session", help="Session name")
    stop_parser.add_argument("--timeout", type=int, help="Grace period in seconds")

    # resume
    resume_parser = subparsers.add_parser("resume", help="Resume a halted session")
    resume_parser.add_argument("session", help="Session name")

    # attach
    attach_parser = subparsers.add_parser("attach", help="Attach to a session")
    attach_parser.add_argument("session", help="Session name")

    # list
    subparsers.add_parser("list", help="List sessions")

    # tasks
    tasks_parser = subparsers.add_parser("tasks", help="Task management")
    tasks_sub = tasks_parser.add_subparsers(dest="tasks_command", help="Task commands")

    # tasks list
    tasks_list = tasks_sub.add_parser("list", help="List tasks")
    tasks_list.add_argument("--status", help="Filter by status")
    tasks_list.add_argument("--assignee", help="Filter by assignee")

    # tasks add
    tasks_add = tasks_sub.add_parser("add", help="Add a task")
    tasks_add.add_argument("-d", "--description", required=True, help="Task description")
    tasks_add.add_argument("-a", "--assignee", help="Assign to agent")
    tasks_add.add_argument("-p", "--priority", default="low", help="Priority: low, normal, high")

    # tasks show
    tasks_show = tasks_sub.add_parser("show", help="Show task")
    tasks_show.add_argument("task_id", help="Task ID")

    # tasks assign
    tasks_assign = tasks_sub.add_parser("assign", help="Assign task")
    tasks_assign.add_argument("task_id", help="Task ID")
    tasks_assign.add_argument("agent", help="Agent name")

    # tasks complete
    tasks_complete = tasks_sub.add_parser("complete", help="Complete task")
    tasks_complete.add_argument("task_id", help="Task ID")
    tasks_complete.add_argument("--result", required=True, help="Result summary")
    tasks_complete.add_argument("--files", help="JSON array of files")
    tasks_complete.add_argument("--diff", help="Git diff")
    tasks_complete.add_argument("--summary", help="Summary")

    # tasks update
    tasks_update = tasks_sub.add_parser("update", help="Update task")
    tasks_update.add_argument("task_id", help="Task ID")
    tasks_update.add_argument("--status", help="New status")
    tasks_update.add_argument("--priority", help="New priority")

    # tasks delete
    tasks_delete = tasks_sub.add_parser("delete", help="Delete task")
    tasks_delete.add_argument("task_id", help="Task ID")

    # tasks history
    tasks_history = tasks_sub.add_parser("history", help="Show task history")
    tasks_history.add_argument("--agent", help="Filter by agent")

    # completions
    comp_parser = subparsers.add_parser("completions", help="Print shell completions")
    comp_parser.add_argument("shell", choices=["bash", "zsh", "fish"], help="Shell type")

    return parser


def main() -> int:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # Dispatch commands
    if args.command == "init-project":
        return cmd_init_project(args)
    elif args.command == "start":
        return cmd_start(args)
    elif args.command == "stop":
        return cmd_stop(args)
    elif args.command == "resume":
        return cmd_resume(args)
    elif args.command == "attach":
        return cmd_attach(args)
    elif args.command == "list":
        return cmd_list(args)
    elif args.command == "tasks":
        return cmd_tasks(args)
    elif args.command == "completions":
        return cmd_completions(args)
    elif args.command == "version":
        return cmd_version(args)
    else:
        parser.print_help()
        return 0


def cmd_completions(args: argparse.Namespace) -> int:
    """Print shell completion script."""
    # TODO: Implement completions
    print(f"# {args.shell} completions for agency")
    return 0


if __name__ == "__main__":
    sys.exit(main())
