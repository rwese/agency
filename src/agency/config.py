"""
Agency v2.0 - Configuration Management

Handles loading and validation of agency configuration files.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import yaml

# Global defaults
DEFAULT_PARALLEL_LIMIT = 2  # Default max parallel tasks across all agents

# Schema base URL
SCHEMA_BASE_URL = "https://raw.githubusercontent.com/rwese/agency/main/schemas"


def _validate_with_schema(data: dict, schema_name: str, agency_dir: Path | None = None) -> list[str]:
    """Validate data against a JSON schema. Returns list of error messages."""
    try:
        from jsonschema import Draft7Validator

        # Load schema from package directory
        schema_path = Path(__file__).parent / "schemas" / f"{schema_name}.json"

        errors = []
        if schema_path.exists():
            schema = json.loads(schema_path.read_text())
            validator = Draft7Validator(schema)
            # Remove $schema key before validation (it's for IDEs, not schema validation)
            data_to_validate = {k: v for k, v in data.items() if k != "$schema"}
            for error in validator.iter_errors(data_to_validate):
                path = ".".join(str(p) for p in error.path) if error.path else "root"
                errors.append(f"{path}: {error.message}")

        return errors
    except ImportError:
        return []  # jsonschema not installed
    except Exception as e:
        return [f"Schema validation error: {e}"]


@dataclass
class AgencyConfig:
    """Project configuration."""

    project: str
    shell: str = "bash"
    template_url: str | None = "https://github.com/rwese/agency-templates"
    stop_timeout: int = 30
    additional_context_files: list[str] | None = None  # Files to add as context (env vars expanded on load)
    template_delimiter: str | None = None  # Custom template delimiter, e.g. "{{...}}"
    parallel_limit: int = DEFAULT_PARALLEL_LIMIT  # Max parallel tasks (default: 2)
    audit_enabled: bool = True  # Enable audit logging


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


def load_agency_config(agency_dir: Path) -> AgencyConfig:
    """Load project configuration from .agency/config.yaml.

    additional_context_files are stored as-is - paths are resolved
    relative to work_dir at session start.

    Logs warnings for schema validation errors.
    """
    import os

    config_path = agency_dir / "config.yaml"

    if not config_path.exists():
        # Return defaults
        return AgencyConfig(project=agency_dir.parent.name)

    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    # Validate against schema
    errors = _validate_with_schema(data, "config", agency_dir)
    if errors:
        import sys

        print("[WARN] Config validation errors:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)

    # Expand ~ in paths (env vars like ${AGENCY_*} resolved at session start)
    context_files_raw = data.get("additional_context_files")
    context_files_expanded = None
    if context_files_raw:
        context_files_expanded = []
        for path in context_files_raw:
            # Expand ~ but not ${VAR}
            expanded = os.path.expanduser(path)
            context_files_expanded.append(expanded)

    return AgencyConfig(
        project=data.get("project", agency_dir.parent.name),
        shell=data.get("shell", "bash"),
        template_url=data.get("template_url"),
        stop_timeout=data.get("stop_timeout", 30),
        additional_context_files=context_files_expanded if context_files_expanded else None,
        template_delimiter=data.get("template_delimiter"),
        parallel_limit=data.get("parallel_limit"),
        audit_enabled=data.get("audit_enabled", True),
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
