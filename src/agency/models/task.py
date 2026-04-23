from __future__ import annotations
from pydantic import BaseModel
from pydantic import field_validator
from typing import Literal
import re

# Pattern from schema: ^[a-z]+-[a-z]+-[0-9a-f]{4}$
_PATTERN_TASK_ID = re.compile(r'^[a-z]+-[a-z]+-[0-9a-f]{4}$')

"""Generated from JSON Schema - do not edit directly."""

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
    def validate_task_id(cls, v):
        if v is not None and not _PATTERN_TASK_ID.match(str(v)):
            raise ValueError(f"task_id must match pattern '^[a-z]+-[a-z]+-[0-9a-f]{4}$', got: {v}")
        return v

    def to_dict(self) -> dict:
        """Convert to dictionary (backwards compatible)."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create Task from dictionary (backwards compatible)."""
        return cls.model_validate(data)
