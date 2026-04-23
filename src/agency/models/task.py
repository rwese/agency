from __future__ import annotations
from pydantic import BaseModel
from typing import Literal

"""Generated from JSON Schema - do not edit directly."""

"""Represents a unit of work to be completed by an agent"""
class Task(BaseModel):
    task_id: str
    description: str
    status: Literal['pending', 'in_progress', 'pending_approval', 'completed', 'failed']
    priority: Literal['low', 'normal', 'high']
    assigned_to: str
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    result: str | None = None
    result_path: str | None = None
    depends_on: list[str] | None = None
    agent_info: dict | None = None
    rejection_reason: str | None = None
    review_notes: str | None = None
    reviewer_assigned: str | None = None
