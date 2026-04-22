"""
Agency v2.0 - Init Wizard

Multi-step interactive wizard for creating agency projects.
Flow: Project → Agents → Context → Template → Review → Create
"""

from __future__ import annotations

import os
import sys
import termios
import tty
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import click


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


def _getch() -> str:
    """Get a single character from stdin without requiring Enter."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def _confirm(prompt: str, default: bool = False) -> bool:
    """Ask a yes/no confirmation question."""
    if not _is_interactive():
        return default

    suffix = " [Y/n]: " if default else " [y/N]: "
    response = click.prompt(prompt + suffix, default="y" if default else "n", type=str, show_default=False).strip().lower()

    return response in ("y", "yes")


def _select_option(prompt: str, options: list[str], default: int = 0) -> int:
    """Ask user to select from numbered options."""
    if not _is_interactive():
        return default

    click.echo(f"\n{prompt}\n")
    for i, opt in enumerate(options, 1):
        marker = " ←" if i - 1 == default else ""
        click.echo(f"  {i}. {opt}{marker}")

    while True:
        click.echo("\nChoice: ", nl=False)
        ch = _getch()
        click.echo(ch)

        if ch == "\r" or ch == "\n":
            return default

        if ch.isdigit():
            idx = int(ch) - 1
            if 0 <= idx < len(options):
                return idx

        if ch == "\x03":  # Ctrl+C
            raise KeyboardInterrupt


def _prompt_text(prompt: str, default: str = "", validate: Callable[[str], str | None] | None = None) -> str:
    """Prompt for text input with optional validation.

    Auto-detects non-interactive mode and returns default without prompting.
    """
    if not _is_interactive():
        return default

    while True:
        # click.prompt with show_default=True displays the default in brackets
        response = click.prompt(f"{prompt}: ", default=default, type=str, show_default=True).strip()

        if not response:
            response = default

        if validate:
            error = validate(response)
            if error:
                click.echo(f"[ERROR] {error}", err=True)
                continue

        return response


def _validate_agent_name(name: str) -> str | None:
    """Validate agent name. Returns error message or None if valid."""
    if not name:
        return "Agent name cannot be empty"

    import re

    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", name):
        return "Agent name must start with letter, contain only alphanumeric, hyphen, underscore"

    if name in ("coordinator", "manager"):
        return f"'{name}' is reserved"

    return None


def _interactive_checkbox(
    items: list[tuple[str, str, Path]], selected: set[int] | None = None
) -> set[int]:
    """Interactive checkbox selection.

    Args:
        items: List of (name, description, path) tuples
        selected: Pre-selected indices

    Returns:
        Set of selected indices
    """
    if not _is_interactive():
        return selected or set()

    current_selection = selected or set()

    def redraw():
        """Clear screen and redraw the menu."""
        click.echo("\033[2J\033[H", nl=False)  # Clear screen
        click.echo("\n[?] Discovered agent context files:")
        click.echo("(Toggle with 1-9, a=all, Enter=done, 0=none)\n")
        for i, (name, description, path) in enumerate(items, 1):
            marker = "[x]" if (i - 1) in current_selection else "[ ]"
            click.echo(f"  {marker} {i}. {name}")
            click.echo(f"      {description}")
            click.echo(f"      → {path}")
            click.echo("")
        if current_selection:
            click.echo(f"Selected: {', '.join(items[i - 1][0] for i in current_selection)}")
        click.echo("")

    redraw()

    while True:
        click.echo("Choice: ", nl=False)
        ch = _getch()
        click.echo(ch)

        if ch == "\r" or ch == "\n":  # Enter - confirm
            break
        elif ch == "0":  # None - clear selection
            current_selection.clear()
            redraw()
        elif ch.isdigit() and ch != "0":  # 1-9 - toggle
            idx = int(ch) - 1
            if 0 <= idx < len(items):
                if idx in current_selection:
                    current_selection.remove(idx)
                else:
                    current_selection.add(idx)
                redraw()
            else:
                click.echo(f"\n[ERROR] Invalid: 1-{len(items)}")
        elif ch.lower() == "a":  # All
            current_selection = set(range(len(items)))
            redraw()
        elif ch == "\x03":  # Ctrl+C
            click.echo("\n[ABORTED]")
            raise KeyboardInterrupt
        elif ch.lower() == "q":  # Quit without selecting
            current_selection.clear()
            break

    return current_selection


# ============================================================================
# Step Functions
# ============================================================================


def step_project(state: WizardState) -> WizardState:
    """Step 1: Project configuration.

    Asks for project name and shell selection.
    Pre-populated from CLI flags if provided.
    """
    click.echo("\n" + "=" * 60)
    click.echo("  Agency Init - Project Configuration")
    click.echo("=" * 60)

    # Project name
    if not state.project_name and state.work_dir:
        state.project_name = state.work_dir.name

    state.project_name = _prompt_text(
        "Project name",
        default=state.project_name,
        validate=lambda n: "Project name cannot be empty" if not n else None,
    )

    # Shell selection
    shells = ["bash", "zsh", "fish"]
    shell_idx = _select_option("Select shell:", shells, default=shells.index(state.shell) if state.shell in shells else 0)
    state.shell = shells[shell_idx]

    return state


def step_agents(state: WizardState) -> WizardState:
    """Step 2: Agent configuration.

    Allows adding agents with names and optional personalities.
    """
    click.echo("\n" + "=" * 60)
    click.echo("  Agency Init - Agent Configuration")
    click.echo("=" * 60)

    # Manager configuration
    click.echo("\n### Manager (Coordinator)")
    state.manager_name = _prompt_text("Manager name", default=state.manager_name, validate=_validate_agent_name)

    click.echo("\nManager personality (optional):")
    click.echo("  This is injected into the coordinator's system prompt.")
    click.echo("  Leave blank for default.\n")
    state.manager_personality = _prompt_text("  Press Enter to skip", default="")

    # Agents
    click.echo("\n### Agents")
    click.echo("  Agents are worker processes that execute tasks.\n")

    if not state.agents:
        state.agents = []

    # Show existing agents
    while True:
        if state.agents:
            click.echo("\nCurrent agents:")
            for i, agent in enumerate(state.agents, 1):
                preview = agent.personality[:40] + "..." if agent.personality and len(agent.personality) > 40 else (agent.personality or "(no personality)")
                click.echo(f"  {i}. {agent.name} - {preview}")

        click.echo("\nOptions:")
        click.echo("  1. Add agent")
        if state.agents:
            click.echo("  2. Remove agent")
        click.echo(f"  {2 if state.agents else 1}. Done adding agents")

        # Build options dynamically
        options = ["Add agent"]
        if state.agents:
            options.append("Remove agent")
        options.append("Done")

        # Default to last option (Done)
        default_idx = len(options) - 1
        choice = _select_option("", options, default=default_idx)

        if choice == 0:  # Add
            name = _prompt_text("Agent name", validate=_validate_agent_name)
            if name in (a.name for a in state.agents):
                click.echo(f"[WARN] Agent '{name}' already exists", err=True)
                continue

            personality = click.prompt("  Personality (optional, Enter to skip)", default="", type=str, show_default=False).strip()
            state.agents.append(AgentEntry(name=name, personality=personality))

        elif choice == 1 and state.agents:  # Remove
            names = [a.name for a in state.agents]
            idx = _select_option("Select agent to remove:", names)
            removed = state.agents.pop(idx)
            click.echo(f"[INFO] Removed agent: {removed.name}")

        else:  # Done
            break

    return state


def step_context(state: WizardState) -> WizardState:
    """Step 3: Context files configuration.

    Discovers and allows selection of agent context files.
    """
    click.echo("\n" + "=" * 60)
    click.echo("  Agency Init - Context Files")
    click.echo("=" * 60)

    click.echo("\nContext files provide additional context to agents.")
    click.echo("They are injected into agent system prompts.\n")

    # Discover context files
    discovered = _discover_agent_files(state.project_name if state.project_name else None)

    available: list[tuple[str, str, Path]] = []
    file_types = [
        ("AGENTS.md", "Universal agent config (Claude, Cursor, Copilot)"),
        ("CLAUDE.md", "Claude Code memory file"),
        ("CLAUDE.local.md", "Personal project preferences"),
    ]

    for file_type, description in file_types:
        path = discovered.get(file_type)
        if path and path.exists():
            available.append((file_type, description, path))

    if not available:
        click.echo("[INFO] No context files discovered")
        click.echo("  Add files later via config.yaml\n")

        if state.work_dir:
            claude_local = state.work_dir / "CLAUDE.local.md"
            if claude_local.exists() and str(claude_local) not in state.context_files:
                if _confirm("Include CLAUDE.local.md from project root?", default=False):
                    state.context_files.append(str(claude_local))

    else:
        click.echo("[?] Discovered context files:")
        click.echo("(Toggle selection with number keys, Enter to confirm)\n")

        # Mark pre-selected files
        pre_selected: set[int] = set()
        for i, (_, _, path) in enumerate(available):
            if str(path) in state.context_files:
                pre_selected.add(i)

        selected_indices = _interactive_checkbox(available, pre_selected)
        state.context_files = [str(available[i][2]) for i in selected_indices]

        # Check for CLAUDE.local.md in project root
        if state.work_dir:
            claude_local = state.work_dir / "CLAUDE.local.md"
            if claude_local.exists() and str(claude_local) not in state.context_files:
                if _confirm("Include CLAUDE.local.md from project root?", default=False):
                    state.context_files.append(str(claude_local))

    # Custom filepath prompt
    click.echo("\n[?] Add custom context file path(s)?")
    click.echo("   Comma or space separated, ~ expanded")
    response = click.prompt("   [Enter to skip]", default="", type=str, show_default=False).strip()

    if response:
        paths = [p.strip() for p in response.replace(",", " ").split() if p.strip()]
        for path in paths:
            expanded = os.path.expanduser(path)
            if Path(expanded).exists() and expanded not in state.context_files:
                state.context_files.append(expanded)
            elif not Path(expanded).exists():
                click.echo(f"[WARN] File not found: {expanded}", err=True)

    return state


def step_template(state: WizardState) -> WizardState:
    """Step 4: Template selection.

    Allows selecting from available templates or using default structure.
    """
    click.echo("\n" + "=" * 60)
    click.echo("  Agency Init - Template Selection")
    click.echo("=" * 60)

    click.echo("\nTemplates provide pre-configured .agency/ structures.")
    click.echo("Select 'None' for a minimal default setup.\n")

    # Fetch available templates
    templates = _fetch_templates()

    if templates:
        options = ["None (use default)", *templates]
        idx = _select_option("Select template:", options)

        if idx == 0:
            state.template_name = None
            state.template_url = None
        else:
            state.template_name = templates[idx - 1]
            state.template_url = "https://github.com/rwese/agency-templates"
    else:
        click.echo("[INFO] Could not fetch templates, using default structure")
        state.template_name = None
        state.template_url = None

    return state


def step_review(state: WizardState) -> WizardState:
    """Step 5: Review and confirm.

    Shows summary of all configured options.
    Allows editing or confirming.
    """
    while True:
        click.echo("\n" + "=" * 60)
        click.echo("  Agency Init - Review")
        click.echo("=" * 60)

        # Project
        click.echo("\n### Project")
        click.echo(f"  Name:    {state.project_name}")
        click.echo(f"  Shell:   {state.shell}")
        click.echo(f"  Dir:     {state.work_dir or '(current directory)'}")

        # Manager
        click.echo("\n### Manager")
        click.echo(f"  Name:        {state.manager_name}")
        if state.manager_personality:
            preview = state.manager_personality[:50] + "..." if len(state.manager_personality) > 50 else state.manager_personality
            click.echo(f"  Personality: {preview}")

        # Agents
        click.echo("\n### Agents")
        if state.agents:
            for agent in state.agents:
                preview = agent.personality[:40] + "..." if agent.personality and len(agent.personality) > 40 else (agent.personality or "(none)")
                click.echo(f"  - {agent.name}: {preview}")
        else:
            click.echo("  (none)")

        # Context files
        click.echo("\n### Context Files")
        if state.context_files:
            for cf in state.context_files:
                click.echo(f"  + {cf}")
        else:
            click.echo("  (none)")

        # Template
        click.echo("\n### Template")
        if state.template_name:
            click.echo(f"  {state.template_name}")
        else:
            click.echo("  Default structure")

        # Options
        click.echo("\n### Options")
        click.echo(f"  Force:   {'Yes' if state.force else 'No'}")
        click.echo("  Audit:   Yes")

        # Choice
        click.echo("\n" + "-" * 40)
        options = ["Create project", "Edit project settings", "Edit agents", "Edit context files", "Abort"]
        choice = _select_option("What would you like to do?", options, default=0)

        if choice == 0:  # Create
            return state
        elif choice == 1:  # Edit project
            state = step_project(state)
        elif choice == 2:  # Edit agents
            state = step_agents(state)
        elif choice == 3:  # Edit context
            state = step_context(state)
        else:  # Abort
            click.echo("\n[ABORTED] Init cancelled")
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
    """Fetch available templates from repository."""
    try:
        import json
        import subprocess

        api_url = "https://api.github.com/repos/rwese/agency-templates/contents"
        result = subprocess.run(["curl", "-sL", api_url], capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            return []

        contents = json.loads(result.stdout)
        templates = [
            item["name"] for item in contents if item.get("type") == "dir" and not item["name"].startswith(".")
        ]

        return sorted(templates)
    except Exception:
        return []


# ============================================================================
# Main Wizard Entry Point
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
        click.echo("[INFO] Non-interactive mode, using defaults\n")
        return step_review(state)

    try:
        # Project step: always show (needs confirmation even with pre-populated values)
        state = step_project(state)

        # Agents step: skip if already configured via CLI
        if not state.agents:
            state = step_agents(state)
        else:
            click.echo("\n[INFO] Agents pre-configured, skipping agents step")

        # Context step: skip if already configured via CLI
        if not state.context_files:
            state = step_context(state)
        else:
            click.echo("\n[INFO] Context files pre-configured, skipping context step")

        # Template step: skip if already configured via CLI
        if not state.template_name:
            state = step_template(state)
        else:
            click.echo("\n[INFO] Template pre-configured, skipping template step")

        state = step_review(state)
        return state

    except KeyboardInterrupt:
        click.echo("\n\n[ABORTED] Init cancelled by user")
        sys.exit(130)
