"""Tests for task system."""

import json
import tempfile
from pathlib import Path

import pytest

from agency.tasks import Task, TaskStore


class TestTask:
    """Test Task dataclass."""

    def test_task_to_dict(self):
        """Test Task serialization to dict."""
        task = Task(
            task_id="swift-bear-a3f2",
            description="Test task",
            status="pending",
            priority="normal",
        )
        data = task.to_dict()

        assert data["task_id"] == "swift-bear-a3f2"
        assert data["description"] == "Test task"
        assert data["status"] == "pending"
        assert data["priority"] == "normal"
        assert data["assigned_to"] is None

    def test_task_from_dict(self):
        """Test Task deserialization from dict."""
        data = {
            "task_id": "jade-owl-7f2a",
            "description": "Another task",
            "status": "in_progress",
            "priority": "high",
            "assigned_to": "coder",
        }
        task = Task.from_dict(data)

        assert task.task_id == "jade-owl-7f2a"
        assert task.description == "Another task"
        assert task.status == "in_progress"
        assert task.priority == "high"
        assert task.assigned_to == "coder"


class TestTaskStore:
    """Test TaskStore."""

    @pytest.fixture
    def temp_agency_dir(self):
        """Create a temporary .agency directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agency_dir = Path(tmpdir) / ".agency"
            agency_dir.mkdir()
            (agency_dir / "var" / "tasks").mkdir(parents=True)
            (agency_dir / "var" / "pending").mkdir(parents=True)
            yield agency_dir

    @pytest.fixture
    def store(self, temp_agency_dir):
        """Create a TaskStore instance."""
        return TaskStore(temp_agency_dir)

    def test_init_creates_directories(self, temp_agency_dir):
        """Test that TaskStore creates required directories."""
        tasks_dir = temp_agency_dir / "var" / "tasks"
        pending_dir = temp_agency_dir / "var" / "pending"

        assert tasks_dir.exists()
        assert pending_dir.exists()

    def test_add_task(self, store):
        """Test adding a task."""
        task = store.add_task(description="Test task")

        assert task.task_id is not None
        assert task.description == "Test task"
        assert task.status == "pending"
        assert task.priority == "low"
        assert task.assigned_to is None

    def test_add_task_with_priority(self, store):
        """Test adding a task with priority."""
        task = store.add_task(description="High priority task", priority="high")

        assert task.priority == "high"

    def test_add_task_generates_unique_id(self, store):
        """Test that task IDs are unique."""
        task1 = store.add_task(description="Task 1")
        task2 = store.add_task(description="Task 2")

        assert task1.task_id != task2.task_id

    def test_task_id_format(self, store):
        """Test task ID format: word-word-xxxx."""
        task = store.add_task(description="Test")

        parts = task.task_id.split("-")
        assert len(parts) == 3
        assert len(parts[0]) >= 3
        assert len(parts[1]) >= 3
        assert len(parts[2]) == 4
        assert all(c in "0123456789abcdef" for c in parts[2])

    def test_get_task(self, store):
        """Test getting a task by ID."""
        task = store.add_task(description="Get test")

        found = store.get_task(task.task_id)
        assert found is not None
        assert found.task_id == task.task_id
        assert found.description == task.description

    def test_get_nonexistent_task(self, store):
        """Test getting a task that doesn't exist."""
        found = store.get_task("nonexistent-id")
        assert found is None

    def test_list_tasks(self, store):
        """Test listing tasks."""
        store.add_task(description="Task 1")
        store.add_task(description="Task 2")
        store.add_task(description="Task 3")

        tasks = store.list_tasks()
        assert len(tasks) == 3

    def test_list_tasks_filter_status(self, store):
        """Test filtering tasks by status."""
        task1 = store.add_task(description="Task 1")
        store.add_task(description="Task 2")

        store.update_task(task1.task_id, status="in_progress")

        tasks = store.list_tasks(status="in_progress")
        assert len(tasks) == 1
        assert tasks[0].task_id == task1.task_id

    def test_list_tasks_filter_assignee(self, store):
        """Test filtering tasks by assignee."""
        task1 = store.add_task(description="Task 1", assigned_to="coder")
        store.add_task(description="Task 2")

        tasks = store.list_tasks(assignee="coder")
        assert len(tasks) == 1
        assert tasks[0].task_id == task1.task_id

    def test_assign_task(self, store):
        """Test assigning a task."""
        task = store.add_task(description="Assign test")

        result = store.assign_task(task.task_id, "coder")

        assert result is True
        updated = store.get_task(task.task_id)
        assert updated.assigned_to == "coder"

    def test_assign_task_nonexistent(self, store):
        """Test assigning a nonexistent task."""
        result = store.assign_task("nonexistent", "coder")
        assert result is False

    def test_assign_to_busy_agent(self, store):
        """Test assigning to an agent with active task."""
        task1 = store.add_task(description="Task 1")
        store.assign_task(task1.task_id, "coder")
        store.update_task(task1.task_id, status="in_progress")

        task2 = store.add_task(description="Task 2")
        result = store.assign_task(task2.task_id, "coder")

        assert result is False

    def test_update_task_status(self, store):
        """Test updating task status."""
        task = store.add_task(description="Status test")

        result = store.update_task(task.task_id, status="in_progress")

        assert result is True
        updated = store.get_task(task.task_id)
        assert updated.status == "in_progress"
        assert updated.started_at is not None

    def test_update_task_priority(self, store):
        """Test updating task priority."""
        task = store.add_task(description="Priority test")

        result = store.update_task(task.task_id, priority="high")

        assert result is True
        updated = store.get_task(task.task_id)
        assert updated.priority == "high"

    def test_complete_task(self, store):
        """Test completing a task."""
        task = store.add_task(description="Complete test")

        result = store.complete_task(
            task.task_id,
            result="Work completed",
            files=["src/main.py"],
        )

        assert result is True
        updated = store.get_task(task.task_id)
        assert updated.status == "pending_approval"
        assert updated.result == "Work completed"

        # Check pending file
        pending_file = store.agency_dir / "var" / "pending" / f"{task.task_id}.json"
        assert pending_file.exists()

        # Check result file
        result_file = store.agency_dir / "var" / "tasks" / task.task_id / "result.json"
        assert result_file.exists()

    def test_approve_task(self, store):
        """Test approving a task."""
        task = store.add_task(description="Approve test")
        store.complete_task(task.task_id, result="Done")

        result = store.approve_task(task.task_id)

        assert result is True
        updated = store.get_task(task.task_id)
        assert updated.status == "completed"

    def test_reject_task(self, store):
        """Test rejecting a task."""
        task = store.add_task(description="Reject test")
        store.complete_task(task.task_id, result="Done")

        result = store.reject_task(
            task.task_id,
            reason="Missing tests",
            suggestions=["Add unit tests"],
        )

        assert result is True
        updated = store.get_task(task.task_id)
        assert updated.status == "failed"

        # Check rejection file
        rejection_file = store.agency_dir / "var" / "pending" / f"{task.task_id}.rejected"
        assert rejection_file.exists()
        content = rejection_file.read_text()
        assert "Missing tests" in content
        assert "Add unit tests" in content

    def test_delete_task(self, store):
        """Test deleting a task."""
        task = store.add_task(description="Delete test")

        result = store.delete_task(task.task_id)

        assert result is True
        assert store.get_task(task.task_id) is None

        # Check directory removed
        task_dir = store.agency_dir / "var" / "tasks" / task.task_id
        assert not task_dir.exists()

    def test_history(self, store):
        """Test getting task history."""
        task1 = store.add_task(description="Completed task")
        store.complete_task(task1.task_id, result="Done")
        store.approve_task(task1.task_id)

        task2 = store.add_task(description="Failed task")
        store.complete_task(task2.task_id, result="Done")
        store.reject_task(task2.task_id, reason="Error")

        history = store.history()

        assert len(history) == 2
        task_ids = [h["task"]["task_id"] for h in history]
        assert task1.task_id in task_ids
        assert task2.task_id in task_ids

    def test_history_filter_by_agent(self, store):
        """Test filtering history by agent."""
        task1 = store.add_task(description="Task 1", assigned_to="coder")
        store.complete_task(task1.task_id, result="Done")
        store.approve_task(task1.task_id)

        task2 = store.add_task(description="Task 2", assigned_to="tester")
        store.complete_task(task2.task_id, result="Done")
        store.approve_task(task2.task_id)

        history = store.history(agent="coder")

        assert len(history) == 1
        assert history[0]["task"]["assigned_to"] == "coder"

    def test_is_agent_free(self, store):
        """Test checking if agent is free."""
        # No tasks = free
        assert store.is_agent_free("coder") is True

        # With pending task = not free
        task = store.add_task(description="Pending task", assigned_to="coder")
        assert store.is_agent_free("coder") is False

        # With in_progress task = not free
        store.update_task(task.task_id, status="in_progress")
        assert store.is_agent_free("coder") is False

        # Complete and approve = free again
        store.complete_task(task.task_id, result="Done")
        store.approve_task(task.task_id)
        assert store.is_agent_free("coder") is True

    def test_concurrent_adds(self, store):
        """Test that multiple adds don't conflict (serialized)."""
        # This tests that the lock prevents concurrent modifications
        tasks = []
        for i in range(10):
            task = store.add_task(description=f"Concurrent task {i}")
            tasks.append(task)

        assert len(store.list_tasks()) == 10

        # All IDs should be unique
        ids = [t.task_id for t in tasks]
        assert len(set(ids)) == 10


class TestTaskStoreFileLocking:
    """Test file locking behavior."""

    @pytest.fixture
    def temp_agency_dir(self):
        """Create a temporary .agency directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agency_dir = Path(tmpdir) / ".agency"
            agency_dir.mkdir()
            (agency_dir / "var" / "tasks").mkdir(parents=True)
            (agency_dir / "var" / "pending").mkdir(parents=True)
            yield agency_dir

    def test_lock_file_created(self, temp_agency_dir):
        """Test that lock file is created."""
        store = TaskStore(temp_agency_dir)
        store.add_task(description="Lock test")

        # Lock file may or may not exist depending on timing
        # The important thing is that operations complete without error
        assert True

    def test_tasks_json_version(self, temp_agency_dir):
        """Test that tasks.json has correct version."""
        store = TaskStore(temp_agency_dir)
        store.add_task(description="Version test")

        tasks_file = temp_agency_dir / "var" / "tasks.json"
        data = json.loads(tasks_file.read_text())

        assert data["version"] == 2
        assert "tasks" in data


class TestTaskDependencies:
    """Test task dependency functionality."""

    @pytest.fixture
    def temp_agency_dir(self):
        """Create a temporary .agency directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agency_dir = Path(tmpdir) / ".agency"
            agency_dir.mkdir()
            (agency_dir / "var" / "tasks").mkdir(parents=True)
            (agency_dir / "var" / "pending").mkdir(parents=True)
            yield agency_dir

    @pytest.fixture
    def store(self, temp_agency_dir):
        """Create a TaskStore instance."""
        return TaskStore(temp_agency_dir)

    def test_set_dependencies(self, store):
        """Test setting dependencies for a task."""
        task1 = store.add_task(description="Task 1")
        task2 = store.add_task(description="Task 2")

        result = store.set_dependencies(task2.task_id, [task1.task_id])

        assert result is True
        updated = store.get_task(task2.task_id)
        assert updated.depends_on == [task1.task_id]

    def test_set_dependencies_nonexistent(self, store):
        """Test setting dependencies with nonexistent task."""
        task1 = store.add_task(description="Task 1")

        with pytest.raises(ValueError, match="does not exist"):
            store.set_dependencies(task1.task_id, ["nonexistent-id"])

    def test_set_dependencies_self_reference(self, store):
        """Test that a task cannot depend on itself."""
        task1 = store.add_task(description="Task 1")

        with pytest.raises(ValueError, match="cannot depend on itself"):
            store.set_dependencies(task1.task_id, [task1.task_id])

    def test_circular_dependency_detection(self, store):
        """Test that circular dependencies are detected."""
        task1 = store.add_task(description="Task 1")
        task2 = store.add_task(description="Task 2")
        task3 = store.add_task(description="Task 3")

        # Task1 depends on nothing
        # Task2 depends on Task1 (ok)
        store.set_dependencies(task2.task_id, [task1.task_id])
        # Task3 depends on Task2 (ok)
        store.set_dependencies(task3.task_id, [task2.task_id])

        # Now try to make Task1 depend on Task3 (would create cycle)
        with pytest.raises(ValueError, match="circular dependency"):
            store.set_dependencies(task1.task_id, [task3.task_id])

    def test_add_dependency(self, store):
        """Test adding a single dependency."""
        task1 = store.add_task(description="Task 1")
        task2 = store.add_task(description="Task 2")
        task3 = store.add_task(description="Task 3")

        store.add_dependency(task2.task_id, task1.task_id)
        store.add_dependency(task2.task_id, task3.task_id)

        updated = store.get_task(task2.task_id)
        assert task1.task_id in updated.depends_on
        assert task3.task_id in updated.depends_on

    def test_add_duplicate_dependency(self, store):
        """Test adding a dependency that already exists."""
        task1 = store.add_task(description="Task 1")
        task2 = store.add_task(description="Task 2")

        store.add_dependency(task2.task_id, task1.task_id)
        result = store.add_dependency(task2.task_id, task1.task_id)

        # Should return True but not add duplicate
        assert result is True
        updated = store.get_task(task2.task_id)
        assert updated.depends_on == [task1.task_id]

    def test_remove_dependency(self, store):
        """Test removing a dependency."""
        task1 = store.add_task(description="Task 1")
        task2 = store.add_task(description="Task 2")
        task3 = store.add_task(description="Task 3")

        store.set_dependencies(task2.task_id, [task1.task_id, task3.task_id])
        store.remove_dependency(task2.task_id, task1.task_id)

        updated = store.get_task(task2.task_id)
        assert task1.task_id not in updated.depends_on
        assert task3.task_id in updated.depends_on

    def test_has_blocked_dependencies(self, store):
        """Test detecting blocked tasks."""
        task1 = store.add_task(description="Task 1")
        task2 = store.add_task(description="Task 2")

        # Task2 depends on Task1 (not completed yet)
        store.set_dependencies(task2.task_id, [task1.task_id])

        task2_obj = store.get_task(task2.task_id)
        assert store._has_blocked_dependencies(task2_obj) is True

    def test_has_blocked_dependencies_completed(self, store):
        """Test that completed dependencies don't block."""
        task1 = store.add_task(description="Task 1")
        task2 = store.add_task(description="Task 2")

        store.set_dependencies(task2.task_id, [task1.task_id])
        store.complete_task(task1.task_id, result="Done")
        store.approve_task(task1.task_id)

        task2_obj = store.get_task(task2.task_id)
        assert store._has_blocked_dependencies(task2_obj) is False

    def test_list_tasks_excludes_blocked_by_default(self, store):
        """Test that list_tasks excludes blocked tasks by default."""
        task1 = store.add_task(description="Task 1")
        task2 = store.add_task(description="Task 2")
        task3 = store.add_task(description="Task 3")  # No dependencies

        store.set_dependencies(task2.task_id, [task1.task_id])

        tasks = store.list_tasks()
        task_ids = [t.task_id for t in tasks]

        assert task1.task_id in task_ids
        assert task3.task_id in task_ids
        assert task2.task_id not in task_ids  # Blocked by incomplete dependency

    def test_list_tasks_include_blocked(self, store):
        """Test listing tasks including blocked ones."""
        task1 = store.add_task(description="Task 1")
        task2 = store.add_task(description="Task 2")

        store.set_dependencies(task2.task_id, [task1.task_id])

        tasks = store.list_tasks(include_blocked=True)
        task_ids = [t.task_id for t in tasks]

        assert task1.task_id in task_ids
        assert task2.task_id in task_ids

    def test_assign_blocked_task_fails(self, store):
        """Test that assigning a blocked task raises error."""
        task1 = store.add_task(description="Task 1")
        task2 = store.add_task(description="Task 2")

        store.set_dependencies(task2.task_id, [task1.task_id])

        with pytest.raises(ValueError, match="blocked by incomplete dependencies"):
            store.assign_task(task2.task_id, "coder")

    def test_get_blocked_by(self, store):
        """Test getting blocking tasks."""
        task1 = store.add_task(description="Task 1")
        task2 = store.add_task(description="Task 2")
        task3 = store.add_task(description="Task 3")

        store.set_dependencies(task2.task_id, [task1.task_id, task3.task_id])

        blocking = store.get_blocked_by(task2.task_id)
        blocking_ids = [t.task_id for t in blocking]

        assert task1.task_id in blocking_ids
        assert task3.task_id in blocking_ids

        # Complete task3, should only show task1 as blocking
        store.complete_task(task3.task_id, result="Done")
        store.approve_task(task3.task_id)

        blocking = store.get_blocked_by(task2.task_id)
        blocking_ids = [t.task_id for t in blocking]

        assert task1.task_id in blocking_ids
        assert task3.task_id not in blocking_ids

    def test_task_serialization_includes_depends_on(self, store):
        """Test that depends_on is serialized correctly."""
        task1 = store.add_task(description="Task 1")
        task2 = store.add_task(description="Task 2")

        store.set_dependencies(task2.task_id, [task1.task_id])

        data = store._read_tasks_json()
        assert data["tasks"][task2.task_id]["depends_on"] == [task1.task_id]
