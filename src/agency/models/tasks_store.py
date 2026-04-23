from __future__ import annotations
from pydantic import BaseModel

"""Generated from JSON Schema - do not edit directly."""

"""Root task registry stored at .agency/var/tasks.json"""
class TasksStore(BaseModel):
    version: int
    tasks: dict
