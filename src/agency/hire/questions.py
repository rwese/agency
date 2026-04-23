"""
Agency Hire — Interview Questions

Defines the questions asked during the agency hiring process.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class Question:
    """A single interview question."""

    key: str
    prompt: str
    options: list[str] | None = None
    default: str | None = None
    required: bool = True


# Project type options
PROJECT_TYPES = Literal["api", "cli", "library", "web", "fullstack", "other"]

# Language options
LANGUAGES = Literal["python", "go", "rust", "typescript", "javascript", "java", "csharp", "other"]

# Team size options
TEAM_SIZES = Literal["solo", "pair", "team"]

# Review options
REVIEW_OPTIONS = Literal["mandatory", "optional", "self"]

# Test options
TEST_OPTIONS = Literal["tdd", "after", "optional"]

# Database options
DATABASES = Literal["postgresql", "mysql", "sqlite", "mongodb", "redis", "none"]


@dataclass
class QuestionGroup:
    """Group of related questions."""

    title: str
    icon: str
    questions: list[Question]


# Interview phases
PROJECT_PROFILE = QuestionGroup(
    title="Project Profile",
    icon="📋",
    questions=[
        Question(
            key="project_type",
            prompt="What type of project is this?",
            options=["api", "cli", "library", "web", "fullstack", "other"],
            default="api",
        ),
        Question(
            key="language",
            prompt="Primary programming language?",
            options=["python", "go", "rust", "typescript", "javascript", "java", "other"],
            required=True,
        ),
        Question(
            key="framework",
            prompt="Framework (if any)?",
            options=["none", "fastapi", "flask", "django", "gin", "echo", "express", "next", "other"],
            default="none",
        ),
        Question(
            key="database",
            prompt="Database?",
            options=["none", "postgresql", "mysql", "sqlite", "mongodb", "redis"],
            default="none",
        ),
    ],
)

TEAM_SETUP = QuestionGroup(
    title="Team Setup",
    icon="👥",
    questions=[
        Question(
            key="team_size",
            prompt="Team size?",
            options=["solo", "pair", "team"],
            default="solo",
        ),
        Question(
            key="agents",
            prompt="Which agents do you need?",
            options=["coder", "tester", "devops", "reviewer"],
            default=["coder"],
        ),
    ],
)

WORKFLOW = QuestionGroup(
    title="Workflow",
    icon="⚙️",
    questions=[
        Question(
            key="review",
            prompt="Review process?",
            options=["mandatory", "optional", "self"],
            default="mandatory",
        ),
        Question(
            key="testing",
            prompt="Testing approach?",
            options=["tdd", "after", "optional"],
            default="after",
        ),
        Question(
            key="cicd",
            prompt="CI/CD required?",
            options=["yes", "no"],
            default="no",
        ),
    ],
)

ALL_GROUPS = [PROJECT_PROFILE, TEAM_SETUP, WORKFLOW]


def get_answers_dict() -> dict[str, str | list[str]]:
    """Return empty answers dict template."""
    return {
        "project_type": "",
        "language": "",
        "framework": "",
        "database": "",
        "team_size": "",
        "agents": [],
        "review": "",
        "testing": "",
        "cicd": "",
    }
