from __future__ import annotations
from pydantic import BaseModel

"""Generated from JSON Schema - do not edit directly."""

"""Configuration for the Agency manager/coordinator stored at .agency/manager.yaml"""
class Manager(BaseModel):
    name: str
    personality: str
    poll_interval: int | None = None
    auto_approve: bool | None = None
    max_retries: int | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary (backwards compatible)."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create Task from dictionary (backwards compatible)."""
        return cls.model_validate(data)
