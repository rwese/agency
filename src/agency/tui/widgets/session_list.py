"""Session list widget for the Agency TUI."""

from dataclasses import dataclass
from typing import Optional

from textual import on
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static


@dataclass
class SessionInfo:
    """Information about a tmux session."""
    name: str
    is_manager: bool
    windows: list[str]
    dir: Optional[str] = None

    @property
    def display_name(self) -> str:
        """Get display name without prefix."""
        prefix = "agency-manager-" if self.is_manager else "agency-"
        return self.name[len(prefix):]

    @property
    def status_icon(self) -> str:
        """Get status icon based on session type."""
        return "👑" if self.is_manager else "🤖"


class SessionSelected(Message):
    """Message sent when a session is selected."""
    def __init__(self, session: SessionInfo) -> None:
        self.session = session
        super().__init__()


class SessionList(Widget):
    """Widget displaying list of agency sessions."""

    BINDINGS = [
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("enter", "select", "Select"),
    ]

    def __init__(self) -> None:
        super().__init__(id="session-list")
        self.sessions: list[SessionInfo] = []
        self._cursor: int = 0

    def compose(self):
        yield Static("Sessions", id="sidebar-header", classes="sidebar-title")

    def watch_sessions(self, sessions: list[SessionInfo]) -> None:
        """Update display when sessions change."""
        self.sessions = sessions
        self.refresh()

    def render(self) -> str:
        """Render the session list."""
        if not self.sessions:
            return "No sessions"

        lines = []
        for i, session in enumerate(self.sessions):
            icon = session.status_icon
            name = session.display_name
            windows = ", ".join(session.windows) if session.windows else "no windows"

            prefix = " > " if i == self._cursor else "   "
            lines.append(f"{prefix}{icon} {name}")
            lines.append(f"    {windows}")

        return "\n".join(lines)

    def action_cursor_down(self) -> None:
        """Move cursor down."""
        if self.sessions and self._cursor < len(self.sessions) - 1:
            self._cursor += 1
            self.refresh()

    def action_cursor_up(self) -> None:
        """Move cursor up."""
        if self._cursor > 0:
            self._cursor -= 1
            self.refresh()

    def action_select(self) -> None:
        """Select the current session."""
        if self.sessions and 0 <= self._cursor < len(self.sessions):
            self.post_message(SessionSelected(self.sessions[self._cursor]))
