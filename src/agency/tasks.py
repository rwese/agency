"""
Agency v2.0 - Task Management

Handles task operations with file locking and directory management.
"""

import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from filelock import FileLock

# Constants
TASKS_FILE = "var/tasks.json"
TASKS_DIR = "var/tasks"
PENDING_DIR = "var/pending"


@dataclass
class Task:
    """Represents a task."""

    subject: str  # Brief title/summary of the task (required)
    description: str  # Detailed description of what needs to be done (required)
    task_id: str = ""
    status: str = "pending"  # pending, in_progress, pending_approval, completed, failed
    priority: str = "low"  # low, normal, high
    assigned_to: str | None = None
    created_at: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    result: str | None = None
    result_path: str | None = None
    depends_on: list[str] | None = None  # List of task IDs this task depends on

    # Acceptance criteria - what must be true for the task to be considered complete
    acceptance_criteria: list[str] | None = None
    # Example: ["Tests pass", "No linting errors", "Documentation updated"]

    # References - file paths, URLs, or other resources relevant to this task
    references: list[str] | None = None
    # Example: ["src/auth.py", "https://docs.example.com/api", "#issue-123"]

    # Attachments - file paths to files stored with this task
    attachments: list[str] | None = None
    # Files are copied to .agency/var/tasks/<task_id>/attachments/ on task creation

    # Agent info (set when agent picks up task)
    agent_info: dict | None = None
    # {
    #   "session_id": "pi-session-coder-a1b2c3",
    #   "pid": 12345,
    #   "started_at": "2024-01-15T10:30:00Z"
    # }

    # Review info
    rejection_reason: str | None = None
    review_notes: str | None = None
    reviewer_assigned: str | None = None  # Track which reviewer is handling this task

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "subject": self.subject,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "result_path": self.result_path,
            "depends_on": self.depends_on,
            "acceptance_criteria": self.acceptance_criteria,
            "references": self.references,
            "attachments": self.attachments,
            "agent_info": self.agent_info,
            "rejection_reason": self.rejection_reason,
            "review_notes": self.review_notes,
            "reviewer_assigned": self.reviewer_assigned,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            task_id=data.get("task_id", ""),
            subject=data["subject"],
            description=data["description"],
            status=data.get("status", "pending"),
            priority=data.get("priority", "low"),
            assigned_to=data.get("assigned_to"),
            created_at=data.get("created_at"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            result=data.get("result"),
            result_path=data.get("result_path"),
            depends_on=data.get("depends_on"),
            acceptance_criteria=data.get("acceptance_criteria"),
            references=data.get("references"),
            attachments=data.get("attachments"),
            agent_info=data.get("agent_info"),
            rejection_reason=data.get("rejection_reason"),
            review_notes=data.get("review_notes"),
            reviewer_assigned=data.get("reviewer_assigned"),
        )


class TaskStore:
    """Manages tasks with file locking."""

    def __init__(self, agency_dir: Path):
        self.agency_dir = agency_dir
        self.tasks_file = agency_dir / TASKS_FILE
        self.lock_file = agency_dir / "var" / ".tasks.lock"
        self._audit_store = None

        # Ensure directories exist
        agency_dir.mkdir(parents=True, exist_ok=True)
        (agency_dir / "var").mkdir(exist_ok=True)
        (agency_dir / TASKS_DIR).mkdir(exist_ok=True)
        (agency_dir / PENDING_DIR).mkdir(exist_ok=True)

    def _get_audit_store(self):
        """Get audit store lazily if audit is enabled in config."""
        if self._audit_store is None:
            try:
                from agency.audit import AuditStore
                from agency.config import load_agency_config

                config = load_agency_config(self.agency_dir)
                if config.audit_enabled:
                    self._audit_store = AuditStore(self.agency_dir)
                else:
                    self._audit_store = False
            except Exception:
                self._audit_store = False  # Mark as unavailable
        return self._audit_store if self._audit_store else None

    def _read_tasks_json(self) -> dict:
        """Read tasks.json."""
        if not self.tasks_file.exists():
            return {"version": 2, "tasks": {}}

        with open(self.tasks_file) as f:
            return json.load(f)

    def _write_tasks_json(self, data: dict) -> None:
        """Write tasks.json."""
        with open(self.tasks_file, "w") as f:
            json.dump(data, f, indent=2)

    def _lock(self):
        """Acquire lock on tasks.json."""
        return FileLock(str(self.lock_file), timeout=10)

    def list_tasks(
        self,
        status: str | None = None,
        assignee: str | None = None,
        include_blocked: bool = False,
    ) -> list[Task]:
        """List tasks with optional filtering.

        Args:
            status: Filter by task status
            assignee: Filter by assigned agent
            include_blocked: If False, filter out tasks with incomplete dependencies
        """
        data = self._read_tasks_json()
        tasks = [Task.from_dict(t) for t in data.get("tasks", {}).values()]

        if status:
            # Support comma-separated status values (e.g., "pending,in_progress")
            status_list = [s.strip() for s in status.split(",")]
            tasks = [t for t in tasks if t.status in status_list]

        if assignee:
            tasks = [t for t in tasks if t.assigned_to == assignee]

        if not include_blocked:
            tasks = [t for t in tasks if not self._has_blocked_dependencies(t)]

        return tasks

    def _has_blocked_dependencies(self, task: Task) -> bool:
        """Check if task has incomplete dependencies.

        A task is blocked if any of its dependencies are not completed.
        """
        if not task.depends_on:
            return False

        for dep_id in task.depends_on:
            dep_task = self.get_task(dep_id)
            if dep_task is None:
                # Dependency task doesn't exist - consider it as blocking
                return True
            if dep_task.status != "completed":
                return True

        return False

    def get_blocked_by(self, task_id: str) -> list[Task]:
        """Get list of tasks blocking the given task."""
        task = self.get_task(task_id)
        if not task or not task.depends_on:
            return []

        blocking = []
        for dep_id in task.depends_on:
            dep_task = self.get_task(dep_id)
            if dep_task and dep_task.status != "completed":
                blocking.append(dep_task)

        return blocking

    def get_task(self, task_id: str) -> Task | None:
        """Get a single task by ID."""
        data = self._read_tasks_json()
        tasks = data.get("tasks", {})

        if task_id in tasks:
            return Task.from_dict(tasks[task_id])

        return None

    def add_task(
        self,
        subject: str,
        description: str,
        priority: str = "low",
        assigned_to: str | None = None,
        acceptance_criteria: list[str] | None = None,
        references: list[str] | None = None,
        attachments: list[str] | None = None,
    ) -> Task:
        """Add a new task.

        Args:
            subject: Brief title/summary of the task (required)
            description: Detailed description of what needs to be done (required)
            priority: Task priority: low, normal, high (default: low)
            assigned_to: Agent to assign the task to (optional)
            acceptance_criteria: List of criteria for task completion (optional)
            references: List of file paths, URLs, or other references (optional)
            attachments: List of file paths to attach (optional, files are copied)

        Returns:
            Created Task object

        Raises:
            ValueError: If subject or description is empty/whitespace only
        """
        # Validate required fields
        if not subject or not subject.strip():
            raise ValueError("Task subject is required and cannot be empty")
        if not description or not description.strip():
            raise ValueError("Task description is required and cannot be empty")

        with self._lock():
            data = self._read_tasks_json()

            # Generate task ID
            task_id = self._generate_task_id(data)

            # Create task directory
            task_dir = self.agency_dir / TASKS_DIR / task_id
            task_dir.mkdir(parents=True, exist_ok=True)

            # Create attachments directory and copy files
            attachment_paths: list[str] = []
            if attachments:
                attachments_dir = task_dir / "attachments"
                attachments_dir.mkdir(parents=True, exist_ok=True)
                for attachment_path in attachments:
                    src = Path(attachment_path).expanduser()
                    if src.exists():
                        dest = attachments_dir / src.name
                        shutil.copy2(src, dest)
                        attachment_paths.append(str(dest.relative_to(task_dir)))
                    else:
                        # Store the path even if file doesn't exist (warn but continue)
                        attachment_paths.append(attachment_path)

            # Create task file
            task_json = task_dir / "task.json"
            now = datetime.now().isoformat()

            task = Task(
                task_id=task_id,
                subject=subject.strip(),
                description=description.strip(),
                status="pending",
                priority=priority,
                assigned_to=assigned_to,
                created_at=now,
                acceptance_criteria=acceptance_criteria,
                references=references,
                attachments=attachment_paths if attachment_paths else None,
            )

            data["tasks"][task_id] = task.to_dict()
            self._write_tasks_json(data)

            # Write task.json to task directory
            task_json.write_text(json.dumps(task.to_dict(), indent=2))

            # Audit log
            audit = self._get_audit_store()
            if audit:
                audit.log_task(
                    action="create",
                    task_id=task_id,
                    details={
                        "subject": subject,
                        "description": description,
                        "priority": priority,
                        "assigned_to": assigned_to,
                        "acceptance_criteria_count": len(acceptance_criteria) if acceptance_criteria else 0,
                        "references_count": len(references) if references else 0,
                        "attachments_count": len(attachment_paths),
                    },
                )

            return task

    def assign_task(self, task_id: str, agent: str) -> bool:
        """Assign a task to an agent."""
        with self._lock():
            data = self._read_tasks_json()
            tasks = data.get("tasks", {})

            if task_id not in tasks:
                return False

            task = Task.from_dict(tasks[task_id])

            # Check if task is blocked by dependencies
            if self._has_blocked_dependencies(task):
                blocking = self.get_blocked_by(task_id)
                blocking_ids = [t.task_id for t in blocking]
                raise ValueError(f"Task {task_id} is blocked by incomplete dependencies: {blocking_ids}")

            # Check if agent is free (no in_progress tasks)
            for tid, t in tasks.items():
                if t.get("assigned_to") == agent and t.get("status") == "in_progress":
                    return False

            tasks[task_id]["assigned_to"] = agent
            self._write_tasks_json(data)

            # Audit log
            audit = self._get_audit_store()
            if audit:
                audit.log_task(
                    action="assign",
                    task_id=task_id,
                    details={"agent": agent},
                )

            return True

    def set_dependencies(self, task_id: str, depends_on: list[str]) -> bool:
        """Set dependencies for a task.

        Args:
            task_id: The task to add dependencies to
            depends_on: List of task IDs this task depends on

        Returns:
            True if dependencies were set successfully
        """
        with self._lock():
            data = self._read_tasks_json()
            tasks = data.get("tasks", {})

            if task_id not in tasks:
                return False

            # Validate that all dependency tasks exist
            for dep_id in depends_on:
                if dep_id not in tasks:
                    raise ValueError(f"Dependency task does not exist: {dep_id}")
                if dep_id == task_id:
                    raise ValueError(f"Task cannot depend on itself: {task_id}")

            # Check for circular dependencies
            if self._would_create_cycle(task_id, depends_on):
                raise ValueError("Setting these dependencies would create a circular dependency")

            tasks[task_id]["depends_on"] = depends_on
            self._write_tasks_json(data)

            # Update task.json in task directory
            task_json_path = self.agency_dir / TASKS_DIR / task_id / "task.json"
            if task_json_path.exists():
                task_json_path.write_text(json.dumps(tasks[task_id], indent=2))

            # Audit log
            audit = self._get_audit_store()
            if audit:
                audit.log_task(
                    action="update",
                    task_id=task_id,
                    details={"depends_on": depends_on},
                )

            return True

    def _would_create_cycle(self, task_id: str, new_depends_on: list[str]) -> bool:
        """Check if adding dependencies would create a cycle.

        A cycle exists if task_id depends on a task that (directly or indirectly)
        depends on task_id.
        """
        visited: set[str] = set()
        stack: list[str] = list(new_depends_on)

        while stack:
            current = stack.pop()
            if current == task_id:
                return True  # Found a cycle
            if current in visited:
                continue
            visited.add(current)

            task = self.get_task(current)
            if task and task.depends_on:
                stack.extend(task.depends_on)

        return False

    def add_dependency(self, task_id: str, depends_on: str) -> bool:
        """Add a single dependency to a task."""
        task = self.get_task(task_id)
        if not task:
            return False

        current_deps = list(task.depends_on) if task.depends_on else []
        if depends_on not in current_deps:
            current_deps.append(depends_on)
            return self.set_dependencies(task_id, current_deps)
        return True  # Already has this dependency

    def remove_dependency(self, task_id: str, depends_on: str) -> bool:
        """Remove a dependency from a task."""
        task = self.get_task(task_id)
        if not task or not task.depends_on:
            return False

        if depends_on not in task.depends_on:
            return False

        new_deps = [d for d in task.depends_on if d != depends_on]
        return self.set_dependencies(task_id, new_deps)

    def update_task(
        self,
        task_id: str,
        status: str | None = None,
        priority: str | None = None,
        reviewer_assigned: str | None = None,
    ) -> bool:
        """Update task fields."""
        with self._lock():
            data = self._read_tasks_json()
            tasks = data.get("tasks", {})

            if task_id not in tasks:
                return False

            now = datetime.now().isoformat()

            if status:
                tasks[task_id]["status"] = status

                if status == "in_progress" and not tasks[task_id].get("started_at"):
                    tasks[task_id]["started_at"] = now
                elif status == "completed":
                    tasks[task_id]["completed_at"] = now
                elif status == "failed":
                    tasks[task_id]["completed_at"] = now

            if priority:
                tasks[task_id]["priority"] = priority

            if reviewer_assigned is not None:
                tasks[task_id]["reviewer_assigned"] = reviewer_assigned

            self._write_tasks_json(data)

            # Update task.json in task directory
            task_json_path = self.agency_dir / TASKS_DIR / task_id / "task.json"
            if task_json_path.exists():
                task_json_path.write_text(json.dumps(tasks[task_id], indent=2))

            # Audit log
            audit = self._get_audit_store()
            if audit:
                audit.log_task(
                    action="update",
                    task_id=task_id,
                    details={"status": status, "priority": priority, "reviewer_assigned": reviewer_assigned},
                )

            return True

    def complete_task(
        self,
        task_id: str,
        result: str,
        files: list | None = None,
        diff: str | None = None,
        summary: str | None = None,
    ) -> bool:
        """Mark task as pending approval."""
        with self._lock():
            data = self._read_tasks_json()
            tasks = data.get("tasks", {})

            if task_id not in tasks:
                return False

            now = datetime.now().isoformat()

            # Update task status
            tasks[task_id]["status"] = "pending_approval"
            tasks[task_id]["completed_at"] = now
            tasks[task_id]["result"] = result
            # Keep agent_info for potential restart on rejection

            # Create result.json
            result_data = {
                "result": result,
                "artifacts": {
                    "files": files or [],
                    "diff": diff or "",
                    "summary": summary or "",
                },
                "completed_at": now,
                "completed_by": tasks[task_id].get("assigned_to"),
            }

            result_path = self.agency_dir / TASKS_DIR / task_id / "result.json"
            result_path.write_text(json.dumps(result_data, indent=2))
            tasks[task_id]["result_path"] = str(result_path.relative_to(self.agency_dir))

            # Move to pending/
            pending_data = {**tasks[task_id], **result_data, "pending_approval_at": now}
            pending_file = self.agency_dir / PENDING_DIR / f"{task_id}.json"
            pending_file.write_text(json.dumps(pending_data, indent=2))

            self._write_tasks_json(data)

            # Audit log
            audit = self._get_audit_store()
            if audit:
                audit.log_task(
                    action="complete",
                    task_id=task_id,
                    details={
                        "result_length": len(result),
                        "files": files,
                    },
                )

            return True

    def approve_task(self, task_id: str) -> bool:
        """Approve a pending task completion."""
        with self._lock():
            data = self._read_tasks_json()
            tasks = data.get("tasks", {})

            if task_id not in tasks:
                return False

            task = tasks[task_id]

            if task["status"] != "pending_approval":
                return False

            # Move pending file to task directory
            pending_file = self.agency_dir / PENDING_DIR / f"{task_id}.json"
            if pending_file.exists():
                shutil.move(
                    str(pending_file),
                    str(self.agency_dir / TASKS_DIR / task_id / "pending_approval.json"),
                )

            # Update status
            task["status"] = "completed"
            self._write_tasks_json(data)

            # Update task.json in task directory
            task_json_path = self.agency_dir / TASKS_DIR / task_id / "task.json"
            if task_json_path.exists():
                task_json_path.write_text(json.dumps(task, indent=2))

            # Audit log
            audit = self._get_audit_store()
            if audit:
                audit.log_task(
                    action="approve",
                    task_id=task_id,
                    details={"approved_by": os.environ.get("AGENCY_AGENT", "unknown")},
                )

            return True

    def reject_task(self, task_id: str, reason: str, suggestions: list | None = None) -> bool:
        """Reject a pending task completion."""
        with self._lock():
            data = self._read_tasks_json()
            tasks = data.get("tasks", {})

            if task_id not in tasks:
                return False

            task = tasks[task_id]

            if task["status"] != "pending_approval":
                return False

            # Create rejection file
            rejection_path = self.agency_dir / PENDING_DIR / f"{task_id}.rejected"
            rejection_content = f"""# Task Rejected: {task_id}

## Reason

{reason}

"""
            if suggestions:
                rejection_content += "## Suggestions\n\n"
                for i, s in enumerate(suggestions, 1):
                    rejection_content += f"{i}. {s}\n"

            rejection_path.write_text(rejection_content)

            # Update status to failed (agent can retry)
            task["status"] = "failed"
            task["completed_at"] = None  # Clear completion time
            task["rejection_reason"] = reason
            self._write_tasks_json(data)

            # Update task.json in task directory
            task_json_path = self.agency_dir / TASKS_DIR / task_id / "task.json"
            if task_json_path.exists():
                task_json_path.write_text(json.dumps(task, indent=2))

            # Audit log
            audit = self._get_audit_store()
            if audit:
                audit.log_task(
                    action="reject",
                    task_id=task_id,
                    details={
                        "reason": reason,
                        "rejected_by": os.environ.get("AGENCY_AGENT", "unknown"),
                    },
                )

            return True

    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        with self._lock():
            data = self._read_tasks_json()
            tasks = data.get("tasks", {})

            if task_id not in tasks:
                return False

            # Remove from tasks.json
            del tasks[task_id]
            self._write_tasks_json(data)

            # Remove task directory
            task_dir = self.agency_dir / TASKS_DIR / task_id
            if task_dir.exists():
                shutil.rmtree(task_dir)

            # Remove pending file if exists
            pending_file = self.agency_dir / PENDING_DIR / f"{task_id}.json"
            if pending_file.exists():
                pending_file.unlink()

            # Audit log
            audit = self._get_audit_store()
            if audit:
                audit.log_task(
                    action="delete",
                    task_id=task_id,
                )

            return True

    def history(self, agent: str | None = None) -> list[dict]:
        """Get completed task history."""
        history = []
        tasks_dir = self.agency_dir / TASKS_DIR

        if not tasks_dir.exists():
            return history

        for task_dir in tasks_dir.iterdir():
            if not task_dir.is_dir():
                continue

            task_file = task_dir / "task.json"
            if not task_file.exists():
                continue

            task_data = json.loads(task_file.read_text())

            if task_data.get("status") not in ("completed", "failed"):
                continue

            if agent and task_data.get("assigned_to") != agent:
                continue

            # Get result if exists
            result_data = None
            result_file = task_dir / "result.json"
            if result_file.exists():
                result_data = json.loads(result_file.read_text())

            history.append(
                {
                    "task": task_data,
                    "result": result_data,
                }
            )

        return sorted(
            history,
            key=lambda x: x["task"].get("completed_at") or "",
            reverse=True,
        )

    def _generate_task_id(self, data: dict) -> str:
        """Generate a unique task ID."""
        import random

        # Get wordlist (eff.org short wordlist subset)
        wordlist = [
            "swift",
            "bold",
            "dark",
            "warm",
            "cool",
            "gray",
            "neon",
            "iron",
            "soft",
            "loud",
            "wolf",
            "fox",
            "bear",
            "hawk",
            "owl",
            "crow",
            "fish",
            "deer",
            "lynx",
            "crane",
            "frog",
            "toad",
            "hare",
            "mole",
            "seal",
            "goat",
            "jade",
            "kite",
            "link",
            "node",
            "orb",
            "pipe",
            "raft",
            "slug",
            "tank",
            "void",
            "wire",
            "atom",
            "base",
            "byte",
            "cache",
            "daemon",
            "ether",
            "fiber",
            "graph",
            "hash",
            "json",
            "kernel",
            "lambda",
            "module",
            "object",
            "parse",
            "query",
            "root",
            "socket",
            "thread",
        ]

        max_attempts = 10
        for _ in range(max_attempts):
            words = [random.choice(wordlist), random.choice(wordlist)]
            hex_suffix = f"{random.randint(0, 65535):04x}"
            task_id = f"{words[0]}-{words[1]}-{hex_suffix}"

            if task_id not in data.get("tasks", {}):
                return task_id

        # Fallback: add random suffix
        return f"{random.choice(wordlist)}-{random.choice(wordlist)}-{random.randint(0, 9999):04x}"

    def is_agent_free(self, agent: str) -> bool:
        """Check if an agent is free (no active or pending tasks)."""
        tasks = self.list_tasks(assignee=agent)
        return not any(t.status in ("in_progress", "pending") for t in tasks)

    def pickup_task(self, task_id: str, session_id: str, pid: int) -> bool:
        """Mark task as picked up by an agent, storing session and PID info.

        Called when an agent starts working on a task.
        Updates status to in_progress and stores agent_info.

        Args:
            task_id: The task ID
            session_id: pi session ID for the agent
            pid: Process ID of the agent

        Returns:
            True if task was picked up, False otherwise
        """
        with self._lock():
            data = self._read_tasks_json()
            tasks = data.get("tasks", {})

            if task_id not in tasks:
                return False

            task = tasks[task_id]

            # Can only pickup pending or failed (rejected) tasks
            if task["status"] not in ("pending", "failed"):
                return False

            now = datetime.now().isoformat()

            # Update task
            task["status"] = "in_progress"
            task["started_at"] = now
            task["agent_info"] = {
                "session_id": session_id,
                "pid": pid,
                "started_at": now,
            }

            # Clear any previous rejection info if re-picking up after rejection
            task["rejection_reason"] = None

            self._write_tasks_json(data)

            # Update task.json in task directory
            task_json_path = self.agency_dir / TASKS_DIR / task_id / "task.json"
            if task_json_path.exists():
                task_json_path.write_text(json.dumps(task, indent=2))

            # Audit log
            audit = self._get_audit_store()
            if audit:
                audit.log_task(
                    action="pickup",
                    task_id=task_id,
                    details={"session_id": session_id, "pid": pid},
                )

            return True

    def clear_agent_info(self, task_id: str) -> bool:
        """Clear agent info from a task (used when agent crashes or task is reassigned).

        Resets the task to pending status, keeping the assignment but clearing
        the agent_info so a new agent can pick it up.

        Args:
            task_id: The task ID

        Returns:
            True if cleared, False otherwise
        """
        with self._lock():
            data = self._read_tasks_json()
            tasks = data.get("tasks", {})

            if task_id not in tasks:
                return False

            task = tasks[task_id]

            # Only clear if task is in_progress
            if task["status"] != "in_progress":
                return False

            # Reset to pending
            task["status"] = "pending"
            task["started_at"] = None
            task["agent_info"] = None

            self._write_tasks_json(data)

            # Update task.json in task directory
            task_json_path = self.agency_dir / TASKS_DIR / task_id / "task.json"
            if task_json_path.exists():
                task_json_path.write_text(json.dumps(task, indent=2))

            # Audit log
            audit = self._get_audit_store()
            if audit:
                audit.log_task(
                    action="agent_cleared",
                    task_id=task_id,
                    details={"reason": "crash_detected"},
                )

            return True

    def set_rejection(self, task_id: str, reason: str) -> bool:
        """Mark a task as rejected with a reason.

        Args:
            task_id: The task ID
            reason: The rejection reason

        Returns:
            True if set, False otherwise
        """
        with self._lock():
            data = self._read_tasks_json()
            tasks = data.get("tasks", {})

            if task_id not in tasks:
                return False

            task = tasks[task_id]
            task["rejection_reason"] = reason

            self._write_tasks_json(data)

            # Update task.json in task directory
            task_json_path = self.agency_dir / TASKS_DIR / task_id / "task.json"
            if task_json_path.exists():
                task_json_path.write_text(json.dumps(task, indent=2))

            return True

    def set_review_notes(self, task_id: str, notes: str) -> bool:
        """Set review notes on a task.

        Args:
            task_id: The task ID
            notes: Review notes

        Returns:
            True if set, False otherwise
        """
        with self._lock():
            data = self._read_tasks_json()
            tasks = data.get("tasks", {})

            if task_id not in tasks:
                return False

            task = tasks[task_id]
            task["review_notes"] = notes

            self._write_tasks_json(data)

            # Update task.json in task directory
            task_json_path = self.agency_dir / TASKS_DIR / task_id / "task.json"
            if task_json_path.exists():
                task_json_path.write_text(json.dumps(task, indent=2))

            return True

    def get_agent_busy_count(self, agent: str) -> int:
        """Get count of in_progress tasks for an agent.

        Args:
            agent: Agent name

        Returns:
            Number of tasks the agent is currently working on
        """
        tasks = self.list_tasks(assignee=agent)
        return sum(1 for t in tasks if t.status == "in_progress")

    def get_in_progress_tasks(self) -> list[Task]:
        """Get all tasks currently in progress.

        Returns:
            List of in_progress tasks
        """
        return self.list_tasks(status="in_progress")

    def get_pending_approval_tasks(self) -> list[Task]:
        """Get all tasks pending approval.

        Returns:
            List of pending_approval tasks
        """
        return self.list_tasks(status="pending_approval")

    def get_unblocked_pending_tasks(self) -> list[Task]:
        """Get pending tasks that are not blocked by dependencies.

        Returns:
            List of unblocked pending tasks
        """
        return self.list_tasks(status="pending", include_blocked=False)


def process_exists(pid: int) -> bool:
    """Check if a process with the given PID exists.

    Args:
        pid: Process ID to check

    Returns:
        True if process exists, False otherwise
    """
    import subprocess

    try:
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", "pid="],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except (ValueError, OSError):
        return False


def check_stale_tasks(agency_dir: Path) -> list[dict]:
    """Check for crashed agent tasks and revert them to pending.

    Args:
        agency_dir: Path to .agency directory

    Returns:
        List of stale task info dicts with task_id, agent, and reason
    """
    store = TaskStore(agency_dir)
    stale = []

    for task in store.get_in_progress_tasks():
        if task.agent_info:
            pid = task.agent_info.get("pid")
            if pid and not process_exists(pid):
                # Process is gone, clear agent info
                session_id = task.agent_info.get("session_id")
                store.clear_agent_info(task.task_id)

                stale.append(
                    {
                        "task_id": task.task_id,
                        "agent": task.assigned_to,
                        "session_id": session_id,
                        "reason": "process_not_found",
                    }
                )

    return stale
