"""Dashboard screen for the Agency TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Static, Log

from agency.tui.widgets.session_list import SessionList, SessionInfo, SessionSelected


class SendMessage(Message):
    """Message sent when user sends a message."""
    def __init__(self, session: str, agent: str | None, message: str) -> None:
        self.session = session
        self.agent = agent
        self.message = message
        super().__init__()


class AttachSession(Message):
    """Message sent when user wants to attach to a session."""
    def __init__(self, session: str) -> None:
        self.session = session
        super().__init__()


class Dashboard(Screen):
    """Main dashboard screen with session list and detail panel."""

    CSS = """
    #sidebar {
        width: 30;
        dock: left;
        background: $panel;
    }

    #sidebar-header {
        dock: top;
        height: 1;
        content-align: center middle;
        background: $accent 20%;
        text-style: bold;
    }

    #main-area {
        width: 100%;
    }

    #detail-header {
        height: 1;
        content-align: center middle;
        background: $accent 10%;
        text-style: bold;
    }

    #session-detail {
        padding: 1;
    }

    #message-section {
        background: $surface;
    }

    #message-input-row {
        height: 3;
        padding: 1;
        background: $panel;
    }

    #send-hint {
        width: 16;
        color: $text-muted;
    }

    #activity-log-section {
        height: 1fr;
    }

    #activity-header {
        dock: top;
        height: 1;
        content-align: center middle;
        background: $accent 10%;
        text-style: bold;
    }

    #actions-bar {
        dock: bottom;
        height: 1;
        content-align: center middle;
        background: $panel;
    }
    """

    BINDINGS = [
        Binding("q", "app.pop_screen", "Close", show=False),
        ("j", "cursor_down", "↓"),
        ("k", "cursor_up", "↑"),
        ("enter", "select_session", "Select"),
        ("a", "attach", "Attach"),
        ("s", "focus_input", "Send"),
        ("escape", "clear_selection", "Clear"),
    ]

    def __init__(self) -> None:
        super().__init__(id="dashboard")
        self._selected_session: SessionInfo | None = None

    def compose(self) -> ComposeResult:
        """Compose the dashboard layout."""
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Static("Sessions", id="sidebar-header")
                yield SessionList()
            with Container(id="main-area"):
                yield Static("Select a session", id="detail-header")
                yield Static("", id="session-detail")
                with Vertical(id="message-section"):
                    yield Static("Send Message", id="message-section-header")
                    with Horizontal(id="message-input-row"):
                        yield Input(placeholder="Type a message...", id="message-input")
                        yield Static("[Enter] send", id="send-hint")
                with Vertical(id="activity-log-section"):
                    yield Static("Activity Log", id="activity-header")
                    yield Log(id="activity-log", highlight=False)
                yield Static("[a]ttach  [s]end  [j/k] navigate  [?] help  [q]uit", id="actions-bar")
        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.refresh_sessions()
        # Focus the session list
        self.query_one(SessionList).focus()

    def refresh_sessions(self) -> None:
        """Refresh the session list."""
        from agency.tui.app import list_agency_sessions
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

    def action_focus_input(self) -> None:
        """Focus the message input."""
        if not self._selected_session:
            log = self.query_one("#activity-log", Log)
            log.write_line("[yellow]No session selected[/yellow]")
            return
        input_widget = self.query_one("#message-input", Input)
        input_widget.focus()

    def action_clear_selection(self) -> None:
        """Clear the current selection."""
        self._selected_session = None
        self.update_session_detail(None)

    def action_attach(self) -> None:
        """Attach to selected session."""
        if not self._selected_session:
            log = self.query_one("#activity-log", Log)
            log.write_line("[yellow]No session selected[/yellow]")
            return

        log = self.query_one("#activity-log", Log)
        log.write_line(f"[green]Attaching to {self._selected_session.display_name}...[/green]")
        self.post_message(AttachSession(self._selected_session.name))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle message input submission."""
        if not self._selected_session:
            return

        message = event.value.strip()
        if not message:
            return

        # Determine target agent
        agent = None
        if self._selected_session.windows:
            agent = self._selected_session.windows[0]

        log = self.query_one("#activity-log", Log)
        log.write_line(f"[cyan]→ {self._selected_session.display_name}: {message}[/cyan]")

        self.post_message(SendMessage(
            session=self._selected_session.name,
            agent=agent,
            message=message,
        ))

        # Clear input
        event.input.value = ""
