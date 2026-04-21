"""Pytest fixtures and configuration for agency tests."""

import os
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def tmux_socket():
    """Unique tmux socket for test session."""
    socket_name = f"agency-test-{os.getpid()}"
    yield socket_name
    # Cleanup
    subprocess.run(
        ["tmux", "-L", socket_name, "kill-server"],
        capture_output=True,
    )


@pytest.fixture
def tmp_project(tmp_path, tmux_socket):
    """Create a temporary project directory."""
    project_dir = tmp_path / "testproject"
    project_dir.mkdir()

    # Initialize git
    subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=project_dir,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=project_dir,
        capture_output=True,
    )

    yield project_dir

    # Cleanup tmux session if exists
    session_name = "agency-testproject"
    subprocess.run(
        ["tmux", "-L", tmux_socket, "kill-session", "-t", session_name],
        capture_output=True,
    )


@pytest.fixture
def mock_agent():
    """Mock agent command for testing."""
    return "python3 -c 'import time; time.sleep(3600)'"


@contextmanager
def tmux_session(socket_name: str, session_name: str, work_dir: Path):
    """Context manager for tmux session."""
    # Kill existing session if any
    subprocess.run(
        ["tmux", "-L", socket_name, "kill-session", "-t", session_name],
        capture_output=True,
    )

    # Create session
    subprocess.run([
        "tmux", "-L", socket_name, "new-session",
        "-d", "-s", session_name,
        "-c", str(work_dir),
    ])

    try:
        yield
    finally:
        subprocess.run(
            ["tmux", "-L", socket_name, "kill-session", "-t", session_name],
            capture_output=True,
        )


def run_in_tmux(socket_name: str, session_name: str, window_name: str, command: str):
    """Run a command in a new tmux window."""
    subprocess.run([
        "tmux", "-L", socket_name, "new-window",
        "-t", f"{session_name}:",
        "-n", window_name,
        "-c", str(Path.home()),
    ])

    # Wait for window to be ready
    time.sleep(0.5)

    # Send command
    subprocess.run([
        "tmux", "-L", socket_name,
        "send-keys", "-t", f"{session_name}:{window_name}",
        command, "C-m",
    ])


def send_to_tmux(socket_name: str, session_name: str, window_name: str, text: str):
    """Send text to a tmux window."""
    subprocess.run([
        "tmux", "-L", socket_name,
        "send-keys", "-t", f"{session_name}:{window_name}",
        text, "C-m",
    ])


def wait_for_window(socket_name: str, session_name: str, window_name: str, timeout: int = 5):
    """Wait for a window to appear."""
    start = time.time()
    while time.time() - start < timeout:
        result = subprocess.run([
            "tmux", "-L", socket_name, "list-windows",
            "-t", session_name, "-F", "#{window_name}",
        ], capture_output=True, text=True)
        if window_name in result.stdout:
            return True
        time.sleep(0.2)
    return False
