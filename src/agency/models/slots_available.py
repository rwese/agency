from __future__ import annotations
from pydantic import BaseModel

"""Generated from JSON Schema - do not edit directly."""

"""Task slot tracking stored at .agency/signals/slots-available.json"""
class SlotsAvailable(BaseModel):
    slots: int
    parallel_limit: int
    in_progress: int
    updated_at: str
