"""
Agency Hire — Manager Generator

Generates manager personality based on project answers.
"""

from pathlib import Path
from typing import Any


def generate_manager_personality(answers: dict[str, Any]) -> str:
    """Generate manager personality based on answers."""

    project_type = answers.get("project_type", "api")
    language = answers.get("language", "python")
    framework = answers.get("framework", "none")
    database = answers.get("database", "none")
    team_size = answers.get("team_size", "solo")
    review = answers.get("review", "mandatory")
    testing = answers.get("testing", "after")
    cicd = answers.get("cicd", "no")

    # Framework display name
    framework_map = {
        "fastapi": "FastAPI",
        "flask": "Flask",
        "django": "Django",
        "gin": "Gin",
        "echo": "Echo",
        "express": "Express.js",
        "next": "Next.js",
    }
    framework_name = framework_map.get(framework, framework.title() if framework != "none" else "None")

    # Database display name
    db_map = {
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
        "sqlite": "SQLite",
        "mongodb": "MongoDB",
        "redis": "Redis",
        "none": "None",
    }
    db_name = db_map.get(database, database.title())

    # Testing approach
    testing_map = {
        "tdd": "Test-Driven Development (write tests first)",
        "after": "Write tests alongside implementation",
        "optional": "Tests are optional",
    }
    testing_approach = testing_map.get(testing, "Write tests alongside implementation")

    # Team description
    team_desc = {
        "solo": "You are working with a single developer agent.",
        "pair": "You are coordinating a pair of agents working together.",
        "team": "You are managing a team of specialized agents.",
    }[team_size]

    # Review description
    review_desc = {
        "mandatory": "All tasks require review and approval before completion.",
        "optional": "Reviews are encouraged but not required.",
        "self": "Agents self-review their work.",
    }[review]

    # Task priorities based on project type
    task_priorities = {
        "api": "1. API endpoints with tests\n2. Data models and schemas\n3. Error handling\n4. Documentation",
        "cli": "1. Command parsing and help\n2. Core functionality\n3. Error handling\n4. Tests",
        "library": "1. Public API design\n2. Core functionality\n3. Documentation\n4. Tests",
        "web": "1. Components and pages\n2. State management\n3. API integration\n4. Tests",
        "fullstack": "1. Database schema\n2. API endpoints\n3. Frontend components\n4. Integration tests",
        "other": "1. Core functionality\n2. Tests\n3. Documentation\n4. Error handling",
    }[project_type]

    # Coordinator approach
    coordinator_style = f"""You are the project coordinator for a {project_type.upper()} project.

## Project Context
- Language: {language.title()}
- Framework: {framework_name}
- Database: {db_name}
- Testing: {testing_approach}
- CI/CD: {"Enabled" if cicd == "yes" else "Not configured"}

## Your Approach
{team_desc}
{review_desc}

## Task Priorities
{task_priorities}

## Key Principles
1. Break work into small, reviewable tasks
2. Ensure tests are written with code
3. Maintain code quality standards
4. Document decisions and architecture

## Available Commands
- `agency tasks list` — See pending tasks
- `agency tasks show <id>` — View task details
- `agency tasks add -s "<subject>" -d "<description>"` — Create task
- `agency tasks assign <id> <agent>` — Assign to agent
- `agency tasks complete <id> --result "<text>"` — Complete task

Start immediately on pending tasks. Do not ask for confirmation."""

    return coordinator_style


def write_manager_config(agency_dir: Path, answers: dict[str, Any]) -> Path:
    """Write manager.yaml configuration."""
    config_path = agency_dir / "manager.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    content = f"""$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/manager.json
name: coordinator
personality: |
{_indent(generate_manager_personality(answers), 4)}

poll_interval: 30
auto_approve: false
"""

    config_path.write_text(content)
    return config_path


def _indent(text: str, spaces: int) -> str:
    """Add leading spaces to each line."""
    prefix = " " * spaces
    return "\n".join(f"{prefix}{line}" if line.strip() else line for line in text.split("\n"))
