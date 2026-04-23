from __future__ import annotations
from pydantic import BaseModel

"""Generated from JSON Schema - do not edit directly."""

"""Notification history stored at .agency/var/notifications.json"""


class Notificationsstore(BaseModel):
    notifications: list[dict]  # List of notification events
