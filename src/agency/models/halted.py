from __future__ import annotations
from pydantic import BaseModel

"""Generated from JSON Schema - do not edit directly."""

"""Halt state marker stored at .agency/.halted"""
class Halted(BaseModel):
    halted_at: str
    reason: str | None = None
