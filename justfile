# Agency - Just recipes

# Default recipe
default: help

# Install the package
install:
    uv pip install -e .

# Install with dev dependencies
install-dev:
    uv pip install -e ".[dev]"

# Run tests
test:
    ./test_agency.sh

# Run tests with pytest
pytest:
    uv run pytest

# Format code (if black is installed)
fmt:
    uv run black src/

# Lint code (if ruff is installed)
lint:
    uv run ruff check src/

# Clean build artifacts
clean:
    rm -rf build/ dist/ *.egg-info/
    rm -rf .venv/ venv/

# Reset config (clears all agency state)
reset:
    rm -rf ~/.config/agency
    agency init

# Attach to a session
attach session:
    agency attach {{session}}

# Attach to a manager
attach-manager name:
    agency attach-manager {{name}}

# Start an agent
start name dir:
    agency start {{name}} --dir {{dir}}

# Start a manager
start-manager name dir:
    agency start-manager {{name}} --dir {{dir}}

# List all sessions
list:
    agency list

# Show this help
help:
    @echo "Agency - Just recipes"
    @echo ""
    @echo "  install        Install package"
    @echo "  install-dev   Install with dev dependencies"
    @echo "  test          Run integration tests"
    @echo "  pytest        Run pytest"
    @echo "  fmt           Format code"
    @echo "  lint          Lint code"
    @echo "  clean         Clean build artifacts"
    @echo "  reset         Reset config"
    @echo "  attach        Attach to session"
    @echo "  attach-manager Attach to manager"
    @echo "  start         Start agent"
    @echo "  start-manager Start manager"
    @echo "  list          List sessions"
