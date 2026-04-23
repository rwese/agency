# Agency v2.0 - Just recipes

default: help

# Install tool (updates global `agency` command)
install:
    uv tool uninstall agency 2>/dev/null; uv tool install -e .

# Build distribution packages
build:
    rm -rf dist/
    uvx hatch build -t wheel -t sdist

# Install with dev dependencies
install-dev:
    uv tool uninstall agency 2>/dev/null; uv tool install -e ".[dev]"

# Install tool + dev + completions
install-all: install-dev completions

# Test
test:
    ./test_agency.sh

# Pytest
pytest:
    uv run pytest

# Lint
lint:
    uvx ruff check src/

# Format
fmt:
    uvx ruff format src/

# Check (lint + format + test)
check: lint fmt test

# Clean build artifacts
clean:
    rm -rf build/ dist/ *.egg-info/
    rm -rf .venv/ venv/

# Reset config
reset:
    rm -rf ~/.config/agency
    rm -rf ~/.cache/agency/

# === Session Management ===

# Create new project
init-project dir:
    agency init --dir {{dir}}

# Start session
session-start:
    agency session start

# Stop session
session-stop session:
    agency session stop {{session}}

# Resume session
session-resume:
    agency session resume

# Attach to session
session-attach:
    agency session attach

# List sessions
session-list:
    agency session list

# Show session members
session-members:
    agency session members

# Kill session
session-kill session:
    agency session kill {{session}}

# List windows
windows-list:
    agency session windows list

# Create window
windows-new name:
    agency session windows new {{name}}

# === Heartbeat Management ===

# Start heartbeat for manager
heartbeat-start-manager:
    AGENCY_ROLE=manager agency heartbeat start

# Start heartbeat for all agents
heartbeat-start-agents:
    @for agent in backend frontend devops architect security qa; do \
        AGENCY_ROLE=agent AGENCY_AGENT=$$agent agency heartbeat start; \
    done

# Start all heartbeats
heartbeat-start: heartbeat-start-manager heartbeat-start-agents

# Stop all heartbeats
heartbeat-stop:
    agency heartbeat stop

# Show heartbeat status
heartbeat-status:
    agency heartbeat status

# Show own heartbeat logs
heartbeat-logs:
    agency heartbeat logs

# === Task Management ===

# Add task
task-add desc:
    agency tasks add -d "{{desc}}"

# Add task with priority
task-add-priority desc priority:
    agency tasks add -d "{{desc}}" -p {{priority}}

# Assign task
task-assign task-id agent:
    agency tasks assign {{task-id}} {{agent}}

# Complete task
task-complete task-id result:
    agency tasks complete {{task-id}} --result "{{result}}"

# List tasks
tasks:
    agency tasks list

# Show task
task-show task-id:
    agency tasks show {{task-id}}

# Task history
task-history:
    agency tasks history

# Delete task
task-delete task-id:
    agency tasks delete {{task-id}}

# === pi Extensions ===

# Extensions are now copied to .agency/pi/extensions/ during `agency init`
# No manual linking required - agency is self-contained

# Show where extensions are located for current project
pi-extensions-info:
	@AGENCY_DIR="$(find . -name '.agency' -type d 2>/dev/null | head -1)"; \
	if [ -z "$$AGENCY_DIR" ]; then \
		echo "No .agency/ directory found. Run 'agency init' first."; \
	else \
		echo "Project pi extensions:"; \
		ls -la "$$AGENCY_DIR/pi/extensions/" 2>/dev/null || echo "  (not yet initialized - run 'agency init')"; \
	fi

# Test pi-status CLI
pi-status-test:
    npx tsx extras/pi/extensions/pi-status/src/pi-status-cli.ts status

pi-status-ping:
    npx tsx extras/pi/extensions/pi-status/src/pi-status-cli.ts ping

pi-status-health:
    npx tsx extras/pi/extensions/pi-status/src/pi-status-cli.ts health

# === Development ===

# Test with mock agent
test-mock dir:
    AGENCY_AGENT_CMD="python3 src/agency/mock_agent.py" \
    agency session start --dir {{dir}}

# === Shell Completions ===

completions-bash:
    mkdir -p ~/.config/bash_completions 2>/dev/null || true
    agency completions bash > ~/.config/bash_completions/agency

completions-zsh:
    mkdir -p ~/.config/zsh/completions 2>/dev/null || true
    agency completions zsh > ~/.config/zsh/completions/_agency

completions-fish:
    mkdir -p ~/.config/fish/completions 2>/dev/null || true
    agency completions fish > ~/.config/fish/completions/agency.fish

completions: completions-bash completions-zsh completions-fish
    @echo "Completions installed for bash, zsh, and fish"

# === Help ===

help:
    @echo "Agency v2.0 - Just recipes"
    @echo ""
    @echo "=== Installation ==="
    @echo "  install          Install tool (updates global agency)"
    @echo "  install-dev      Install with dev dependencies"
    @echo "  check            Lint + format + test"
    @echo ""
    @echo "=== Session Management ==="
    @echo "  init-project <dir>     Create project"
    @echo "  session-start         Start session"
    @echo "  session-stop <sess>    Stop session"
    @echo "  session-resume        Resume halted session"
    @echo "  session-attach       Attach to session"
    @echo "  session-list          List sessions"
    @echo "  session-members       Show session members"
    @echo "  session-kill <sess>   Kill session"
    @echo "  windows-list          List windows"
    @echo "  windows-new <name>    Create window"
    @echo ""
    @echo "=== Heartbeat Management ==="
    @echo "  heartbeat-start-manager             Start manager heartbeat"
    @echo "  heartbeat-start                     Start all heartbeats"
    @echo "  heartbeat-stop                      Stop all heartbeats"
    @echo "  heartbeat-status                    Show status"
    @echo "  heartbeat-logs                      Show manager logs"
    @echo ""
    @echo "=== Task Management ==="
    @echo "  task-add <desc>                       Add task"
    @echo "  task-assign <id> <agent>             Assign task"
    @echo "  task-complete <id> <result>          Complete task"
    @echo "  tasks                                 List all tasks"
    @echo "  task-show <id>                        Show task"
    @echo "  task-history                          Show history"
    @echo ""
    @echo "=== pi Extensions ==="
    @echo "  pi-extensions-info                   Show project extensions location"
    @echo "  (Extensions auto-copied during agency init)"
    @echo ""
    @echo "=== Development ==="
    @echo "  test-mock <dir>                      Test with mock agent"
    @echo "  completions                           Install shell completions"
    @echo ""
    @echo "=== Utilities ==="
    @echo "  clean                                 Clean artifacts"
    @echo "  reset                                Reset config + cache"
