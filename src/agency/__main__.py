#!/usr/bin/env python3
"""
Agency v2.0 - AI Agent Session Manager

A tmux-based multi-agent orchestration tool.
"""

import os
import signal
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import click

from agency import __version__
from agency.audit import EVENT_AGENT, EVENT_CLI, EVENT_SESSION, EVENT_TASK, AuditStore
from agency.config import (
    load_agency_config,
    load_agents_config,
    load_manager_config,
)
from agency.session import (
    SessionManager,
    create_project_session,
    start_agent_window,
    start_manager_window,
)
from agency.tasks import TaskStore
from agency.template import TemplateManager

VERSION = __version__


def _log_cli_command(command: str, **opts):
    """Log a CLI command invocation to audit trail."""
    agency_dir = find_agency_dir()
    if agency_dir:
        config = load_agency_config(agency_dir)
        if config.audit_enabled:
            audit = AuditStore(agency_dir)
            audit.log_cli(command=command, args=opts, cwd=os.getcwd())


def find_agency_dir(path: Path = Path.cwd()) -> Path | None:
    """Find .agency/ directory by walking up from path."""
    current = path.absolute()
    while current != current.parent:
        if (current / ".agency").is_dir():
            return current / ".agency"
        current = current.parent
    return None


def find_git_root(path: Path = Path.cwd()) -> Path | None:
    """Find the git repository root containing the given path."""
    current = path.absolute()
    while current != current.parent:
        if (current / ".git").is_dir():
            return current
        current = current.parent
    return None


def resolve_path(path: str) -> Path:
    """Expand ~ and ${VAR} environment variables in paths.

    Args:
        path: Path string that may contain ~ or ${VAR} patterns

    Returns:
        Expanded Path object
    """
    expanded = os.path.expanduser(path)
    expanded = os.path.expandvars(expanded)
    return Path(expanded)


def discover_agent_files(project_name: str | None = None) -> dict[str, Path | None]:
    """Discover common agent configuration files on the system.

    Searches standard locations for:
    - AGENTS.md (universal standard)
    - CLAUDE.md (Claude Code specific)
    - CLAUDE.local.md (personal project preferences)

    Args:
        project_name: Optional project name for ~/.claude/projects/<name>/ lookup

    Returns:
        Dict mapping file type to discovered Path or None
    """
    home = Path.home()
    results: dict[str, Path | None] = {
        "AGENTS.md": None,
        "CLAUDE.md": None,
        "CLAUDE.local.md": None,
    }

    # Discover AGENTS.md
    agents_md_locations = [
        home / ".agents" / "AGENTS.md",
        home / ".agents" / "AGENTS.system.md",
        home / "AGENTS.md",
    ]
    for loc in agents_md_locations:
        if loc.exists() and loc.is_file():
            results["AGENTS.md"] = loc
            break

    # Discover CLAUDE.md
    claude_md_locations = [
        home / ".claude" / "projects" / (project_name or "") / "CLAUDE.md",
        home / ".claude" / "CLAUDE.md",
    ]
    for loc in claude_md_locations:
        if loc.exists() and loc.is_file():
            results["CLAUDE.md"] = loc
            break

    # CLAUDE.local.md is typically in project root, not discovered automatically
    # but we note the expected location pattern

    return results


def _get_default_epilog() -> str:
    """Get epilog with examples for default (interactive) mode."""
    return """Examples:
  # Quick start
  cd ~/projects/myapp && agency init
  agency session start

  # Task management
  agency tasks add -d "Implement login"
  agency tasks assign task-001 coder
  agency tasks list

  # Session management
  agency session list
  agency session attach
  agency session stop"""


def _get_manager_epilog() -> str:
    """Get epilog with examples for manager/coordinator mode."""
    return """Examples:
  # Coordinator workflow
  agency tasks list
  agency tasks assign task-001 coder
  agency session members

  # Monitor sessions
  agency session windows list
  agency session stop"""


def _get_agent_epilog() -> str:
    """Get epilog with examples for agent mode."""
    return """Examples:
  # Agent workflow
  agency tasks list
  agency tasks show task-001
  agency tasks update task-001 --status in_progress
  agency tasks complete task-001 --result "Done!"""


@click.group(
    epilog=(
        _get_manager_epilog()
        if os.environ.get("AGENCY_ROLE", "").upper() == "MANAGER"
        else _get_agent_epilog()
        if os.environ.get("AGENCY_ROLE", "").upper() == "AGENT"
        else _get_default_epilog()
    )
)
@click.version_option(version=VERSION)
@click.pass_context
def cli(ctx):
    """Agency - AI Agent Session Manager."""
    role = os.environ.get("AGENCY_ROLE", "").upper()
    if role in ("MANAGER", "AGENT"):
        ctx.info_name = f"agency ({role.lower()})"


# === Project Commands ===


@click.command("templates")
@click.option("--repo", default="local", help="Template repository URL (default: local)")
@click.option("--refresh", is_flag=True, help="Bypass cache")
def list_templates(repo, refresh):
    """List available project templates.

    Shows local templates by default (bundled with agency).
    Use --repo to specify a different GitHub repository.
    """
    # Try local templates first
    local_templates_dir = Path(__file__).parent.parent.parent / "templates"
    if local_templates_dir.exists():
        local_templates = [
            d.name for d in local_templates_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]
        if local_templates:
            click.echo("Available templates (local):\n")
            for template in sorted(local_templates):
                click.echo(f"  • {template}")
            click.echo("\nUse: agency init --template <template-name>")
            return

    # Fall back to GitHub if no local templates
    if repo == "local":
        repo = "https://github.com/rwese/agency-templates"

    try:
        import json

        repo_name = repo.replace("https://github.com/", "")
        api_url = f"https://api.github.com/repos/{repo_name}/contents"

        result = subprocess.run(["curl", "-sL", api_url], capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            click.echo("[ERROR] Failed to fetch templates", err=True)
            return

        contents = json.loads(result.stdout)
        templates = [
            item["name"] for item in contents if item.get("type") == "dir" and not item["name"].startswith(".")
        ]

        if not templates:
            click.echo("No templates found.")
            return

        click.echo("Available templates:\n")
        for template in sorted(templates):
            click.echo(f"  • {template}")

        click.echo("\nUse: agency init --template <template-name>")

    except Exception as e:
        click.echo(f"[ERROR] {e}", err=True)


# Global flag for signal handling
_init_aborted = False
_session_created = False
_session_name = None
_socket_name = None
_sm = None


def _init_signal_handler(signum, frame):
    """Handle SIGINT (Ctrl+C) to abort init gracefully."""
    global _init_aborted, _session_created, _session_name, _sm
    _init_aborted = True
    click.echo("\n[ABORTED] Init cancelled by user", err=True)
    # Cleanup tmux session if created
    if _session_created and _session_name and _sm:
        try:
            _sm.kill_session()
        except Exception:
            pass
    sys.exit(130)


@dataclass
class AgentEntry:
    """An agent entry for init."""

    name: str
    personality: str = ""


@dataclass
class InitConfig:
    """Configuration for project initialization."""

    project_name: str
    shell: str = "bash"
    work_dir: Path | None = None
    agents: list[AgentEntry] = field(default_factory=list)
    manager_name: str = "coordinator"
    manager_personality: str = ""
    context_files: list[str] = field(default_factory=list)
    template_name: str | None = None
    template_url: str | None = None
    template_subdir: str | None = None
    force: bool = False


@click.command()
@click.option("--dir", "dir", type=click.Path(), default=".", help="Project directory (default: current)")
@click.option("--force", is_flag=True, help="Overwrite existing session")
@click.option("--yes", "non_interactive", is_flag=True, help="Non-interactive mode, use defaults")
@click.option("--refresh", is_flag=True, help="Bypass template cache")
@click.option("--template", "template_name", default=None, help="Template name (e.g., 'basic') or URL")
@click.option("--template-subdir", "template_subdir", default=None, help="Template subdirectory")
@click.option("--context-file", "context_files", multiple=True, help="Path to context file (repeatable)")
def init_project(dir, force, non_interactive, refresh, template_name, template_subdir, context_files):
    """Create a new project with session and .agency/ directory.

    Uses sensible defaults. Use --yes for non-interactive mode.
    """
    global _init_aborted, _session_created, _session_name, _socket_name, _sm

    # Register signal handler for proper ctrl-c abort
    signal.signal(signal.SIGINT, _init_signal_handler)

    _log_cli_command("init", dir=dir, force=force, non_interactive=non_interactive, template=template_name)

    # Determine work directory
    work_dir = Path(dir).expanduser().absolute()
    if not work_dir.exists():
        work_dir.mkdir(parents=True, exist_ok=True)

    # Validate CLI context files
    cli_context_files: list[str] = []
    for cf in context_files:
        expanded = resolve_path(cf)
        if not expanded.exists():
            click.echo(f"[ERROR] Context file not found: {expanded}", err=True)
            sys.exit(1)
        cli_context_files.append(str(expanded))

    # Build init config with defaults
    config = InitConfig(
        work_dir=work_dir,
        project_name=work_dir.name,
        force=force,
        context_files=cli_context_files,
        template_name=template_name,
        template_url=template_name if template_name and template_name.startswith(("http://", "https://")) else ("https://github.com/rwese/agency-templates" if template_name else None),
        template_subdir=template_subdir,
        agents=[AgentEntry(name="coder")],
    )

    # In interactive mode, offer context file discovery
    if not non_interactive and sys.stdin.isatty():
        discovered = discover_agent_files(config.project_name)
        available = []
        for name, path in discovered.items():
            if path and path.exists() and str(path) not in cli_context_files:
                available.append((name, path))

        if available:
            click.echo("\n[?] Discovered agent context files:")
            for name, path in available:
                click.echo(f"  - {name}: {path}")
            response = click.prompt("    Include these files? [y/N]", default="n", type=str, show_default=False).strip().lower()
            if response in ("y", "yes"):
                for name, path in available:
                    if str(path) not in config.context_files:
                        config.context_files.append(str(path))

    # Create the project
    _create_project(config, refresh=refresh)


def _create_project(config: InitConfig, refresh: bool = False) -> None:
    """Create the project based on init config.

    Creates .agency/ directory, configs, and tmux session.
    """
    global _session_created, _session_name, _socket_name, _sm

    work_dir = config.work_dir
    if not work_dir:
        work_dir = Path.cwd()

    agency_dir = work_dir / ".agency"

    # Copy pi extensions from agency package to project
    click.echo("\n[1/4] Setting up extensions...")
    _copy_pi_extensions(agency_dir)

    # Check/create tmux session
    session_name = f"agency-{config.project_name}"
    socket_name = session_name
    sm = SessionManager(session_name, socket_name=socket_name)

    if sm.session_exists():
        if config.force:
            click.echo("[WARN] Killing existing session...")
            sm.kill_session()
        else:
            click.echo(f"[ERROR] Session '{session_name}' already exists", err=True)
            click.echo("[ERROR] Use --force to overwrite", err=True)
            sys.exit(1)

    # Handle template or default structure
    click.echo("[2/4] Creating configuration...")
    if config.template_name:
        # Resolve template
        # If template_url is a full URL, extract the subdir from it
        tm = TemplateManager(
            config.template_url or "https://github.com/rwese/agency-templates",
            cache_dir=Path.home() / ".cache" / "agency" / "templates",
        )

        # Determine the subdir: explicit --template-subdir, or extract from URL
        template_subdir = config.template_subdir
        if not template_subdir:
            # Extract subdir from URL if template_name is a full URL
            if config.template_name.startswith(("http://", "https://")):
                # Parse the URL to extract path after /tree/<branch>/
                _, _, rest = config.template_name.partition("/tree/")
                if rest:
                    parts = rest.split("/")
                    template_subdir = "/".join(parts[1:]) if len(parts) > 1 else ""
            else:
                # Use template name as subdir
                template_subdir = config.template_name

        template_path = tm.get_template(subdir=template_subdir, refresh=refresh)
        if template_path:
            click.echo(f"[INFO] Using template: {template_path}")
            _copy_template_to_agency(template_path, agency_dir)
        else:
            click.echo("[WARN] Template not found, using default structure")
            _create_agency_structure_from_config(agency_dir, config)
    else:
        _create_agency_structure_from_config(agency_dir, config)

    # Create tmux session
    click.echo("[3/4] Creating tmux session...")
    create_project_session(session_name, socket_name, work_dir)
    _session_created = True
    _session_name = session_name
    _socket_name = socket_name
    _sm = sm

    # Summary
    click.echo("[4/4] Done!")
    click.echo("")
    click.echo(f"  Session:     {session_name}")
    click.echo(f"  Project:     {config.project_name}")
    click.echo(f"  Directory:   {agency_dir}")
    click.echo(f"  Agents:      {len(config.agents)}")
    click.echo("")
    click.echo("Next steps:")
    click.echo("  agency session start   # Start all agents")
    click.echo("  agency session attach  # Attach to session")


def _create_agency_structure_from_config(agency_dir: Path, config: InitConfig) -> None:
    """Create .agency/ directory structure from init config.

    Creates config.yaml, agents.yaml, manager.yaml based on init settings.
    """
    from agency.config import DEFAULT_PARALLEL_LIMIT

    agency_dir.mkdir(parents=True, exist_ok=True)

    # Create directories
    (agency_dir / "agents").mkdir(exist_ok=True)
    (agency_dir / "var" / "tasks").mkdir(parents=True, exist_ok=True)
    (agency_dir / "var" / "pending").mkdir(parents=True, exist_ok=True)
    (agency_dir / "run" / ".scripts").mkdir(parents=True, exist_ok=True)
    (agency_dir / "pi" / "extensions").mkdir(parents=True, exist_ok=True)

    # .gitignore in .scripts
    (agency_dir / "run" / ".scripts" / ".gitignore").write_text("*")

    # config.yaml
    context_section = ""
    if config.context_files:
        files_yaml = "\n".join(f"  - {f}" for f in config.context_files)
        context_section = f"\nadditional_context_files:\n{files_yaml}"

    config_content = f"""$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/config.json
project: {config.project_name}
shell: {config.shell}
parallel_limit: {DEFAULT_PARALLEL_LIMIT}{context_section}
"""
    (agency_dir / "config.yaml").write_text(config_content)

    # manager.yaml
    personality = config.manager_personality or "You are the project coordinator."
    manager_content = f"""$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/manager.json
name: {config.manager_name}
personality: |
  {personality}

poll_interval: 30
auto_approve: false
"""
    (agency_dir / "manager.yaml").write_text(manager_content)

    # agents.yaml and individual agent configs
    agents_list = []
    for agent in config.agents:
        agents_list.append({"name": agent.name, "config": f"agents/{agent.name}.yaml"})

        agent_config = f"""$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/agent.json
name: {agent.name}
"""
        if agent.personality:
            agent_config += f"\npersonality: |\n  {agent.personality}\n"

        (agency_dir / "agents" / f"{agent.name}.yaml").write_text(agent_config)

    agents_content = """$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/agents.json
agents:
"""
    if agents_list:
        for a in agents_list:
            agents_content += f"  - name: {a['name']}\n    config: {a['config']}\n"
    else:
        agents_content += "  []\n"

    (agency_dir / "agents.yaml").write_text(agents_content)

    # README.md
    (agency_dir / "README.md").write_text("# Agency Project\n\nThis project uses Agency for AI agent orchestration.\n")


def _fix_yaml_multiline_blocks(content: str) -> str:
    """Fix YAML multiline block syntax issues.

    The issue: In YAML literal blocks (|), blank lines end the block.
    After a blank line, ALL lines must be indented until the next top-level key.

    Properly indents markdown headers (## Title) and list items (- item).
    """
    import re

    lines = content.split("\n")
    fixed_lines = []
    in_block = False
    block_indent = 0

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Detect start of literal block (key: |)
        if re.match(r"^\s*\w+: \|$", line):
            in_block = True
            # Content indent = 2 spaces (for continuation of block)
            block_indent = len(line) - len(line.lstrip()) + 2
            fixed_lines.append(line)
            continue

        if in_block:
            if stripped == "":
                # Blank line - add indent to continue block
                fixed_lines.append(" " * block_indent)
            elif line.startswith(" " * 2):
                # Already indented - OK
                fixed_lines.append(line)
            elif stripped.startswith("## ") or stripped.startswith("- "):
                # Markdown header or list item - indent it
                fixed_lines.append(" " * block_indent + stripped)
            elif re.match(r"^\s*\w+:", line):
                # Next top-level key - end block
                in_block = False
                fixed_lines.append(line)
            else:
                # Other content - indent it
                fixed_lines.append(" " * block_indent + stripped)
        else:
            fixed_lines.append(line)

    return "\n".join(fixed_lines)


def _copy_template_to_agency(template_path: Path, agency_dir: Path) -> None:
    """Copy template files to project.

    Copies .agency/ to project's .agency/ and other project files to project root.
    Fixes YAML files with multiline block syntax issues.
    """
    import shutil

    import yaml

    work_dir = agency_dir.parent  # Project root
    agency_dir.mkdir(parents=True, exist_ok=True)

    # Template structure may have .agency/ at root level or inside a subdir
    template_agency = template_path / ".agency"

    # Find the actual .agency source
    if template_agency.exists():
        # .agency is at template root
        agency_source = template_agency
    else:
        # Look for .agency inside template
        for item in template_path.rglob(".agency"):
            agency_source = item
            break
        else:
            agency_source = None

    # Copy .agency contents with YAML fix
    if agency_source and agency_source.exists():
        for item in agency_source.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(agency_source)
                dest = agency_dir / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)

                # Fix YAML files
                if item.suffix in (".yaml", ".yml"):
                    content = item.read_text()
                    fixed_content = _fix_yaml_multiline_blocks(content)
                    try:
                        # Verify it parses
                        yaml.safe_load(fixed_content)  # Verify it parses
                        dest.write_text(fixed_content)
                    except Exception:
                        # Still broken - use raw copy
                        shutil.copy2(item, dest)
                else:
                    shutil.copy2(item, dest)

    # Copy other project files (backend, frontend, k8s, etc.)
    for item in template_path.iterdir():
        if item.name == ".agency":
            continue  # Already handled
        if item.is_file():
            dest = work_dir / item.name
            shutil.copy2(item, dest)
        elif item.is_dir():
            dest = work_dir / item.name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)


def _create_default_agency_structure(agency_dir: Path, additional_context_files: list[str] | None = None) -> None:
    """Create default .agency/ directory structure.

    Args:
        agency_dir: Path to the .agency/ directory
        additional_context_files: List of paths to agent context files to reference
    """
    from agency.config import DEFAULT_PARALLEL_LIMIT

    agency_dir.mkdir(parents=True, exist_ok=True)
    (agency_dir / "agents").mkdir(exist_ok=True)
    (agency_dir / "var").mkdir(exist_ok=True)
    (agency_dir / "var" / "tasks").mkdir(exist_ok=True)
    (agency_dir / "var" / "pending").mkdir(exist_ok=True)
    (agency_dir / "run").mkdir(exist_ok=True)
    (agency_dir / "run" / ".scripts").mkdir(exist_ok=True)
    # Create .gitignore in .scripts to ignore all scripts
    scripts_gitignore = agency_dir / "run" / ".scripts" / ".gitignore"
    scripts_gitignore.write_text("*")
    (agency_dir / "pi" / "extensions").mkdir(parents=True, exist_ok=True)  # pi extensions (copied during init)

    config_path = agency_dir / "config.yaml"
    if not config_path.exists():
        context_section = ""
        if additional_context_files:
            files_yaml = "\n".join(f"  - {f}" for f in additional_context_files)
            context_section = f"\nadditional_context_files:\n{files_yaml}"
        config_path.write_text(
            f"""$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/config.json
project: default
shell: bash
parallel_limit: {DEFAULT_PARALLEL_LIMIT}  # Max parallel tasks across all agents
{context_section}
"""
        )

    agents_path = agency_dir / "agents.yaml"
    if not agents_path.exists():
        agents_path.write_text(
            """$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/agents.json
agents: []
"""
        )

    manager_path = agency_dir / "manager.yaml"
    if not manager_path.exists():
        manager_path.write_text(
            """$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/manager.json
name: coordinator
personality: |
  You are the project coordinator.

poll_interval: 30
auto_approve: false
"""
        )

    readme_path = agency_dir / "README.md"
    if not readme_path.exists():
        readme_path.write_text("# Agency Project\n\nThis project uses Agency for AI agent orchestration.\n")


def _copy_pi_extensions(agency_dir: Path) -> None:
    """Copy pi extensions from agency package to project .agency/pi/extensions/.

    This ensures agency projects are self-contained with their own pi extensions,
    rather than relying on the global ~/.pi/agent/extensions/ installation.

    Extensions are copied from the agency's extras/pi/extensions/ directory.
    The source is resolved in this order:
    1. Current working directory (for development)
    2. Agency package directory (for installed version)

    Args:
        agency_dir: Path to the .agency/ directory
    """
    import shutil

    # Find agency extras directory
    # Try current working directory first (development mode)
    # Then try package directory (installed mode)
    # Note: __file__ is in src/agency/, so we need parent.parent.parent to reach repo root
    agency_package_dir = Path(__file__).parent.parent.parent

    possible_sources = [
        Path.cwd() / "extras" / "pi" / "extensions",  # Development: repo root
        agency_package_dir / "extras" / "pi" / "extensions",  # Installed: package dir
    ]

    source_extensions_dir = None
    for src in possible_sources:
        if src.exists():
            source_extensions_dir = src
            break

    if not source_extensions_dir:
        print("[WARN] Agency package extras not found, pi extensions not copied")
        return

    # Destination: .agency/pi/extensions/
    dest_extensions_dir = agency_dir / "pi" / "extensions"
    dest_extensions_dir.mkdir(parents=True, exist_ok=True)

    # Extensions to copy (must be self-contained with their own node_modules)
    extensions_to_copy = ["pi-inject", "pi-status", "no-frills"]

    for ext_name in extensions_to_copy:
        source_ext = source_extensions_dir / ext_name
        dest_ext = dest_extensions_dir / ext_name

        if not source_ext.exists():
            print(f"[WARN] Extension '{ext_name}' not found in agency package")
            continue

        # Copy extension (excluding .git, .ruff_cache, etc.)
        if dest_ext.exists():
            shutil.rmtree(dest_ext)

        # Use copytree with ignore to exclude unnecessary files
        def ignore_func(src, names):
            ignore = {".git", ".ruff_cache", "__pycache__", ".pytest_cache"}
            return ignore.intersection(names)

        shutil.copytree(source_ext, dest_ext, ignore=ignore_func)
        print(f"[INFO] Copied pi extension: {ext_name}")


# === Task Commands ===


@click.group()
def tasks():
    """Task management commands."""


# Agent-only tasks (limited commands)
@click.group()
def tasks_agent():
    """Task commands for agents."""
    pass


def _list_tasks(agency_dir, status, assignee, include_blocked=False):
    """List tasks helper function.

    Args:
        agency_dir: Path to .agency directory
        status: Filter by status
        assignee: Filter by assignee
        include_blocked: If True, include tasks blocked by dependencies
    """
    store = TaskStore(agency_dir)
    task_list = store.list_tasks(status=status, assignee=assignee, include_blocked=include_blocked)

    if not task_list:
        click.echo("No tasks found")
        return

    for task in task_list:
        status_icon = {
            "pending": "⏳",
            "in_progress": "🔄",
            "pending_approval": "👀",
            "completed": "✅",
            "failed": "❌",
        }.get(task.status, "?")

        click.echo(f"## {task.task_id}")
        click.echo("")
        click.echo(f"- status: {task.status} {status_icon}")
        click.echo(f"- priority: {task.priority}")
        click.echo(f"- assigned_to: {task.assigned_to or 'null'}")
        click.echo(f"- description: {task.description}")
        click.echo(f"- created_at: {task.created_at}")
        if task.started_at:
            click.echo(f"- started_at: {task.started_at}")
        if task.completed_at:
            click.echo(f"- completed_at: {task.completed_at}")
        click.echo("")


@tasks.command("list")
@click.option("--status", help="Filter by status")
@click.option("--assignee", help="Filter by assignee")
@click.option(
    "--include-blocked",
    is_flag=True,
    help="Include tasks blocked by dependencies (default: excluded for agents, included for managers)",
)
def tasks_list(status, assignee, include_blocked):
    """List tasks assigned to current agent (when AGENCY_AGENT is set), otherwise all tasks.

    Agents only see their own tasks that are pending or in_progress.
    Managers see all tasks unless filtered.
    """
    is_agent = bool(os.environ.get("AGENCY_AGENT"))

    # Auto-filter to current agent's tasks when running as an agent
    if is_agent and not assignee:
        assignee = os.environ["AGENCY_AGENT"]
        # Agents only see pending or in_progress tasks (not completed/failed)
        if not status:
            status = "pending,in_progress"

    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        click.echo("[ERROR] Run 'agency init-project --dir <path>' first", err=True)
        sys.exit(1)

    # Agents always see only unblocked tasks
    include_blocked = include_blocked and not is_agent

    _list_tasks(agency_dir, status, assignee, include_blocked=include_blocked)


@tasks.command("add")
@click.option("-d", "--description", required=True, help="Task description")
@click.option("-a", "--assignee", help="Assign to agent")
@click.option("-p", "--priority", default="low", help="Priority: low, normal, high")
def tasks_add(description, assignee, priority):
    """Add a new task."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)

    store = TaskStore(agency_dir)
    task = store.add_task(description=description, priority=priority, assigned_to=assignee)
    click.echo(f"[INFO] Created task: {task.task_id}")


@tasks.command("show")
@click.argument("task_id")
def tasks_show(task_id):
    """Show task details."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)

    store = TaskStore(agency_dir)
    task = store.get_task(task_id)

    if not task:
        click.echo(f"[ERROR] Task not found: {task_id}", err=True)
        sys.exit(1)

    status_icon = {
        "pending": "⏳",
        "in_progress": "🔄",
        "pending_approval": "👀",
        "completed": "✅",
        "failed": "❌",
    }.get(task.status, "?")

    click.echo(f"# {task.task_id}")
    click.echo("")
    click.echo("## Task")
    click.echo("")
    click.echo(f"- **Description**: {task.description}")
    click.echo(f"- **Status**: {task.status} {status_icon}")
    click.echo(f"- **Priority**: {task.priority}")
    click.echo(f"- **Assigned to**: {task.assigned_to or 'Unassigned'}")
    click.echo(f"- **Created**: {task.created_at or 'Unknown'}")
    click.echo(f"- **Started**: {task.started_at or 'Not started'}")
    click.echo(f"- **Completed**: {task.completed_at or 'In progress'}")

    # Show dependencies
    if task.depends_on:
        click.echo(f"- **Depends on**: {', '.join(task.depends_on)}")
        # Show blocking status
        blocking = store.get_blocked_by(task_id)
        if blocking:
            blocking_ids = [f"{t.task_id} ({t.status})" for t in blocking]
            click.echo(f"- **Blocked by**: {', '.join(blocking_ids)} 🚫")
        else:
            click.echo("- **Blocked by**: None ✅")
    else:
        click.echo("- **Depends on**: None")

    click.echo("")

    if task.result:
        click.echo("## Result")
        click.echo("")
        click.echo(task.result)
        click.echo("")


@tasks.command("assign")
@click.argument("task_id")
@click.argument("agent")
def tasks_assign(task_id, agent):
    """Assign task to an agent."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)

    store = TaskStore(agency_dir)

    if not store.is_agent_free(agent):
        click.echo(f"[WARN] Agent '{agent}' may not be free (has pending/in_progress tasks)", err=True)

    try:
        if store.assign_task(task_id, agent):
            click.echo(f"[INFO] Assigned {task_id} to {agent}")
        else:
            click.echo("[ERROR] Failed to assign task", err=True)
            sys.exit(1)
    except ValueError as e:
        click.echo(f"[ERROR] {e}", err=True)
        sys.exit(1)


@tasks.command("depends")
@click.argument("task_id")
@click.option("--add", "action", flag_value="add", default=True, help="Add dependencies")
@click.option("--remove", "action", flag_value="remove", help="Remove a dependency")
@click.option("--set", "action", flag_value="set", help="Set all dependencies (replaces existing)")
@click.argument("dependencies", nargs=-1, required=True)
def tasks_depends(task_id, action, dependencies):
    """Manage task dependencies.

    Tasks will only be available to agents once all their dependencies are completed.

    Examples:
        agency tasks depends task-1 --add task-2 task-3
        agency tasks depends task-1 --set task-2
        agency tasks depends task-1 --remove task-2
    """
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)

    store = TaskStore(agency_dir)

    # Validate task exists
    task = store.get_task(task_id)
    if not task:
        click.echo(f"[ERROR] Task not found: {task_id}", err=True)
        sys.exit(1)

    try:
        if action == "set":
            store.set_dependencies(task_id, list(dependencies))
            click.echo(f"[INFO] Set dependencies for {task_id}: {', '.join(dependencies) or '(none)'}")
        elif action == "add":
            for dep in dependencies:
                store.add_dependency(task_id, dep)
            task = store.get_task(task_id)
            click.echo(f"[INFO] Added dependencies to {task_id}: {', '.join(task.depends_on or [])}")
        elif action == "remove":
            for dep in dependencies:
                store.remove_dependency(task_id, dep)
            task = store.get_task(task_id)
            click.echo(f"[INFO] Removed dependency from {task_id}: {', '.join(task.depends_on or [])}")
    except ValueError as e:
        click.echo(f"[ERROR] {e}", err=True)
        sys.exit(1)


@tasks.command("complete")
@click.argument("task_id")
@click.option("--result", required=True, help="Result summary")
@click.option("--files", help="JSON array of files")
@click.option("--diff", help="Git diff")
@click.option("--summary", help="Summary")
def tasks_complete(task_id, result, files, diff, summary):
    """Complete a task."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)

    store = TaskStore(agency_dir)

    import json

    files_list = None
    if files:
        try:
            files_list = json.loads(files)
        except json.JSONDecodeError:
            click.echo("[ERROR] Invalid JSON in --files", err=True)
            sys.exit(1)

    if store.complete_task(
        task_id=task_id,
        result=result,
        files=files_list,
        diff=diff,
        summary=summary,
    ):
        click.echo(f"[INFO] Task {task_id} marked for approval")
    else:
        click.echo("[ERROR] Failed to complete task", err=True)
        sys.exit(1)


@tasks.command("approve")
@click.argument("task_id")
def tasks_approve(task_id):
    """Approve a pending task completion."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)

    store = TaskStore(agency_dir)
    if store.approve_task(task_id):
        click.echo(f"[INFO] Task {task_id} approved and archived")
    else:
        click.echo("[ERROR] Failed to approve task", err=True)
        sys.exit(1)


@tasks.command("reject")
@click.argument("task_id")
@click.option("--reason", required=True, help="Rejection reason")
@click.argument("suggestions", nargs=-1, required=False)
def tasks_reject(task_id, suggestions, reason):
    """Reject a pending task completion."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)

    store = TaskStore(agency_dir)
    if store.reject_task(task_id, reason=reason, suggestions=list(suggestions) if suggestions else None):
        click.echo(f"[INFO] Task {task_id} rejected")
    else:
        click.echo("[ERROR] Failed to reject task", err=True)
        sys.exit(1)


@tasks.command("reopen")
@click.argument("task_id")
def tasks_reopen(task_id):
    """Reopen a completed or failed task."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)

    store = TaskStore(agency_dir)
    task = store.get_task(task_id)

    if not task:
        click.echo(f"[ERROR] Task not found: {task_id}", err=True)
        sys.exit(1)

    if task.status not in ("completed", "failed"):
        click.echo(f"[ERROR] Task {task_id} is not completed or failed", err=True)
        sys.exit(1)

    if store.update_task(task_id, status="pending"):
        # Clear result fields
        task_json_path = agency_dir / "tasks" / task_id / "task.json"
        if task_json_path.exists():
            import json

            data = json.loads(task_json_path.read_text())
            data["status"] = "pending"
            data["completed_at"] = None
            data["result"] = None
            task_json_path.write_text(json.dumps(data, indent=2))

        click.echo(f"[INFO] Task {task_id} reopened")
    else:
        click.echo("[ERROR] Failed to reopen task", err=True)
        sys.exit(1)


@tasks.command("update")
@click.argument("task_id")
@click.option("--status", help="New status")
@click.option("--priority", help="New priority")
def tasks_update(task_id, status, priority):
    """Update a task."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)

    if not status and not priority:
        click.echo("[ERROR] At least one of --status or --priority required", err=True)
        sys.exit(1)

    store = TaskStore(agency_dir)
    if store.update_task(task_id, status=status, priority=priority):
        click.echo(f"[INFO] Updated task {task_id}")
    else:
        click.echo("[ERROR] Failed to update task", err=True)
        sys.exit(1)


@tasks.command("delete")
@click.argument("task_id")
def tasks_delete(task_id):
    """Delete a task."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)

    store = TaskStore(agency_dir)
    if store.delete_task(task_id):
        click.echo(f"[INFO] Deleted task {task_id}")
    else:
        click.echo("[ERROR] Failed to delete task", err=True)
        sys.exit(1)


@tasks.command("history")
@click.option("--agent", help="Filter by agent")
def tasks_history(agent):
    """Show task history."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)

    store = TaskStore(agency_dir)
    history = store.history(agent=agent)

    if not history:
        click.echo("No completed tasks found")
        return

    click.echo("## Completed Tasks")
    click.echo("")

    for item in history:
        task = item["task"]
        result = item.get("result", {})

        status_icon = "✅" if task["status"] == "completed" else "❌"

        click.echo(f"### {task['task_id']} {status_icon}")
        click.echo(f"- **Agent**: {task.get('assigned_to', 'unknown')}")
        click.echo(f"- **Completed**: {task.get('completed_at', 'unknown')}")

        if result:
            res = result.get("result", "No result")
            if len(res) > 100:
                res = res[:100] + "..."
            click.echo(f"- **Result**: {res}")

        click.echo("")


# === Agent-only task commands ===


def _get_agent_name():
    """Get agent name from AGENCY_AGENT env var."""
    agent = os.environ.get("AGENCY_AGENT", "")
    if not agent:
        click.echo("[ERROR] AGENCY_AGENT not set", err=True)
        sys.exit(1)
    return agent


def _verify_task_ownership(agency_dir: Path, task_id: str, agent: str) -> bool:
    """Verify task is assigned to this agent."""
    store = TaskStore(agency_dir)
    task = store.get_task(task_id)
    if not task:
        click.echo(f"[ERROR] Task not found: {task_id}", err=True)
        return False
    if task.assigned_to != agent:
        click.echo(f"[ERROR] Task {task_id} not assigned to you", err=True)
        return False
    return True


@tasks_agent.command("list")
def agent_tasks_list():
    """List tasks assigned to you (only unblocked tasks)."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)
    agent = _get_agent_name()
    _list_tasks(agency_dir, status=None, assignee=agent, include_blocked=False)


@tasks_agent.command("my-work")
def agent_my_work():
    """Show your work queue - tasks to work on right now."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)

    import os

    agent = os.environ.get("AGENCY_AGENT", "")
    if not agent:
        click.echo("[ERROR] AGENCY_AGENT not set", err=True)
        sys.exit(1)

    click.echo(f"📋 YOUR WORK QUEUE ({agent})")
    click.echo("=" * 50)

    store = TaskStore(agency_dir)

    # 1. First: in_progress tasks (working on now)
    in_progress = store.list_tasks(status="in_progress", assignee=agent)
    if in_progress:
        click.echo("\n🔄 IN PROGRESS:")
        for task in in_progress:
            click.echo(f"  [{task.task_id}]")
            click.echo(f"    {task.description[:60]}...")
            click.echo(f"    Status: {task.status}")

    # 2. Second: pending tasks (next to work on)
    pending = store.list_tasks(status="pending", assignee=agent)
    if pending:
        click.echo(f"\n⏳ PENDING ({len(pending)} task(s)):")
        for i, task in enumerate(pending, 1):
            click.echo(f"  {i}. [{task.task_id}]")
            click.echo(f"     {task.description}")

    # 3. Third: pending_approval (waiting for manager)
    approval = store.list_tasks(status="pending_approval", assignee=agent)
    if approval:
        click.echo(f"\n👀 PENDING APPROVAL ({len(approval)} task(s)):")
        for task in approval:
            click.echo(f"  [{task.task_id}] - Awaiting review")

    if not in_progress and not pending and not approval:
        click.echo("\n✅ No tasks assigned. Check 'agency tasks list' for available work.")
    else:
        click.echo("\n" + "=" * 50)
        if pending:
            click.echo("Next: Run 'agency tasks-agent show <id>' then start working!")


@tasks_agent.command("show")
@click.argument("task_id")
def agent_tasks_show(task_id):
    """Show task details."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)
    agent = _get_agent_name()
    if not _verify_task_ownership(agency_dir, task_id, agent):
        sys.exit(1)
    tasks_show(task_id)


@tasks_agent.command("update")
@click.argument("task_id")
@click.option("--status", help="Status: pending, in_progress, pending_approval")
@click.option("--priority", help="Priority: low, normal, high")
def agent_tasks_update(task_id, status, priority):
    """Update task status or priority."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)
    agent = _get_agent_name()
    if not _verify_task_ownership(agency_dir, task_id, agent):
        sys.exit(1)
    tasks_update(task_id, status, priority)


@tasks_agent.command("complete")
@click.argument("task_id")
@click.option("--result", required=True, help="Result summary")
@click.option("--files", help="JSON array of files")
@click.option("--diff", help="Git diff")
@click.option("--summary", help="Summary")
def agent_tasks_complete(task_id, result, files, diff, summary):
    """Complete a task."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)
    agent = _get_agent_name()
    if not _verify_task_ownership(agency_dir, task_id, agent):
        sys.exit(1)
    tasks_complete(task_id, result, files, diff, summary)


# === Completions ===


@click.command()
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
def completions(shell):
    """Print shell completion script."""
    from agency.completions import get_completion_script

    click.echo(get_completion_script(shell))


# === Session Commands ===


@click.group("session")
def session_cmd():
    """Session management commands."""
    pass


# ---- Session lifecycle commands ----


# Helper function used by session_start
def _start_all_members(
    session_name: str,
    socket_name: str,
    agency_dir: Path,
    work_dir: Path,
    sm: SessionManager,
) -> None:
    """Start all configured members (manager + agents)."""
    # Load manager config
    manager_config = load_manager_config(agency_dir)
    manager_name = manager_config.name if manager_config else "coordinator"

    # Load agents config
    agents = load_agents_config(agency_dir)

    if not manager_config and not agents:
        click.echo("[WARN] No manager or agents configured", err=True)
        return

    click.echo(f"[INFO] Starting all members for {session_name}")

    # Start manager first
    if manager_config:
        if sm.manager_exists():
            click.echo(f"  [SKIP] Manager already running: [MGR] {manager_name}")
        else:
            start_manager_window(session_name, socket_name, manager_name, agency_dir, work_dir)
            click.echo(f"  [OK] Started: [MGR] {manager_name}")

    # Start all agents
    for agent in agents:
        if sm.window_exists(agent.name):
            click.echo(f"  [SKIP] Agent already running: {agent.name}")
        else:
            start_agent_window(session_name, socket_name, agent.name, agency_dir, work_dir)
            click.echo(f"  [OK] Started: {agent.name}")

    click.echo("[INFO] All members started")


@session_cmd.command("start")
@click.option(
    "--dir",
    "dir",
    type=click.Path(),
    default=None,
    help="Project directory (auto-detected from .agency/)",
)
def session_start(dir):
    """Start the session (manager + all agents).

    Auto-detects project directory from .agency/ if not specified.
    """
    _log_cli_command("session start", dir=dir)
    # Auto-detect from .agency/ if --dir not provided
    if dir:
        work_dir = Path(dir).expanduser().absolute()
    else:
        agency_dir_path = find_agency_dir()
        if not agency_dir_path:
            click.echo("[ERROR] No .agency/ found", err=True)
            click.echo("[ERROR] Run 'agency init' or use --dir", err=True)
            sys.exit(1)
        work_dir = agency_dir_path.parent

    git_root = find_git_root(work_dir)
    if not git_root:
        click.echo("[ERROR] Not in a git repository", err=True)
        sys.exit(1)

    # Use work_dir for agency_dir, not git_root (allows subdirectory projects)
    agency_dir = work_dir / ".agency"
    if not agency_dir.exists():
        click.echo(f"[ERROR] No .agency/ found in {work_dir}", err=True)
        click.echo("[ERROR] Run 'agency init' first", err=True)
        sys.exit(1)

    project_name = work_dir.name
    session_name = f"agency-{project_name}"
    socket_name = f"agency-{project_name}"

    sm = SessionManager(session_name, socket_name=socket_name)

    # Create session if it doesn't exist
    if not sm.session_exists():
        click.echo(f"[INFO] Creating new session: {session_name}")
        create_project_session(session_name, socket_name, work_dir)

    # Start all members (manager will be at window:0)
    _start_all_members(session_name, socket_name, agency_dir, work_dir, sm)


@session_cmd.command("stop")
@click.argument("session", required=False)
@click.option("--timeout", type=int, help="Grace period in seconds (default: 300)")
@click.option("--force", is_flag=True, help="Force kill without graceful shutdown")
@click.option("--idle", type=int, default=15, help="Seconds of inactivity before killing windows (default: 15)")
def session_stop(session, timeout, force, idle):
    """Stop a session gracefully.

    Stop mechanism:
    1. Send Escape to all windows (cancel ongoing operations)
    2. Wait briefly for agents to cancel
    3. Send wrapup command (cleanup, update tasks, say goodbye)
    4. Wait for idle windows
    5. Kill idle windows
    6. Force kill after --timeout

    Auto-detects session from .agency/ if not specified.
    """
    _log_cli_command("session stop", session=session, timeout=timeout, force=force, idle=idle)
    # Auto-detect from .agency/ if session not provided
    if not session:
        agency_dir_path = find_agency_dir()
        if not agency_dir_path:
            click.echo("[ERROR] No .agency/ found", err=True)
            click.echo("[ERROR] Use 'agency session stop <session>' or run from project directory", err=True)
            sys.exit(1)
        work_dir = agency_dir_path.parent
        session = f"agency-{work_dir.name}"
    elif not session.startswith("agency-"):
        session = f"agency-{session}"

    socket_name = session
    sm = SessionManager(session, socket_name=socket_name)

    if not sm.session_exists():
        click.echo(f"[ERROR] Session not found: {session}", err=True)
        sys.exit(1)

    if force:
        # Direct kill
        sm.kill_session()
        sm.cleanup_socket()
        click.echo("[INFO] Session killed")
        return

    import time

    timeout = timeout or 300  # 5 minutes default
    idle_check_interval = 2  # Check idle status every 2 seconds
    idle_target = idle  # Seconds of inactivity to consider idle

    # Phase 1: Send Escape to cancel ongoing operations
    click.echo("[INFO] Phase 1: Sending Escape to cancel ongoing operations...")
    sm.broadcast_escape()
    time.sleep(2)  # Brief pause for agents to react

    # Phase 2: Send wrapup command
    click.echo("[INFO] Phase 2: Sending wrapup command...")
    sm.broadcast_wrapup()

    # Wait for idle with graceful kill of idle windows
    elapsed = 0.0
    last_progress = 0.0
    killed_windows: set[str] = set()

    while elapsed < timeout:
        time.sleep(idle_check_interval)
        elapsed += idle_check_interval

        if not sm.session_exists():
            click.echo("[INFO] Session stopped gracefully")
            sm.cleanup_socket()
            return

        # Check idle status
        idle_windows = [w for w in sm.get_idle_windows(idle_target) if w not in killed_windows]

        if idle_windows:
            click.echo(f"[INFO] Idle windows: {', '.join(idle_windows)}")

            # Kill idle windows that haven't been killed yet
            for window in idle_windows:
                click.echo(f"[INFO] Killing idle window: {window}")
                sm.kill_window(window)
                killed_windows.add(window)

        # Progress indicator every 30 seconds
        if elapsed - last_progress >= 30:
            click.echo(f"[INFO] Waiting for graceful shutdown... ({elapsed:.0f}s elapsed)")
            last_progress = elapsed

    # Force kill after timeout
    click.echo("[WARN] Graceful shutdown timed out, force killing...", err=True)
    sm.kill_session()
    sm.cleanup_socket()
    click.echo("[INFO] Session killed")


@session_cmd.command("kill")
@click.argument("session", required=False)
def session_kill(session):
    """Force kill a session immediately.

    Auto-detects session from .agency/ if not specified.
    """
    _log_cli_command("session kill", session=session)
    # Auto-detect from .agency/ if session not provided
    if not session:
        agency_dir_path = find_agency_dir()
        if not agency_dir_path:
            click.echo("[ERROR] No .agency/ found", err=True)
            click.echo("[ERROR] Use 'agency session kill <session>' or run from project directory", err=True)
            sys.exit(1)
        work_dir = agency_dir_path.parent
        session = f"agency-{work_dir.name}"
    elif not session.startswith("agency-"):
        session = f"agency-{session}"

    socket_name = session
    sm = SessionManager(session, socket_name=socket_name)

    if not sm.session_exists():
        click.echo(f"[ERROR] Session not found: {session}", err=True)
        sys.exit(1)

    sm.kill_session()
    sm.cleanup_socket()
    click.echo(f"[INFO] Session {session} killed")


@session_cmd.command("attach")
@click.option(
    "--dir",
    "dir",
    type=click.Path(),
    default=None,
    help="Project directory (auto-detected from .agency/)",
)
def session_attach(dir):
    """Attach to the project session.

    Auto-detects session from .agency/ directory.
    """
    _log_cli_command("session attach", dir=dir)
    # Auto-detect from .agency/ if --dir not provided
    if dir:
        work_dir = Path(dir).expanduser().absolute()
    else:
        agency_dir_path = find_agency_dir()
        if not agency_dir_path:
            click.echo("[ERROR] No .agency/ found", err=True)
            sys.exit(1)
        work_dir = agency_dir_path.parent

    git_root = find_git_root(work_dir)
    if not git_root:
        click.echo("[ERROR] Not in a git repository", err=True)
        sys.exit(1)

    agency_dir = git_root / ".agency"
    if not agency_dir.exists():
        click.echo(f"[ERROR] No .agency/ found in {git_root}", err=True)
        sys.exit(1)

    project_name = work_dir.name
    session_name = f"agency-{project_name}"

    # Use tmux attach
    os.execvp("tmux", ["tmux", "-L", session_name, "attach-session", "-t", session_name])


@session_cmd.command("list")
@click.option(
    "--dir",
    "dir",
    type=click.Path(),
    default=None,
    help="Project directory (auto-detected from .agency/)",
)
def session_list(dir):
    """List agency sessions.

    Shows sessions from current project or all agency sessions.
    """
    _log_cli_command("session list", dir=dir)
    # Check if we're in an agency project
    if dir:
        work_dir = Path(dir).expanduser().absolute()
    else:
        agency_dir_path = find_agency_dir()
        work_dir = agency_dir_path.parent if agency_dir_path else None

    # If in a project, show that session first
    if work_dir and (work_dir / ".agency").exists():
        project_name = work_dir.name
        session_name = f"agency-{project_name}"
        sm = SessionManager(session_name, socket_name=session_name)

        if sm.session_exists():
            click.echo(f"{session_name} (current)")
            for w in sm.list_windows():
                click.echo(f"  {w}")
            click.echo("")

    # Also show all sessions on default socket
    from agency.session import list_agency_sessions

    sessions = list_agency_sessions()

    if sessions:
        click.echo("# All Sessions")
        for session in sessions:
            click.echo(f"{session['name']}")
            for window in session.get("windows", []):
                click.echo(f"  {window['name']}")
    elif (
        not work_dir
        or not (work_dir / ".agency").exists()
        or not SessionManager(f"agency-{work_dir.name}", socket_name=f"agency-{work_dir.name}").session_exists()
    ):
        click.echo("[INFO] No agency sessions running")


@session_cmd.command("members")
@click.option(
    "--dir",
    "dir",
    type=click.Path(),
    default=None,
    help="Project directory (auto-detected from .agency/)",
)
def session_members(dir):
    """Show all configured members (manager and agents)."""
    _log_cli_command("session members", dir=dir)
    # Auto-detect from .agency/ if --dir not provided
    if dir:
        work_dir = Path(dir).expanduser().absolute()
    else:
        agency_dir_path = find_agency_dir()
        if not agency_dir_path:
            click.echo("[ERROR] No .agency/ found", err=True)
            click.echo("[ERROR] Run 'agency init-project' or use --dir", err=True)
            sys.exit(1)
        work_dir = agency_dir_path.parent

    git_root = find_git_root(work_dir)
    if not git_root:
        click.echo("[ERROR] Not in a git repository", err=True)
        sys.exit(1)

    agency_dir = git_root / ".agency"
    if not agency_dir.exists():
        click.echo(f"[ERROR] No .agency/ found in {git_root}", err=True)
        sys.exit(1)

    # Load configs
    manager_config = load_manager_config(agency_dir)
    agents = load_agents_config(agency_dir)

    # Get running status
    project_name = work_dir.name
    session_name = f"agency-{project_name}"
    sm = SessionManager(session_name, socket_name=session_name)
    running_windows = sm.list_windows() if sm.session_exists() else []

    click.echo(f"# {project_name}")
    click.echo("")

    # Show manager
    click.echo("## Manager")
    click.echo("")
    if manager_config:
        is_running = any(w.startswith("[MGR]") for w in running_windows)
        status = "🟢 running" if is_running else "⚪ stopped"
        click.echo(f"- **Name**: {manager_config.name}")
        click.echo(f"- **Status**: {status}")
        if manager_config.personality:
            preview = (
                manager_config.personality[:50] + "..."
                if len(manager_config.personality) > 50
                else manager_config.personality
            )
            click.echo(f"- **Personality**: {preview}")
    else:
        click.echo("- _No manager configured_")
    click.echo("")

    # Show agents
    click.echo("## Agents")
    click.echo("")
    if agents:
        for agent in agents:
            is_running = agent.name in running_windows
            status = "🟢 running" if is_running else "⚪ stopped"
            click.echo(f"### {agent.name}")
            click.echo("")
            click.echo(f"- **Status**: {status}")
            if agent.personality:
                preview = agent.personality[:50] + "..." if len(agent.personality) > 50 else agent.personality
                click.echo(f"- **Personality**: {preview}")
            click.echo("")
    else:
        click.echo("- _No agents configured_")
        click.echo("")


# ---- Session windows commands ----


@session_cmd.group("windows")
def session_windows():
    """Session window operations."""
    pass


@session_windows.command("list")
@click.pass_context
def session_windows_list(ctx):
    """List windows in the session."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        click.echo("[ERROR] Run 'agency init' or use --dir", err=True)
        ctx.exit(1)

    config = load_agency_config(agency_dir)
    session_name = f"agency-{config.project}"
    socket_name = f"agency-{config.project}"

    sm = SessionManager(session_name, socket_name)
    if not sm.session_exists():
        click.echo(f"[ERROR] Session '{session_name}' not found", err=True)
        ctx.exit(1)

    click.echo(f"Session: {session_name} (socket: {socket_name})")
    click.echo("")

    for window in sm.list_windows():
        is_mgr = window.startswith("[MGR]")
        marker = " [MGR]" if is_mgr else ""
        click.echo(f"  {window}{marker}")


@session_windows.command("send")
@click.argument("window")
@click.argument("text")
@click.pass_context
def session_windows_send(ctx, window, text):
    """Send keys to a window."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        ctx.exit(1)

    config = load_agency_config(agency_dir)
    session_name = f"agency-{config.project}"
    socket_name = f"agency-{config.project}"

    sm = SessionManager(session_name, socket_name)
    if not sm.session_exists():
        click.echo(f"[ERROR] Session '{session_name}' not found", err=True)
        ctx.exit(1)

    sm.send_keys(window, text)
    click.echo(f"[OK] Sent to {window}: {text}")


@session_windows.command("new")
@click.argument("name")
@click.option("--command", "cmd", default=None, help="Command to run in window")
@click.pass_context
def session_windows_new(ctx, name, cmd):
    """Create a new window."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        ctx.exit(1)

    config = load_agency_config(agency_dir)
    session_name = f"agency-{config.project}"
    socket_name = f"agency-{config.project}"
    work_dir = agency_dir.parent

    result = subprocess.run(
        [
            "tmux",
            "-L",
            socket_name,
            "new-window",
            "-d",
            "-t",
            session_name,
            "-n",
            name,
            "-c",
            str(work_dir),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        click.echo(f"[ERROR] Failed to create window: {result.stderr}", err=True)
        ctx.exit(1)

    if cmd:
        sm = SessionManager(session_name, socket_name)
        sm.send_keys(name, cmd)

    click.echo(f"[OK] Created window: {name}")


@session_windows.command("run")
@click.argument("window")
@click.argument("command")
@click.pass_context
def session_windows_run(ctx, window, command):
    """Run a command in a window."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        ctx.exit(1)

    config = load_agency_config(agency_dir)
    session_name = f"agency-{config.project}"
    socket_name = f"agency-{config.project}"

    sm = SessionManager(session_name, socket_name)
    if not sm.session_exists():
        click.echo(f"[ERROR] Session '{session_name}' not found", err=True)
        ctx.exit(1)

    # Send command with Enter
    sm.send_keys(window, command)
    click.echo(f"[OK] Running in {window}: {command}")


# === Heartbeat Commands ===


@click.group("heartbeat")
def heartbeat_cmd():
    """Heartbeat process management.

    Manages heartbeat processes for manager and agents.
    Heartbeats monitor tasks and notify agents of available work.
    """
    pass


def _get_heartbeat_pid_file(agency_dir: Path, role: str, name: str = "") -> Path:
    """Get the PID file path for a heartbeat process."""
    suffix = f"-{name}" if name else ""
    return agency_dir / "run" / f".heartbeat-{role.lower()}{suffix}.pid"


def _read_heartbeat_pid(pid_file: Path) -> int | None:
    """Read heartbeat PID from file. Returns None if not running."""
    if not pid_file.exists():
        return None
    try:
        pid = int(pid_file.read_text().strip())
        import subprocess

        result = subprocess.run(["ps", "-p", str(pid), "-o", "pid="], capture_output=True)
        if result.returncode == 0:
            return pid
        else:
            pid_file.unlink()
            return None
    except (ValueError, OSError):
        return None


def _write_heartbeat_pid(pid_file: Path, pid: int) -> None:
    """Write heartbeat PID to file."""
    pid_file.write_text(str(pid))


def _kill_heartbeat(pid: int) -> bool:
    """Kill a heartbeat process."""
    import subprocess

    try:
        subprocess.run(["kill", str(pid)], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


@heartbeat_cmd.command("start")
@click.option("--role", type=click.Choice(["manager", "agent"]), default=None, help="Role: manager or agent")
@click.option("--agent", "agent_name", default=None, help="Agent name (required for agent role)")
@click.pass_context
def heartbeat_start(ctx, role, agent_name):
    """Start heartbeat for manager or agent.

    Auto-detects role from AGENCY_ROLE env var if not specified.
    For agent role, --agent is required to specify which agent.
    """
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        ctx.exit(1)

    env_role = os.environ.get("AGENCY_ROLE", "").upper()
    if role:
        role = role.upper()
    elif env_role in ("MANAGER", "AGENT"):
        role = env_role
    else:
        click.echo("[ERROR] Role not specified and AGENCY_ROLE not set", err=True)
        click.echo("[ERROR] Use --role manager or --role agent", err=True)
        ctx.exit(1)

    if role == "AGENT":
        if not agent_name:
            agent_name = os.environ.get("AGENCY_AGENT")
        if not agent_name:
            click.echo("[ERROR] Agent name required for agent role", err=True)
            click.echo("[ERROR] Use --agent <name> or set AGENCY_AGENT", err=True)
            ctx.exit(1)
        pid_file = _get_heartbeat_pid_file(agency_dir, "AGENT", agent_name)
        existing_pid = _read_heartbeat_pid(pid_file)
        if existing_pid:
            click.echo(f"[WARN] Heartbeat already running for agent '{agent_name}' (PID: {existing_pid})", err=True)
            ctx.exit(1)
    else:
        pid_file = _get_heartbeat_pid_file(agency_dir, "MANAGER")
        existing_pid = _read_heartbeat_pid(pid_file)
        if existing_pid:
            click.echo(f"[WARN] Heartbeat already running for manager (PID: {existing_pid})", err=True)
            ctx.exit(1)

    config = load_agency_config(agency_dir)
    project_name = config.project if config else agency_dir.parent.name
    session_name = f"agency-{project_name}"
    socket_name = session_name

    manager_config = load_manager_config(agency_dir)
    poll_interval = 30
    if manager_config and hasattr(manager_config, "poll_interval"):
        poll_interval = manager_config.poll_interval

    heartbeat_env = dict(os.environ)
    heartbeat_env["AGENCY_DIR"] = str(agency_dir)
    heartbeat_env["AGENCY_SOCKET"] = socket_name
    heartbeat_env["AGENCY_ROLE"] = role
    heartbeat_env["AGENCY_POLL_INTERVAL"] = str(poll_interval)

    if role == "MANAGER":
        manager_name = manager_config.name if manager_config else "coordinator"
        heartbeat_env["AGENCY_MANAGER"] = manager_name
        heartbeat_env["PI_INJECTOR_SOCKET"] = str(agency_dir / f"injector-{manager_name}.sock")
        heartbeat_env["PI_STATUS_SOCKET"] = str(agency_dir / f"status-{manager_name}.sock")
    else:
        heartbeat_env["AGENCY_AGENT"] = agent_name
        heartbeat_env["AGENCY_PING_INTERVAL"] = "120"
        heartbeat_env["PI_INJECTOR_SOCKET"] = str(agency_dir / f"injector-{agent_name}.sock")
        heartbeat_env["PI_STATUS_SOCKET"] = str(agency_dir / f"status-{agent_name}.sock")

    heartbeat_module = Path(__file__).parent / "heartbeat.py"
    log_file = agency_dir / "var" / f".heartbeat-{role.lower()}{'-' + agent_name if agent_name else ''}.log"

    with open(log_file, "w") as f:
        proc = subprocess.Popen(
            [sys.executable, "-u", str(heartbeat_module)],
            env=heartbeat_env,
            stdout=f,
            stderr=subprocess.STDOUT,
            cwd=str(agency_dir),
        )

    _write_heartbeat_pid(pid_file, proc.pid)
    role_desc = "manager" if role == "MANAGER" else f"agent '{agent_name}'"
    click.echo(f"[INFO] Started heartbeat for {role_desc} (PID: {proc.pid})")


@heartbeat_cmd.command("stop")
@click.option("--role", type=click.Choice(["manager", "agent"]), default=None, help="Role")
@click.option("--agent", "agent_name", default=None, help="Agent name (for agent role)")
@click.pass_context
def heartbeat_stop(ctx, role, agent_name):
    """Stop heartbeat process."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        ctx.exit(1)

    targets = []
    if agent_name:
        targets.append(("AGENT", agent_name))
    elif role:
        if role.upper() == "MANAGER":
            targets.append(("MANAGER", ""))
        else:
            agents = load_agents_config(agency_dir)
            for a in agents:
                targets.append(("AGENT", a.name))
    else:
        targets.append(("MANAGER", ""))
        agents = load_agents_config(agency_dir)
        for a in agents:
            targets.append(("AGENT", a.name))

    stopped = 0
    for r, name in targets:
        pid_file = _get_heartbeat_pid_file(agency_dir, r, name)
        pid = _read_heartbeat_pid(pid_file)
        if pid:
            if _kill_heartbeat(pid):
                click.echo(f"[OK] Stopped {r.lower()}{'-' + name if name else ''} (PID: {pid})")
                stopped += 1
            else:
                click.echo(f"[ERROR] Failed to kill PID {pid}", err=True)
        else:
            click.echo(f"[INFO] No heartbeat running for {r.lower()}{'-' + name if name else ''}")

    if stopped == 0:
        click.echo("[INFO] No heartbeats stopped")


@heartbeat_cmd.command("status")
@click.pass_context
def heartbeat_status(ctx):
    """Show heartbeat status.

    For agents: shows own heartbeat only.
    For managers or no role: shows all heartbeats.
    """
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        ctx.exit(1)

    role = os.environ.get("AGENCY_ROLE", "").upper()
    agent_name = os.environ.get("AGENCY_AGENT") if role == "AGENT" else None

    click.echo("# Heartbeat Status")
    click.echo("")

    if role == "AGENT" and agent_name:
        # Show only own heartbeat
        pid_file = _get_heartbeat_pid_file(agency_dir, "AGENT", agent_name)
        pid = _read_heartbeat_pid(pid_file)
        if pid:
            click.echo(f"- **Agent**: 🟢 running (PID: {pid})")
        else:
            click.echo("- **Agent**: ⚪ stopped")
    else:
        # Show all
        manager_pid_file = _get_heartbeat_pid_file(agency_dir, "MANAGER")
        manager_pid = _read_heartbeat_pid(manager_pid_file)
        if manager_pid:
            click.echo(f"- **Manager**: 🟢 running (PID: {manager_pid})")
        else:
            click.echo("- **Manager**: ⚪ stopped")

        agents = load_agents_config(agency_dir)
        if agents:
            click.echo("")
            click.echo("## Agents")
            click.echo("")
            for agent in agents:
                pid_file = _get_heartbeat_pid_file(agency_dir, "AGENT", agent.name)
                pid = _read_heartbeat_pid(pid_file)
                if pid:
                    click.echo(f"- **{agent.name}**: 🟢 running (PID: {pid})")
                else:
                    click.echo(f"- **{agent.name}**: ⚪ stopped")
    click.echo("")


@heartbeat_cmd.command("logs")
@click.option("--lines", "-n", default=30, help="Number of lines")
@click.pass_context
def heartbeat_logs(ctx, lines):
    """Show own heartbeat logs."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        ctx.exit(1)

    role = os.environ.get("AGENCY_ROLE", "").upper()
    agent_name = os.environ.get("AGENCY_AGENT") if role == "AGENT" else None

    if role == "AGENT" and agent_name:
        log_file = agency_dir / "var" / f".heartbeat-agent-{agent_name}.log"
    elif role == "MANAGER":
        log_file = agency_dir / "var" / ".heartbeat-manager.log"
    else:
        click.echo("[ERROR] AGENCY_ROLE must be set to MANAGER or AGENT", err=True)
        ctx.exit(1)

    if not log_file.exists():
        click.echo("[ERROR] Log file not found", err=True)
        ctx.exit(1)

    content = log_file.read_text()
    all_lines = content.split("\n")
    last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
    for line in last_lines:
        click.echo(line)


# === Audit Commands ===


@click.group("audit")
def audit_cmd():
    """Audit trail management."""
    pass


@audit_cmd.command("list")
@click.option("--type", "event_type", help="Filter by event type (cli, task, session, agent)")
@click.option("--action", help="Filter by action")
@click.option("--task", help="Filter by task ID")
@click.option("--since", help="Events since timestamp (ISO format)")
@click.option("--until", help="Events until timestamp (ISO format)")
@click.option("--limit", default=50, help="Max events to show")
@click.pass_context
def audit_list(ctx, event_type, action, task, since, until, limit):
    """List audit events."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        ctx.exit(1)

    store = AuditStore(agency_dir)
    events = store.query(
        event_type=event_type,
        action=action,
        task_id=task,
        since=since,
        until=until,
        limit=limit,
    )

    if not events:
        click.echo("No audit events found")
        return

    type_icon = {
        EVENT_CLI: "⌨️",
        EVENT_TASK: "📋",
        EVENT_SESSION: "🖥️",
        EVENT_AGENT: "🤖",
    }

    for event in events:
        icon = type_icon.get(event.event_type, "?")
        ts = event.timestamp or "unknown"
        user = event.os_user or "unknown"
        session = event.agency_session or "-"

        click.echo(f"{icon} [{ts}] {event.event_type}/{event.action}")
        click.echo(f"   user={user} session={session}")

        if event.cli_command:
            click.echo(f"   cli={event.cli_command}")

        if event.task_id:
            click.echo(f"   task={event.task_id}")

        if event.details:
            import json

            details_str = json.dumps(event.details, indent=None)
            if len(details_str) <= 100:
                click.echo(f"   details={details_str}")
            else:
                click.echo(f"   details={details_str[:100]}...")

        click.echo("")


@audit_cmd.command("stats")
@click.pass_context
def audit_stats(ctx):
    """Show audit statistics."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        ctx.exit(1)

    store = AuditStore(agency_dir)
    stats = store.stats()

    click.echo("# Audit Statistics")
    click.echo("")
    click.echo(f"- **Total events**: {stats['total_events']}")
    click.echo(f"- **Last 24 hours**: {stats['last_24h']}")
    click.echo(f"- **First event**: {stats['first_event'] or 'none'}")
    click.echo(f"- **Last event**: {stats['last_event'] or 'none'}")
    click.echo("")

    if stats["by_event_type"]:
        click.echo("## By Event Type")
        click.echo("")
        for etype, count in stats["by_event_type"].items():
            click.echo(f"- {etype}: {count}")
        click.echo("")

    if stats["by_action"]:
        click.echo("## By Action")
        click.echo("")
        for action, count in stats["by_action"].items():
            click.echo(f"- {action}: {count}")
        click.echo("")


@audit_cmd.command("export")
@click.option("--format", "fmt", default="json", type=click.Choice(["json", "csv"]), help="Export format")
@click.option("--output", "-o", help="Output file (default: stdout)")
@click.option("--since", help="Export since timestamp")
@click.option("--until", help="Export until timestamp")
@click.pass_context
def audit_export(ctx, fmt, output, since, until):
    """Export audit events."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        ctx.exit(1)

    store = AuditStore(agency_dir)
    output_content = store.export(format=fmt, since=since, until=until)

    if output:
        Path(output).write_text(output_content)
        click.echo(f"[INFO] Exported to {output}")
    else:
        click.echo(output_content)


@audit_cmd.command("clear")
@click.option("--before", help="Delete events before timestamp")
@click.option("--force", is_flag=True, help="Actually delete events")
@click.pass_context
def audit_clear(ctx, before, force):
    """Clear old audit events."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        ctx.exit(1)

    store = AuditStore(agency_dir)

    if not force:
        # Preview
        if before:
            events = store.query(until=before, limit=100000)
        else:
            events = store.query(until="datetime('now', '-30 days')", limit=100000)

        click.echo(f"[INFO] Would delete {len(events)} events")
        click.echo("[INFO] Use --force to confirm")
        return

    deleted = store.clear(before=before)
    click.echo(f"[INFO] Deleted {deleted} events")


# === Skill Commands ===


@click.group("skill")
def skill_cmd():
    """Skill management commands."""
    pass


def _get_agency_skills_dir() -> Path | None:
    """Find the agency's skills directory.

    Checks:
    1. Current working directory (development mode)
    2. Agency package directory (installed mode)

    Returns:
        Path to .agents/skills/ directory, or None if not found
    """
    # Try current working directory
    skills_dir = Path.cwd() / ".agents" / "skills"
    if skills_dir.exists():
        return skills_dir

    # Try package directory
    package_dir = Path(__file__).parent.parent.parent
    skills_dir = package_dir / ".agents" / "skills"
    if skills_dir.exists():
        return skills_dir

    return None


def _get_skill_source_path(skill_name: str) -> Path | None:
    """Get the source path for a skill.

    Args:
        skill_name: Name of the skill (e.g., 'agency')

    Returns:
        Path to the skill directory, or None if not found
    """
    skills_dir = _get_agency_skills_dir()
    if not skills_dir:
        return None

    skill_path = skills_dir / skill_name
    if skill_path.exists() and skill_path.is_dir():
        return skill_path

    return None


@skill_cmd.command("install")
@click.argument("path", type=click.Path())
@click.option("--force", is_flag=True, help="Overwrite if skill already exists")
def skill_install(path, force):
    """Install an agency skill to the specified path.

    Copies the skill to <path>/.agents/skills/<skill-name>/

    Examples:

        agency skill install ~/.pi/agent/skills/
        agency skill install ~/projects/myproject/
    """
    import shutil

    # Resolve the path
    target_path = resolve_path(path)

    # Find the skill to install (agency by default)
    skill_name = "agency"
    skill_source = _get_skill_source_path(skill_name)

    if not skill_source:
        click.echo("[ERROR] Agency skill not found in package", err=True)
        click.echo("[ERROR] Make sure you're running from the agency repository", err=True)
        sys.exit(1)

    # Target: <path>/.agents/skills/<skill-name>/
    target_skill_dir = target_path / ".agents" / "skills" / skill_name

    if target_skill_dir.exists() and not force:
        click.echo(f"[ERROR] Skill already exists at {target_skill_dir}", err=True)
        click.echo("[ERROR] Use --force to overwrite", err=True)
        sys.exit(1)

    # Create parent directories
    target_skill_dir.mkdir(parents=True, exist_ok=True)

    # Copy skill files
    for item in skill_source.iterdir():
        dest = target_skill_dir / item.name
        if item.is_file():
            shutil.copy2(item, dest)
        elif item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)

    click.echo(f"[INFO] Skill '{skill_name}' installed to {target_skill_dir}")


# Register commands based on AGENCY_ROLE
_agency_role = os.environ.get("AGENCY_ROLE", "").upper()

if _agency_role == "MANAGER":
    # Manager sees: session, tasks, heartbeat, audit (no templates/completions)
    cli.add_command(init_project, name="init")
    cli.add_command(session_cmd)
    cli.add_command(tasks)
    cli.add_command(heartbeat_cmd)
    cli.add_command(audit_cmd)
elif _agency_role == "AGENT":
    # Agent sees: tasks_agent and tasks (limited commands)
    cli.add_command(tasks_agent)
    cli.add_command(tasks)
    cli.add_command(heartbeat_cmd)
else:
    # Default: all commands (no role set)
    cli.add_command(init_project, name="init")
    cli.add_command(list_templates, name="templates")
    cli.add_command(skill_cmd)
    cli.add_command(session_cmd)
    cli.add_command(tasks)
    cli.add_command(completions)
    cli.add_command(heartbeat_cmd)
    cli.add_command(audit_cmd)


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
