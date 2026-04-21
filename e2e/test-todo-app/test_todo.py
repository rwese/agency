#!/usr/bin/env python3
"""Pytest tests for the todo CLI application."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Path to the todo.py script
TODO_SCRIPT = Path(__file__).parent / "todo.py"
TODO_FILE = Path.home() / ".todos.json"


@pytest.fixture(autouse=True)
def clean_todos():
    """Clean up todos.json before and after each test."""
    # Setup: remove todos file if it exists
    if TODO_FILE.exists():
        TODO_FILE.unlink()
    yield
    # Teardown: remove todos file
    if TODO_FILE.exists():
        TODO_FILE.unlink()


def run_todo(*args):
    """Run the todo CLI with given arguments."""
    result = subprocess.run(
        [sys.executable, str(TODO_SCRIPT)] + list(args),
        capture_output=True,
        text=True
    )
    return result


def test_add_task():
    """Test adding a task and verifying it appears in list."""
    # Add a task
    result = run_todo("add", "Buy groceries")
    assert result.returncode == 0
    assert "Added task: Buy groceries" in result.stdout

    # Verify task appears in list
    result = run_todo("list")
    assert result.returncode == 0
    assert "Buy groceries" in result.stdout
    assert "[ ]" in result.stdout  # Not done yet


def test_list_tasks():
    """Test verifying list output format."""
    # Add multiple tasks
    run_todo("add", "First task")
    run_todo("add", "Second task")
    run_todo("add", "Third task")

    # List tasks
    result = run_todo("list")
    assert result.returncode == 0

    # Verify format: "id. [ ] text"
    assert "1." in result.stdout
    assert "2." in result.stdout
    assert "3." in result.stdout
    assert "First task" in result.stdout
    assert "Second task" in result.stdout
    assert "Third task" in result.stdout


def test_list_empty():
    """Test list output when no tasks exist."""
    result = run_todo("list")
    assert result.returncode == 0
    assert "No tasks found." in result.stdout


def test_done_task():
    """Test marking a task as done and verifying status."""
    # Add a task
    run_todo("add", "Task to complete")

    # Mark as done
    result = run_todo("done", "1")
    assert result.returncode == 0
    assert "marked as done" in result.stdout

    # Verify status is now done
    result = run_todo("list")
    assert result.returncode == 0
    assert "[x]" in result.stdout  # Done
    assert "Task to complete" in result.stdout


def test_rm_task():
    """Test removing a task and verifying deletion."""
    # Add tasks
    run_todo("add", "Keep this")
    run_todo("add", "Remove this")
    run_todo("add", "Keep this too")

    # Remove task 2
    result = run_todo("rm", "2")
    assert result.returncode == 0
    assert "removed" in result.stdout

    # Verify only tasks 1 and 3 remain
    result = run_todo("list")
    assert result.returncode == 0
    assert "Keep this" in result.stdout
    assert "Keep this too" in result.stdout
    assert "Remove this" not in result.stdout


def test_persistence():
    """Test verifying todos.json is updated and persists."""
    # Add a task
    run_todo("add", "Persistent task")

    # Verify todos.json was created
    assert TODO_FILE.exists(), "todos.json should be created"

    # Verify contents
    with open(TODO_FILE, "r") as f:
        todos = json.load(f)

    assert len(todos) == 1
    assert todos[0]["text"] == "Persistent task"
    assert todos[0]["done"] is False
    assert "id" in todos[0]

    # Mark as done and verify persistence
    run_todo("done", "1")

    with open(TODO_FILE, "r") as f:
        todos = json.load(f)

    assert len(todos) == 1
    assert todos[0]["done"] is True

    # Remove and verify
    run_todo("rm", "1")

    with open(TODO_FILE, "r") as f:
        todos = json.load(f)

    assert len(todos) == 0


def test_invalid_task_id():
    """Test handling of invalid task IDs."""
    # Try to mark non-existent task as done
    result = run_todo("done", "999")
    assert result.returncode == 0
    assert "not found" in result.stdout

    # Try to remove non-existent task
    result = run_todo("rm", "999")
    assert result.returncode == 0
    assert "not found" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
