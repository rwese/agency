# Agency v2.0 - Just recipes

default: help

# Install
install:
    uv pip install -e .

# Install with dev dependencies
install-dev:
    uv pip install -e ".[dev]"

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
    agency init-project --dir {{dir}}

# Create project with manager
init-project-with-manager dir manager:
    agency init-project --dir {{dir}} --start-manager {{manager}}

# Start agent
start name dir:
    agency start {{name}} --dir {{dir}}

# Start manager
start-manager name dir:
    agency start {{name}} --dir {{dir}}

# Stop session
stop session:
    agency stop {{session}}

# Resume session
resume session:
    agency resume {{session}}

# Attach to session
attach session:
    agency attach {{session}}

# List sessions
list:
    agency list

# Kill all sessions
kill-all:
    agency kill-all

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

# Link pi-status extension to ~/.pi/agent/extensions/
pi-status-link:
    ln -sf {{justfile_directory()}}/extras/pi/extensions/pi-status ~/.pi/agent/extensions/pi-status

# Link no-frills extension to ~/.pi/agent/extensions/
pi-no-frills-link:
    ln -sf {{justfile_directory()}}/extras/pi/extensions/no-frills ~/.pi/agent/extensions/no-frills

# Link all pi extensions
pi-extensions-link: pi-status-link pi-no-frills-link
    @echo "All pi extensions linked"

# Test pi-status CLI
pi-status-test:
    npx tsx extras/pi/extensions/pi-status/src/pi-status-cli.ts status

pi-status-ping:
    npx tsx extras/pi/extensions/pi-status/src/pi-status-cli.ts ping

pi-status-health:
    npx tsx extras/pi/extensions/pi-status/src/pi-status-cli.ts health

# === Development ===

# Test with mock agent
test-mock name dir:
    AGENCY_AGENT_CMD="python3 src/agency/mock_agent.py" \
    uv run agency start {{name}} --dir {{dir}}

# Test mock manager
test-mock-manager name dir:
    AGENCY_AGENT_CMD="python3 src/agency/mock_agent.py" \
    uv run agency start {{name}} --dir {{dir}}

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
    @echo "  install          Install package"
    @echo "  install-dev      Install with dev dependencies"
    @echo "  check            Lint + format + test"
    @echo ""
    @echo "=== Session Management ==="
    @echo "  init-project <dir>                    Create project"
    @echo "  init-project-with-manager <dir> <mgr> Create with manager"
    @echo "  start <name> <dir>                   Start agent"
    @echo "  start-manager <name> <dir>           Start manager"
    @echo "  stop <session>                       Stop session"
    @echo "  resume <session>                     Resume halted session"
    @echo "  attach <session>                     Attach to session"
    @echo "  list                                  List sessions"
    @echo ""
    @echo "=== Heartbeat Management ==="
    @echo "  heartbeat-start                     Start all heartbeats"
    @echo "  heartbeat-start-manager             Start manager heartbeat"
    @echo "  heartbeat-start-agents              Start all agent heartbeats"
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
    @echo "  pi-extensions-link                   Link all extensions"
    @echo "  pi-status-link                       Link pi-status"
    @echo "  pi-no-frills-link                    Link no-frills"
    @echo ""
    @echo "=== Development ==="
    @echo "  test-mock <name> <dir>               Test with mock agent"
    @echo "  test-mock-manager <name> <dir>        Test with mock manager"
    @echo "  completions                           Install shell completions"
    @echo ""
    @echo "=== Utilities ==="
    @echo "  clean                                 Clean artifacts"
    @echo "  reset                                Reset config + cache"
    @echo "  kill-all                             Kill all sessions"
