from __future__ import annotations
from pydantic import BaseModel

"""Generated from JSON Schema - do not edit directly."""

"""Task slot tracking stored at .agency/signals/slots-available.json"""
class SlotsAvailable(BaseModel):
    slots: int
    parallel_limit: int
    in_progress: int
    updated_at: str

    def to_dict(self) -> dict:
        """Convert to dictionary (backwards compatible)."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict) -> SlotsAvailable:
        """Create from dictionary (backwards compatible)."""
        return cls.model_validate(data)
