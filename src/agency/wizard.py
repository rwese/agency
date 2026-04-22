"""
Agency v2.0 - Init Wizard

Multi-step interactive wizard for creating agency projects.
Flow: Project → Agents → Context → Template → Review → Create

Uses questionary for interactive prompts.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import click
import questionary


@dataclass
class WizardState:
    """State passed between wizard steps."""

    # Project settings
    project_name: str = ""
    shell: str = "bash"
    work_dir: Path | None = None

    # Agents
    agents: list[AgentEntry] = field(default_factory=list)

    # Manager
    manager_name: str = "coordinator"
    manager_personality: str = ""

    # Context files
    context_files: list[str] = field(default_factory=list)

    # Template
    template_url: str | None = None
    template_name: str | None = None
    template_subdir: str | None = None  # CLI-only, not part of wizard flow

    # Options
    force: bool = False
    non_interactive: bool = False  # --yes flag

    # Session info (populated after creation)
    session_name: str | None = None
    agency_dir: Path | None = None


@dataclass
class AgentEntry:
    """An agent entry in the wizard."""

    name: str
    personality: str = ""


def _is_interactive() -> bool:
    """Check if we're in interactive terminal mode."""
    return sys.stdin.isatty()


def _prompt_text(prompt: str, default: str = "", validate=None) -> str:
    """Prompt for text input using questionary."""
    if not _is_interactive():
        return default

    result = questionary.text(
        prompt,
        default=default,
        validate=validate,
    ).ask()

    return result or default


def _select(prompt: str, choices: list[str], default: str = None) -> str:
    """Select from choices using questionary."""
    if not _is_interactive():
        return default or choices[0]

    result = questionary.select(
        prompt,
        choices=choices,
        default=default or choices[0],
    ).ask()

    return result


def _confirm(prompt: str, default: bool = False) -> bool:
    """Ask a yes/no confirmation using questionary."""
    if not _is_interactive():
        return default

    result = questionary.confirm(
        prompt,
        default=default,
    ).ask()

    return result


def _checkbox(prompt: str, choices: list[str], defaults: list[str] = None) -> list[str]:
    """Multi-select using questionary."""
    if not _is_interactive():
        return defaults or []

    result = questionary.checkbox(
        prompt,
        choices=choices,
        defaults=defaults or [],
    ).ask()

    return result or []


def _validate_agent_name(name: str) -> str | None:
    """Validate agent name. Returns error message or None if valid."""
    if not name:
        return "Agent name cannot be empty"

    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", name):
        return "Agent name must start with letter, contain only alphanumeric, hyphen, underscore"

    return None


# ============================================================================
# Step Functions
# ============================================================================


def step_project(state: WizardState) -> WizardState:
    """Step 1: Project configuration."""
    # Project name
    if not state.project_name and state.work_dir:
        state.project_name = state.work_dir.name

    state.project_name = _prompt_text(
        "Project name",
        default=state.project_name,
        validate=lambda x: "Project name cannot be empty" if not x else None,
    )

    # Shell selection
    shells = ["bash", "zsh", "fish"]
    state.shell = _select(
        "Select shell:",
        choices=shells,
        default=state.shell if state.shell in shells else "bash",
    )

    return state


def step_agents(state: WizardState) -> WizardState:
    """Step 2: Agent configuration."""
    # Manager name
    state.manager_name = _prompt_text(
        "Manager name",
        default=state.manager_name,
        validate=_validate_agent_name,
    )

    # Manager personality (optional)
    state.manager_personality = _prompt_text(
        "Manager personality (optional, Enter to skip)",
        default="",
    )

    # Agents
    click.echo("\n### Agents")
    click.echo("  Agents are worker processes that execute tasks.\n")

    while True:
        # Show current agents
        if state.agents:
            click.echo("Current agents:")
            for i, agent in enumerate(state.agents, 1):
                preview = agent.personality[:40] + "..." if agent.personality and len(agent.personality) > 40 else "(no personality)"
                click.echo(f"  {i}. {agent.name} - {preview}")
            click.echo("")

        options = ["Add agent"]
        if state.agents:
            options.append("Remove agent")
        options.append("Done")

        choice = _select("What would you like to do?", choices=options)

        if choice == "Add agent":
            name = _prompt_text("Agent name", validate=_validate_agent_name)
            if name in (a.name for a in state.agents):
                click.echo(f"[WARN] Agent '{name}' already exists")
                continue

            personality = _prompt_text("  Personality (optional, Enter to skip)", default="")
            state.agents.append(AgentEntry(name=name, personality=personality))

        elif choice == "Remove agent" and state.agents:
            names = [a.name for a in state.agents]
            to_remove = _select("Select agent to remove:", choices=names)
            state.agents = [a for a in state.agents if a.name != to_remove]
            click.echo(f"[INFO] Removed agent: {to_remove}")

        else:  # Done
            break

    return state


def step_context(state: WizardState) -> WizardState:
    """Step 3: Context files configuration."""
    # Discover context files
    discovered = _discover_agent_files(state.project_name if state.project_name else None)

    available: list[tuple[str, str, Path]] = []
    file_types = [
        ("AGENTS.md", "Universal agent config"),
        ("CLAUDE.md", "Claude Code memory file"),
        ("CLAUDE.local.md", "Personal project preferences"),
    ]

    for file_type, description in file_types:
        path = discovered.get(file_type)
        if path and path.exists():
            available.append((file_type, description, path))

    if available:
        # Format choices for checkbox
        choices = [f"{name} ({path})" for name, description, path in available]
        selected = _checkbox(
            "Select context files to include:",
            choices=choices,
        )

        # Parse selections back to paths
        state.context_files = []
        for selection in selected:
            for name, description, path in available:
                if name in selection and str(path) in selection:
                    state.context_files.append(str(path))
                    break

    # Check for CLAUDE.local.md in project root
    if state.work_dir:
        claude_local = state.work_dir / "CLAUDE.local.md"
        if claude_local.exists() and str(claude_local) not in state.context_files:
            if _confirm("Include CLAUDE.local.md from project root?", default=False):
                state.context_files.append(str(claude_local))

    # Custom filepath
    custom = _prompt_text(
        "Add custom context file path(s), comma or space separated (Enter to skip)",
        default="",
    )
    if custom:
        paths = [p.strip() for p in custom.replace(",", " ").split() if p.strip()]
        for path in paths:
            expanded = os.path.expanduser(path)
            if Path(expanded).exists() and expanded not in state.context_files:
                state.context_files.append(expanded)
            elif not Path(expanded).exists():
                click.echo(f"[WARN] File not found: {expanded}")

    return state


def step_template(state: WizardState) -> WizardState:
    """Step 4: Template selection."""
    templates = _fetch_templates()

    if templates:
        options = ["None (use default)"] + templates
        selected = _select("Select template:", choices=options)

        if selected != "None (use default)":
            state.template_name = selected
            state.template_url = "https://github.com/rwese/agency-templates"
    else:
        click.echo("[INFO] Could not fetch templates, using default structure")

    return state


def step_review(state: WizardState) -> WizardState:
    """Step 5: Review and confirm."""
    while True:
        click.echo("\n" + "=" * 60)
        click.echo("  Agency Init - Review")
        click.echo("=" * 60)

        click.echo(f"\nProject:  {state.project_name}")
        click.echo(f"Shell:    {state.shell}")
        click.echo(f"Manager:   {state.manager_name}")
        click.echo(f"Agents:    {', '.join(a.name for a in state.agents) or '(none)'}")
        click.echo(f"Context:   {len(state.context_files)} file(s)")
        click.echo(f"Template:  {state.template_name or 'Default'}")
        click.echo(f"Force:     {'Yes' if state.force else 'No'}")

        if _confirm("Create project?", default=True):
            return state

        # Edit options
        edit_choice = _select(
            "What would you like to edit?",
            choices=["Project settings", "Agents", "Context files", "Cancel"],
        )

        if edit_choice == "Project settings":
            state = step_project(state)
        elif edit_choice == "Agents":
            state = step_agents(state)
        elif edit_choice == "Context files":
            state = step_context(state)
        else:
            click.echo("\n[ABORTED]")
            sys.exit(0)


# ============================================================================
# Helper Functions
# ============================================================================


def _discover_agent_files(project_name: str | None = None) -> dict[str, Path | None]:
    """Discover common agent configuration files."""
    home = Path.home()
    results: dict[str, Path | None] = {
        "AGENTS.md": None,
        "CLAUDE.md": None,
        "CLAUDE.local.md": None,
    }

    # AGENTS.md locations
    for loc in [
        home / ".agents" / "AGENTS.md",
        home / ".agents" / "AGENTS.system.md",
        home / "AGENTS.md",
    ]:
        if loc.exists() and loc.is_file():
            results["AGENTS.md"] = loc
            break

    # CLAUDE.md locations
    for loc in [
        home / ".claude" / "projects" / (project_name or "") / "CLAUDE.md",
        home / ".claude" / "CLAUDE.md",
    ]:
        if loc.exists() and loc.is_file():
            results["CLAUDE.md"] = loc
            break

    return results


def _fetch_templates() -> list[str]:
    """Fetch available templates from GitHub."""
    try:
        import json
        import urllib.request

        api_url = "https://api.github.com/repos/rwese/agency-templates/contents"
        req = urllib.request.Request(api_url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            templates = [
                item["name"]
                for item in data
                if item.get("type") == "dir" and not item["name"].startswith(".")
            ]
            return sorted(templates)
    except Exception:
        return []


# ============================================================================
# Main Entry Point
# ============================================================================


def run_wizard(state: WizardState) -> WizardState:
    """Run the full wizard flow.

    Steps: Project → Agents → Context → Template → Review
    Skips steps when values are pre-populated from CLI flags.
    Auto-detects non-interactive mode if not explicitly set.
    """
    # Auto-detect non-interactive mode
    if not state.non_interactive and not _is_interactive():
        state.non_interactive = True

    if state.non_interactive:
        # Non-interactive mode: skip to review with defaults
        click.echo("[INFO] Non-interactive mode, using defaults")
        return step_review(state)

    try:
        # Project step
        state = step_project(state)

        # Agents step (skip if pre-configured)
        if not state.agents:
            state = step_agents(state)
        else:
            click.echo("\n[INFO] Agents pre-configured, skipping")

        # Context step (skip if pre-configured)
        if not state.context_files:
            state = step_context(state)
        else:
            click.echo("\n[INFO] Context files pre-configured, skipping")

        # Template step (skip if pre-configured)
        if not state.template_name:
            state = step_template(state)
        else:
            click.echo("\n[INFO] Template pre-configured, skipping")

        state = step_review(state)
        return state

    except KeyboardInterrupt:
        click.echo("\n\n[ABORTED]")
        sys.exit(130)
