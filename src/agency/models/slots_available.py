from __future__ import annotations
from pydantic import BaseModel

"""Generated from JSON Schema - do not edit directly."""

"""Task slot tracking stored at .agency/signals/slots-available.json"""


class Slotsavailable(BaseModel):
    slots: int  # Available slots
    parallel_limit: int  # Max parallel tasks allowed
    in_progress: int  # Currently in-progress tasks
    updated_at: str  # Last update timestamp
