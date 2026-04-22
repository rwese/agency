#!/usr/bin/env python3
"""
Agency v2.0 - AI Agent Session Manager

A tmux-based multi-agent orchestration tool.
"""

import os
import subprocess
import sys
from pathlib import Path

import click

from agency import __version__
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
from agency.audit import AuditStore, EVENT_AGENT, EVENT_CLI, EVENT_SESSION, EVENT_TASK
from agency.template import TemplateManager

VERSION = __version__


def _log_cli_command(command: str, **opts):
    """Log a CLI command invocation to audit trail."""
    agency_dir = find_agency_dir()
    if agency_dir:
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
  agency start

  # Task management
  agency tasks add -d "Implement login"
  agency tasks assign task-001 coder
  agency tasks list

  # Session management
  agency list
  agency attach
  agency stop"""


def _get_manager_epilog() -> str:
    """Get epilog with examples for manager/coordinator mode."""
    return """Examples:
  # Coordinator workflow
  agency tasks list
  agency tasks assign task-001 coder
  agency members

  # Monitor sessions
  agency tmux list
  agency stop"""


def _get_agent_epilog() -> str:
    """Get epilog with examples for agent mode."""
    return """Examples:
  # Agent workflow
  agency tasks list
  agency tasks show task-001
  agency tasks update task-001 --status in_progress
  agency tasks complete task-001 --result "Done!"""


@click.group(epilog=(_get_manager_epilog() if os.environ.get("AGENCY_ROLE", "").upper() == "MANAGER" else _get_agent_epilog() if os.environ.get("AGENCY_ROLE", "").upper() == "AGENT" else _get_default_epilog()))
@click.version_option(version=VERSION)
@click.pass_context
def cli(ctx):
    """Agency - AI Agent Session Manager."""
    role = os.environ.get("AGENCY_ROLE", "").upper()
    if role in ("MANAGER", "AGENT"):
        ctx.info_name = f"agency ({role.lower()})"


# === Project Commands ===


@click.command("templates")
@click.option("--repo", default="https://github.com/rwese/agency-templates", help="Template repository URL")
@click.option("--refresh", is_flag=True, help="Bypass cache")
def list_templates(repo, refresh):
    """List available project templates."""
    try:
        import tempfile
        import json

        repo_name = repo.replace("https://github.com/", "")
        api_url = f"https://api.github.com/repos/{repo_name}/contents"

        result = subprocess.run(
            ["curl", "-sL", api_url],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            click.echo("[ERROR] Failed to fetch templates", err=True)
            return

        contents = json.loads(result.stdout)
        templates = [item["name"] for item in contents if item.get("type") == "dir" and not item["name"].startswith(".")]

        if not templates:
            click.echo("No templates found.")
            return

        click.echo("Available templates:\n")
        for template in sorted(templates):
            click.echo(f"  • {template}")

        click.echo(f"\nUse: agency init --template https://github.com/rwese/agency-templates/tree/main/<template>")

    except Exception as e:
        click.echo(f"[ERROR] {e}", err=True)


@click.command()
@click.option("--dir", "dir", type=click.Path(), default=".", help="Project directory (default: current)")
@click.option("--template", help="Template repository URL")
@click.option("--template-subdir", help="Template subdirectory")
@click.option("--force", is_flag=True, help="Overwrite existing")
@click.option("--refresh", is_flag=True, help="Bypass template cache")
@click.option("--no-context", is_flag=True, help="Skip context file discovery")
def init_project(dir, template, template_subdir, force, refresh, no_context):
    """Create a new project with session and .agency/ directory.

    Creates .agency/ in the project directory. Use --dir to specify,
    defaults to current directory.

    Optionally discovers and includes agent configuration files like AGENTS.md and CLAUDE.md.
    """
    _log_cli_command("init", dir=dir, template=template, force=force)
    work_dir = Path(dir).expanduser().absolute()

    if not work_dir.exists():
        work_dir.mkdir(parents=True, exist_ok=True)

    # Find git root (optional - for session naming)
    git_root = find_git_root(work_dir)

    # Create .agency/ in work_dir (not git root) unless git_root equals work_dir
    if git_root and git_root != work_dir:
        agency_dir = work_dir / ".agency"
    else:
        agency_dir = work_dir / ".agency"

    # Use work_dir name for session
    project_name = work_dir.name
    session_name = f"agency-{project_name}"
    socket_name = f"agency-{project_name}"
    sm = SessionManager(session_name, socket_name=socket_name)

    if sm.session_exists():
        if force:
            sm.kill_session()
        else:
            click.echo(f"[ERROR] Session '{session_name}' already exists", err=True)
            click.echo("[ERROR] Use --force to overwrite", err=True)
            sys.exit(1)

    # Discover context files if not skipped
    additional_context_files: list[str] = []
    if not no_context:
        additional_context_files = _prompt_context_files(work_dir, project_name)

    # Determine template to use
    # If template is a simple name (e.g., 'fullstack-ts'), use agency-templates repo
    template_name = template or ""
    
    # Resolve template URL and subdir
    if template_name and "/" not in template_name and "github.com" not in template_name:
        # Simple template name - use agency-templates repo
        tm = TemplateManager("https://github.com/rwese/agency-templates", cache_dir=Path.home() / ".cache" / "agency" / "templates")
        template_path = tm.get_template(template_name, refresh=refresh)
    elif template_name:
        # Full URL or path
        tm = TemplateManager(template_name, cache_dir=Path.home() / ".cache" / "agency" / "templates")
        template_path = tm.get_template(template_subdir or "", refresh=refresh)
    else:
        template_path = None
    
    if template_path:
        click.echo(f"[INFO] Using template: {template_path}")
        _copy_template_to_agency(template_path, agency_dir)
    else:
        click.echo("[INFO] Creating default .agency/ structure")
        _create_default_agency_structure(agency_dir, additional_context_files)

    # Create tmux session with socket
    create_project_session(session_name, socket_name, work_dir)

    click.echo(f"[INFO] Created project session: {session_name}")
    click.echo(f"[INFO] .agency/ created at: {agency_dir}")
    if additional_context_files:
        click.echo(f"[INFO] Added {len(additional_context_files)} context files")
    click.echo("[INFO] Run 'agency start' to start agents")


def _prompt_context_files(work_dir: Path, project_name: str) -> list[str]:
    """Prompt user to select agent context files to include.

    Discovers available files and asks user which to include.

    Args:
        work_dir: Project working directory
        project_name: Project name for discovery lookups

    Returns:
        List of selected file paths
    """
    discovered = discover_agent_files(project_name)

    # Build list of available files with descriptions
    available: list[tuple[str, str, Path]] = []
    file_types = [
        ("AGENTS.md", "Universal agent config (Claude, Cursor, Copilot)"),
        ("CLAUDE.md", "Claude Code memory file"),
        ("CLAUDE.local.md", "Personal project preferences (git-ignored)"),
    ]

    for file_type, description in file_types:
        path = discovered.get(file_type)
        if path and path.exists():
            available.append((file_type, description, path))

    if not available:
        click.echo("[INFO] No agent context files discovered")
        return []

    click.echo("\n[?] Discovered agent context files:")
    click.echo("")
    for i, (file_type, description, path) in enumerate(available, 1):
        click.echo(f"  {i}. {file_type}")
        click.echo(f"     {description}")
        click.echo(f"     → {path}")
        click.echo("")

    click.echo("Select files to include (comma-separated or 'none'): ", nl=False)

    try:
        response = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        click.echo("")
        return []

    if response in ("none", "n", ""):
        return []

    selected: list[str] = []
    for part in response.replace(" ", "").split(","):
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(available):
                selected.append(str(available[idx][2]))
        elif part in ("all", "a"):
            selected = [str(p) for _, _, p in available]
            break

    # Also check for CLAUDE.local.md in project root
    claude_local = work_dir / "CLAUDE.local.md"
    if claude_local.exists() and str(claude_local) not in selected:
        click.echo(f"\n[?] Include CLAUDE.local.md from project root? ({claude_local})")
        click.echo("    (y/N): ", nl=False)
        try:
            response = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            response = "n"
        if response in ("y", "yes"):
            selected.append(str(claude_local))

    return selected


def _fix_yaml_multiline_blocks(content: str) -> str:
    """Fix YAML multiline block syntax issues.
    
    The issue: In YAML literal blocks (|), blank lines end the block.
    After a blank line, ALL lines must be indented until the next top-level key.
    
    Properly indents markdown headers (## Title) and list items (- item).
    """
    import re
    
    lines = content.split('\n')
    fixed_lines = []
    in_block = False
    block_indent = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Detect start of literal block (key: |)
        if re.match(r'^\s*\w+: \|$', line):
            in_block = True
            # Content indent = 2 spaces (for continuation of block)
            block_indent = len(line) - len(line.lstrip()) + 2
            fixed_lines.append(line)
            continue
        
        if in_block:
            if stripped == '':
                # Blank line - add indent to continue block
                fixed_lines.append(' ' * block_indent)
            elif line.startswith(' ' * 2):
                # Already indented - OK
                fixed_lines.append(line)
            elif stripped.startswith('## ') or stripped.startswith('- '):
                # Markdown header or list item - indent it
                fixed_lines.append(' ' * block_indent + stripped)
            elif re.match(r'^\s*\w+:', line):
                # Next top-level key - end block
                in_block = False
                fixed_lines.append(line)
            else:
                # Other content - indent it
                fixed_lines.append(' ' * block_indent + stripped)
        else:
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)


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
                        data = yaml.safe_load(fixed_content)
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
    (agency_dir / "tasks").mkdir(exist_ok=True)
    (agency_dir / "pending").mkdir(exist_ok=True)
    (agency_dir / ".scripts").mkdir(exist_ok=True)

    config_path = agency_dir / "config.yaml"
    if not config_path.exists():
        context_section = ""
        if additional_context_files:
            files_yaml = "\n".join(f"  - {f}" for f in additional_context_files)
            context_section = f"\nadditional_context_files:\n{files_yaml}"
        config_path.write_text(
            f"""project: default
shell: bash
parallel_limit: {DEFAULT_PARALLEL_LIMIT}  # Max parallel tasks across all agents
{context_section}
"""
        )

    agents_path = agency_dir / "agents.yaml"
    if not agents_path.exists():
        agents_path.write_text("agents: []\n")

    readme_path = agency_dir / "README.md"
    if not readme_path.exists():
        readme_path.write_text("# Agency Project\n\nThis project uses Agency for AI agent orchestration.\n")


@click.command()
@click.option(
    "--dir",
    "dir",
    type=click.Path(),
    default=None,
    help="Project directory (auto-detected from .agency/)",
)
def start(dir):
    """Start the agency (manager + all agents).

    Auto-detects project directory from .agency/ if not specified.
    """
    _log_cli_command("start", dir=dir)
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

    # Start all members
    _start_all_members(session_name, socket_name, agency_dir, work_dir, sm)


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


def _get_manager_name(agency_dir: Path) -> str | None:
    """Get manager name from agency config."""
    return None


@click.command()
@click.argument("session", required=False)
@click.option("--timeout", type=int, help="Grace period in seconds (default: 300)")
@click.option("--force", is_flag=True, help="Force kill without graceful shutdown")
@click.option("--idle", type=int, default=10, help="Seconds of inactivity before killing windows (default: 10)")
def stop(session, timeout, force, idle):
    """Stop a session gracefully.
    
    Waits for windows to become idle (no output for --idle seconds) then kills them.
    Falls back to force kill after --timeout seconds total.
    
    Auto-detects session from .agency/ if not specified.
    """
    _log_cli_command("stop", session=session, timeout=timeout, force=force, idle=idle)
    # Auto-detect from .agency/ if session not provided
    if not session:
        agency_dir_path = find_agency_dir()
        if not agency_dir_path:
            click.echo("[ERROR] No .agency/ found", err=True)
            click.echo("[ERROR] Use 'agency stop <session>' or run from project directory", err=True)
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

    # Broadcast shutdown to all windows
    sm.broadcast_shutdown()

    # Wait for idle with graceful kill of idle windows
    import time

    timeout = timeout or 300  # 5 minutes default
    idle_check_interval = 2  # Check idle status every 2 seconds
    idle_target = idle  # Seconds of inactivity to consider idle

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
        windows = sm.list_windows()
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


@click.command()
@click.argument("session", required=False)
def kill(session):
    """Force kill a session immediately.

    Auto-detects session from .agency/ if not specified.
    """
    _log_cli_command("kill", session=session)
    # Auto-detect from .agency/ if session not provided
    if not session:
        agency_dir_path = find_agency_dir()
        if not agency_dir_path:
            click.echo("[ERROR] No .agency/ found", err=True)
            click.echo("[ERROR] Use 'agency kill <session>' or run from project directory", err=True)
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


@click.command()
@click.option(
    "--dir",
    "dir",
    type=click.Path(),
    default=None,
    help="Project directory (auto-detected from .agency/)",
)
def resume(dir):
    """Resume a halted session.

    Auto-detects session from .agency/ if not specified.
    """
    _log_cli_command("resume", dir=dir)
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
    halted_file = agency_dir / ".halted"

    if not halted_file.exists():
        click.echo("[WARN] No halt marker found. Session may not be halted.", err=True)

    project_name = work_dir.name
    session_name = f"agency-{project_name}"
    socket_name = session_name

    from agency.session import resume_halted_session

    if resume_halted_session(session_name, socket_name, agency_dir, work_dir):
        click.echo(f"[INFO] Resumed session: {session_name}")
    else:
        click.echo("[ERROR] Failed to resume session", err=True)
        sys.exit(1)


def _find_work_dir_for_session(session_name: str) -> Path | None:
    """Find the working directory for a session."""
    # TODO: Implement session registry
    return None


@click.command()
@click.option(
    "--dir",
    "dir",
    type=click.Path(),
    default=None,
    help="Project directory (auto-detected from .agency/)",
)
def attach(dir):
    """Attach to the project session.

    Auto-detects session from .agency/ directory.
    """
    _log_cli_command("attach", dir=dir)
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


@click.command()
@click.option(
    "--dir",
    "dir",
    type=click.Path(),
    default=None,
    help="Project directory (auto-detected from .agency/)",
)
def list(dir):
    """List agency sessions.

    Shows sessions from current project or all agency sessions.
    """
    _log_cli_command("list", dir=dir)
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


@click.command()
@click.option(
    "--dir",
    "dir",
    type=click.Path(),
    default=None,
    help="Project directory (auto-detected from .agency/)",
)
def members(dir):
    """Show all configured members (manager and agents)."""
    _log_cli_command("members", dir=dir)
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
@click.option("--include-blocked", is_flag=True, help="Include tasks blocked by dependencies (default: excluded for agents, included for managers)")
def tasks_list(status, assignee, include_blocked):
    """List tasks assigned to current agent (when AGENCY_AGENT is set), otherwise all tasks.
    
    Agents only see tasks that are not blocked by dependencies.
    Managers see all tasks by default unless --include-blocked is used.
    """
    # Auto-filter to current agent's tasks when running as an agent
    if not assignee and os.environ.get("AGENCY_AGENT"):
        assignee = os.environ["AGENCY_AGENT"]

    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        click.echo("[ERROR] Run 'agency init-project --dir <path>' first", err=True)
        sys.exit(1)

    # Agents always see only unblocked tasks
    is_agent = bool(os.environ.get("AGENCY_AGENT"))
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
            click.echo(f"- **Blocked by**: None ✅")
    else:
        click.echo(f"- **Depends on**: None")

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
    """List tasks assigned to you."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        sys.exit(1)
    agent = _get_agent_name()
    _list_tasks(agency_dir, status=None, assignee=agent)


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


# === Tmux Commands ===


@click.group("tmux")
def tmux_cmd():
    """Tmux session operations via agency config."""
    pass


@tmux_cmd.command("list")
@click.pass_context
def tmux_list(ctx):
    """List windows in the agency session."""
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


@tmux_cmd.command("send")
@click.argument("window")
@click.argument("text")
@click.pass_context
def tmux_send(ctx, window, text):
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


@tmux_cmd.command("new")
@click.argument("name")
@click.option("--command", "cmd", default=None, help="Command to run in window")
@click.pass_context
def tmux_new(ctx, name, cmd):
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


@tmux_cmd.command("attach")
@click.pass_context
def tmux_attach(ctx):
    """Attach to the agency session (opens new terminal)."""
    agency_dir = find_agency_dir()
    if not agency_dir:
        click.echo("[ERROR] No .agency/ found", err=True)
        ctx.exit(1)

    config = load_agency_config(agency_dir)
    session_name = f"agency-{config.project}"
    socket_name = f"agency-{config.project}"

    # Detach any existing clients first
    subprocess.run(
        ["tmux", "-L", socket_name, "detach", "-s", session_name],
        capture_output=True,
    )

    # Launch terminal with attach
    os.execlp("tmux", "tmux", "-L", socket_name, "attach", "-t", session_name)


@tmux_cmd.command("run")
@click.argument("window")
@click.argument("command")
@click.pass_context
def tmux_run(ctx, window, command):
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


# Register commands based on AGENCY_ROLE
_agency_role = os.environ.get("AGENCY_ROLE", "").upper()

if _agency_role == "MANAGER":
    # Manager sees: all commands except templates and completions
    cli.add_command(init_project, name="init")
    cli.add_command(start)
    cli.add_command(stop)
    cli.add_command(kill)
    cli.add_command(resume)
    cli.add_command(attach)
    cli.add_command(list)
    cli.add_command(members)
    cli.add_command(tasks)
    cli.add_command(tmux_cmd)
    cli.add_command(audit_cmd)
elif _agency_role == "AGENT":
    # Agent sees: tasks_agent and tasks (limited commands)
    cli.add_command(tasks_agent)
    cli.add_command(tasks)
else:
    # Default: all commands
    cli.add_command(init_project, name="init")
    cli.add_command(list_templates, name="templates")
    cli.add_command(start)
    cli.add_command(stop)
    cli.add_command(kill)
    cli.add_command(resume)
    cli.add_command(attach)
    cli.add_command(list)
    cli.add_command(members)
    cli.add_command(tasks)
    cli.add_command(completions)
    cli.add_command(tmux_cmd)
    cli.add_command(audit_cmd)


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
