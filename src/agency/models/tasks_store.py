from __future__ import annotations
from pydantic import BaseModel

"""Generated from JSON Schema - do not edit directly."""

"""Root task registry stored at .agency/var/tasks.json"""
class TasksStore(BaseModel):
    version: int
    tasks: dict

    def to_dict(self) -> dict:
        """Convert to dictionary (backwards compatible)."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create Task from dictionary (backwards compatible)."""
        return cls.model_validate(data)
