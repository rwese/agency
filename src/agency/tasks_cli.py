"""
Agency v2.0 - Tasks CLI

Command-line interface for task management.
"""

import argparse
import json
import sys
from pathlib import Path

from agency.tasks import TaskStore


def handle_tasks_command(args: argparse.Namespace, agency_dir: Path) -> int:
    """Handle tasks subcommands."""
    store = TaskStore(agency_dir)

    if args.tasks_command == "list":
        return cmd_list(store, args)
    elif args.tasks_command == "add":
        return cmd_add(store, args)
    elif args.tasks_command == "show":
        return cmd_show(store, args)
    elif args.tasks_command == "assign":
        return cmd_assign(store, args)
    elif args.tasks_command == "complete":
        return cmd_complete(store, args)
    elif args.tasks_command == "approve":
        return cmd_approve(store, args)
    elif args.tasks_command == "reject":
        return cmd_reject(store, args)
    elif args.tasks_command == "reopen":
        return cmd_reopen(store, args)
    elif args.tasks_command == "update":
        return cmd_update(store, args)
    elif args.tasks_command == "delete":
        return cmd_delete(store, args)
    elif args.tasks_command == "history":
        return cmd_history(store, args)
    else:
        print(
            "Usage: agency tasks <list|add|show|assign|complete|approve|reject|reopen|update|delete|history>",
            file=sys.stderr,
        )
        return 1


def cmd_list(store: TaskStore, args: argparse.Namespace) -> int:
    """List tasks."""
    tasks = store.list_tasks(status=args.status, assignee=args.assignee)

    if not tasks:
        print("No tasks found")
        return 0

    for task in tasks:
        status_icon = {
            "pending": "⏳",
            "in_progress": "🔄",
            "pending_approval": "👀",
            "completed": "✅",
            "failed": "❌",
        }.get(task.status, "?")

        print(f"## {task.task_id}")
        print()
        print(f"- status: {task.status} {status_icon}")
        print(f"- priority: {task.priority}")
        print(f"- assigned_to: {task.assigned_to or 'null'}")
        print(f"- description: {task.description}")
        print(f"- created_at: {task.created_at}")
        if task.started_at:
            print(f"- started_at: {task.started_at}")
        if task.completed_at:
            print(f"- completed_at: {task.completed_at}")
        print()

    return 0


def cmd_add(store: TaskStore, args: argparse.Namespace) -> int:
    """Add a new task."""
    try:
        task = store.add_task(
            subject=args.subject,
            description=args.description,
            priority=args.priority,
            assigned_to=args.assignee,
            acceptance_criteria=args.acceptance_criteria if hasattr(args, 'acceptance_criteria') else None,
            references=args.references if hasattr(args, 'references') else None,
            attachments=args.attachments if hasattr(args, 'attachments') else None,
        )
        print(f"[INFO] Created task: {task.task_id}")
        return 0
    except ValueError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


def cmd_show(store: TaskStore, args: argparse.Namespace) -> int:
    """Show task details."""
    task = store.get_task(args.task_id)

    if not task:
        print(f"[ERROR] Task not found: {args.task_id}", file=sys.stderr)
        return 1

    status_icon = {
        "pending": "⏳",
        "in_progress": "🔄",
        "pending_approval": "👀",
        "completed": "✅",
        "failed": "❌",
    }.get(task.status, "?")

    print(f"# {task.task_id}")
    print()
    print("## Task")
    print()
    print(f"- **Subject**: {getattr(task, 'subject', 'N/A')}")
    print(f"- **Description**: {task.description}")
    print(f"- **Status**: {task.status} {status_icon}")
    print(f"- **Priority**: {task.priority}")
    print(f"- **Assigned to**: {task.assigned_to or 'Unassigned'}")
    print(f"- **Created**: {task.created_at or 'Unknown'}")
    print(f"- **Started**: {task.started_at or 'Not started'}")
    print(f"- **Completed**: {task.completed_at or 'In progress'}")

    # Show acceptance criteria
    if getattr(task, 'acceptance_criteria', None):
        print()
        print("## Acceptance Criteria")
        for i, criterion in enumerate(task.acceptance_criteria, 1):
            print(f"{i}. {criterion}")

    # Show references
    if getattr(task, 'references', None):
        print()
        print("## References")
        for ref in task.references:
            print(f"- {ref}")

    # Show attachments
    if getattr(task, 'attachments', None):
        print()
        print("## Attachments")
        for attachment in task.attachments:
            print(f"- {attachment}")

    print()

    if task.result:
        print("## Result")
        print()
        print(task.result)
        print()

    # Check for result file
    if task.result_path:
        result_file = store.agency_dir / task.result_path
        if result_file.exists():
            result_data = json.loads(result_file.read_text())
            if result_data.get("artifacts"):
                print("## Artifacts")
                print()
                artifacts = result_data["artifacts"]
                if artifacts.get("files"):
                    print(f"- Files: {', '.join(artifacts['files'])}")
                if artifacts.get("summary"):
                    print(f"- Summary: {artifacts['summary']}")
                print()

    return 0


def cmd_assign(store: TaskStore, args: argparse.Namespace) -> int:
    """Assign a task to an agent."""
    # Check if agent is free
    if not store.is_agent_free(args.agent):
        print(
            f"[WARN] Agent '{args.agent}' may not be free (has pending/in_progress tasks)",
            file=sys.stderr,
        )

    if store.assign_task(args.task_id, args.agent):
        print(f"[INFO] Assigned {args.task_id} to {args.agent}")
        return 0
    else:
        print("[ERROR] Failed to assign task", file=sys.stderr)
        return 1


def cmd_complete(store: TaskStore, args: argparse.Namespace) -> int:
    """Complete a task."""
    # Parse files JSON if provided
    files = None
    if args.files:
        try:
            files = json.loads(args.files)
        except json.JSONDecodeError:
            print("[ERROR] Invalid JSON in --files", file=sys.stderr)
            return 1

    if store.complete_task(
        task_id=args.task_id,
        result=args.result,
        files=files,
        diff=args.diff,
        summary=args.summary,
    ):
        print(f"[INFO] Task {args.task_id} marked for approval")
        return 0
    else:
        print("[ERROR] Failed to complete task", file=sys.stderr)
        return 1


def cmd_approve(store: TaskStore, args: argparse.Namespace) -> int:
    """Approve a pending task completion."""
    if store.approve_task(args.task_id):
        print(f"[INFO] Task {args.task_id} approved and archived")
        return 0
    else:
        print("[ERROR] Failed to approve task", file=sys.stderr)
        return 1


def cmd_reject(store: TaskStore, args: argparse.Namespace) -> int:
    """Reject a pending task completion."""
    if store.reject_task(args.task_id, reason=args.reason, suggestions=args.suggestions):
        print(f"[INFO] Task {args.task_id} rejected")
        return 0
    else:
        print("[ERROR] Failed to reject task", file=sys.stderr)
        return 1


def cmd_reopen(store: TaskStore, args: argparse.Namespace) -> int:
    """Reopen a completed or failed task."""
    task = store.get_task(args.task_id)
    if not task:
        print(f"[ERROR] Task not found: {args.task_id}", file=sys.stderr)
        return 1

    if task.status not in ("completed", "failed"):
        print(f"[ERROR] Task {args.task_id} is not completed or failed", file=sys.stderr)
        return 1

    if store.update_task(args.task_id, status="pending"):
        # Clear result fields
        import json

        task_json_path = store.agency_dir / "tasks" / args.task_id / "task.json"
        if task_json_path.exists():
            data = json.loads(task_json_path.read_text())
            data["status"] = "pending"
            data["completed_at"] = None
            data["result"] = None
            task_json_path.write_text(json.dumps(data, indent=2))

        print(f"[INFO] Task {args.task_id} reopened")
        return 0
    else:
        print("[ERROR] Failed to reopen task", file=sys.stderr)
        return 1


def cmd_update(store: TaskStore, args: argparse.Namespace) -> int:
    """Update a task."""
    if not args.status and not args.priority:
        print("[ERROR] At least one of --status or --priority required", file=sys.stderr)
        return 1

    # Validate status - only allow transitional states, not terminal states
    # completed/failed must go through approve/reject commands
    if args.status and args.status not in (
        "pending",
        "in_progress",
        "pending_approval",
    ):
        print(f"[ERROR] Invalid status: {args.status}", file=sys.stderr)
        print("[ERROR] Use 'agency tasks complete' or 'agency tasks approve' for completed tasks", file=sys.stderr)
        return 1

    # Validate priority
    if args.priority and args.priority not in ("low", "normal", "high"):
        print(f"[ERROR] Invalid priority: {args.priority}", file=sys.stderr)
        return 1

    if store.update_task(args.task_id, status=args.status, priority=args.priority):
        print(f"[INFO] Updated task {args.task_id}")
        return 0
    else:
        print("[ERROR] Failed to update task", file=sys.stderr)
        return 1


def cmd_delete(store: TaskStore, args: argparse.Namespace) -> int:
    """Delete a task."""
    if store.delete_task(args.task_id):
        print(f"[INFO] Deleted task {args.task_id}")
        return 0
    else:
        print("[ERROR] Failed to delete task", file=sys.stderr)
        return 1


def cmd_history(store: TaskStore, args: argparse.Namespace) -> int:
    """Show task history."""
    history = store.history(agent=args.agent)

    if not history:
        print("No completed tasks found")
        return 0

    print("## Completed Tasks")
    print()

    for item in history:
        task = item["task"]
        result = item.get("result", {})

        status_icon = "✅" if task["status"] == "completed" else "❌"

        print(f"### {task['task_id']} {status_icon}")
        print(f"- **Agent**: {task.get('assigned_to', 'unknown')}")
        print(f"- **Completed**: {task.get('completed_at', 'unknown')}")

        if result:
            print(f"- **Result**: {result.get('result', 'No result')[:100]}...")

        print()

    return 0
