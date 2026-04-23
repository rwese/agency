from __future__ import annotations
from pydantic import BaseModel

"""Generated from JSON Schema - do not edit directly."""

"""Configuration for the Agency manager/coordinator stored at .agency/manager.yaml"""


class Manager(BaseModel):
    name: str = "coordinator"  # Manager name (used in window title as [MGR] <name>)
    personality: str  # Manager personality/prompt (supports template injection with ${{file:path}} and ${{shell:cmd}})
    poll_interval: int = 30  # Seconds between heartbeat polling
    auto_approve: bool = False  # Auto-approve completed tasks (not recommended)
    max_retries: int | None = None  # Max retries for failed tasks (null = unlimited)
