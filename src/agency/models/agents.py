from __future__ import annotations
from pydantic import BaseModel

"""Generated from JSON Schema - do not edit directly."""

"""Registry of agents in an Agency project stored at .agency/agents.yaml"""
class Agents(BaseModel):
    agents: list[dict]

    def to_dict(self) -> dict:
        """Convert to dictionary (backwards compatible)."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict) -> "Agents":
        """Create from dictionary (backwards compatible)."""
        return cls.model_validate(data)
