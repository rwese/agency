from __future__ import annotations
from pydantic import BaseModel

"""Generated from JSON Schema - do not edit directly."""

"""Root task registry stored at .agency/var/tasks.json"""


class Tasksstore(BaseModel):
    version: int  # Schema version (always 2)
    tasks: dict  # Map of task_id to Task object
