from __future__ import annotations
from pydantic import BaseModel

"""Generated from JSON Schema - do not edit directly."""

"""Completion result with artifacts, stored at .agency/var/tasks/<id>/result.json"""


class Result(BaseModel):
    result: str  # Markdown result summary
    artifacts: dict | None = None  # Changed files and diffs
    completed_at: str  # ISO8601 completion timestamp
    completed_by: str | None = None  # Agent name who completed the task
