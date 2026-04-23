"""
Agency v2.0 - Configuration Management

Handles loading and validation of agency configuration files.
"""

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel


# Global defaults
DEFAULT_PARALLEL_LIMIT = 2  # Default max parallel tasks across all agents


class AgencyConfig(BaseModel):
    """Project configuration."""

    project: str
    shell: Literal["bash", "zsh", "fish"] = "bash"
    template_url: str | None = "https://github.com/rwese/agency-templates"
    stop_timeout: int = 30
    additional_context_files: list[str] | None = None
    template_delimiter: str | None = None
    parallel_limit: int = DEFAULT_PARALLEL_LIMIT
    audit_enabled: bool = True


class ManagerConfig(BaseModel):
    """Manager configuration."""

    name: str = "coordinator"
    personality: str = ""
    poll_interval: int = 30
    auto_approve: bool = False
    max_retries: int | None = None


class AgentConfig(BaseModel):
    """Agent configuration."""

    name: str
    personality: str | None = None


def load_agency_config(agency_dir: Path) -> AgencyConfig:
    """Load project configuration from .agency/config.yaml.

    additional_context_files are stored as-is - paths are resolved
    relative to work_dir at session start.

    Raises ValidationError if config is invalid.
    """
    config_path = agency_dir / "config.yaml"

    if not config_path.exists():
        # Return defaults
        return AgencyConfig(project=agency_dir.parent.name)

    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    # Expand ~ in paths (env vars like ${AGENCY_*} resolved at session start)
    context_files_raw = data.get("additional_context_files")
    if context_files_raw:
        data["additional_context_files"] = [os.path.expanduser(p) for p in context_files_raw]

    return AgencyConfig.model_validate(data)


def load_manager_config(agency_dir: Path) -> ManagerConfig | None:
    """Load manager configuration from .agency/manager.yaml."""
    config_path = agency_dir / "manager.yaml"

    if not config_path.exists():
        return None

    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    return ManagerConfig.model_validate(data)


def load_agents_config(agency_dir: Path) -> list[AgentConfig]:
    """Load agents configuration from .agency/agents.yaml."""
    config_path = agency_dir / "agents.yaml"

    if not config_path.exists():
        return []

    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    agents = []
    for agent_data in data.get("agents", []):
        config_path = agency_dir / agent_data.get("config", f"agents/{agent_data['name']}.yaml")

        if config_path.exists():
            with open(config_path) as f:
                agent_full = yaml.safe_load(f) or {}
                agents.append(AgentConfig.model_validate(agent_full))
        else:
            agents.append(AgentConfig(name=agent_data["name"]))

    return agents


def load_agent_config(agency_dir: Path, agent_name: str) -> AgentConfig | None:
    """Load a single agent's configuration."""
    config_path = agency_dir / "agents" / f"{agent_name}.yaml"

    if not config_path.exists():
        return None

    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    return AgentConfig.model_validate(data)


def save_agency_config(agency_dir: Path, config: AgencyConfig) -> None:
    """Save project configuration."""
    config_path = agency_dir / "config.yaml"

    data = {
        "$schema": "https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/config.json",
        "project": config.project,
        "shell": config.shell,
        "template_url": config.template_url,
        "stop_timeout": config.stop_timeout,
        "audit_enabled": config.audit_enabled,
    }

    if config.additional_context_files:
        data["additional_context_files"] = config.additional_context_files

    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)


def save_manager_config(agency_dir: Path, config: ManagerConfig) -> None:
    """Save manager configuration."""
    config_path = agency_dir / "manager.yaml"

    with open(config_path, "w") as f:
        yaml.dump(
            {
                "$schema": "https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/manager.json",
                "name": config.name,
                "personality": config.personality,
                "poll_interval": config.poll_interval,
                "auto_approve": config.auto_approve,
                "max_retries": config.max_retries,
            },
            f,
            default_flow_style=False,
        )


def save_agents_config(agency_dir: Path, agents: list[AgentConfig]) -> None:
    """Save agents configuration."""
    agents_path = agency_dir / "agents.yaml"
    agents_dir = agency_dir / "agents"

    # Save agents list with schema directive
    agents_list = []
    for agent in agents:
        agents_list.append(
            {
                "name": agent.name,
                "config": f"agents/{agent.name}.yaml",
            }
        )

        # Save individual agent config with schema directive
        agents_dir.mkdir(exist_ok=True)
        agent_config_path = agents_dir / f"{agent.name}.yaml"

        with open(agent_config_path, "w") as f:
            yaml.dump(
                {
                    "$schema": "https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/agent.json",
                    "name": agent.name,
                    "personality": agent.personality,
                },
                f,
                default_flow_style=False,
            )

    with open(agents_path, "w") as f:
        yaml.dump(
            {
                "$schema": "https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/agents.json",
                "agents": agents_list,
            },
            f,
            default_flow_style=False,
        )
