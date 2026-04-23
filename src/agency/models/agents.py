from __future__ import annotations
from pydantic import BaseModel

"""Generated from JSON Schema - do not edit directly."""

"""Registry of agents in an Agency project stored at .agency/agents.yaml"""
class Agents(BaseModel):
    agents: list[dict]
