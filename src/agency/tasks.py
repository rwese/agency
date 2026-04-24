"""
Agency v2.0 - Task Management

Handles task operations with file locking and directory management.
Uses Pydantic models generated from JSON schemas for validation.
"""

import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

from filelock import FileLock
from pydantic import ValidationError

from agency.models.task import Task as TaskModel

# Alias for backwards compatibility
Task = TaskModel

# Constants
TASKS_FILE = "var/tasks.json"
TASKS_DIR = "var/tasks"
PENDING_DIR = "var/pending"

# Valid status and priority values (for methods that need them)
VALID_STATUSES = {"pending", "in_progress", "pending_approval", "completed", "failed"}
VALID_PRIORITIES = {"low", "normal", "high"}


def _is_valid_task_id(task_id: str) -> bool:
    """Check if task_id matches pattern word-word-hex."""
    return bool(re.match(r"^[a-z]+-[a-z]+-[0-9a-f]{4}$", task_id))


def validate_task_data(data: dict) -> list[str]:
    """Validate task data against schema using Pydantic.

    Returns list of error messages. Empty list means valid.
    """
    try:
        Task.model_validate(data)
        return []
    except ValidationError as e:
        return [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]


class TaskStore:
    """Manages tasks with file locking."""

    def __init__(self, agency_dir: Path):
        self.agency_dir = agency_dir
        self.tasks_file = agency_dir / TASKS_FILE
        self.lock_file = agency_dir / "var" / ".tasks.lock"
        self._lock = FileLock(str(self.lock_file), timeout=10)
        self._audit_store = None  # Lazy init

        # Ensure directories exist
        agency_dir.mkdir(parents=True, exist_ok=True)
        (agency_dir / "var" / "tasks").mkdir(parents=True, exist_ok=True)
        (agency_dir / "var" / "pending").mkdir(parents=True, exist_ok=True)

    def _read_tasks_json(self) -> dict:
        """Read and parse tasks.json."""
        if not self.tasks_file.exists():
            return {"version": 2, "tasks": {}}

        try:
            with open(self.tasks_file) as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"version": 2, "tasks": {}}

    def _write_tasks_json(self, data: dict) -> None:
        """Write tasks.json atomically."""
        # Write to temp file first, then rename
        temp_file = self.tasks_file.with_suffix(".tmp")
        with open(temp_file, "w") as f:
            json.dump(data, f, indent=2)
        temp_file.rename(self.tasks_file)

    def _generate_task_id(self, data: dict) -> str:
        """Generate unique task ID using word-word-hex format."""
        import secrets

        # Get used IDs
        used_ids = set(data.get("tasks", {}).keys())

        # Use eff.org short words (subset for readability)
        words = [
            "atom", "bird", "cake", "desk", "eagle", "fire", "gold", "harp",
            "iris", "jade", "kite", "lamp", "moon", "nest", "oaks", "palm",
            "rain", "sage", "tree", "unit", "vine", "wave", "yarn", "zion",
            "apex", "bark", "cave", "dawn", "echo", "fern", "glow", "haze",
            "icon", "jolt", "knot", "lark", "mist", "node", "opal", "peak",
            "quad", "rust", "sand", "tide", "volt", "wind", "xray", "year",
        ]

        for _ in range(100):  # Max attempts
            word1 = secrets.choice(words)
            word2 = secrets.choice(words)
            hex_id = secrets.token_hex(2)[:4]
            task_id = f"{word1}-{word2}-{hex_id}"
            if task_id not in used_ids:
                return task_id

        raise RuntimeError("Failed to generate unique task ID")

    def _get_audit_store(self):
        """Get audit store if available."""
        if self._audit_store is None:
            try:
                from agency.audit import AuditStore
                from agency.config import load_agency_config

                config = load_agency_config(self.agency_dir)
                if config and config.audit_enabled:
                    self._audit_store = AuditStore(self.agency_dir)
                else:
                    self._audit_store = False
            except Exception:
                self._audit_store = False  # Mark as unavailable
        return self._audit_store if self._audit_store else None

    def _find_task_by_subject(self, data: dict, subject: str) -> Task | None:
        """Find existing task by subject (case-insensitive).

        Used for deduplication to prevent creating duplicate tasks.
        Returns the first matching task or None if not found.
        """
        tasks = data.get("tasks", {})
        subject_lower = subject.lower()
        for task_data in tasks.values():
            if task_data.get("subject", "").lower() == subject_lower:
                return Task.model_validate(task_data)
        return None

    def list_tasks(
        self,
        status: str | None = None,
        assignee: str | None = None,
        include_blocked: bool = False,
    ) -> list[Task]:
        """List tasks with optional filters."""
        data = self._read_tasks_json()
        tasks = []

        for task_data in data.get("tasks", {}).values():
            # Validate task data
            errors = validate_task_data(task_data)
            if errors:
                continue  # Skip invalid tasks

            task = Task.model_validate(task_data)

            # Filter by status
            if status and task.status != status:
                continue

            # Filter by assignee
            if assignee and task.assigned_to != assignee:
                continue

            # Filter blocked tasks
            if not include_blocked and task.depends_on:
                blocked = self.get_blocked_by(task.task_id)
                if blocked:
                    continue

            tasks.append(task)

        # Sort by priority (high > normal > low), then created_at
        priority_order = {"high": 0, "normal": 1, "low": 2}
        tasks.sort(
            key=lambda t: (
                priority_order.get(t.priority or "low", 1),
                t.created_at or "",
            )
        )
        return tasks

    def get_task(self, task_id: str) -> Task | None:
        """Get a single task by ID."""
        data = self._read_tasks_json()
        tasks = data.get("tasks", {})

        if task_id in tasks:
            try:
                return Task.model_validate(tasks[task_id])
            except ValidationError:
                return None

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

        # Validate priority
        if priority not in VALID_PRIORITIES:
            raise ValueError(f"Task priority must be one of {VALID_PRIORITIES}")

        with self._lock:
            data = self._read_tasks_json()

            # Deduplication: Check for existing task with same subject (case-insensitive)
            existing_task = self._find_task_by_subject(data, subject.strip())
            if existing_task:
                # Return existing task instead of creating duplicate
                return existing_task

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

            data["tasks"][task_id] = task.model_dump(mode="json")
            self._write_tasks_json(data)

            # Audit log
            audit = self._get_audit_store()
            if audit:
                audit.log_task(
                    action="create",
                    task_id=task_id,
                    details={"subject": subject, "priority": priority},
                )

            return task

    def get_in_progress_tasks(self) -> list[Task]:
        """Get all tasks currently in progress."""
        return self.list_tasks(status="in_progress")

    def get_unblocked_pending_tasks(self) -> list[Task]:
        """Get pending tasks that are not blocked by dependencies."""
        pending = self.list_tasks(status="pending")
        return [t for t in pending if not self.get_blocked_by(t.task_id)]

    def get_agent_busy_count(self, agent: str) -> int:
        """Get count of pending + in_progress tasks for an agent."""
        pending = self.list_tasks(status="pending", assignee=agent)
        in_progress = self.list_tasks(status="in_progress", assignee=agent)
        return len(pending) + len(in_progress)

    def assign_task(self, task_id: str, agent: str) -> bool:
        """Assign a task to an agent.

        Returns False if task doesn't exist.
        Raises ValueError if task is blocked by incomplete dependencies.
        """
        with self._lock:
            data = self._read_tasks_json()
            tasks = data.get("tasks", {})

            if task_id not in tasks:
                return False  # Return False for nonexistent

            # Check if blocked by incomplete dependencies
            if tasks[task_id].get("depends_on"):
                blocked = []
                for dep_id in tasks[task_id]["depends_on"]:
                    if dep_id in tasks and tasks[dep_id]["status"] != "completed":
                        blocked.append(dep_id)
                if blocked:
                    raise ValueError(f"Task is blocked by incomplete dependencies: {', '.join(blocked)}")

            # Check if agent is busy (has in_progress task)
            for t_data in tasks.values():
                if t_data.get("assigned_to") == agent and t_data.get("status") == "in_progress":
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

    def pickup_task(self, task_id: str, agent: str, session_id: str | None = None) -> bool:
        """Mark a task as picked up by an agent (sets status to in_progress)."""
        with self._lock:
            data = self._read_tasks_json()
            tasks = data.get("tasks", {})

            if task_id not in tasks:
                return False

            task = tasks[task_id]

            # Check if blocked
            if task.get("depends_on"):
                blocked = False
                for dep_id in task["depends_on"]:
                    if dep_id in tasks and tasks[dep_id]["status"] != "completed":
                        blocked = True
                        break
                if blocked:
                    return False

            # Update task
            task["status"] = "in_progress"
            task["assigned_to"] = agent
            task["started_at"] = datetime.now().isoformat()
            task["agent_info"] = {
                "session_id": session_id,
                "pid": os.getpid(),
                "started_at": task["started_at"],
            }

            self._write_tasks_json(data)

            # Audit log
            audit = self._get_audit_store()
            if audit:
                audit.log_task(
                    action="pickup",
                    task_id=task_id,
                    details={"agent": agent, "session_id": session_id},
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
        with self._lock:
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
            result_path.parent.mkdir(parents=True, exist_ok=True)
            result_path.write_text(json.dumps(result_data, indent=2))
            tasks[task_id]["result_path"] = str(result_path.relative_to(self.agency_dir))

            # Move to pending/
            pending_data = {**tasks[task_id], **result_data, "pending_approval_at": now}
            pending_file = self.agency_dir / PENDING_DIR / f"{task_id}.json"
            pending_file.parent.mkdir(parents=True, exist_ok=True)
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
        """Approve a task (move to completed)."""
        with self._lock:
            data = self._read_tasks_json()
            tasks = data.get("tasks", {})

            if task_id not in tasks:
                return False

            if tasks[task_id]["status"] != "pending_approval":
                return False

            tasks[task_id]["status"] = "completed"
            tasks[task_id]["completed_at"] = datetime.now().isoformat()

            # Remove pending file
            pending_file = self.agency_dir / PENDING_DIR / f"{task_id}.json"
            if pending_file.exists():
                pending_file.unlink()

            # Archive task directory
            task_dir = self.agency_dir / TASKS_DIR / task_id
            archive_dir = self.agency_dir / "var" / "tasks" / task_id
            if task_dir.exists() and not archive_dir.exists():
                task_dir.rename(archive_dir)

            self._write_tasks_json(data)

            # Audit log
            audit = self._get_audit_store()
            if audit:
                audit.log_task(
                    action="approve",
                    task_id=task_id,
                    details={},
                )

            return True

    def reject_task(
        self, task_id: str, reason: str, suggestions: list | None = None
    ) -> bool:
        """Reject a task (mark as failed with reason)."""
        with self._lock:
            data = self._read_tasks_json()
            tasks = data.get("tasks", {})

            if task_id not in tasks:
                return False

            if tasks[task_id]["status"] != "pending_approval":
                return False

            tasks[task_id]["status"] = "failed"
            tasks[task_id]["completed_at"] = datetime.now().isoformat()
            tasks[task_id]["rejection_reason"] = reason

            # Clear agent_info to allow re-assignment
            tasks[task_id]["agent_info"] = None
            tasks[task_id]["started_at"] = None

            # Create rejection file
            rejection_path = self.agency_dir / PENDING_DIR / f"{task_id}.rejected"
            rejection_path.write_text(
                json.dumps(
                    {
                        "reason": reason,
                        "suggestions": suggestions or [],
                        "rejected_at": datetime.now().isoformat(),
                    },
                    indent=2,
                )
            )

            # Remove pending file
            pending_file = self.agency_dir / PENDING_DIR / f"{task_id}.json"
            if pending_file.exists():
                pending_file.unlink()

            self._write_tasks_json(data)

            # Audit log
            audit = self._get_audit_store()
            if audit:
                audit.log_task(
                    action="reject",
                    task_id=task_id,
                    details={"reason": reason, "suggestions": suggestions},
                )

            return True

    def reopen_task(self, task_id: str) -> bool:
        """Reopen a completed or failed task (set back to pending)."""
        with self._lock:
            data = self._read_tasks_json()
            tasks = data.get("tasks", {})

            if task_id not in tasks:
                return False

            current_status = tasks[task_id].get("status")
            if current_status not in ("completed", "failed"):
                return False

            # Clear completion fields
            tasks[task_id]["status"] = "pending"
            tasks[task_id]["completed_at"] = None
            tasks[task_id]["result"] = None
            tasks[task_id]["rejection_reason"] = None
            tasks[task_id]["agent_info"] = None
            tasks[task_id]["started_at"] = None

            # Remove rejection file if exists
            rejection_file = self.agency_dir / PENDING_DIR / f"{task_id}.rejected"
            if rejection_file.exists():
                rejection_file.unlink()

            self._write_tasks_json(data)

            # Audit log
            audit = self._get_audit_store()
            if audit:
                audit.log_task(
                    action="reopen",
                    task_id=task_id,
                    details={"from_status": current_status},
                )

            return True

    def is_agent_free(self, agent: str) -> bool:
        """Check if agent has no assigned tasks (pending or in_progress)."""
        return self.get_agent_busy_count(agent) == 0

    def get_blocked_by(self, task_id: str) -> list[Task]:
        """Get list of incomplete tasks that this task depends on."""
        task = self.get_task(task_id)
        if not task or not task.depends_on:
            return []

        blocking = []
        for dep_id in task.depends_on:
            dep_task = self.get_task(dep_id)
            if dep_task and dep_task.status != "completed":
                blocking.append(dep_task)

        return blocking

    def _has_blocked_dependencies(self, task: Task) -> bool:
        """Check if task is blocked by incomplete dependencies (internal method)."""
        if not task.depends_on:
            return False
        for dep_id in task.depends_on:
            dep_task = self.get_task(dep_id)
            if dep_task and dep_task.status != "completed":
                return True
        return False

    def set_dependencies(self, task_id: str, depends_on: list[str]) -> bool:
        """Set dependencies for a task.

        Raises:
            ValueError: If task doesn't exist, dependency doesn't exist,
                        self-reference, or circular dependency.
        """
        with self._lock:
            data = self._read_tasks_json()
            tasks = data.get("tasks", {})

            # Check task exists
            if task_id not in tasks:
                raise ValueError(f"Task '{task_id}' does not exist")

            # Validate dependencies
            for dep_id in depends_on:
                # Self-reference check
                if dep_id == task_id:
                    raise ValueError(f"Task '{task_id}' cannot depend on itself")
                # Existence check
                if dep_id not in tasks:
                    raise ValueError(f"Dependency '{dep_id}' does not exist")
                # Circular dependency check
                if self._would_create_cycle(task_id, dep_id, tasks):
                    raise ValueError(f"Would create circular dependency: {task_id} -> {dep_id}")

            tasks[task_id]["depends_on"] = depends_on
            self._write_tasks_json(data)

            # Audit log
            audit = self._get_audit_store()
            if audit:
                audit.log_task(
                    action="set_dependencies",
                    task_id=task_id,
                    details={"depends_on": depends_on},
                )

            return True

    def _would_create_cycle(self, task_id: str, new_dep: str, tasks: dict) -> bool:
        """Check if adding new_dep as dependency for task_id would create a cycle."""
        # Check if task_id is reachable from new_dep
        visited = set()
        stack = [new_dep]
        while stack:
            current = stack.pop()
            if current == task_id:
                return True  # Cycle detected
            if current in visited:
                continue
            visited.add(current)
            deps = tasks.get(current, {}).get("depends_on", [])
            if deps:
                stack.extend(deps)
        return False

    def add_dependency(self, task_id: str, depends_on: str) -> bool:
        """Add a dependency to a task.

        Returns True if dependency was added or already exists (no-op).
        """
        task = self.get_task(task_id)
        if not task:
            return False

        current_deps = list(task.depends_on) if task.depends_on else []
        if depends_on in current_deps:
            return True  # Already a dependency - no-op is success

        current_deps.append(depends_on)
        return self.set_dependencies(task_id, current_deps)

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
        """Update task fields.

        Status transitions allowed:
        - pending -> in_progress
        - in_progress -> pending
        - in_progress -> pending_approval
        - pending_approval -> pending (reject flow)
        - completed/failed -> pending (reopen)

        Note: completed/failed must be set via approve_task/reject_task,
        not via update_task.
        """
        with self._lock:
            data = self._read_tasks_json()
            tasks = data.get("tasks", {})

            if task_id not in tasks:
                return False

            now = datetime.now().isoformat()
            current_status = tasks[task_id].get("status", "pending")

            if status:
                # Validate status transitions - prevent completed/failed via update_task
                valid_transitions = {
                    "pending": ["in_progress"],
                    "in_progress": ["pending", "pending_approval"],
                    "pending_approval": ["pending"],  # For rejection
                    "completed": ["pending"],  # For reopening
                    "failed": ["pending"],  # For reopening
                }

                allowed = valid_transitions.get(current_status, [])
                if status not in allowed:
                    # Also allow no-op transitions (setting same status)
                    if status != current_status:
                        return False

                # Validate status value
                if status not in VALID_STATUSES:
                    return False

                tasks[task_id]["status"] = status

                if status == "in_progress" and not tasks[task_id].get("started_at"):
                    tasks[task_id]["started_at"] = now
                elif status == "completed":
                    tasks[task_id]["completed_at"] = now
                elif status == "failed":
                    tasks[task_id]["completed_at"] = now

            if priority:
                if priority not in VALID_PRIORITIES:
                    return False
                tasks[task_id]["priority"] = priority

            if reviewer_assigned is not None:
                tasks[task_id]["reviewer_assigned"] = reviewer_assigned

            self._write_tasks_json(data)

            # Audit log
            audit = self._get_audit_store()
            if audit:
                audit.log_task(action="update", task_id=task_id, details={})

            return True

    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        with self._lock:
            data = self._read_tasks_json()
            tasks = data.get("tasks", {})

            if task_id not in tasks:
                return False

            del tasks[task_id]
            self._write_tasks_json(data)

            # Clean up files
            task_dir = self.agency_dir / TASKS_DIR / task_id
            if task_dir.exists():
                shutil.rmtree(task_dir)

            pending_file = self.agency_dir / PENDING_DIR / f"{task_id}.json"
            if pending_file.exists():
                pending_file.unlink()

            rejection_file = self.agency_dir / PENDING_DIR / f"{task_id}.rejected"
            if rejection_file.exists():
                rejection_file.unlink()

            # Audit log
            audit = self._get_audit_store()
            if audit:
                audit.log_task(action="delete", task_id=task_id, details={})

            return True

    def history(self, agent: str | None = None) -> list[dict]:
        """Get task history for audit purposes."""
        data = self._read_tasks_json()
        history = []

        for task_data in data.get("tasks", {}).values():
            if agent and task_data.get("assigned_to") != agent:
                continue

            history.append(
                {
                    "task": {
                        "task_id": task_data.get("task_id", ""),
                        "subject": task_data.get("subject", ""),
                        "status": task_data.get("status", ""),
                        "assigned_to": task_data.get("assigned_to"),
                        "created_at": task_data.get("created_at"),
                        "completed_at": task_data.get("completed_at"),
                    }
                }
            )

        return sorted(history, key=lambda x: x.get("task", {}).get("created_at") or "", reverse=True)
