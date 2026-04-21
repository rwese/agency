#!/usr/bin/env python3
"""
Agency v2.0 - AI Agent Session Manager

A tmux-based multi-agent orchestration tool.
"""

import os
import sys
from pathlib import Path

import click

from agency import __version__
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
def cli():
    """Agency - AI Agent Session Manager."""
    pass


# === Project Commands ===


@click.command()
@click.option("--dir", required=True, type=click.Path(), help="Project directory")
@click.option("--template", help="Template repository URL")
@click.option("--template-subdir", help="Template subdirectory")
@click.option("--start-manager", help="Start manager on init")
@click.option("--force", is_flag=True, help="Overwrite existing")
@click.option("--refresh", is_flag=True, help="Bypass template cache")
def init_project(dir, template, template_subdir, start_manager, force, refresh):
    """Create a new project with session and .agency/ directory."""
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
        tm = TemplateManager(
            template_url, cache_dir=Path.home() / ".cache" / "agency" / "templates"
        )
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

    # Start manager if specified
    if start_manager:
        start_manager_window(session_name, socket_name, start_manager, agency_dir, work_dir)
        click.echo(f"[INFO] Started manager: [MGR] {start_manager}")


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
        readme_path.write_text(
            "# Agency Project\n\nThis project uses Agency for AI agent orchestration.\n"
        )


@click.command()
@click.argument("name")
@click.option("--dir", required=True, type=click.Path(), help="Project directory")
@click.option("--manager", is_flag=True, help="Start as manager")
def start(name, dir, manager):
    """Start an agent or manager in the project session."""
    work_dir = Path(dir).expanduser().absolute()

    # Find git root
    git_root = find_git_root(work_dir)
    if not git_root:
        click.echo("[ERROR] Not in a git repository", err=True)
        sys.exit(1)

    agency_dir = git_root / ".agency"
    if not agency_dir.exists():
        click.echo(f"[ERROR] No .agency/ found in {git_root}", err=True)
        click.echo("[ERROR] Run 'agency init-project --dir <path>' first", err=True)
        sys.exit(1)

    project_name = work_dir.name
    session_name = f"agency-{project_name}"
    socket_name = f"agency-{project_name}"

    sm = SessionManager(session_name, socket_name=socket_name)

    # Create session if it doesn't exist
    if not sm.session_exists():
        click.echo(f"[INFO] Creating new session: {session_name}")
        create_project_session(session_name, socket_name, work_dir)

    # Check if it's a manager
    is_manager = (
        manager or (agency_dir / "manager.yaml").exists() and name == _get_manager_name(agency_dir)
    )

    if is_manager:
        if sm.manager_exists():
            click.echo("[ERROR] Manager already exists in session", err=True)
            sys.exit(1)
        start_manager_window(session_name, socket_name, name, agency_dir, work_dir)
        click.echo(f"[INFO] Started manager: [MGR] {name}")
    else:
        config_path = agency_dir / "agents" / f"{name}.yaml"
        if not config_path.exists():
            click.echo(f"[ERROR] Agent config not found: {config_path}", err=True)
            sys.exit(1)

        if sm.window_exists(name):
            click.echo(f"[INFO] Agent '{name}' already running, attaching...", err=True)
        else:
            start_agent_window(session_name, socket_name, name, agency_dir, work_dir)
            click.echo(f"[INFO] Started agent: {name}")


def _get_manager_name(agency_dir: Path) -> str | None:
    """Get manager name from agency config."""
    return None


@click.command()
@click.argument("session")
@click.option("--timeout", type=int, help="Grace period in seconds")
@click.option("--force", is_flag=True, help="Force kill without graceful shutdown")
def stop(session, timeout, force):
    """Stop a session gracefully."""
    if not session.startswith("agency-"):
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

    timeout = timeout or 5  # Shorter default for tests
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
@click.argument("session")
def resume(session):
    """Resume a halted session."""
    if not session.startswith("agency-"):
        session = f"agency-{session}"

    socket_name = session

    # Find work dir for session (placeholder)
    work_dir = _find_work_dir_for_session(session)
    if not work_dir:
        click.echo(f"[ERROR] Could not find project directory for {session}", err=True)
        sys.exit(1)

    agency_dir = work_dir / ".agency"
    halted_file = agency_dir / ".halted"

    if not halted_file.exists():
        click.echo("[WARN] No halt marker found. Session may not be halted.", err=True)

    from agency.session import resume_halted_session

    if resume_halted_session(session, socket_name, agency_dir, work_dir):
        click.echo(f"[INFO] Resumed session: {session}")
    else:
        click.echo("[ERROR] Failed to resume session", err=True)
        sys.exit(1)


def _find_work_dir_for_session(session_name: str) -> Path | None:
    """Find the working directory for a session."""
    # TODO: Implement session registry
    return None


@click.command()
@click.argument("session")
def attach(session):
    """Attach to a session."""
    if not session.startswith("agency-"):
        session = f"agency-{session}"

    socket_name = session

    # Use tmux attach
    os.execvp("tmux", ["tmux", "-L", socket_name, "attach-session", "-t", session])


@click.command()
def list():
    """List all agency sessions."""
    from agency.session import list_agency_sessions

    sessions = list_agency_sessions()

    if not sessions:
        click.echo("[INFO] No agency sessions running")
        return

    for session in sessions:
        click.echo(f"{session['name']}")
        for window in session.get("windows", []):
            is_manager = window.get("is_manager", False)
            prefix = "  [MGR] " if is_manager else "  "
            click.echo(f"{prefix}{window['name']}")


# === Task Commands ===


@click.group()
def tasks():
    """Task management commands."""
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
        click.echo(
            f"[WARN] Agent '{agent}' may not be free (has pending/in_progress tasks)", err=True
        )

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
    if store.reject_task(
        task_id, reason=reason, suggestions=list(suggestions) if suggestions else None
    ):
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


# === Completions ===


@click.command()
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
def completions(shell):
    """Print shell completion script."""
    from agency.completions import get_completion_script
    click.echo(get_completion_script(shell))


# Register commands
cli.add_command(init_project)
cli.add_command(start)
cli.add_command(stop)
cli.add_command(resume)
cli.add_command(attach)
cli.add_command(list)
cli.add_command(tasks)
cli.add_command(completions)


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
