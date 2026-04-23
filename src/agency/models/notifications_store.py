from __future__ import annotations
from pydantic import BaseModel

"""Generated from JSON Schema - do not edit directly."""

"""Notification history stored at .agency/var/notifications.json"""
class NotificationsStore(BaseModel):
    notifications: list[dict]

    def to_dict(self) -> dict:
        """Convert to dictionary (backwards compatible)."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict) -> "NotificationsStore":
        """Create from dictionary (backwards compatible)."""
        return cls.model_validate(data)
