from __future__ import annotations
from pydantic import BaseModel

"""Generated from JSON Schema - do not edit directly."""

"""Configuration for an individual Agency agent stored at .agency/agents/<name>.yaml"""
class Agent(BaseModel):
    name: str
    personality: str | None = None
