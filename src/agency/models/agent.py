from __future__ import annotations
from pydantic import BaseModel

"""Generated from JSON Schema - do not edit directly."""

"""Configuration for an individual Agency agent stored at .agency/agents/<name>.yaml"""
class Agent(BaseModel):
    name: str
    personality: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary (backwards compatible)."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict) -> "Agent":
        """Create from dictionary (backwards compatible)."""
        return cls.model_validate(data)
