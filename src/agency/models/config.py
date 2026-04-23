from __future__ import annotations
from pydantic import BaseModel
from typing import Literal

"""Generated from JSON Schema - do not edit directly."""

"""Configuration for an Agency project stored at .agency/config.yaml"""
class Config(BaseModel):
    project: str
    shell: Literal['bash', 'zsh', 'fish'] | None = None
    template_url: str | None = None
    stop_timeout: int | None = None
    additional_context_files: list[str] | None = None
    template_delimiter: str | None = None
    parallel_limit: int | None = None
    audit_enabled: bool | None = None
