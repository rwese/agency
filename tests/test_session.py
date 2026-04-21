"""Tests for session management."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from agency.session import (
    MANAGER_PREFIX,
    SESSION_PREFIX,
    SessionManager,
    create_project_session,
    start_agent_window,
    start_manager_window,
)


class TestSessionManager:
    """Test SessionManager class."""

    @pytest.fixture
    def temp_socket(self):
        """Create a unique socket name for testing."""
        import uuid

        return f"agency-test-{uuid.uuid4().hex[:8]}"

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_session_exists_false(self, temp_socket):
        """Test session_exists returns False for non-existent session."""
        sm = SessionManager("nonexistent-session", socket_name=temp_socket)
        assert sm.session_exists() is False

    def test_create_and_exists(self, temp_socket, temp_dir):
        """Test creating a session and checking existence."""
        session_name = f"{temp_socket}-test"

        # Create session
        create_project_session(session_name, temp_socket, temp_dir)

        # Check exists
        sm = SessionManager(session_name, socket_name=temp_socket)
        assert sm.session_exists() is True

        # Cleanup
        sm.kill_session()

    def test_list_windows_empty(self, temp_socket, temp_dir):
        """Test listing windows in new session."""
        session_name = f"{temp_socket}-test"
        create_project_session(session_name, temp_socket, temp_dir)

        sm = SessionManager(session_name, socket_name=temp_socket)
        windows = sm.list_windows()

        assert windows == []

        # Cleanup
        sm.kill_session()

    def test_kill_session(self, temp_socket, temp_dir):
        """Test killing a session."""
        session_name = f"{temp_socket}-test"
        create_project_session(session_name, temp_socket, temp_dir)

        sm = SessionManager(session_name, socket_name=temp_socket)
        sm.kill_session()

        assert sm.session_exists() is False

    def test_window_naming(self, temp_socket, temp_dir):
        """Test window naming conventions."""
        session_name = f"{temp_socket}-test"
        create_project_session(session_name, temp_socket, temp_dir)

        sm = SessionManager(session_name, socket_name=temp_socket)

        # Manager window
        manager_name = "coordinator"
        start_manager_window(session_name, temp_socket, manager_name, temp_dir / ".agency", temp_dir)

        assert sm.window_exists(f"{MANAGER_PREFIX}{manager_name}")
        assert sm.manager_exists()

        # Agent window
        agent_name = "coder"
        start_agent_window(session_name, temp_socket, agent_name, temp_dir / ".agency", temp_dir)

        assert sm.window_exists(agent_name)

        # Cleanup
        sm.kill_session()

    def test_send_keys(self, temp_socket, temp_dir):
        """Test sending keys to a window."""
        session_name = f"{temp_socket}-test"
        create_project_session(session_name, temp_socket, temp_dir)

        agent_name = "coder"
        start_agent_window(session_name, temp_socket, agent_name, temp_dir / ".agency", temp_dir)

        # Send a test command
        sm = SessionManager(session_name, socket_name=temp_socket)
        sm.send_keys(agent_name, "echo 'hello world'")

        # Give tmux time to process
        import time

        time.sleep(0.5)

        # Cleanup
        sm.kill_session()


class TestSessionNaming:
    """Test session naming conventions."""

    def test_session_prefix(self):
        """Test that sessions use correct prefix."""
        project_name = "my-project"
        expected_session_name = f"{SESSION_PREFIX}{project_name}"

        # The prefix should be used in session names
        assert expected_session_name == "agency-my-project"

    def test_manager_prefix(self):
        """Test that manager windows use correct prefix."""
        manager_name = "coordinator"
        expected_window_name = f"{MANAGER_PREFIX}{manager_name}"

        assert expected_window_name == "[MGR] coordinator"


class TestTmuxIntegration:
    """Integration tests that require tmux."""

    @pytest.fixture
    def temp_socket(self):
        """Create a unique socket name for testing."""
        import uuid

        return f"agency-test-{uuid.uuid4().hex[:8]}"

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.mark.skipif(
        subprocess.run(["which", "tmux"], capture_output=True).returncode != 0,
        reason="tmux not installed",
    )
    def test_full_workflow(self, temp_socket, temp_dir):
        """Test full session workflow."""
        session_name = f"{temp_socket}-workflow"

        # Create .agency directory structure
        agency_dir = temp_dir / ".agency"
        agency_dir.mkdir()
        (agency_dir / "tasks").mkdir()
        (agency_dir / "pending").mkdir()
        (agency_dir / ".scripts").mkdir()

        # Create session
        create_project_session(session_name, temp_socket, temp_dir)

        sm = SessionManager(session_name, socket_name=temp_socket)
        assert sm.session_exists()

        # Start manager
        start_manager_window(session_name, temp_socket, "coordinator", agency_dir, temp_dir)
        assert sm.manager_exists()

        # Start agents
        start_agent_window(session_name, temp_socket, "coder", agency_dir, temp_dir)
        start_agent_window(session_name, temp_socket, "tester", agency_dir, temp_dir)

        windows = sm.list_windows()
        assert len(windows) == 3  # manager + 2 agents
        assert "[MGR] coordinator" in windows
        assert "coder" in windows
        assert "tester" in windows

        # Broadcast shutdown
        sm.broadcast_shutdown()

        # Cleanup
        sm.kill_session()
        assert not sm.session_exists()
