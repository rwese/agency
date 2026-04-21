"""Task board widget for displaying tracked tasks."""

from dataclasses import dataclass
from typing import Optional

from textual import on
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static


@dataclass
class TaskInfo:
    """Information about a tracked task."""
    task_id: str
    description: str
    status: str  # pending, in_progress, completed, failed
    assigned_to: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[str] = None

    @property
    def status_icon(self) -> str:
        """Get status icon."""
        icons = {
            "pending": "⏳",
            "in_progress": "🔄",
            "completed": "✅",
            "failed": "❌",
        }
        return icons.get(self.status, "❓")


class TaskSelected(Message):
    """Message sent when a task is selected."""
    def __init__(self, task: TaskInfo) -> None:
        self.task = task
        super().__init__()


class TaskBoard(Widget):
    """Widget displaying tracked tasks."""

    BINDINGS = [
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("enter", "select", "Select"),
    ]

    def __init__(self, id: str | None = None) -> None:
        super().__init__(id=id)
        self.tasks: list[TaskInfo] = []
        self._cursor: int = 0

    def compose(self):
        yield Static("Tasks", id="task-board-header")

    def watch_tasks(self, tasks: list[TaskInfo]) -> None:
        """Update display when tasks change."""
        self.tasks = tasks
        self.refresh()

    def render(self) -> str:
        """Render the task board."""
        if not self.tasks:
            return "No tasks"

        lines = []
        for i, task in enumerate(self.tasks):
            icon = task.status_icon
            desc = task.description[:40] + "..." if len(task.description) > 40 else task.description

            prefix = " > " if i == self._cursor else "   "
            lines.append(f"{prefix}{icon} {task.task_id}: {desc}")
            
            if task.assigned_to:
                lines.append(f"    Assigned: {task.assigned_to}")

        return "\n".join(lines)

    def action_cursor_down(self) -> None:
        """Move cursor down."""
        if self.tasks and self._cursor < len(self.tasks) - 1:
            self._cursor += 1
            self.refresh()

    def action_cursor_up(self) -> None:
        """Move cursor up."""
        if self._cursor > 0:
            self._cursor -= 1
            self.refresh()

    def action_select(self) -> None:
        """Select the current task."""
        if self.tasks and 0 <= self._cursor < len(self.tasks):
            self.post_message(TaskSelected(self.tasks[self._cursor]))
