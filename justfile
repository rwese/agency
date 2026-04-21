# Agency - Just recipes

default: help

# Install
install:
    uv pip install -e .
    @mkdir -p ~/.local/bin
    @ln -sf {{justfile_directory()}}/.venv/bin/agency ~/.local/bin/agency
    @echo "Installed: ~/.local/bin/agency"

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

# Clean build artifacts
clean:
    rm -rf build/ dist/ *.egg-info/
    rm -rf .venv/ venv/

# Reset config
reset:
    rm -rf ~/.config/agency
    agency init

# Test mock agent
test-mock name dir:
    AGENCY_AGENT_CMD="python3 src/agency/mock_agent.py" uv run agency start {{name}} --dir {{dir}}

# Test mock manager
test-mock-manager name dir:
    AGENCY_AGENT_CMD="python3 src/agency/mock_agent.py" uv run agency start-manager {{name}} --dir {{dir}}

# Attach to session
attach session:
    agency attach {{session}}

# Attach to manager
attach-manager name:
    agency attach-manager {{name}}

# Start agent
start name dir:
    agency start {{name}} --dir {{dir}}

# Start manager
start-manager name dir:
    agency start-manager {{name}} --dir {{dir}}

# List sessions
list:
    agency list

help:
    @echo "Agency - Just recipes"
    @echo ""
    @echo "  install              Install package"
    @echo "  install-dev          Install with dev dependencies"
    @echo "  test                 Run integration tests"
    @echo "  pytest               Run pytest"
    @echo "  lint                 Run ruff"
    @echo "  fmt                  Format code"
    @echo "  clean                Clean build artifacts"
    @echo "  reset                Reset config"
    @echo "  test-mock            Test with mock agent"
    @echo "  test-mock-manager    Test with mock manager"
    @echo "  attach               Attach to session"
    @echo "  attach-manager       Attach to manager"
    @echo "  start                Start agent"
    @echo "  start-manager        Start manager"
    @echo "  list                 List sessions"
    @echo "  completions-bash     Install bash completions"
    @echo "  completions-zsh      Install zsh completions"
    @echo "  completions-fish     Install fish completions"
    @echo "  completions          Install all completions"

# Shell completions
completions-bash:
    mkdir -p ~/.config/fish/completions 2>/dev/null || true
    cp completions/bash ~/.config/bash_completions/agency 2>/dev/null || \
    cp completions/bash /usr/local/etc/bash_completion.d/agency

completions-zsh:
    mkdir -p ~/.config/zsh/completions 2>/dev/null || true
    cp completions/zsh ~/.config/zsh/completions/_agency

completions-fish:
    mkdir -p ~/.config/fish/completions 2>/dev/null || true
    cp completions/fish ~/.config/fish/completions/agency.fish

completions: completions-bash completions-zsh completions-fish
    @echo "Completions installed for bash, zsh, and fish"
