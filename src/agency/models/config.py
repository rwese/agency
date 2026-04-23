from __future__ import annotations
from pydantic import BaseModel
from typing import Any
from typing import Literal

"""Generated from JSON Schema - do not edit directly."""

"""Configuration for an Agency project stored at .agency/config.yaml"""


class Config(BaseModel):
    project: str  # Project name (derived from directory name if not set)
    shell: Literal["bash", "zsh", "fish"] = "bash"  # Shell to use for session
    template_url: str | None = "https://github.com/rwese/agency-templates"  # Template repository URL
    stop_timeout: int = 30  # Seconds to wait before force killing on stop
    additional_context_files: list[Any] | None = (
        None  # Files to add as context (env vars expanded, supports ${VAR} and ~)
    )
    template_delimiter: str | None = None  # Custom template delimiter, e.g. '{{...}}'
    parallel_limit: int = 2  # Max parallel tasks across all agents
    audit_enabled: bool = True  # Enable audit logging to var/audit.db
