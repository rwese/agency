"""Agency TUI Application."""

import os
import subprocess
import sys
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.timer import Timer
from textual.widgets import Footer, Header, Input, Static, Log

from agency.tui.widgets.session_list import SessionList, SessionInfo, SessionSelected


# Tmux socket for agency sessions
TMUX_SOCKET = "agency"
SESSION_PREFIX = "agency-"
MANAGER_PREFIX = "agency-manager-"
MESSAGES_FILE = "messages.json"


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


def send_keys(session_name: str, window_name: str, msg: str) -> None:
    """Send keys to a tmux window."""
    tmux("send-keys", "-t", f"{session_name}:{window_name}", msg, "Enter")


def list_available_agents() -> list[str]:
    """List available agent configurations."""
    agents_dir = Path.home() / ".config" / "agency" / "agents"
    if not agents_dir.exists():
        return []
    return sorted([f.stem for f in agents_dir.glob("*.yaml")])


def list_available_managers() -> list[str]:
    """List available manager configurations."""
    managers_dir = Path.home() / ".config" / "agency" / "managers"
    if not managers_dir.exists():
        return []
    return sorted([f.stem for f in managers_dir.glob("*.yaml")])


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


class StartAgent(Message):
    """Message sent when user wants to start an agent."""
    def __init__(self, agent_name: str, work_dir: str) -> None:
        self.agent_name = agent_name
        self.work_dir = work_dir
        super().__init__()


class StopAgent(Message):
    """Message sent when user wants to stop an agent."""
    def __init__(self, session: str, agent: str) -> None:
        self.session = session
        self.agent = agent
        super().__init__()


class AgencyTUI(App):
    """Main TUI application for Agency."""

    CSS = """
    Screen {
        background: $surface;
    }

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
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("j", "cursor_down", "↓"),
        ("k", "cursor_up", "↑"),
        ("enter", "select_session", "Select"),
        ("a", "attach", "Attach"),
        ("s", "focus_input", "Send"),
        ("n", "start_agent", "New Agent"),
        ("x", "stop_agent", "Stop"),
        ("escape", "clear_selection", "Clear"),
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
                with Vertical(id="message-section"):
                    yield Static("Send Message", id="message-section-header")
                    with Horizontal(id="message-input-row"):
                        yield Input(placeholder="Type a message...", id="message-input")
                        yield Static("[Enter] send", id="send-hint")
                with Vertical(id="activity-log-section"):
                    yield Static("Activity Log", id="activity-header")
                    yield Log(id="activity-log", highlight=False)
                yield Static("[a]ttach  [s]end  [n]ew  [x]stop  [j/k] navigate  [?] help  [q]uit", id="actions-bar")
        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted."""
        self.title = "Agency TUI"
        self.sub_title = "AI Agent Session Manager"

        # Start auto-refresh timer (every 2 seconds)
        self._refresh_timer = self.set_interval(2.0, self.refresh_sessions)

        # Initial load
        self.refresh_sessions()
        self.query_one(SessionList).focus()

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

    def action_start_agent(self) -> None:
        """Show agent selection dialog."""
        agents = list_available_agents()
        if not agents:
            log = self.query_one("#activity-log", Log)
            log.write_line("[red]No agent configs found. Run 'agency init' first.[/red]")
            return

        # For now, use the first agent with current directory
        # In a full implementation, show a dialog
        agent_name = agents[0]
        work_dir = os.getcwd()
        
        log = self.query_one("#activity-log", Log)
        log.write_line(f"[cyan]Starting agent '{agent_name}' in {work_dir}...[/cyan]")
        self.post_message(StartAgent(agent_name, work_dir))

    def action_stop_agent(self) -> None:
        """Stop the selected agent."""
        if not self._selected_session:
            log = self.query_one("#activity-log", Log)
            log.write_line("[yellow]No session selected[/yellow]")
            return

        if not self._selected_session.windows:
            log = self.query_one("#activity-log", Log)
            log.write_line("[yellow]No agents in session[/yellow]")
            return

        # For now, stop the first agent
        agent = self._selected_session.windows[0]
        log = self.query_one("#activity-log", Log)
        log.write_line(f"[cyan]Stopping agent '{agent}'...[/cyan]")
        self.post_message(StopAgent(self._selected_session.name, agent))

    def action_toggle_help(self) -> None:
        """Toggle help panel."""
        log = self.query_one("#activity-log", Log)
        help_text = """
[b]Keyboard Shortcuts:[/b]

[b]Navigation[/b]
  ↑/k   Move up
  ↓/j   Move down
  Enter Select session
  Esc   Clear selection

[b]Actions[/b]
  a     Attach to selected session
  s     Focus message input
  n     Start new agent
  x     Stop selected agent
  r     Refresh sessions
  ?     Show this help
  q     Quit
"""
        log.write_line(help_text)

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

    def on_send_message(self, event: SendMessage) -> None:
        """Handle message send request."""
        from datetime import datetime

        # Save to message log
        save_message(
            session=event.session,
            agent=event.agent,
            content=event.message,
            direction="out",
            timestamp=datetime.now().isoformat(),
        )

        # Send to tmux if target specified
        if event.agent:
            send_keys(event.session, event.agent, event.message)

    def on_attach_session(self, event: AttachSession) -> None:
        """Handle attach request."""
        # Detach from TUI and attach to tmux session
        os.execvp("tmux", ["tmux", "-L", TMUX_SOCKET, "attach-session", "-t", event.session])

    def on_start_agent(self, event: StartAgent) -> None:
        """Handle start agent request."""
        from agency.tui.commands import start_agent
        try:
            result = start_agent(event.agent_name, event.work_dir)
            log = self.query_one("#activity-log", Log)
            log.write_line(f"[green]✓ Started {event.agent_name}[/green]")
            # Refresh to show new agent
            self.refresh_sessions()
        except Exception as e:
            log = self.query_one("#activity-log", Log)
            log.write_line(f"[red]✗ Failed to start: {e}[/red]")

    def on_stop_agent(self, event: StopAgent) -> None:
        """Handle stop agent request."""
        from agency.tui.commands import stop_agent
        try:
            result = stop_agent(event.session, event.agent)
            log = self.query_one("#activity-log", Log)
            log.write_line(f"[green]✓ Stopped {event.agent}[/green]")
            # Refresh to update list
            self.refresh_sessions()
        except Exception as e:
            log = self.query_one("#activity-log", Log)
            log.write_line(f"[red]✗ Failed to stop: {e}[/red]")

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


def load_messages() -> list[dict]:
    """Load messages from JSON file."""
    messages_path = Path.home() / ".config" / "agency" / MESSAGES_FILE
    if not messages_path.exists():
        return []

    import json
    with open(messages_path) as f:
        return json.load(f)


def save_message(session: str, agent: str | None, content: str, direction: str, timestamp: str) -> None:
    """Save a message to the messages log."""
    import json
    messages_path = Path.home() / ".config" / "agency" / MESSAGES_FILE
    messages_path.parent.mkdir(parents=True, exist_ok=True)

    messages = []
    if messages_path.exists():
        with open(messages_path) as f:
            messages = json.load(f)

    messages.append({
        "session": session,
        "agent": agent,
        "content": content,
        "direction": direction,
        "timestamp": timestamp,
    })

    # Keep only last 1000 messages
    if len(messages) > 1000:
        messages = messages[-1000:]

    with open(messages_path, 'w') as f:
        json.dump(messages, f, indent=2)


def run_tui() -> None:
    """Entry point for the TUI."""
    app = AgencyTUI()
    app.run()
