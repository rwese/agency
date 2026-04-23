from __future__ import annotations
from pydantic import BaseModel
from typing import Literal

"""Generated from JSON Schema - do not edit directly."""

"""A single notification event logged to var/notifications.json"""
class Notification(BaseModel):
    id: str
    timestamp: str
    recipient: Literal['manager', 'agent']
    recipient_name: str | None = None
    type: Literal['unassigned_tasks', 'task_assigned', 'task_completed', 'task_approved', 'task_rejected', 'agent_idle', 'crash_detected', 'heartbeat']
    message: str
    task_ids: list[str] | None = None
