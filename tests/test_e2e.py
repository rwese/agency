"""End-to-end integration tests for agency."""

import os
import subprocess
import time

import pytest


def run_agency(args, cwd=None, check=True):
    """Run agency CLI and return result."""
    env = os.environ.copy()
    return subprocess.run(
        ["agency"] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
        check=check,
    )


class TestCompletions:
    """Test shell completions - these are fast and reliable."""

    def test_bash_completion(self):
        """Test bash completion script."""
        result = run_agency(["completions", "bash"], check=False)
        assert result.returncode == 0
        assert "_agency_completions" in result.stdout
        assert "init)" in result.stdout
        assert "session" in result.stdout
        assert "tasks" in result.stdout

    def test_zsh_completion(self):
        """Test zsh completion script."""
        result = run_agency(["completions", "zsh"], check=False)
        assert result.returncode == 0
        assert "_agency" in result.stdout
        assert '"init:Create' in result.stdout
        assert '"session:Session' in result.stdout

    def test_fish_completion(self):
        """Test fish completion script."""
        result = run_agency(["completions", "fish"], check=False)
        assert result.returncode == 0
        assert "complete -c agency" in result.stdout


class TestInitProject:
    """Test init-project command."""

    @pytest.fixture(autouse=True)
    def unique_project(self, tmp_path):
        """Create unique project per test to avoid session collisions."""
        # Use unique name based on test and random
        import uuid

        project_name = f"test-{uuid.uuid4().hex[:8]}"
        project_dir = tmp_path / project_name
        project_dir.mkdir()
        return project_dir

    def test_init_project_creates_agency_dir(self, unique_project):
        """Test that init-project creates .agency/ directory."""
        result = run_agency(
            ["init", "--dir", str(unique_project)],
            check=False,
        )

        assert result.returncode == 0, f"stdout: {result.stdout}, stderr: {result.stderr}"
        assert (unique_project / ".agency").exists()
        assert (unique_project / ".agency" / "config.yaml").exists()

        # Cleanup
        session_name = f"agency-{unique_project.name}"
        subprocess.run(["tmux", "kill-session", "-t", session_name], capture_output=True)

    def test_init_project_with_template(self, unique_project):
        """Test init-project with template."""
        result = run_agency(
            [
                "init",
                "--dir",
                str(unique_project),
                "--template",
                "https://github.com/rwese/agency-templates",
                "--template-subdir",
                "basic",
            ],
            check=False,
        )

        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert (unique_project / ".agency").exists()

        # Cleanup
        session_name = f"agency-{unique_project.name}"
        subprocess.run(["tmux", "kill-session", "-t", session_name], capture_output=True)

    def test_init_project_with_context_file(self, unique_project):
        """Test init-project with --context-file option."""
        # Create a context file
        context_file = unique_project / "context.md"
        context_file.write_text("# Context file content")

        result = run_agency(
            [
                "init",
                "--dir",
                str(unique_project),
                "--context-file",
                str(context_file),
            ],
            check=False,
        )

        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert (unique_project / ".agency").exists()

        # Check config contains the context file
        config = (unique_project / ".agency" / "config.yaml").read_text()
        assert str(context_file) in config

        # Cleanup
        session_name = f"agency-{unique_project.name}"
        subprocess.run(["tmux", "kill-session", "-t", session_name], capture_output=True)

    def test_init_project_with_invalid_context_file(self, unique_project):
        """Test init-project with --context-file pointing to non-existent file."""
        result = run_agency(
            [
                "init",
                "--dir",
                str(unique_project),
                "--context-file",
                "/nonexistent/path/to/file.md",
            ],
            check=False,
        )

        assert result.returncode == 1
        assert "not found" in result.stderr or "ERROR" in result.stderr

        # Ensure .agency was not created
        assert not (unique_project / ".agency").exists()

    def test_init_project_with_multiple_context_files(self, unique_project):
        """Test init-project with multiple --context-file options."""
        # Create multiple context files
        context1 = unique_project / "context1.md"
        context2 = unique_project / "context2.md"
        context1.write_text("# Context 1")
        context2.write_text("# Context 2")

        result = run_agency(
            [
                "init",
                "--dir",
                str(unique_project),
                "--context-file",
                str(context1),
                "--context-file",
                str(context2),
            ],
            check=False,
        )

        assert result.returncode == 0, f"stderr: {result.stderr}"

        # Check config contains both context files
        config = (unique_project / ".agency" / "config.yaml").read_text()
        assert str(context1) in config
        assert str(context2) in config

        # Cleanup
        session_name = f"agency-{unique_project.name}"
        subprocess.run(["tmux", "kill-session", "-t", session_name], capture_output=True)


class TestTaskWorkflow:
    """Test task management workflow using in-project .agency."""

    @pytest.fixture(autouse=True)
    def project_with_agency(self, tmp_path):
        """Create project with .agency directory manually."""
        import uuid

        project_name = f"task-test-{uuid.uuid4().hex[:8]}"
        project_dir = tmp_path / project_name
        project_dir.mkdir()

        # Create .agency structure manually
        agency_dir = project_dir / ".agency"
        agency_dir.mkdir()
        (agency_dir / "var" / "tasks").mkdir(parents=True)
        (agency_dir / "var" / "pending").mkdir(parents=True)
        (agency_dir / "config.yaml").write_text("project: test\n")

        return project_dir

    def test_add_task(self, project_with_agency):
        """Test adding a task."""
        # Change to project dir so find_agency_dir() works
        result = subprocess.run(
            ["agency", "tasks", "add", "-s", "Test task", "-d", "Test task description"],
            capture_output=True,
            text=True,
            cwd=str(project_with_agency),
        )

        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "Created task:" in result.stdout

    def test_list_tasks(self, project_with_agency):
        """Test listing tasks."""
        # Add a task first
        subprocess.run(
            ["agency", "tasks", "add", "-s", "List test", "-d", "List test task description"],
            capture_output=True,
            cwd=str(project_with_agency),
        )

        # List tasks
        result = subprocess.run(
            ["agency", "tasks", "list"],
            capture_output=True,
            text=True,
            cwd=str(project_with_agency),
        )

        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "List test task" in result.stdout

    def test_complete_and_approve_workflow(self, project_with_agency):
        """Test complete -> approve workflow."""
        # Add task
        result = subprocess.run(
            ["agency", "tasks", "add", "-s", "Complete test", "-d", "Complete test description"],
            capture_output=True,
            text=True,
            cwd=str(project_with_agency),
        )
        task_id = result.stdout.split("Created task: ")[1].strip()

        # Complete task
        result = subprocess.run(
            ["agency", "tasks", "complete", task_id, "--result", "Done"],
            capture_output=True,
            text=True,
            cwd=str(project_with_agency),
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "marked for approval" in result.stdout

        # Verify pending_approval
        result = subprocess.run(
            ["agency", "tasks", "show", task_id],
            capture_output=True,
            text=True,
            cwd=str(project_with_agency),
        )
        assert "pending_approval" in result.stdout

        # Approve task
        result = subprocess.run(
            ["agency", "tasks", "approve", task_id],
            capture_output=True,
            text=True,
            cwd=str(project_with_agency),
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "approved" in result.stdout

        # Verify completed
        result = subprocess.run(
            ["agency", "tasks", "show", task_id],
            capture_output=True,
            text=True,
            cwd=str(project_with_agency),
        )
        assert "completed" in result.stdout

    def test_reject_and_reopen_workflow(self, project_with_agency):
        """Test complete -> reject -> reopen workflow."""
        # Add and complete task
        result = subprocess.run(
            ["agency", "tasks", "add", "-s", "Reject test", "-d", "Reject test description"],
            capture_output=True,
            text=True,
            cwd=str(project_with_agency),
        )
        task_id = result.stdout.split("Created task: ")[1].strip()

        subprocess.run(
            ["agency", "tasks", "complete", task_id, "--result", "Done"],
            capture_output=True,
            cwd=str(project_with_agency),
        )

        # Reject task
        result = subprocess.run(
            ["agency", "tasks", "reject", task_id, "--reason", "Missing tests"],
            capture_output=True,
            text=True,
            cwd=str(project_with_agency),
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "rejected" in result.stdout

        # Verify failed
        result = subprocess.run(
            ["agency", "tasks", "show", task_id],
            capture_output=True,
            text=True,
            cwd=str(project_with_agency),
        )
        assert "failed" in result.stdout

        # Reopen task
        result = subprocess.run(
            ["agency", "tasks", "reopen", task_id],
            capture_output=True,
            text=True,
            cwd=str(project_with_agency),
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "reopened" in result.stdout

        # Verify pending
        result = subprocess.run(
            ["agency", "tasks", "show", task_id],
            capture_output=True,
            text=True,
            cwd=str(project_with_agency),
        )
        assert "pending" in result.stdout


class TestStopSession:
    """Test stop command."""

    @pytest.fixture(autouse=True)
    def clean_session(self, tmp_path):
        """Ensure session is cleaned up after test."""
        import uuid

        project_name = f"stop-test-{uuid.uuid4().hex[:8]}"
        project_dir = tmp_path / project_name
        project_dir.mkdir()

        # Run init
        subprocess.run(
            ["agency", "init", "--dir", str(project_dir)],
            capture_output=True,
        )

        session_name = f"agency-{project_name}"

        yield session_name

        # Cleanup
        subprocess.run(
            ["tmux", "kill-session", "-t", session_name],
            capture_output=True,
        )

    def test_stop_session(self, clean_session):
        """Test stopping a session."""
        result = run_agency(["session", "stop", clean_session, "--force"], check=False)

        # Give tmux time to clean up
        time.sleep(1)

        assert result.returncode == 0, f"stderr: {result.stderr}"

        # Verify session is gone
        result = subprocess.run(
            ["tmux", "has-session", "-t", clean_session],
            capture_output=True,
        )
        assert result.returncode != 0  # Should fail if session doesn't exist
