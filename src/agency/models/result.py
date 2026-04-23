from __future__ import annotations
from pydantic import BaseModel

"""Generated from JSON Schema - do not edit directly."""

"""Completion result with artifacts, stored at .agency/var/tasks/<id>/result.json"""
class Result(BaseModel):
    result: str
    artifacts: dict | None = None
    completed_at: str
    completed_by: str | None = None
