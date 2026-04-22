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
TASKS_FILE = "tasks.json"
TASKS_DIR = "tasks"
PENDING_DIR = "pending"
HALTED_FILE = ".halted"


@dataclass
class Task:
    """Represents a task."""

    task_id: str
    description: str
    status: str = "pending"  # pending, in_progress, pending_approval, completed, failed
    priority: str = "low"  # low, normal, high
    assigned_to: str | None = None
    created_at: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    result: str | None = None
    result_path: str | None = None
    depends_on: list[str] | None = None  # List of task IDs this task depends on

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
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
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            task_id=data["task_id"],
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
        )


class TaskStore:
    """Manages tasks with file locking."""

    def __init__(self, agency_dir: Path):
        self.agency_dir = agency_dir
        self.tasks_file = agency_dir / TASKS_FILE
        self.lock_file = agency_dir / ".tasks.lock"
        self._audit_store = None

        # Ensure directories exist
        agency_dir.mkdir(parents=True, exist_ok=True)
        (agency_dir / TASKS_DIR).mkdir(exist_ok=True)
        (agency_dir / PENDING_DIR).mkdir(exist_ok=True)

    def _get_audit_store(self):
        """Get audit store lazily."""
        if self._audit_store is None:
            try:
                from agency.audit import AuditStore
                self._audit_store = AuditStore(self.agency_dir)
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
            tasks = [t for t in tasks if t.status == status]

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
        description: str,
        priority: str = "low",
        assigned_to: str | None = None,
    ) -> Task:
        """Add a new task."""
        with self._lock():
            data = self._read_tasks_json()

            # Generate task ID
            task_id = self._generate_task_id(data)

            # Create task directory
            task_dir = self.agency_dir / TASKS_DIR / task_id
            task_dir.mkdir(parents=True, exist_ok=True)

            # Create task file
            task_json = task_dir / "task.json"
            now = datetime.now().isoformat()

            task = Task(
                task_id=task_id,
                description=description,
                status="pending",
                priority=priority,
                assigned_to=assigned_to,
                created_at=now,
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
                        "description": description,
                        "priority": priority,
                        "assigned_to": assigned_to,
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
                raise ValueError(f"Setting these dependencies would create a circular dependency")

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
                    details={"status": status, "priority": priority},
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
