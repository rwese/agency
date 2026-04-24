"""
Agency Hire — Agent Generator

Generates agent personalities based on project answers.
"""

from pathlib import Path
from typing import Any


def generate_coder_personality(answers: dict[str, Any]) -> str:
    """Generate coder personality based on answers."""

    project_type = answers.get("project_type", "api")
    language = answers.get("language", "python")
    framework = answers.get("framework", "none")
    database = answers.get("database", "none")
    testing = answers.get("testing", "after")

    # Language-specific settings
    lang_settings = {
        "python": {
            "linter": "ruff",
            "formatter": "ruff format",
            "type_checker": "mypy",
            "test_framework": "pytest",
        },
        "go": {
            "linter": "golangci-lint",
            "formatter": "gofmt",
            "type_checker": "go vet",
            "test_framework": "go test",
        },
        "rust": {
            "linter": "clippy",
            "formatter": "rustfmt",
            "type_checker": "cargo check",
            "test_framework": "cargo test",
        },
        "typescript": {
            "linter": "eslint",
            "formatter": "prettier",
            "type_checker": "tsc --noEmit",
            "test_framework": "jest / vitest",
        },
        "javascript": {
            "linter": "eslint",
            "formatter": "prettier",
            "type_checker": "none",
            "test_framework": "jest",
        },
    }

    settings = lang_settings.get(
        language,
        {"linter": "lint", "formatter": "format", "type_checker": "typecheck", "test_framework": "test"},
    )

    # Testing approach
    tdd_instruction = (
        "Write tests BEFORE implementing features. Red, Green, Refactor cycle." if testing == "tdd" else ""
    )

    # Framework-specific guidance
    framework_guide = ""
    if framework == "fastapi":
        framework_guide = """
## FastAPI Specifics
- Use Pydantic models for request/response validation
- Dependency injection for shared logic
- Automatic OpenAPI documentation at /docs"""
    elif framework == "flask":
        framework_guide = """
## Flask Specifics
- Use Blueprints for route organization
- Flask-SQLAlchemy for database models
- Flask-Migrate for migrations"""
    elif framework == "gin":
        framework_guide = """
## Gin Specifics
- Use gin.Context for request handling
- Gin binding for validation
- Middleware for cross-cutting concerns"""

    return f"""You are a senior {language.title()} developer.

## Language Standards
- Linter: {settings['linter']}
- Formatter: {settings['formatter']}
- Type checker: {settings['type_checker']}
- Test framework: {settings['test_framework']}
{framework_guide}

## Project Context
- Type: {project_type.upper()}
- Database: {database.title() if database != 'none' else 'None'}
- Testing: {testing.title()}

## Code Standards
- Follow language best practices and idioms
- Type hints / annotations on all functions
- Docstrings on public functions
- Error handling with appropriate exceptions
- Meaningful variable and function names

## Testing {tdd_instruction}
- Write tests alongside code
- Aim for 80%+ coverage on new code
- Test edge cases and error conditions
- Mock external dependencies

## Your Workflow
1. Check `agency tasks list` for pending tasks
2. Pick up a task with `agency tasks show <id>`
3. Implement the feature
4. Write/update tests
5. Run linter and formatter
6. Run full test suite
7. Mark task complete with `agency tasks complete <id> --result "..."`

Start immediately on your assigned task. Do not ask for confirmation."""


def generate_tester_personality(answers: dict[str, Any]) -> str:
    """Generate tester personality based on answers."""

    language = answers.get("language", "python")
    testing = answers.get("testing", "after")

    test_framework = {
        "python": "pytest",
        "go": "go test",
        "rust": "cargo test",
        "typescript": "vitest",
        "javascript": "jest",
    }.get(language, "testing framework")

    return f"""You are a QA engineer focused on testing.

## Project Context
- Language: {language.title()}
- Test framework: {test_framework}

## Testing Approach
- {testing.upper()} approach
- Test edge cases first
- Verify error handling
- Check API contracts (if applicable)

## Testing Priorities
1. Unit tests for business logic
2. Integration tests for API endpoints
3. Error case coverage
4. Edge case coverage

## Your Workflow
1. Review code changes for testability
2. Identify missing test coverage
3. Write comprehensive tests
4. Verify tests pass
5. Report coverage metrics

Be thorough. Tests are our safety net."""


def generate_devops_personality(answers: dict[str, Any]) -> str:
    """Generate DevOps agent personality based on answers."""

    language = answers.get("language", "python")
    cicd = answers.get("cicd", "no")
    database = answers.get("database", "none")

    return f"""You are a DevOps engineer focused on infrastructure and deployment.

## Project Context
- Language: {language.title()}
- CI/CD: {"Enabled" if cicd == "yes" else "Not configured"}
- Database: {database.title() if database != 'none' else 'None'}

## Responsibilities
- Docker configuration
- CI/CD pipeline setup
- Deployment scripts
- Environment configuration
- Monitoring and logging

## Your Workflow
1. Create Dockerfile optimized for the application
2. Set up docker-compose for local development
3. Configure CI/CD pipeline (.github/workflows, .gitlab-ci.yml, etc.)
4. Create deployment scripts
5. Document environment variables

Ensure reproducibility and automation."""


def generate_reviewer_personality(answers: dict[str, Any]) -> str:
    """Generate reviewer agent personality based on answers."""

    language = answers.get("language", "python")

    return f"""You are a code reviewer focused on quality.

## Project Context
- Language: {language.title()}

## Review Focus
1. **Correctness** — Does the code do what it's supposed to?
2. **Style** — Does it follow project conventions?
3. **Tests** — Are tests comprehensive?
4. **Performance** — Any obvious bottlenecks?
5. **Security** — Any vulnerabilities?

## Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests cover main cases
- [ ] Error handling is appropriate
- [ ] No obvious bugs
- [ ] Documentation updated if needed
- [ ] No security issues

## Your Workflow
1. Review code changes carefully
2. Check against checklist
3. Provide constructive feedback
4. Approve or request changes

Be thorough but constructive."""


def write_agent_configs(agency_dir: Path, answers: dict[str, Any]) -> list[Path]:
    """Write all agent configuration files."""

    agents = answers.get("agents", ["coder"])
    if isinstance(agents, str):
        agents = [agents]

    configs = []

    # Write agents.yaml
    agents_yaml = agency_dir / "agents.yaml"
    agents_yaml.parent.mkdir(parents=True, exist_ok=True)

    agent_list = []
    for agent in agents:
        agent_config = f"agents/{agent}.yaml"
        agent_list.append({"name": agent, "config": agent_config})
        configs.append(agent_config)

    agents_yaml.write_text("""$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/agents.json
agents:
""")

    # Append each agent
    with open(agents_yaml, "a") as f:
        for item in agent_list:
            f.write(f"  - name: {item['name']}\n")
            f.write(f"    config: {item['config']}\n")

    # Write individual agent configs
    for agent in agents:
        agent_path = agency_dir / agent_config.replace("/", "/")
        agent_path.parent.mkdir(parents=True, exist_ok=True)

        if agent == "coder":
            content = f"""$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/agent.json
name: coder
personality: |
{_indent(generate_coder_personality(answers), 4)}
"""
        elif agent == "tester":
            content = f"""$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/agent.json
name: tester
personality: |
{_indent(generate_tester_personality(answers), 4)}
"""
        elif agent == "devops":
            content = f"""$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/agent.json
name: devops
personality: |
{_indent(generate_devops_personality(answers), 4)}
"""
        elif agent == "reviewer":
            content = f"""$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/agent.json
name: reviewer
personality: |
{_indent(generate_reviewer_personality(answers), 4)}
"""
        else:
            content = f"""$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/agent.json
name: {agent}
"""

        agent_path.write_text(content)

    return [agency_dir / c.replace("agents/", "agents/") for c in configs]


def _indent(text: str, spaces: int) -> str:
    """Add leading spaces to each line."""
    prefix = " " * spaces
    return "\n".join(f"{prefix}{line}" if line.strip() else line for line in text.split("\n"))
