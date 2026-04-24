"""
Tests for Pydantic model validation throughout the codebase.

These tests verify that invalid data is properly rejected by Pydantic models.
"""


import pytest
from pydantic import ValidationError

from agency.config import AgencyConfig, AgentConfig, ManagerConfig
from agency.models.task import Task


class TestTaskValidation:
    """Tests for Task model validation."""

    def test_valid_task(self):
        """Valid task should create without errors."""
        task = Task(
            task_id="fix-bug-a001",
            subject="Fix bug",
            description="Fix the login bug",
            status="pending",
            priority="high",
        )
        assert task.task_id == "fix-bug-a001"
        assert task.status == "pending"

    def test_invalid_status(self):
        """Invalid status should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                task_id="fix-bug-a001",
                subject="Fix bug",
                description="Fix the login bug",
                status="invalid_status",
                priority="high",
            )
        assert "status" in str(exc_info.value)

    def test_invalid_priority(self):
        """Invalid priority should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                task_id="fix-bug-a001",
                subject="Fix bug",
                description="Fix the login bug",
                status="pending",
                priority="super_urgent",
            )
        assert "priority" in str(exc_info.value)

    def test_invalid_task_id_format(self):
        """Task ID not matching pattern should raise ValidationError."""
        # Too short
        with pytest.raises(ValidationError) as exc_info:
            Task(
                task_id="abc",
                subject="Fix bug",
                description="Fix the login bug",
                status="pending",
                priority="high",
            )
        assert "task_id" in str(exc_info.value)

    def test_invalid_task_id_uppercase(self):
        """Task ID with uppercase should raise ValidationError (pattern requires lowercase)."""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                task_id="FIX-BUG-A001",
                subject="Fix bug",
                description="Fix the login bug",
                status="pending",
                priority="high",
            )
        assert "task_id" in str(exc_info.value)

    def test_missing_required_fields(self):
        """Missing required fields should raise ValidationError."""
        with pytest.raises(ValidationError):
            Task(
                task_id="fix-bug-a001",
                subject="Fix bug",
                # Missing description
            )

    def test_task_from_dict_valid(self):
        """Valid dict should create Task via from_dict."""
        data = {
            "task_id": "fix-bug-a001",
            "subject": "Fix bug",
            "description": "Fix the login bug",
            "status": "pending",
            "priority": "high",
        }
        task = Task.from_dict(data)
        assert task.task_id == "fix-bug-a001"

    def test_task_from_dict_invalid(self):
        """Invalid dict should raise ValidationError via from_dict."""
        data = {
            "task_id": "INVALID",
            "subject": "Fix bug",
            "description": "Fix the login bug",
            "status": "invalid",
            "priority": "high",
        }
        with pytest.raises(ValidationError):
            Task.from_dict(data)


class TestConfigValidation:
    """Tests for config model validation."""

    def test_valid_agency_config(self):
        """Valid config should create without errors."""
        config = AgencyConfig(
            project="my-project",
            shell="bash",
            parallel_limit=3,
        )
        assert config.project == "my-project"
        assert config.shell == "bash"

    def test_invalid_shell(self):
        """Invalid shell should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AgencyConfig(
                project="my-project",
                shell="csh",  # Not in Literal['bash', 'zsh', 'fish']
            )
        assert "shell" in str(exc_info.value)

    def test_default_agency_config(self):
        """Default config should use sensible defaults."""
        config = AgencyConfig(project="test")
        assert config.shell == "bash"
        assert config.parallel_limit == 2
        assert config.audit_enabled is True

    def test_valid_manager_config(self):
        """Valid manager config should create without errors."""
        config = ManagerConfig(
            name="coordinator",
            personality="You are the coordinator",
            poll_interval=60,
        )
        assert config.name == "coordinator"
        assert config.poll_interval == 60

    def test_default_manager_config(self):
        """Default manager config should use sensible defaults."""
        config = ManagerConfig(personality="Be helpful")
        assert config.name == "coordinator"
        assert config.poll_interval == 30
        assert config.auto_approve is False

    def test_valid_agent_config(self):
        """Valid agent config should create without errors."""
        config = AgentConfig(
            name="coder",
            personality="You are a coder",
        )
        assert config.name == "coder"

    def test_missing_required_agent_name(self):
        """Missing name should raise ValidationError."""
        with pytest.raises(ValidationError):
            AgentConfig(personality="Some personality")


class TestInjectionValidation:
    """Tests for template injection model validation."""

    def test_injection_result_valid(self):
        """Valid result should create without errors."""
        from agency.template_inject import InjectionResult

        result = InjectionResult(
            content="processed content",
            errors=[],
        )
        assert result.content == "processed content"
        assert result.errors == []

    def test_injection_result_with_errors(self):
        """Result with errors should work."""
        from agency.template_inject import InjectionResult

        result = InjectionResult(
            content="partial content",
            errors=["[WARN] File not found: /path/to/file"],
        )
        assert len(result.errors) == 1

    def test_injection_options_defaults(self):
        """Options should have sensible defaults."""
        from agency.template_inject import InjectionOptions

        options = InjectionOptions()
        assert options.strip_newlines is True
        assert options.max_shell_output == 100_000


class TestAuditEventValidation:
    """Tests for audit event validation."""

    def test_valid_audit_event(self):
        """Valid event should create without errors."""
        from agency.audit import AuditEvent

        event = AuditEvent(
            event_type="task",
            action="create",
            task_id="fix-bug-a001",
        )
        assert event.event_type == "task"
        assert event.action == "create"

    def test_audit_event_to_dict(self):
        """to_dict should return serializable dict."""
        from agency.audit import AuditEvent

        event = AuditEvent(
            event_type="task",
            action="create",
            task_id="fix-bug-a001",
            details={"priority": "high"},
        )
        d = event.to_dict()
        assert d["event_type"] == "task"
        assert d["task_id"] == "fix-bug-a001"


class TestPiInjectValidation:
    """Tests for pi-inject model validation."""

    def test_inject_response_valid(self):
        """Valid response should create without errors."""
        from agency.pi_inject import InjectResponse

        resp = InjectResponse(type="ok", message="Success")
        assert resp.type == "ok"
        assert resp.is_ok is True

    def test_inject_response_properties(self):
        """Response properties should work correctly."""
        from agency.pi_inject import InjectResponse

        ok_resp = InjectResponse(type="ok")
        assert ok_resp.is_ok is True
        assert ok_resp.is_error is False
        assert ok_resp.is_pong is False

        error_resp = InjectResponse(type="error", message="Failed")
        assert error_resp.is_ok is False
        assert error_resp.is_error is True

        pong_resp = InjectResponse(type="pong")
        assert pong_resp.is_pong is True
