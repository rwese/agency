"""Session list widget for the Agency TUI."""

from dataclasses import dataclass
from typing import Optional

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


@dataclass 
class SelectionInfo:
    """Represents current selection state."""
    session_index: int
    agent_index: int  # -1 for session level, 0+ for specific agent
    
    @property
    def is_session_level(self) -> bool:
        return self.agent_index == -1


class SessionSelected(Message):
    """Message sent when a session/agent is selected."""
    def __init__(self, session: SessionInfo, agent: str | None = None) -> None:
        self.session = session
        self.agent = agent  # None = session level, str = specific agent
        super().__init__()


class SessionList(Widget):
    """Widget displaying list of agency sessions with agents."""

    def __init__(self) -> None:
        super().__init__(id="session-list")
        self.sessions: list[SessionInfo] = []
        self._selection = SelectionInfo(0, -1)  # Start at first session, session level
        self._expanded_sessions: set[int] = set()  # Track which sessions are expanded

    def compose(self):
        yield Static("Sessions", id="sidebar-header", classes="sidebar-title")

    def watch_sessions(self, sessions: list[SessionInfo]) -> None:
        """Update display when sessions change."""
        self.sessions = sessions
        # Clamp selection to valid range
        if self._selection.session_index >= len(sessions):
            self._selection.session_index = max(0, len(sessions) - 1)
        self.refresh()

    def expand_session(self) -> None:
        """Expand current session to show agents."""
        if self._selection.session_index < len(self.sessions):
            self._expanded_sessions.add(self._selection.session_index)
            self._selection.agent_index = 0  # Select first agent
            self.refresh()

    def collapse_session(self) -> None:
        """Collapse current session."""
        if self._selection.session_index in self._expanded_sessions:
            self._expanded_sessions.remove(self._selection.session_index)
            self._selection.agent_index = -1
            self.refresh()

    def move_up(self) -> None:
        """Move selection up."""
        if not self.sessions:
            return
        
        if self._selection.agent_index == -1:
            # On session level - go to previous session
            if self._selection.session_index > 0:
                self._selection.session_index -= 1
                # If expanded, go to last agent of previous session
                if self._selection.session_index in self._expanded_sessions:
                    prev_session = self.sessions[self._selection.session_index]
                    self._selection.agent_index = max(0, len(prev_session.windows) - 1)
        else:
            # On agent level
            if self._selection.agent_index > 0:
                self._selection.agent_index -= 1
            else:
                # Go to session level
                self._selection.agent_index = -1
        self.refresh()

    def move_down(self) -> None:
        """Move selection down."""
        if not self.sessions:
            return
        
        session = self.sessions[self._selection.session_index]
        
        if self._selection.agent_index == -1:
            # On session level - expand or go to first agent
            if session.windows:
                self._expanded_sessions.add(self._selection.session_index)
                self._selection.agent_index = 0
            elif self._selection.session_index < len(self.sessions) - 1:
                # Go to next session
                self._selection.session_index += 1
        else:
            # On agent level
            if self._selection.agent_index < len(session.windows) - 1:
                self._selection.agent_index += 1
            else:
                # Go to session level and next session
                self._selection.agent_index = -1
                if self._selection.session_index < len(self.sessions) - 1:
                    self._selection.session_index += 1
                    # Auto-expand next session if it has windows
                    if self.sessions[self._selection.session_index].windows:
                        self._expanded_sessions.add(self._selection.session_index)
                        self._selection.agent_index = 0
        self.refresh()

    # Aliases for dashboard compatibility (called by action bindings)
    def action_cursor_up(self) -> None:
        """Move cursor up (alias for move_up)."""
        self.move_up()

    def action_cursor_down(self) -> None:
        """Move cursor down (alias for move_down)."""
        self.move_down()

    def get_selected_target(self) -> tuple[SessionInfo, str | None]:
        """Get the currently selected session and agent (if any)."""
        if not self.sessions:
            return None, None
        
        session = self.sessions[self._selection.session_index]
        agent = None
        
        if self._selection.agent_index >= 0 and self._selection.agent_index < len(session.windows):
            agent = session.windows[self._selection.agent_index]
        
        return session, agent

    def render(self) -> str:
        """Render the session list."""
        if not self.sessions:
            return "No sessions"

        lines = []
        for i, session in enumerate(self.sessions):
            is_selected = i == self._selection.session_index
            is_expanded = i in self._expanded_sessions
            
            # Session line
            prefix = "▶ " if is_expanded else "▶ " if is_selected and self._selection.agent_index == -1 else "  "
            if is_selected and self._selection.agent_index == -1:
                prefix = "[▶] " 
            else:
                prefix = "    " if is_expanded else "    "
            
            icon = session.status_icon
            lines.append(f"{prefix}{icon} {session.display_name}")
            
            # Agent lines (if expanded)
            if is_expanded:
                for j, window in enumerate(session.windows):
                    is_agent_selected = is_selected and j == self._selection.agent_index
                    agent_prefix = "  → " if is_agent_selected else "    "
                    lines.append(f"{agent_prefix}• {window}")
            
            # "No agents" placeholder
            if is_expanded and not session.windows:
                lines.append("    (no agents)")

        return "\n".join(lines)
