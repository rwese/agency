from __future__ import annotations
from pydantic import BaseModel
from typing import Any
from typing import Literal

"""Generated from JSON Schema - do not edit directly."""

"""Represents a unit of work to be completed by an agent"""


class Task(BaseModel):
    task_id: str  # Unique identifier using eff.org wordlist + hex suffix (e.g., swift-bear-a3f2)
    description: str  # Human-readable task description
    status: Literal["pending", "in_progress", "pending_approval", "completed", "failed"]  # Current task state
    priority: Literal["low", "normal", "high"] = "low"  # Task priority
    assigned_to: str | None  # Agent name or null if unassigned
    created_at: str  # ISO8601 creation timestamp
    started_at: str | None = None  # ISO8601 timestamp when agent started work
    completed_at: str | None = None  # ISO8601 timestamp when task was completed
    result: str | None = None  # Markdown result summary
    result_path: str | None = None  # Path to result.json file
    depends_on: list[Any] | None = None  # List of task IDs this task depends on
    agent_info: dict | None = None  # Agent tracking info (set when picked up)
    rejection_reason: str | None = None  # Reason if task was rejected
    review_notes: str | None = None  # Notes from reviewer
    reviewer_assigned: str | None = None  # Name of reviewer agent handling pending_approval task
