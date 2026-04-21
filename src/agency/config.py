"""
Agency v2.0 - Configuration Management

Handles loading and validation of agency configuration files.
"""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class AgencyConfig:
    """Project configuration."""

    project: str
    shell: str = "bash"
    template_url: str | None = "https://github.com/rwese/agency-templates"
    stop_timeout: int = 30
    additional_context_files: list[str] | None = None  # Files to add as context (env vars expanded on load)


@dataclass
class ManagerConfig:
    """Manager configuration."""

    name: str
    personality: str
    poll_interval: int = 30
    auto_approve: bool = False
    max_retries: int | None = None


@dataclass
class AgentConfig:
    """Agent configuration."""

    name: str
    personality: str | None = None


def _has_unresolved_vars(path: str) -> bool:
    """Check if path contains unresolved ${VAR} or $VAR patterns."""
    import re

    return bool(re.search(r"\$\{[^}]+\}|\$[A-Z_][A-Z0-9_]*", path))


def load_agency_config(agency_dir: Path) -> AgencyConfig:
    """Load project configuration from .agency/config.yaml.

    Environment variables in additional_context_files are expanded when loading.
    Warns to stderr if referenced files don't exist after expansion.
    """
    import os
    import sys

    config_path = agency_dir / "config.yaml"

    if not config_path.exists():
        # Return defaults
        return AgencyConfig(project=agency_dir.parent.name)

    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    # Expand environment variables in additional_context_files
    context_files_raw = data.get("additional_context_files")
    context_files_expanded = None
    if context_files_raw:
        context_files_expanded = []
        for path in context_files_raw:
            # Expand ~ and ${VAR} in paths
            expanded = os.path.expanduser(path)
            expanded = os.path.expandvars(expanded)

            # Check for unresolved vars (indicates missing env var)
            if _has_unresolved_vars(expanded):
                print(f"[WARN] Unresolved env var in context file: {path} -> {expanded}", file=sys.stderr)
                continue

            # Check if file exists (warn if not)
            expanded_path = Path(expanded)
            if not expanded_path.exists():
                print(f"[WARN] Context file not found: {expanded}", file=sys.stderr)

            context_files_expanded.append(expanded)

    return AgencyConfig(
        project=data.get("project", agency_dir.parent.name),
        shell=data.get("shell", "bash"),
        template_url=data.get("template_url"),
        stop_timeout=data.get("stop_timeout", 30),
        additional_context_files=context_files_expanded if context_files_expanded else None,
    )


def load_manager_config(agency_dir: Path) -> ManagerConfig | None:
    """Load manager configuration from .agency/manager.yaml."""
    config_path = agency_dir / "manager.yaml"

    if not config_path.exists():
        return None

    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    return ManagerConfig(
        name=data.get("name", "coordinator"),
        personality=data.get("personality", ""),
        poll_interval=data.get("poll_interval", 30),
        auto_approve=data.get("auto_approve", False),
        max_retries=data.get("max_retries"),
    )


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
                agents.append(
                    AgentConfig(
                        name=agent_full.get("name", agent_data["name"]),
                        personality=agent_full.get("personality"),
                    )
                )
        else:
            agents.append(
                AgentConfig(
                    name=agent_data["name"],
                    personality=None,
                )
            )

    return agents


def load_agent_config(agency_dir: Path, agent_name: str) -> AgentConfig | None:
    """Load a single agent's configuration."""
    config_path = agency_dir / "agents" / f"{agent_name}.yaml"

    if not config_path.exists():
        return None

    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    return AgentConfig(
        name=data.get("name", agent_name),
        personality=data.get("personality"),
    )


def save_agency_config(agency_dir: Path, config: AgencyConfig) -> None:
    """Save project configuration."""
    config_path = agency_dir / "config.yaml"

    data = {
        "project": config.project,
        "shell": config.shell,
        "template_url": config.template_url,
        "stop_timeout": config.stop_timeout,
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

    # Save agents list
    agents_list = []
    for agent in agents:
        agents_list.append(
            {
                "name": agent.name,
                "config": f"agents/{agent.name}.yaml",
            }
        )

        # Save individual agent config
        agents_dir.mkdir(exist_ok=True)
        agent_config_path = agents_dir / f"{agent.name}.yaml"

        with open(agent_config_path, "w") as f:
            yaml.dump(
                {
                    "name": agent.name,
                    "personality": agent.personality,
                },
                f,
                default_flow_style=False,
            )

    with open(agents_path, "w") as f:
        yaml.dump({"agents": agents_list}, f, default_flow_style=False)
