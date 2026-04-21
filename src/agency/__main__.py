#!/usr/bin/env python3
"""
Agency v2.0 - AI Agent Session Manager

A tmux-based multi-agent orchestration tool.
"""

import os
import subprocess
import sys
from pathlib import Path

import click

from agency import __version__
from agency.config import (
    load_agency_config,
    load_agents_config,
    load_manager_config,
)
from agency.session import (
    SessionManager,
    create_project_session,
    start_agent_window,
    start_manager_window,
)
from agency.tasks import TaskStore
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


def find_git_root(path: Path = Path.cwd()) -> Path | None:
    """Find the git repository root containing the given path."""
    current = path.absolute()
    while current != current.parent:
        if (current / ".git").is_dir():
            return current
        current = current.parent
    return None


@click.group()
@click.version_option(version=VERSION)
@click.pass_context
def cli(ctx):
    """Agency - AI Agent Session Manager."""
    role = os.environ.get("AGENCY_ROLE", "").upper()
    if role in ("MANAGER", "AGENT"):
        ctx.info_name = f"agency ({role.lower()})"


# === Project Commands ===


# === Project Commands ===


@click.command()
@click.option("--dir", "dir", type=click.Path(), default=".", help="Project directory (default: current)")
@click.option("--template", help="Template repository URL")
@click.option("--template-subdir", help="Template subdirectory")
@click.option("--force", is_flag=True, help="Overwrite existing")
@click.option("--refresh", is_flag=True, help="Bypass template cache")
def init_project(dir, template, template_subdir, force, refresh):
    """Create a new project with session and .agency/ directory.

    Creates .agency/ in the project directory. Use --dir to specify,
    defaults to current directory.
    """
    work_dir = Path(dir).expanduser().absolute()

    if not work_dir.exists():
        work_dir.mkdir(parents=True, exist_ok=True)

    # Find git root (optional - for session naming)
    git_root = find_git_root(work_dir)

    # Create .agency/ in work_dir (not git root) unless git_root equals work_dir
    if git_root and git_root != work_dir:
        agency_dir = work_dir / ".agency"
    else:
        agency_dir = work_dir / ".agency"

    # Use work_dir name for session
    project_name = work_dir.name
    session_name = f"agency-{project_name}"
    socket_name = f"agency-{project_name}"
    sm = SessionManager(session_name, socket_name=socket_name)

    if sm.session_exists():
        if force:
            sm.kill_session()
        else:
            click.echo(f"[ERROR] Session '{session_name}' already exists", err=True)
            click.echo("[ERROR] Use --force to overwrite", err=True)
            sys.exit(1)

    # Download template if specified
    template_url = template or "https://github.com/rwese/agency-templates"

    if template_url:
        tm = TemplateManager(template_url, cache_dir=Path.home() / ".cache" / "agency" / "templates")
        template_path = tm.get_template(template_subdir or "basic", refresh=refresh)
        if template_path:
            click.echo(f"[INFO] Using template from {template_url}")
            _copy_template_to_agency(template_path, agency_dir)
        else:
            click.echo("[WARN] Could not download template, creating default structure", err=True)
            _create_default_agency_structure(agency_dir)
    else:
        _create_default_agency_structure(agency_dir)

    # Create tmux session with socket
    create_project_session(session_name, socket_name, work_dir)

    click.echo(f"[INFO] Created project session: {session_name}")
    click.echo(f"[INFO] .agency/ created at: {agency_dir}")
    click.echo("[INFO] Run 'agency start' to start agents")


def _copy_template_to_agency(template_path: Path, agency_dir: Path) -> None:
    """Copy template files to .agency/ directory."""
    import shutil

    agency_dir.mkdir(parents=True, exist_ok=True)

    # Check if template has .agency/ inside
    template_agency = template_path / ".agency"
    source_dir = template_agency if template_agency.exists() else template_path

    for item in source_dir.rglob("*"):
        if item.is_file():
            rel_path = item.relative_to(source_dir)
            dest = agency_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest)


def _create_default_agency_structure(agency_dir: Path) -> None:
    """Create default .agency/ directory structure."""

    agency_dir.mkdir(parents=True, exist_ok=True)
    (agency_dir / "agents").mkdir(exist_ok=True)
    (agency_dir / "tasks").mkdir(exist_ok=True)
    (agency_dir / "pending").mkdir(exist_ok=True)
    (agency_dir / ".scripts").mkdir(exist_ok=True)

    config_path = agency_dir / "config.yaml"
    if not config_path.exists():
        config_path.write_text("project: default\nshell: bash\n")

    agents_path = agency_dir / "agents.yaml"
    if not agents_path.exists():
        agents_path.write_text("agents: []\n")

    readme_path = agency_dir / "README.md"
    if not readme_path.exists():
        readme_path.write_text("# Agency Project\n\nThis project uses Agency for AI agent orchestration.\n")


@click.command()
@click.option(
    "--dir",
    "dir",
    type=click.Path(),
    default=None,
    help="Project directory (auto-detected from .agency/)",
)
def start(dir):
    """Start the agency (manager + all agents).

    Auto-detects project directory from .agency/ if not specified.
    """
    # Auto-detect from .agency/ if --dir not provided
    if dir:
        work_dir = Path(dir).expanduser().absolute()
    else:
        agency_dir_path = find_agency_dir()
        if not agency_dir_path:
            click.echo("[ERROR] No .agency/ found", err=True)
            click.echo("[ERROR] Run 'agency init' or use --dir", err=True)
            sys.exit(1)
        work_dir = agency_dir_path.parent

    git_root = find_git_root(work_dir)
    if not git_root:
        click.echo("[ERROR] Not in a git repository", err=True)
        sys.exit(1)

    agency_dir = git_root / ".agency"
    if not agency_dir.exists():
        click.echo(f"[ERROR] No .agency/ found in {git_root}", err=True)
        click.echo("[ERROR] Run 'agency init' first", err=True)
        sys.exit(1)

    project_name = work_dir.name
    session_name = f"agency-{project_name}"
    socket_name = f"agency-{project_name}"

    sm = SessionManager(session_name, socket_name=socket_name)

    # Create session if it doesn't exist
    if not sm.session_exists():
        click.echo(f"[INFO] Creating new session: {session_name}")
        create_project_session(session_name, socket_name, work_dir)

    # Start all members
    _start_all_members(session_name, socket_name, agency_dir, work_dir, sm)


def _start_all_members(
    session_name: str,
    socket_name: str,
    agency_dir: Path,
    work_dir: Path,
    sm: SessionManager,
) -> None:
    """Start all configured members (manager + agents)."""
    # Load manager config
    manager_config = load_manager_config(agency_dir)
    manager_name = manager_config.name if manager_config else "coordinator"

    # Load agents config
    agents = load_agents_config(agency_dir)

    if not manager_config and not agents:
        click.echo("[WARN] No manager or agents configured", err=True)
        return

    click.echo(f"[INFO] Starting all members for {session_name}")

    # Start manager first
    if manager_config:
        if sm.manager_exists():
            click.echo(f"  [SKIP] Manager already running: [MGR] {manager_name}")
        else:
            start_manager_window(session_name, socket_name, manager_name, agency_dir, work_dir)
            click.echo(f"  [OK] Started: [MGR] {manager_name}")

    # Start all agents
    for agent in agents:
        if sm.window_exists(agent.name):
            click.echo(f"  [SKIP] Agent already running: {agent.name}")
        else:
            start_agent_window(session_name, socket_name, agent.name, agency_dir, work_dir)
            click.echo(f"  [OK] Started: {agent.name}")

    click.echo("[INFO] All members started")


def _get_manager_name(agency_dir: Path) -> str | None:
    """Get manager name from agency config."""
    return None


@click.command()
@click.argument("session", required=False)
@click.option("--timeout", type=int, help="Grace period in seconds (default: 300)")
@click.option("--force", is_flag=True, help="Force kill without graceful shutdown")
def stop(session, timeout, force):
    """Stop a session gracefully.

    Auto-detects session from .agency/ if not specified.
    """
    # Auto-detect from .agency/ if session not provided
    if not session:
        agency_dir_path = find_agency_dir()
        if not agency_dir_path:
            click.echo("[ERROR] No .agency/ found", err=True)
            click.echo("[ERROR] Use 'agency stop <session>' or run from project directory", err=True)
            sys.exit(1)
        work_dir = agency_dir_path.parent
        session = f"agency-{work_dir.name}"
    elif not session.startswith("agency-"):
        session = f"agency-{session}"

    socket_name = session
    sm = SessionManager(session, socket_name=socket_name)

    if not sm.session_exists():
        click.echo(f"[ERROR] Session not found: {session}", err=True)
        sys.exit(1)

    if force:
        # Direct kill
        sm.kill_session()
        sm.cleanup_socket()
        click.echo("[INFO] Session killed")
        return

    # Broadcast shutdown to all windows
    sm.broadcast_shutdown()

    # Wait for graceful exit
    import time

    timeout = timeout or 300  # 5 minutes default
    interval = 0.5

    elapsed = 0.0
    while elapsed < timeout:
        time.sleep(interval)
        elapsed += interval
        if not sm.session_exists():
            click.echo("[INFO] Session stopped gracefully")
            sm.cleanup_socket()
            return

    # Force kill
    click.echo("[WARN] Graceful shutdown timed out, force killing...", err=True)
    sm.kill_session()
    sm.cleanup_socket()
    click.echo("[INFO] Session killed")


@click.command()
@click.argument("session", required=False)
def kill(session):
    """Force kill a session immediately.

    Auto-detects session from .agency/ if not specified.
    """
    # Auto-detect from .agency/ if session not provided
    if not session:
        agency_dir_path = find_agency_dir()
        if not agency_dir_path:
            click.echo("[ERROR] No .agency/ found", err=True)
            click.echo("[ERROR] Use 'agency kill <session>' or run from project directory", err=True)
            sys.exit(1)
        work_dir = agency_dir_path.parent
        session = f"agency-{work_dir.name}"
    elif not session.startswith("agency-"):
        session = f"agency-{session}"

    socket_name = session
    sm = SessionManager(session, socket_name=socket_name)

    if not sm.session_exists():
        click.echo(f"[ERROR] Session not found: {session}", err=True)
        sys.exit(1)

    sm.kill_session()
    sm.cleanup_socket()
    click.echo(f"[INFO] Session {session} killed")


@click.command()
@click.option(
    "--dir",
    "dir",
    type=click.Path(),
    default=None,
    help="Project directory (auto-detected from .agency/)",
)
def resume(dir):
    """Resume a halted session.

    Auto-detects session from .agency/ if not specified.
    """
    # Auto-detect from .agency/ if --dir not provided
    if dir:
        work_dir = Path(dir).expanduser().absolute()
    else:
        agency_dir_path = find_agency_dir()
        if not agency_dir_path:
            click.echo("[ERROR] No .agency/ found", err=True)
            sys.exit(1)
        work_dir = agency_dir_path.parent

    git_root = find_git_root(work_dir)
    if not git_root:
        click.echo("[ERROR] Not in a git repository", err=True)
        sys.exit(1)

    agency_dir = git_root / ".agency"
    halted_file = agency_dir / ".halted"

    if not halted_file.exists():
        click.echo("[WARN] No halt marker found. Session may not be halted.", err=True)

    project_name = work_dir.name
    session_name = f"agency-{project_name}"
    socket_name = session_name

    from agency.session import resume_halted_session

    if resume_halted_session(session_name, socket_name, agency_dir, work_dir):
        click.echo(f"[INFO] Resumed session: {session_name}")
    else:
        click.echo("[ERROR] Failed to resume session", err=True)
        sys.exit(1)


def _find_work_dir_for_session(session_name: str) -> Path | None:
    """Find the working directory for a session."""
    # TODO: Implement session registry
    return None


@click.command()
@click.option(
    "--dir",
    "dir",
    type=click.Path(),
    default=None,
    help="Project directory (auto-detected from .agency/)",
)
def attach(dir):
    """Attach to the project session.

    Auto-detects session from .agency/ directory.
    """
    # Auto-detect from .agency/ if --dir not provided
    if dir:
        work_dir = Path(dir).expanduser().absolute()
    else:
        agency_dir_path = find_agency_dir()
        if not agency_dir_path:
            click.echo("[ERROR] No .agency/ found", err=True)
            sys.exit(1)
        work_dir = agency_dir_path.parent

    git_root = find_git_root(work_dir)
    if not git_root:
        click.echo("[ERROR] Not in a git repository", err=True)
        sys.exit(1)

    agency_dir = git_root / ".agency"
    if not agency_dir.exists():
        click.echo(f"[ERROR] No .agency/ found in {git_root}", err=True)
        sys.exit(1)

    project_name = work_dir.name
    session_name = f"agency-{project_name}"

    # Use tmux attach
    os.execvp("tmux", ["tmux", "-L", session_name, "attach-session", "-t", session_name])


@click.command()
@click.option(
    "--dir",
    "dir",
    type=click.Path(),
    default=None,
    help="Project directory (auto-detected from .agency/)",
)
def list(dir):
    """List agency sessions.

    Shows sessions from current project or all agency sessions.
    """
    # Check if we're in an agency project
    if dir:
        work_dir = Path(dir).expanduser().absolute()
    else:
        agency_dir_path = find_agency_dir()
        work_dir = agency_dir_path.parent if agency_dir_path else None

    # If in a project, show that session first
    if work_dir and (work_dir / ".agency").exists():
        project_name = work_dir.name
        session_name = f"agency-{project_name}"
        sm = SessionManager(session_name, socket_name=session_name)

        if sm.session_exists():
            click.echo(f"{session_name} (current)")
            for w in sm.list_windows():
                click.echo(f"  {w}")
            click.echo("")

    # Also show all sessions on default socket
    from agency.session import list_agency_sessions

    sessions = list_agency_sessions()

    if sessions:
        click.echo("# All Sessions")
        for session in sessions:
            click.echo(f"{session['name']}")
            for window in session.get("windows", []):
                click.echo(f"  {window['name']}")
    elif (
        not work_dir
        or not (work_dir / ".agency").exists()
        or not SessionManager(f"agency-{work_dir.name}", socket_name=f"agency-{work_dir.name}").session_exists()
    ):
        click.echo("[INFO] No agency sessions running")


@click.command()
@click.option(
    "--dir",
    "dir",
    type=click.Path(),
    default=None,
    help="Project directory (auto-detected from .agency/)",
)
def members(dir):
    """Show all configured members (manager and agents)."""
    # Auto-detect from .agency/ if --dir not provided
    if dir:
        work_dir = Path(dir).expanduser().absolute()
    else:
        agency_dir_path = find_agency_dir()
        if not agency_dir_path:
            click.echo("[ERROR] No .agency/ found", err=True)
            click.echo("[ERROR] Run 'agency init-project' or use --dir", err=True)
            sys.exit(1)
        work_dir = agency_dir_path.parent

    git_root = find_git_root(work_dir)
    if not git_root:
        click.echo("[ERROR] Not in a git repository", err=True)
        sys.exit(1)

    agency_dir = git_root / ".agency"
    if not agency_dir.exists():
        click.echo(f"[ERROR] No .agency/ found in {git_root}", err=True)
        sys.exit(1)

    # Load configs
    manager_config = load_manager_config(agency_dir)
    agents = load_agents_config(agency_dir)

    # Get running status
    project_name = work_dir.name
    session_name = f"agency-{project_name}"
    sm = SessionManager(session_name, socket_name=session_name)
    running_windows = sm.list_windows() if sm.session_exists() else []

    click.echo(f"# {project_name}")
    click.echo("")

    # Show manager
    click.echo("## Manager")
    click.echo("")
    if manager_config:
        is_running = any(w.startswith("[MGR]") for w in running_windows)
        status = "🟢 running" if is_running else "⚪ stopped"
        click.echo(f"- **Name**: {manager_config.name}")
        click.echo(f"- **Status**: {status}")
        if manager_config.personality:
            preview = (
                manager_config.personality[:50] + "..."
                if len(manager_config.personality) > 50
                else manager_config.personality
            )
            click.echo(f"- **Personality**: {preview}")
    else:
        click.echo("- _No manager configured_")
    click.echo("")

    # Show agents
    click.echo("## Agents")
    click.echo("")
    if agents:
        for agent in agents:
            is_running = agent.name in running_windows
            status = "🟢 running" if is_running else "⚪ stopped"
            click.echo(f"### {agent.name}")
            click.echo("")
            click.echo(f"- **Status**: {status}")
            if agent.personality:
                preview = agent.personality[:50] + "..." if len(agent.personality) > 50 else agent.personality
                click.echo(f"- **Personality**: {preview}")
            click.echo("")
    else:
        click.echo("- _No agents configured_")
        click.echo("")


# === Task Commands ===


@click.group()
def tasks():
    """Task management commands."""


# Agent-only tasks (limited commands)
@click.group()
def tasks_agent():
    """Task commands for agents."""
    pass


@tasks.command("list")
@click.option("--status", help="Filter by status")
@click.option("--assignee", help="Filter by assignee")
def tasks_list(status, assignee):
    """List tasks."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        click.echo("[ERROR] Run 'agency init-project --dir <path>' first", err=True)
        sys.exit(1)

    store = TaskStore(agency_dir)
    task_list = store.list_tasks(status=status, assignee=assignee)

    if not task_list:
        click.echo("No tasks found")
        return

    for task in task_list:
        status_icon = {
            "pending": "⏳",
            "in_progress": "🔄",
            "pending_approval": "👀",
            "completed": "✅",
            "failed": "❌",
        }.get(task.status, "?")

        click.echo(f"## {task.task_id}")
        click.echo("")
        click.echo(f"- status: {task.status} {status_icon}")
        click.echo(f"- priority: {task.priority}")
        click.echo(f"- assigned_to: {task.assigned_to or 'null'}")
        click.echo(f"- description: {task.description}")
        click.echo(f"- created_at: {task.created_at}")
        if task.started_at:
            click.echo(f"- started_at: {task.started_at}")
        if task.completed_at:
            click.echo(f"- completed_at: {task.completed_at}")
        click.echo("")


@tasks.command("add")
@click.option("-d", "--description", required=True, help="Task description")
@click.option("-a", "--assignee", help="Assign to agent")
@click.option("-p", "--priority", default="low", help="Priority: low, normal, high")
def tasks_add(description, assignee, priority):
    """Add a new task."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)

    store = TaskStore(agency_dir)
    task = store.add_task(description=description, priority=priority, assigned_to=assignee)
    click.echo(f"[INFO] Created task: {task.task_id}")


@tasks.command("show")
@click.argument("task_id")
def tasks_show(task_id):
    """Show task details."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)

    store = TaskStore(agency_dir)
    task = store.get_task(task_id)

    if not task:
        click.echo(f"[ERROR] Task not found: {task_id}", err=True)
        sys.exit(1)

    status_icon = {
        "pending": "⏳",
        "in_progress": "🔄",
        "pending_approval": "👀",
        "completed": "✅",
        "failed": "❌",
    }.get(task.status, "?")

    click.echo(f"# {task.task_id}")
    click.echo("")
    click.echo("## Task")
    click.echo("")
    click.echo(f"- **Description**: {task.description}")
    click.echo(f"- **Status**: {task.status} {status_icon}")
    click.echo(f"- **Priority**: {task.priority}")
    click.echo(f"- **Assigned to**: {task.assigned_to or 'Unassigned'}")
    click.echo(f"- **Created**: {task.created_at or 'Unknown'}")
    click.echo(f"- **Started**: {task.started_at or 'Not started'}")
    click.echo(f"- **Completed**: {task.completed_at or 'In progress'}")
    click.echo("")

    if task.result:
        click.echo("## Result")
        click.echo("")
        click.echo(task.result)
        click.echo("")


@tasks.command("assign")
@click.argument("task_id")
@click.argument("agent")
def tasks_assign(task_id, agent):
    """Assign task to an agent."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)

    store = TaskStore(agency_dir)

    if not store.is_agent_free(agent):
        click.echo(f"[WARN] Agent '{agent}' may not be free (has pending/in_progress tasks)", err=True)

    if store.assign_task(task_id, agent):
        click.echo(f"[INFO] Assigned {task_id} to {agent}")
    else:
        click.echo("[ERROR] Failed to assign task", err=True)
        sys.exit(1)


@tasks.command("complete")
@click.argument("task_id")
@click.option("--result", required=True, help="Result summary")
@click.option("--files", help="JSON array of files")
@click.option("--diff", help="Git diff")
@click.option("--summary", help="Summary")
def tasks_complete(task_id, result, files, diff, summary):
    """Complete a task."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)

    store = TaskStore(agency_dir)

    import json

    files_list = None
    if files:
        try:
            files_list = json.loads(files)
        except json.JSONDecodeError:
            click.echo("[ERROR] Invalid JSON in --files", err=True)
            sys.exit(1)

    if store.complete_task(
        task_id=task_id,
        result=result,
        files=files_list,
        diff=diff,
        summary=summary,
    ):
        click.echo(f"[INFO] Task {task_id} marked for approval")
    else:
        click.echo("[ERROR] Failed to complete task", err=True)
        sys.exit(1)


@tasks.command("approve")
@click.argument("task_id")
def tasks_approve(task_id):
    """Approve a pending task completion."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)

    store = TaskStore(agency_dir)
    if store.approve_task(task_id):
        click.echo(f"[INFO] Task {task_id} approved and archived")
    else:
        click.echo("[ERROR] Failed to approve task", err=True)
        sys.exit(1)


@tasks.command("reject")
@click.argument("task_id")
@click.option("--reason", required=True, help="Rejection reason")
@click.argument("suggestions", nargs=-1, required=False)
def tasks_reject(task_id, suggestions, reason):
    """Reject a pending task completion."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)

    store = TaskStore(agency_dir)
    if store.reject_task(task_id, reason=reason, suggestions=list(suggestions) if suggestions else None):
        click.echo(f"[INFO] Task {task_id} rejected")
    else:
        click.echo("[ERROR] Failed to reject task", err=True)
        sys.exit(1)


@tasks.command("reopen")
@click.argument("task_id")
def tasks_reopen(task_id):
    """Reopen a completed or failed task."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)

    store = TaskStore(agency_dir)
    task = store.get_task(task_id)

    if not task:
        click.echo(f"[ERROR] Task not found: {task_id}", err=True)
        sys.exit(1)

    if task.status not in ("completed", "failed"):
        click.echo(f"[ERROR] Task {task_id} is not completed or failed", err=True)
        sys.exit(1)

    if store.update_task(task_id, status="pending"):
        # Clear result fields
        task_json_path = agency_dir / "tasks" / task_id / "task.json"
        if task_json_path.exists():
            import json

            data = json.loads(task_json_path.read_text())
            data["status"] = "pending"
            data["completed_at"] = None
            data["result"] = None
            task_json_path.write_text(json.dumps(data, indent=2))

        click.echo(f"[INFO] Task {task_id} reopened")
    else:
        click.echo("[ERROR] Failed to reopen task", err=True)
        sys.exit(1)


@tasks.command("update")
@click.argument("task_id")
@click.option("--status", help="New status")
@click.option("--priority", help="New priority")
def tasks_update(task_id, status, priority):
    """Update a task."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)

    if not status and not priority:
        click.echo("[ERROR] At least one of --status or --priority required", err=True)
        sys.exit(1)

    store = TaskStore(agency_dir)
    if store.update_task(task_id, status=status, priority=priority):
        click.echo(f"[INFO] Updated task {task_id}")
    else:
        click.echo("[ERROR] Failed to update task", err=True)
        sys.exit(1)


@tasks.command("delete")
@click.argument("task_id")
def tasks_delete(task_id):
    """Delete a task."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)

    store = TaskStore(agency_dir)
    if store.delete_task(task_id):
        click.echo(f"[INFO] Deleted task {task_id}")
    else:
        click.echo("[ERROR] Failed to delete task", err=True)
        sys.exit(1)


@tasks.command("history")
@click.option("--agent", help="Filter by agent")
def tasks_history(agent):
    """Show task history."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)

    store = TaskStore(agency_dir)
    history = store.history(agent=agent)

    if not history:
        click.echo("No completed tasks found")
        return

    click.echo("## Completed Tasks")
    click.echo("")

    for item in history:
        task = item["task"]
        result = item.get("result", {})

        status_icon = "✅" if task["status"] == "completed" else "❌"

        click.echo(f"### {task['task_id']} {status_icon}")
        click.echo(f"- **Agent**: {task.get('assigned_to', 'unknown')}")
        click.echo(f"- **Completed**: {task.get('completed_at', 'unknown')}")

        if result:
            res = result.get("result", "No result")
            if len(res) > 100:
                res = res[:100] + "..."
            click.echo(f"- **Result**: {res}")

        click.echo("")


# === Agent-only task commands ===


def _get_agent_name():
    """Get agent name from AGENCY_AGENT env var."""
    agent = os.environ.get("AGENCY_AGENT", "")
    if not agent:
        click.echo("[ERROR] AGENCY_AGENT not set", err=True)
        sys.exit(1)
    return agent


def _verify_task_ownership(agency_dir: Path, task_id: str, agent: str) -> bool:
    """Verify task is assigned to this agent."""
    store = TaskStore(agency_dir)
    task = store.get_task(task_id)
    if not task:
        click.echo(f"[ERROR] Task not found: {task_id}", err=True)
        return False
    if task.assigned_to != agent:
        click.echo(f"[ERROR] Task {task_id} not assigned to you", err=True)
        return False
    return True


@tasks_agent.command("list")
def agent_tasks_list():
    """List tasks assigned to you."""
    agent = _get_agent_name()
    tasks_list(status=None, assignee=agent)


@tasks_agent.command("show")
@click.argument("task_id")
def agent_tasks_show(task_id):
    """Show task details."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)
    agent = _get_agent_name()
    if not _verify_task_ownership(agency_dir, task_id, agent):
        sys.exit(1)
    tasks_show(task_id)


@tasks_agent.command("update")
@click.argument("task_id")
@click.option("--status", help="Status: pending, in_progress, pending_approval")
@click.option("--priority", help="Priority: low, normal, high")
def agent_tasks_update(task_id, status, priority):
    """Update task status or priority."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)
    agent = _get_agent_name()
    if not _verify_task_ownership(agency_dir, task_id, agent):
        sys.exit(1)
    tasks_update(task_id, status, priority)


@tasks_agent.command("complete")
@click.argument("task_id")
@click.option("--result", required=True, help="Result summary")
@click.option("--files", help="JSON array of files")
@click.option("--diff", help="Git diff")
@click.option("--summary", help="Summary")
def agent_tasks_complete(task_id, result, files, diff, summary):
    """Complete a task."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)
    agent = _get_agent_name()
    if not _verify_task_ownership(agency_dir, task_id, agent):
        sys.exit(1)
    tasks_complete(task_id, result, files, diff, summary)


# === Completions ===


@click.command()
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
def completions(shell):
    """Print shell completion script."""
    from agency.completions import get_completion_script

    click.echo(get_completion_script(shell))


# === Tmux Commands ===


@click.group("tmux")
def tmux_cmd():
    """Tmux session operations via agency config."""
    pass


@tmux_cmd.command("list")
@click.pass_context
def tmux_list(ctx):
    """List windows in the agency session."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        click.echo("[ERROR] Run 'agency init' or use --dir", err=True)
        ctx.exit(1)

    config = load_agency_config(agency_dir)
    session_name = f"agency-{config.project}"
    socket_name = f"agency-{config.project}"

    sm = SessionManager(session_name, socket_name)
    if not sm.session_exists():
        click.echo(f"[ERROR] Session '{session_name}' not found", err=True)
        ctx.exit(1)

    click.echo(f"Session: {session_name} (socket: {socket_name})")
    click.echo("")

    for window in sm.list_windows():
        is_mgr = window.startswith("[MGR]")
        marker = " [MGR]" if is_mgr else ""
        click.echo(f"  {window}{marker}")


@tmux_cmd.command("send")
@click.argument("window")
@click.argument("text")
@click.pass_context
def tmux_send(ctx, window, text):
    """Send keys to a window."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        ctx.exit(1)

    config = load_agency_config(agency_dir)
    session_name = f"agency-{config.project}"
    socket_name = f"agency-{config.project}"

    sm = SessionManager(session_name, socket_name)
    if not sm.session_exists():
        click.echo(f"[ERROR] Session '{session_name}' not found", err=True)
        ctx.exit(1)

    sm.send_keys(window, text)
    click.echo(f"[OK] Sent to {window}: {text}")


@tmux_cmd.command("new")
@click.argument("name")
@click.option("--command", "cmd", default=None, help="Command to run in window")
@click.pass_context
def tmux_new(ctx, name, cmd):
    """Create a new window."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        ctx.exit(1)

    config = load_agency_config(agency_dir)
    session_name = f"agency-{config.project}"
    socket_name = f"agency-{config.project}"
    work_dir = agency_dir.parent

    result = subprocess.run(
        [
            "tmux",
            "-L",
            socket_name,
            "new-window",
            "-d",
            "-t",
            session_name,
            "-n",
            name,
            "-c",
            str(work_dir),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        click.echo(f"[ERROR] Failed to create window: {result.stderr}", err=True)
        ctx.exit(1)

    if cmd:
        sm = SessionManager(session_name, socket_name)
        sm.send_keys(name, cmd)

    click.echo(f"[OK] Created window: {name}")


@tmux_cmd.command("attach")
@click.pass_context
def tmux_attach(ctx):
    """Attach to the agency session (opens new terminal)."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        ctx.exit(1)

    config = load_agency_config(agency_dir)
    session_name = f"agency-{config.project}"
    socket_name = f"agency-{config.project}"

    # Detach any existing clients first
    subprocess.run(
        ["tmux", "-L", socket_name, "detach", "-s", session_name],
        capture_output=True,
    )

    # Launch terminal with attach
    os.execlp("tmux", "tmux", "-L", socket_name, "attach", "-t", session_name)


@tmux_cmd.command("run")
@click.argument("window")
@click.argument("command")
@click.pass_context
def tmux_run(ctx, window, command):
    """Run a command in a window."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        ctx.exit(1)

    config = load_agency_config(agency_dir)
    session_name = f"agency-{config.project}"
    socket_name = f"agency-{config.project}"

    sm = SessionManager(session_name, socket_name)
    if not sm.session_exists():
        click.echo(f"[ERROR] Session '{session_name}' not found", err=True)
        ctx.exit(1)

    # Send command with Enter
    sm.send_keys(window, command)
    click.echo(f"[OK] Running in {window}: {command}")


# Register commands based on AGENCY_ROLE
_agency_role = os.environ.get("AGENCY_ROLE", "").upper()

if _agency_role == "MANAGER":
    # Manager sees: all commands except completions
    cli.add_command(init_project, name="init")
    cli.add_command(start)
    cli.add_command(stop)
    cli.add_command(kill)
    cli.add_command(resume)
    cli.add_command(attach)
    cli.add_command(list)
    cli.add_command(members)
    cli.add_command(tasks)
    cli.add_command(tmux_cmd)
elif _agency_role == "AGENT":
    # Agent sees: tasks_agent only (limited commands)
    cli.add_command(tasks_agent)
else:
    # Default: all commands
    cli.add_command(init_project, name="init")
    cli.add_command(start)
    cli.add_command(stop)
    cli.add_command(kill)
    cli.add_command(resume)
    cli.add_command(attach)
    cli.add_command(list)
    cli.add_command(members)
    cli.add_command(tasks)
    cli.add_command(completions)
    cli.add_command(tmux_cmd)


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
