from __future__ import annotations
from pydantic import BaseModel

"""Generated from JSON Schema - do not edit directly."""

"""Configuration for the Agency manager/coordinator stored at .agency/manager.yaml"""
class Manager(BaseModel):
    name: str
    personality: str
    poll_interval: int | None = None
    auto_approve: bool | None = None
    max_retries: int | None = None
