"""Tests for audit trail system."""

import json
import tempfile
from pathlib import Path

import pytest

from agency.audit import (
    ACTION_APPROVE,
    ACTION_ASSIGN,
    ACTION_COMPLETE,
    ACTION_CREATE,
    ACTION_HEARTBEAT,
    ACTION_START,
    ACTION_UPDATE,
    EVENT_AGENT,
    EVENT_CLI,
    EVENT_SESSION,
    EVENT_TASK,
    AuditEvent,
    AuditStore,
)


class TestAuditEvent:
    """Test AuditEvent dataclass."""

    def test_audit_event_to_dict(self):
        """Test AuditEvent serialization to dict."""
        event = AuditEvent(
            event_type=EVENT_TASK,
            action=ACTION_CREATE,
            task_id="swift-bear-a3f2",
            os_user="testuser",
            agency_session="test-project",
        )
        data = event.to_dict()

        assert data["event_type"] == EVENT_TASK
        assert data["action"] == ACTION_CREATE
        assert data["task_id"] == "swift-bear-a3f2"
        assert data["os_user"] == "testuser"
        assert data["agency_session"] == "test-project"

    def test_audit_event_from_row(self):
        """Test AuditEvent creation from row."""
        row = (
            1,
            "2024-01-15T10:30:00",
            EVENT_TASK,
            ACTION_CREATE,
            "testuser",
            "test-project",
            None,
            None,
            None,
            None,
            "swift-bear-a3f2",
            None,
        )
        event = AuditEvent.from_row(row)

        assert event.id == 1
        assert event.timestamp == "2024-01-15T10:30:00"
        assert event.event_type == EVENT_TASK
        assert event.action == ACTION_CREATE
        assert event.task_id == "swift-bear-a3f2"


class TestAuditStore:
    """Test AuditStore."""

    @pytest.fixture
    def temp_agency_dir(self):
        """Create a temporary .agency directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agency_dir = Path(tmpdir) / ".agency"
            agency_dir.mkdir()
            yield agency_dir

    @pytest.fixture
    def audit_store(self, temp_agency_dir):
        """Create an AuditStore instance."""
        return AuditStore(temp_agency_dir)

    def test_init_creates_db(self, temp_agency_dir):
        """Test that initialization creates the database."""
        AuditStore(temp_agency_dir)
        db_path = temp_agency_dir / "var" / "audit.db"
        assert db_path.exists()

    def test_init_creates_tables(self, audit_store):
        """Test that initialization creates required tables."""
        conn = audit_store._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        assert "events" in tables
        assert "meta" in tables

    def test_log_cli(self, audit_store):
        """Test CLI command logging."""
        event_id = audit_store.log_cli(
            command="start",
            args={"dir": "/tmp"},
            cwd="/home/user",
        )
        assert event_id > 0

        events = audit_store.query(event_type=EVENT_CLI)
        assert len(events) == 1
        assert events[0].cli_command == "start"

    def test_log_task(self, audit_store):
        """Test task event logging."""
        event_id = audit_store.log_task(
            action=ACTION_CREATE,
            task_id="swift-bear-a3f2",
            details={"priority": "high"},
        )
        assert event_id > 0

        events = audit_store.query(event_type=EVENT_TASK)
        assert len(events) == 1
        assert events[0].action == ACTION_CREATE
        assert events[0].task_id == "swift-bear-a3f2"

    def test_log_session(self, audit_store):
        """Test session event logging."""
        event_id = audit_store.log_session(
            action=ACTION_START,
            details={"session_name": "agency-test"},
        )
        assert event_id > 0

        events = audit_store.query(event_type=EVENT_SESSION)
        assert len(events) == 1
        assert events[0].action == ACTION_START

    def test_log_agent(self, audit_store):
        """Test agent event logging."""
        event_id = audit_store.log_agent(
            action=ACTION_HEARTBEAT,
            agency_role="manager",
            details={"notification": "unassigned_tasks"},
        )
        assert event_id > 0

        events = audit_store.query(event_type=EVENT_AGENT)
        assert len(events) == 1
        assert events[0].agency_role == "manager"

    def test_query_by_task_id(self, audit_store):
        """Test querying events by task ID."""
        audit_store.log_task(ACTION_CREATE, task_id="task-1")
        audit_store.log_task(ACTION_ASSIGN, task_id="task-2")
        audit_store.log_task(ACTION_COMPLETE, task_id="task-1")

        events = audit_store.query(task_id="task-1")
        assert len(events) == 2

    def test_query_by_event_type(self, audit_store):
        """Test querying events by type."""
        audit_store.log_cli(command="start")
        audit_store.log_cli(command="stop")
        audit_store.log_task(ACTION_CREATE, task_id="task-1")

        cli_events = audit_store.query(event_type=EVENT_CLI)
        task_events = audit_store.query(event_type=EVENT_TASK)

        assert len(cli_events) == 2
        assert len(task_events) == 1

    def test_query_limit(self, audit_store):
        """Test query limit."""
        for i in range(10):
            audit_store.log_cli(command=f"cmd-{i}")

        events = audit_store.query(event_type=EVENT_CLI, limit=5)
        assert len(events) == 5

    def test_stats(self, audit_store):
        """Test statistics generation."""
        audit_store.log_cli(command="start")
        audit_store.log_cli(command="stop")
        audit_store.log_task(ACTION_CREATE, task_id="task-1")

        stats = audit_store.stats()

        assert stats["total_events"] == 3
        assert stats["by_event_type"][EVENT_CLI] == 2
        assert stats["by_event_type"][EVENT_TASK] == 1

    def test_export_json(self, audit_store):
        """Test JSON export."""
        audit_store.log_cli(command="start", args={"dir": "/tmp"})

        exported = audit_store.export(format="json")
        data = json.loads(exported)

        assert len(data) == 1
        assert data[0]["event_type"] == EVENT_CLI
        assert data[0]["cli_command"] == "start"

    def test_export_csv(self, audit_store):
        """Test CSV export."""
        audit_store.log_cli(command="start")

        exported = audit_store.export(format="csv")
        lines = exported.strip().split("\n")

        assert len(lines) == 2  # header + 1 event
        assert "event_type" in lines[0]
        assert EVENT_CLI in lines[1]

    def test_clear_events(self, audit_store):
        """Test clearing old events."""
        audit_store.log_cli(command="start")
        audit_store.log_cli(command="stop")

        # Clear all events (before now)
        deleted = audit_store.clear(before="datetime('now')")
        assert deleted == 2

        # Verify all cleared
        events = audit_store.query()
        assert len(events) == 0


class TestAuditIntegration:
    """Integration tests for audit trail."""

    @pytest.fixture
    def temp_agency_dir(self):
        """Create a temporary .agency directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agency_dir = Path(tmpdir) / ".agency"
            agency_dir.mkdir()
            yield agency_dir

    def test_task_lifecycle_logged(self, temp_agency_dir):
        """Test that task lifecycle events are logged."""
        from agency.tasks import TaskStore

        # Create task store
        task_store = TaskStore(temp_agency_dir)

        # Create audit store
        audit_store = AuditStore(temp_agency_dir)

        # Create task
        task = task_store.add_task(subject="Test task", description="Test task description", priority="high")

        # Check audit log
        events = audit_store.query(task_id=task.task_id)
        assert len(events) >= 1
        assert any(e.action == ACTION_CREATE for e in events)

        # Assign task
        task_store.assign_task(task.task_id, "coder")

        events = audit_store.query(task_id=task.task_id)
        assert any(e.action == ACTION_ASSIGN for e in events)

        # Update task
        task_store.update_task(task.task_id, status="in_progress")

        events = audit_store.query(task_id=task.task_id)
        assert any(e.action == ACTION_UPDATE for e in events)

        # Complete task
        task_store.complete_task(task.task_id, result="Done!")

        events = audit_store.query(task_id=task.task_id)
        assert any(e.action == ACTION_COMPLETE for e in events)

        # Approve task
        task_store.approve_task(task.task_id)

        events = audit_store.query(task_id=task.task_id)
        assert any(e.action == ACTION_APPROVE for e in events)
