from __future__ import annotations
from pydantic import BaseModel, field_validator
from typing import Literal
import re

"""Generated from JSON Schema - do not edit directly."""

# Compile regex patterns from schema for validation
_TASK_ID_PATTERN = re.compile(r"^[a-z]+-[a-z]+-[0-9a-f]{4}$")


"""Represents a unit of work to be completed by an agent"""
class Task(BaseModel):
    task_id: str | None = None
    subject: str
    description: str
    status: Literal['pending', 'in_progress', 'pending_approval', 'completed', 'failed'] | None = None
    priority: Literal['low', 'normal', 'high'] | None = None
    assigned_to: str | None = None
    created_at: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    result: str | None = None
    result_path: str | None = None
    depends_on: list[str] | None = None
    acceptance_criteria: list[str] | None = None
    references: list[str] | None = None
    attachments: list[str] | None = None
    agent_info: dict | None = None
    rejection_reason: str | None = None
    review_notes: str | None = None
    reviewer_assigned: str | None = None

    @field_validator('task_id')
    @classmethod
    def validate_task_id(cls, v: str | None) -> str | None:
        """Validate task_id matches pattern word-word-hex."""
        if v is not None and not _TASK_ID_PATTERN.match(v):
            raise ValueError(f"task_id must match pattern 'word-word-hex' (e.g., swift-bear-a3f2), got: {v}")
        return v

    def to_dict(self) -> dict:
        """Convert to dictionary (backwards compatible)."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create Task from dictionary (backwards compatible)."""
        return cls.model_validate(data)
