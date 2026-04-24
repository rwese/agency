"""
Agency Hire — CLI Commands

Interactive CLI for hiring project-specific agencies.
"""

from pathlib import Path
from typing import Any

import click

from agency.hire.generators.agent import write_agent_configs
from agency.hire.generators.manager import write_manager_config
from agency.hire.questions import ALL_GROUPS, Question, get_answers_dict


@click.command()
@click.option("--dir", "-d", "agency_dir", type=click.Path(), default=".", help="Project directory")
@click.option("--type", "-t", "project_type", type=click.Choice(["api", "cli", "library", "web", "fullstack", "other"]), help="Project type")
@click.option("--language", "-l", "language", type=str, help="Primary language")
@click.option("--team", type=click.Choice(["solo", "pair", "team"]), help="Team size")
@click.option("--non-interactive", "-y", is_flag=True, help="Skip interview, use defaults")
@click.option("--preview", is_flag=True, help="Preview configuration without writing files")
@click.pass_context
def hire(
    ctx: click.Context,
    agency_dir: str,
    project_type: str | None,
    language: str | None,
    team: str | None,
    non_interactive: bool,
    preview: bool,
) -> None:
    """
    Hire an agency for your project.

    Interactively configures manager and agent personalities based on your project.

    Examples:

        agency hire                          # Interactive interview
        agency hire --type api --language python  # Pre-configured
        agency hire --preview               # Preview without writing
    """
    agency_path = Path(agency_dir).resolve()

    click.echo("\n🚀 Agency Hire — Let's build your team!\n")

    # Collect answers
    answers = get_answers_dict()

    # Use provided answers or defaults
    if project_type:
        answers["project_type"] = project_type
    if language:
        answers["language"] = language
    if team:
        answers["team_size"] = team

    # Run interview if not fully configured
    if not (project_type and language and team) and not non_interactive:
        answers = _run_interview(answers)
    elif not non_interactive:
        # Fill in defaults for missing
        answers = _fill_defaults(answers)
    else:
        # Non-interactive with minimal config
        answers = _fill_defaults(answers)

    # Generate configurations
    click.echo("\n📝 Generating your agency...\n")

    if preview:
        _preview_config(answers)
    else:
        _write_configs(agency_path / ".agency", answers)
        click.echo("\n🎉 Your agency is ready!\n")
        click.echo(f"   Config: {agency_path / '.agency'}")
        click.echo("\nTo start working:")
        click.echo("   agency session start")


def _run_interview(initial_answers: dict[str, Any]) -> dict[str, Any]:
    """Run the interactive interview."""

    answers = initial_answers.copy()

    for group in ALL_GROUPS:
        click.echo(f"\n{group.icon} {group.title}")
        click.echo("-" * 40)

        for question in group.questions:
            answer = _ask_question(question, answers.get(question.key))
            answers[question.key] = answer

    return answers


def _ask_question(question: Question, current: str | None = None) -> str | list[str]:
    """Ask a single question and return the answer."""

    if question.options:
        # Multiple choice question
        if isinstance(question.options[0], str) and question.key == "agents":
            # Special handling for agents (multi-select)
            return _multi_select(question)
        else:
            # Single select
            return _single_select(question)
    else:
        # Free text question
        return click.prompt(question.prompt, default=current or "")


def _single_select(question: Question) -> str:
    """Single selection from options."""

    # Show numbered options
    for i, option in enumerate(question.options, 1):
        marker = "◉" if option == question.default else "○"
        click.echo(f"   {marker} {i} - {option}")

    while True:
        try:
            choice = click.prompt(
                f"? {question.prompt}: ({question.default or question.options[0]})",
                default=question.default,
                show_default=False,
            )

            if choice == "":
                return question.options[0] if question.default is None else question.default

            idx = int(choice) - 1
            if 0 <= idx < len(question.options):
                return question.options[idx]

            click.echo(f"Please enter 1-{len(question.options)}")
        except ValueError:
            click.echo("Please enter a number")


def _multi_select(question: Question) -> list[str]:
    """Multi-select from options."""

    agents = ["coder", "tester", "devops", "reviewer"]

    click.echo("? Select agents (space to select, enter to confirm):")

    selected = []
    for i, agent in enumerate(agents, 1):
        marker = "[*]" if agent in ["coder"] else "[ ]"  # coder default
        if agent == "coder" and "coder" not in selected:
            selected.append("coder")
        click.echo(f"   {marker} {i} - {agent}")

    click.echo("\n(Press Enter to confirm with defaults, or enter numbers)")

    while True:
        choice = click.prompt("?", default="1", show_default=False)

        if choice == "":
            return selected if selected else ["coder"]

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(agents):
                agent = agents[idx]
                if agent in selected:
                    selected.remove(agent)
                else:
                    selected.append(agent)

            click.echo(f"   Selected: {', '.join(selected) if selected else 'none'}")
        except ValueError:
            break

    return selected if selected else ["coder"]


def _fill_defaults(answers: dict[str, Any]) -> dict[str, Any]:
    """Fill in default values for missing answers."""

    defaults = {
        "project_type": "api",
        "language": "python",
        "framework": "none",
        "database": "none",
        "team_size": "solo",
        "agents": ["coder"],
        "review": "mandatory",
        "testing": "after",
        "cicd": "no",
    }

    for key, default in defaults.items():
        if key not in answers or not answers[key]:
            answers[key] = default

    return answers


def _preview_config(answers: dict[str, Any]) -> None:
    """Preview generated configuration."""

    click.echo("\n📋 Manager Personality Preview:\n")
    from agency.hire.generators.manager import generate_manager_personality

    personality = generate_manager_personality(answers)
    # Show first 30 lines
    lines = personality.split("\n")
    for line in lines[:30]:
        click.echo(f"   {line}")
    if len(lines) > 30:
        click.echo("   ... (truncated)")

    click.echo(f"\n👥 Agents: {', '.join(answers.get('agents', ['coder']))}")


def _copy_pi_extensions(agency_dir: Path) -> None:
    """Copy pi extensions from agency package to project .agency/pi/extensions/.

    This ensures agency projects are self-contained with their own pi extensions.
    """
    import shutil

    # Find agency extras directory
    agency_package_dir = Path(__file__).parent.parent.parent

    possible_sources = [
        Path.cwd() / "extras" / "pi" / "extensions",
        agency_package_dir / "extras" / "pi" / "extensions",
    ]

    source_extensions_dir = None
    for src in possible_sources:
        if src.exists():
            source_extensions_dir = src
            break

    if not source_extensions_dir:
        click.echo("[WARN] Agency package extras not found, pi extensions not copied")
        return

    dest_extensions_dir = agency_dir / "pi" / "extensions"
    dest_extensions_dir.mkdir(parents=True, exist_ok=True)

    extensions_to_copy = ["pi-inject", "pi-status", "no-frills"]
    for ext_name in extensions_to_copy:
        source_ext = source_extensions_dir / ext_name
        dest_ext = dest_extensions_dir / ext_name
        if source_ext.exists():
            if dest_ext.exists():
                shutil.rmtree(dest_ext)
            shutil.copytree(source_ext, dest_ext)
            click.echo(f"✓ Copied pi extension: {ext_name}")


def _write_configs(agency_dir: Path, answers: dict[str, Any]) -> None:
    """Write all configuration files."""

    # Create directory structure
    agency_dir.mkdir(parents=True, exist_ok=True)
    (agency_dir / "agents").mkdir(exist_ok=True)
    (agency_dir / "var" / "tasks").mkdir(parents=True, exist_ok=True)
    (agency_dir / "var" / "pending").mkdir(parents=True, exist_ok=True)

    # Copy pi extensions
    _copy_pi_extensions(agency_dir)

    # Write manager config
    manager_path = write_manager_config(agency_dir, answers)
    click.echo(f"✓ Created {manager_path.relative_to(agency_dir)}")

    # Write agent configs
    agent_paths = write_agent_configs(agency_dir, answers)
    for path in agent_paths:
        click.echo(f"✓ Created {path.relative_to(agency_dir)}")

    # Write config.yaml
    config_path = agency_dir / "config.yaml"
    config_path.write_text(f"""$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/config.json
project: {agency_dir.parent.name}
shell: bash
audit_enabled: true
parallel_limit: {2 if answers.get('team_size') == 'solo' else 4}
""")
    click.echo(f"✓ Created {config_path.relative_to(agency_dir)}")
