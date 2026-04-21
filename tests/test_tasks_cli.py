"""Tests for tasks CLI."""

import argparse

import pytest

from agency.tasks import TaskStore
from agency.tasks_cli import (
    cmd_approve,
    cmd_reject,
    cmd_reopen,
)


def make_args(**kwargs):
    """Create an argparse.Namespace."""
    return argparse.Namespace(**kwargs)


class TestApproveCommand:
    """Test cmd_approve."""

    @pytest.fixture
    def store_and_id(self, tmp_path):
        """Create a TaskStore with a pending task."""
        agency_dir = tmp_path / ".agency"
        agency_dir.mkdir()
        (agency_dir / "tasks").mkdir()
        (agency_dir / "pending").mkdir()

        store = TaskStore(agency_dir)
        task = store.add_task(description="Test task")
        store.complete_task(task.task_id, result="Done")
        return store, task.task_id

    def test_approve_success(self, store_and_id):
        """Test successful approval."""
        store, task_id = store_and_id
        args = make_args(task_id=task_id)
        result = cmd_approve(store, args)

        assert result == 0
        task = store.get_task(task_id)
        assert task.status == "completed"

    def test_approve_nonexistent(self, store_and_id):
        """Test approving nonexistent task."""
        store, _ = store_and_id
        args = make_args(task_id="nonexistent")
        result = cmd_approve(store, args)

        assert result == 1


class TestRejectCommand:
    """Test cmd_reject."""

    @pytest.fixture
    def store_and_id(self, tmp_path):
        """Create a TaskStore with a pending task."""
        agency_dir = tmp_path / ".agency"
        agency_dir.mkdir()
        (agency_dir / "tasks").mkdir()
        (agency_dir / "pending").mkdir()

        store = TaskStore(agency_dir)
        task = store.add_task(description="Test task")
        store.complete_task(task.task_id, result="Done")
        return store, task.task_id

    def test_reject_success(self, store_and_id):
        """Test successful rejection."""
        store, task_id = store_and_id
        args = make_args(task_id=task_id, reason="Missing tests", suggestions=None)
        result = cmd_reject(store, args)

        assert result == 0
        task = store.get_task(task_id)
        assert task.status == "failed"

        # Check rejection file
        rejection_file = store.agency_dir / "pending" / f"{task_id}.rejected"
        assert rejection_file.exists()
        content = rejection_file.read_text()
        assert "Missing tests" in content

    def test_reject_with_suggestions(self, store_and_id):
        """Test rejection with suggestions."""
        store, task_id = store_and_id
        args = make_args(
            task_id=task_id,
            reason="Incomplete",
            suggestions=["Add error handling", "Write tests"],
        )
        result = cmd_reject(store, args)

        assert result == 0
        content = (store.agency_dir / "pending" / f"{task_id}.rejected").read_text()
        assert "Incomplete" in content
        assert "Add error handling" in content
        assert "Write tests" in content

    def test_reject_nonexistent(self, store_and_id):
        """Test rejecting nonexistent task."""
        store, _ = store_and_id
        args = make_args(task_id="nonexistent", reason="Error", suggestions=None)
        result = cmd_reject(store, args)

        assert result == 1


class TestReopenCommand:
    """Test cmd_reopen."""

    @pytest.fixture
    def completed_store_and_id(self, tmp_path):
        """Create a TaskStore with a completed task."""
        agency_dir = tmp_path / ".agency"
        agency_dir.mkdir()
        (agency_dir / "tasks").mkdir()
        (agency_dir / "pending").mkdir()

        store = TaskStore(agency_dir)
        task = store.add_task(description="Test task")
        store.complete_task(task.task_id, result="Done")
        store.approve_task(task.task_id)
        return store, task.task_id

    @pytest.fixture
    def failed_store_and_id(self, tmp_path):
        """Create a TaskStore with a failed task."""
        agency_dir = tmp_path / ".agency"
        agency_dir.mkdir()
        (agency_dir / "tasks").mkdir()
        (agency_dir / "pending").mkdir()

        store = TaskStore(agency_dir)
        task = store.add_task(description="Test task")
        store.complete_task(task.task_id, result="Done")
        store.reject_task(task.task_id, reason="Failed")
        return store, task.task_id

    def test_reopen_completed(self, completed_store_and_id):
        """Test reopening completed task."""
        store, task_id = completed_store_and_id
        args = make_args(task_id=task_id)
        result = cmd_reopen(store, args)

        assert result == 0
        task = store.get_task(task_id)
        assert task.status == "pending"

    def test_reopen_failed(self, failed_store_and_id):
        """Test reopening failed task."""
        store, task_id = failed_store_and_id
        args = make_args(task_id=task_id)
        result = cmd_reopen(store, args)

        assert result == 0
        task = store.get_task(task_id)
        assert task.status == "pending"

    def test_reopen_nonexistent(self, completed_store_and_id):
        """Test reopening nonexistent task."""
        store, _ = completed_store_and_id
        args = make_args(task_id="nonexistent")
        result = cmd_reopen(store, args)

        assert result == 1

    def test_reopen_pending_task(self, tmp_path):
        """Test reopening a pending task (should fail)."""
        agency_dir = tmp_path / ".agency"
        agency_dir.mkdir()
        (agency_dir / "tasks").mkdir()
        (agency_dir / "pending").mkdir()

        store = TaskStore(agency_dir)
        task = store.add_task(description="Test task")
        args = make_args(task_id=task.task_id)
        result = cmd_reopen(store, args)

        assert result == 1
