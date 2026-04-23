from __future__ import annotations
from pydantic import BaseModel
from typing import Any
from typing import Literal

"""Generated from JSON Schema - do not edit directly."""

"""Task awaiting approval, stored at .agency/var/pending/<id>.json"""
class PendingTask(BaseModel):
    task_id: str | None = None
    subject: str
    description: str
    status: Any | None = None
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
    pending_approval_at: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary (backwards compatible)."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create Task from dictionary (backwards compatible)."""
        return cls.model_validate(data)
