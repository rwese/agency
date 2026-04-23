from __future__ import annotations
from pydantic import BaseModel
from typing import Any
from typing import Literal

"""Generated from JSON Schema - do not edit directly."""

"""A single notification event logged to var/notifications.json"""


class Notification(BaseModel):
    id: str  # Unique notification ID
    timestamp: str  # ISO8601 notification timestamp
    recipient: Literal["manager", "agent"]  # Who was notified
    recipient_name: str | None = None  # Specific agent/manager name if applicable
    type: Literal[
        "unassigned_tasks",
        "task_assigned",
        "task_completed",
        "task_approved",
        "task_rejected",
        "agent_idle",
        "crash_detected",
        "heartbeat",
    ]  # Notification type
    message: str  # Human-readable notification message
    task_ids: list[Any] | None = None  # Related task IDs
