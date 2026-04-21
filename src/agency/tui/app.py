"""Agency TUI Application."""

import os
import subprocess
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding
from textual.message import Message
from textual.timer import Timer
from textual.widgets import Header, Footer, Static, Log

from agency.tui.widgets.session_list import SessionList, SessionInfo, SessionSelected


# Tmux socket for agency sessions
TMUX_SOCKET = "agency"
SESSION_PREFIX = "agency-"
MANAGER_PREFIX = "agency-manager-"


def tmux(*args: str) -> subprocess.CompletedProcess:
    """Run a tmux command with agency socket."""
    result = subprocess.run(
        ["tmux", "-L", TMUX_SOCKET] + list(args),
        capture_output=True,
        text=True,
    )
    return result


def list_agency_sessions() -> list[SessionInfo]:
    """List all agency sessions."""
    result = tmux("list-sessions", "-F", "#S")
    if result.returncode != 0:
        return []

    sessions = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        is_manager = line.startswith(MANAGER_PREFIX)
        if is_manager or line.startswith(SESSION_PREFIX):
            # Get windows for this session
            windows = list_session_windows(line)
            sessions.append(SessionInfo(
                name=line,
                is_manager=is_manager,
                windows=windows,
            ))

    return sessions


def list_session_windows(session_name: str) -> list[str]:
    """List windows in a session."""
    result = tmux("list-windows", "-t", session_name, "-F", "#W")
    if result.returncode != 0:
        return []
    return [w.strip() for w in result.stdout.strip().split("\n") if w.strip() and w.strip() != "zsh"]


def session_exists(session_name: str) -> bool:
    """Check if a session exists."""
    result = tmux("has-session", "-t", session_name)
    return result.returncode == 0


class AgencyTUI(App):
    """Main TUI application for Agency."""

    CSS = """
    Screen {
        background: $surface;
    }

    #sidebar {
        width: 35;
        min-width: 35;
        height: 100%;
        background: $panel;
        border-right: solid $border;
    }

    #sidebar-header {
        dock: top;
        height: 3;
        background: $accent 20%;
        padding: 1 2;
        text-style: bold;
    }

    #main-area {
        width: 100%;
        height: 100%;
    }

    #detail-header {
        height: 3;
        background: $accent 10%;
        padding: 1 2;
        text-style: bold;
    }

    #session-detail {
        height: auto;
        padding: 1 2;
        background: $surface;
    }

    #message-log {
        height: 1fr;
        border-top: solid $border;
    }

    #message-log-header {
        dock: top;
        height: 3;
        background: $accent 10%;
        padding: 1 2;
        text-style: bold;
    }

    #actions {
        dock: bottom;
        height: 3;
        background: $panel;
        padding: 1 2;
    }

    .session-item {
        padding: 1 2;
    }

    .session-item:hover {
        background: $accent 20%;
    }

    .session-item:focus {
        background: $accent 40%;
    }

    #help-panel {
        width: 60;
        height: auto;
        background: $panel;
        border: solid $accent;
        padding: 2;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("j", "cursor_down", "↓"),
        ("k", "cursor_up", "↑"),
        ("enter", "select_session", "Select"),
        ("a", "attach", "Attach"),
        ("s", "send_message", "Send"),
        ("?", "toggle_help", "Help"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._refresh_timer: Timer | None = None
        self._selected_session: SessionInfo | None = None

    def compose(self) -> ComposeResult:
        """Compose the TUI layout."""
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Static("Sessions", id="sidebar-header")
                yield SessionList()
            with Container(id="main-area"):
                yield Static("Select a session", id="detail-header")
                yield Static("", id="session-detail")
                with Vertical(id="message-log"):
                    yield Static("Activity Log", id="message-log-header")
                    yield Log(id="activity-log", highlight=False)
                yield Static("[b]a[/b]ttach  [b]s[/b]end  [b]?[/b] help", id="actions")
        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted."""
        self.title = "Agency TUI"
        self.sub_title = "AI Agent Session Manager"

        # Start auto-refresh timer (every 2 seconds)
        self._refresh_timer = self.set_interval(2.0, self.refresh_sessions)

        # Initial load
        self.refresh_sessions()

    def on_unmount(self) -> None:
        """Called when app is unmounted."""
        if self._refresh_timer:
            self._refresh_timer.stop()

    def refresh_sessions(self) -> None:
        """Refresh the session list."""
        sessions = list_agency_sessions()
        session_list = self.query_one(SessionList)
        session_list.watch_sessions(sessions)

        # Update detail if session still exists
        if self._selected_session:
            updated = next((s for s in sessions if s.name == self._selected_session.name), None)
            if updated:
                self._selected_session = updated
                self.update_session_detail(updated)
            else:
                self._selected_session = None
                self.update_session_detail(None)

    def update_session_detail(self, session: SessionInfo | None) -> None:
        """Update the session detail panel."""
        header = self.query_one("#detail-header", Static)
        detail = self.query_one("#session-detail", Static)

        if session is None:
            header.update("Select a session")
            detail.update("")
            return

        icon = "👑" if session.is_manager else "🤖"
        header.update(f"{icon} {session.display_name}")

        lines = [
            f"Session: {session.name}",
            f"Type: {'Manager' if session.is_manager else 'Project'}",
            f"Windows: {len(session.windows)}",
        ]
        if session.windows:
            lines.append("")
            lines.append("Agents:")
            for win in session.windows:
                lines.append(f"  • {win}")

        detail.update("\n".join(lines))

    def on_session_selected(self, event: SessionSelected) -> None:
        """Handle session selection."""
        self._selected_session = event.session
        self.update_session_detail(event.session)

    def action_refresh(self) -> None:
        """Refresh session list."""
        self.refresh_sessions()
        log = self.query_one("#activity-log", TextLog)
        log.write_line("[dim]Sessions refreshed[/dim]")

    def action_cursor_down(self) -> None:
        """Move cursor down in session list."""
        session_list = self.query_one(SessionList)
        session_list.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up in session list."""
        session_list = self.query_one(SessionList)
        session_list.action_cursor_up()

    def action_select_session(self) -> None:
        """Select the current session."""
        session_list = self.query_one(SessionList)
        if session_list.sessions and 0 <= session_list._cursor < len(session_list.sessions):
            session = session_list.sessions[session_list._cursor]
            self._selected_session = session
            self.update_session_detail(session)

    def action_toggle_help(self) -> None:
        """Toggle help panel."""
        log = self.query_one("#activity-log", TextLog)
        help_text = """
[b]Keyboard Shortcuts:[/b]

[b]Navigation[/b]
  ↑/k   Move up
  ↓/j   Move down
  Enter Select session

[b]Actions[/b]
  a     Attach to selected session
  s     Send message to agent
  r     Refresh sessions
  ?     Show this help
  q     Quit
"""
        log.write_line(help_text)

    def action_attach(self) -> None:
        """Attach to selected session in tmux."""
        if not self._selected_session:
            self.notify("No session selected", severity="warning")
            return

        self.exit(self._selected_session.name)

    def action_send_message(self) -> None:
        """Open message input."""
        if not self._selected_session:
            self.notify("No session selected", severity="warning")
            return

        log = self.query_one("#activity-log", TextLog)
        log.write_line(f"[yellow]Send message to {self._selected_session.display_name}...[/yellow]")
        log.write_line("[dim]Use 'agency send' CLI for now[/dim]")

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


def run_tui() -> None:
    """Entry point for the TUI."""
    app = AgencyTUI()
    result = app.run()
    if result:
        print(result)
