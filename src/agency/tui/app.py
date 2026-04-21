"""Agency TUI Application."""

import json
import os
import subprocess
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.timer import Timer
from textual.widgets import Footer, Header, Input, Static, Log
from rich.text import Text

from agency.tui.widgets.task_board import TaskInfo


TMUX_SOCKET = "agency"
SESSION_PREFIX = "agency-"
MANAGER_PREFIX = "agency-manager-"
MESSAGES_FILE = "messages.json"


class Panel(Enum):
    SESSIONS = "sessions"
    TASKS = "tasks"
    MAIN = "main"


@dataclass
class SessionInfo:
    name: str
    is_manager: bool
    windows: list[str]
    dir: Optional[str] = None

    @property
    def display_name(self) -> str:
        prefix = "agency-manager-" if self.is_manager else "agency-"
        return self.name[len(prefix):]

    @property
    def status_icon(self) -> str:
        return "👑" if self.is_manager else "🤖"


def tmux(*args: str) -> subprocess.CompletedProcess:
    result = subprocess.run(
        ["tmux", "-L", TMUX_SOCKET] + list(args),
        capture_output=True, text=True)
    return result


def list_agency_sessions() -> list[SessionInfo]:
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
            sessions.append(SessionInfo(name=line, is_manager=is_manager, windows=windows))
    return sessions


def list_session_windows(session_name: str) -> list[str]:
    result = tmux("list-windows", "-t", session_name, "-F", "#W")
    if result.returncode != 0:
        return []
    return [w.strip() for w in result.stdout.strip().split("\n") if w.strip() and w.strip() != "zsh"]


def send_keys(session_name: str, window_name: str, msg: str) -> None:
    tmux("send-keys", "-t", f"{session_name}:{window_name}", msg, "Enter")


def list_available_agents() -> list[str]:
    agents_dir = Path.home() / ".config" / "agency" / "agents"
    if not agents_dir.exists():
        return []
    return sorted([f.stem for f in agents_dir.glob("*.yaml")])


def list_available_managers() -> list[str]:
    managers_dir = Path.home() / ".config" / "agency" / "managers"
    if not managers_dir.exists():
        return []
    return sorted([f.stem for f in managers_dir.glob("*.yaml")])


def load_tasks() -> list[TaskInfo]:
    import json
    tasks_file = Path.home() / ".config" / "agency" / "sessions" / "tasks.json"
    if not tasks_file.exists():
        return []
    with open(tasks_file) as f:
        data = json.load(f)
    tasks = []
    for tid, tdata in data.items():
        tasks.append(TaskInfo(
            task_id=tdata.get("task_id", tid),
            description=tdata.get("description", ""),
            status=tdata.get("status", "pending"),
            assigned_to=tdata.get("assigned_to"),
            created_at=tdata.get("created_at"),
            completed_at=tdata.get("completed_at"),
            result=tdata.get("result")))
    return tasks


class SendMessage(Message):
    def __init__(self, session: str, agent: str | None, message: str) -> None:
        self.session = session
        self.agent = agent
        self.message = message
        super().__init__()


class AttachSession(Message):
    def __init__(self, session: str, target: str | None = None) -> None:
        self.session = session
        self.target = target
        super().__init__()


class StartAgent(Message):
    def __init__(self, agent_name: str, work_dir: str) -> None:
        self.agent_name = agent_name
        self.work_dir = work_dir
        super().__init__()


class StartManager(Message):
    def __init__(self, manager_name: str, work_dir: str) -> None:
        self.manager_name = manager_name
        self.work_dir = work_dir
        super().__init__()


class StopAgent(Message):
    def __init__(self, session: str, agent: str) -> None:
        self.session = session
        self.agent = agent
        super().__init__()


class AgencyTUI(App):
    CSS = """
    Screen { background: $surface; }
    
    /* Panel styling - compact widths */
    #left-panel { width: 28; dock: left; background: $panel; }
    #main-col { width: 1fr; }
    
    /* Header styling */
    .panel-header { height: 1; padding: 0 1; text-style: bold; }
    #sessions-header { background: $accent 20%; color: $text; }
    #tasks-header { background: $secondary 20%; color: $text; }
    #main-header { background: $success 20%; color: $text; }
    
    /* Active panel indicator */
    .panel-active #sessions-header,
    .panel-active-tasks #tasks-header,
    .panel-active-main #main-header {
        background: $accent 40%;
        text-style: bold;
    }
    
    /* Content areas - compact */
    #sessions-content { padding: 0 1; }
    #tasks-content { padding: 0 1; }
    
    /* Message area */
    #message-row { height: 3; padding: 1 2; background: $panel; }
    #target-label { width: 4; color: $text-muted; }
    #target-display { width: 18; color: $accent; text-style: bold; }
    
    /* Input */
    #message-input { width: 1fr; }
    
    /* Activity log */
    #activity-section { height: 1fr; }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("left", "panel_left", "←"),
        ("right", "panel_right", "→"),
        ("up", "nav_up", "↑"),
        ("down", "nav_down", "↓"),
        ("j", "nav_up", "↑"),
        ("k", "nav_down", "↓"),
        ("enter", "select", "Select"),
        ("a", "attach", "Attach"),
        ("s", "focus_input", "Send"),
        ("n", "start_agent", "New Agent"),
        ("m", "start_manager", "New Manager"),
        ("x", "stop_agent", "Stop"),
        ("c", "create_task", "Create"),
        ("u", "update_task", "Update"),
        ("d", "delete_task", "Delete"),
        ("escape", "clear_selection", "Clear"),
        ("?", "toggle_help", "Help"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._refresh_timer: Timer | None = None
        self._current_panel = Panel.SESSIONS
        self._sessions: list[SessionInfo] = []
        self._selected_session_index = 0
        self._selected_agent_index: int | None = None
        self._tasks: list[TaskInfo] = []
        self._selected_task_index = 0

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="left-panel"):
                yield Static("[S] Sessions", id="sessions-header", classes="panel-header")
                yield Static("", id="sessions-content")
                yield Static("[T] Tasks", id="tasks-header", classes="panel-header")
                yield Static("", id="tasks-content")
            with Vertical(id="main-col"):
                yield Static("[M] Send Message", id="main-header", classes="panel-header")
                with Horizontal(id="message-row"):
                    yield Static("To:", id="target-label")
                    yield Static("-", id="target-display")
                    yield Input(placeholder="Type message...", id="message-input")
                with Vertical(id="activity-section"):
                    yield Static("Activity Log", classes="panel-header")
                    yield Log(id="activity-log")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Agency TUI"
        self.sub_title = "AI Agent Session Manager"
        self._refresh_timer = self.set_interval(2.0, self.refresh_all)
        self.refresh_all()
        self.update_panel_indicators()

    def on_unmount(self) -> None:
        if self._refresh_timer:
            self._refresh_timer.stop()

    def refresh_all(self) -> None:
        self.refresh_sessions()
        self.refresh_tasks()

    def refresh_sessions(self) -> None:
        self._sessions = list_agency_sessions()
        widget = self.query_one("#sessions-content", Static)
        
        is_active = self._current_panel == Panel.SESSIONS
        
        if not self._sessions:
            widget.update("[dim]No sessions[/dim]")
            return
        
        lines = []
        for i, s in enumerate(self._sessions):
            is_selected = i == self._selected_session_index
            icon = s.status_icon
            agents = ", ".join(s.windows) if s.windows else "[dim]no agents[/dim]"
            
            # Session line with simple connector
            if is_selected:
                if is_active:
                    lines.append(f"[bold cyan]▌ {icon} {s.display_name}[/bold cyan]")
                else:
                    lines.append(f"[cyan]▌ {icon} {s.display_name}[/cyan]")
            else:
                lines.append(f"  {icon} {s.display_name}")
            
            # Agents line
            if is_selected:
                lines.append(f"    {agents}")
            else:
                lines.append(f"  [dim]{agents}[/dim]")
            
            # Expand agents if selected
            if is_selected and s.windows:
                for j, agent in enumerate(s.windows):
                    is_agent_selected = j == self._selected_agent_index
                    
                    if is_agent_selected:
                        if is_active:
                            lines.append(f"[bold yellow]▌   └ {agent}[/bold yellow]")
                        else:
                            lines.append(f"[yellow]    └ {agent}[/yellow]")
                    else:
                        lines.append(f"      └ {agent}")
        
        widget.update("\n".join(lines))

    def refresh_tasks(self) -> None:
        self._tasks = load_tasks()
        widget = self.query_one("#tasks-content", Static)
        
        if not self._tasks:
            widget.update("[dim]No tasks[/dim]")
            return
        
        # Reset index if out of bounds
        if self._selected_task_index >= len(self._tasks):
            self._selected_task_index = 0
        
        is_active = self._current_panel == Panel.TASKS
        lines = []
        
        for i, t in enumerate(self._tasks):
            icon = {
                "pending": "⏳",
                "in_progress": "🔄",
                "completed": "✅",
                "failed": "❌"
            }.get(t.status, "❓")
            
            desc = t.description
            if len(desc) > 30:
                desc = desc[:27] + "..."
            
            is_selected = i == self._selected_task_index
            
            if is_selected and is_active:
                lines.append(f"[bold cyan]▌[/bold cyan] {icon} {t.task_id}: {desc}")
            elif is_selected:
                lines.append(f"[cyan]▌[/cyan] {icon} {t.task_id}: {desc}")
            else:
                lines.append(f"  {icon} {t.task_id}: {desc}")
            
            if t.assigned_to:
                if is_selected:
                    lines.append(f"[cyan]    → {t.assigned_to}[/cyan]")
                else:
                    lines.append(f"  [dim]→ {t.assigned_to}[/dim]")
        
        widget.update("\n".join(lines))

    def update_target(self) -> None:
        display = self.query_one("#target-display", Static)
        if not self._sessions:
            display.update("-")
            return
        s = self._sessions[self._selected_session_index]
        if self._selected_agent_index is not None and self._selected_agent_index < len(s.windows):
            agent = s.windows[self._selected_agent_index]
            display.update(f"{s.display_name}/{agent}")
        else:
            display.update(s.display_name)

    def update_panel_indicators(self) -> None:
        """Update panel headers to show which is active."""
        left_panel = self.query_one("#left-panel", Vertical)
        
        left_panel.remove_class("panel-active")
        left_panel.remove_class("panel-active-tasks")
        
        if self._current_panel == Panel.SESSIONS:
            left_panel.add_class("panel-active")
        elif self._current_panel == Panel.TASKS:
            left_panel.add_class("panel-active-tasks")
        
        sessions_h = self.query_one("#sessions-header", Static)
        tasks_h = self.query_one("#tasks-header", Static)
        main_h = self.query_one("#main-header", Static)
        
        sessions_text = "[S] Sessions"
        tasks_text = "[T] Tasks"
        main_text = "[M] Send Message"
        
        if self._current_panel == Panel.SESSIONS:
            sessions_text = "[S] Sessions ◀"
        elif self._current_panel == Panel.TASKS:
            tasks_text = "[T] Tasks ◀"
        elif self._current_panel == Panel.MAIN:
            main_text = "[M] Send Message ◀"
        
        sessions_h.update(sessions_text)
        tasks_h.update(tasks_text)
        main_h.update(main_text)

    # Navigation
    def action_panel_left(self) -> None:
        if self._current_panel == Panel.MAIN:
            self._current_panel = Panel.TASKS
        elif self._current_panel == Panel.TASKS:
            self._current_panel = Panel.SESSIONS
        elif self._current_panel == Panel.SESSIONS:
            self._current_panel = Panel.MAIN
        self.update_panel_indicators()
        self.refresh_sessions()
        self.refresh_tasks()

    def action_panel_right(self) -> None:
        if self._current_panel == Panel.SESSIONS:
            self._current_panel = Panel.TASKS
        elif self._current_panel == Panel.TASKS:
            self._current_panel = Panel.MAIN
        elif self._current_panel == Panel.MAIN:
            self._current_panel = Panel.SESSIONS
        self.update_panel_indicators()
        self.refresh_sessions()
        self.refresh_tasks()

    def action_nav_up(self) -> None:
        if self._current_panel == Panel.SESSIONS:
            if not self._sessions:
                return
            s = self._sessions[self._selected_session_index]
            if self._selected_agent_index is not None:
                if self._selected_agent_index > 0:
                    self._selected_agent_index -= 1
                else:
                    self._selected_agent_index = None
            elif self._selected_session_index > 0:
                self._selected_session_index -= 1
                if self._sessions[self._selected_session_index].windows:
                    self._selected_agent_index = 0
            self.refresh_sessions()
            self.update_target()
        elif self._current_panel == Panel.TASKS:
            if self._tasks and self._selected_task_index > 0:
                self._selected_task_index -= 1
                self.refresh_tasks()

    def action_nav_down(self) -> None:
        if self._current_panel == Panel.SESSIONS:
            if not self._sessions:
                return
            s = self._sessions[self._selected_session_index]
            if self._selected_agent_index is not None:
                if self._selected_agent_index < len(s.windows) - 1:
                    self._selected_agent_index += 1
                else:
                    self._selected_agent_index = None
                    if self._selected_session_index < len(self._sessions) - 1:
                        self._selected_session_index += 1
                        if self._sessions[self._selected_session_index].windows:
                            self._selected_agent_index = 0
            else:
                if s.windows:
                    self._selected_agent_index = 0
                elif self._selected_session_index < len(self._sessions) - 1:
                    self._selected_session_index += 1
            self.refresh_sessions()
            self.update_target()
        elif self._current_panel == Panel.TASKS:
            if self._tasks and self._selected_task_index < len(self._tasks) - 1:
                self._selected_task_index += 1
                self.refresh_tasks()

    def action_select(self) -> None:
        if self._current_panel == Panel.SESSIONS and self._sessions:
            s = self._sessions[self._selected_session_index]
            if s.windows:
                if self._selected_agent_index is None:
                    self._selected_agent_index = 0
                else:
                    self._selected_agent_index = None
                self.refresh_sessions()
                self.update_target()
        elif self._current_panel == Panel.TASKS and self._tasks:
            task = self._tasks[self._selected_task_index]
            log = self.query_one("#activity-log", Log)
            self.log_msg(f"[cyan]Task:[/cyan] {task.task_id}")
            self.log_msg(f"  {task.description}")
            self.log_msg(f"  Status: {task.status}")
            if task.assigned_to:
                self.log_msg(f"  Assigned: {task.assigned_to}")
            if task.result:
                self.log_msg(f"  Result: {task.result}")

    def action_focus_input(self) -> None:
        self._current_panel = Panel.MAIN
        self.update_panel_indicators()
        self.query_one("#message-input", Input).focus()

    def action_clear_selection(self) -> None:
        self._current_panel = Panel.SESSIONS
        self._selected_agent_index = None
        self._selected_task_index = 0
        self.update_panel_indicators()
        self.refresh_sessions()
        self.refresh_tasks()
        self.update_target()

    def action_attach(self) -> None:
        if not self._sessions:
            log = self.query_one("#activity-log", Log)
            self.log_msg("[yellow]No session selected[/yellow]")
            return
        s = self._sessions[self._selected_session_index]
        target = None
        if self._selected_agent_index is not None and self._selected_agent_index < len(s.windows):
            target = s.windows[self._selected_agent_index]
        log = self.query_one("#activity-log", Log)
        self.log_msg(f"[cyan]Attaching to {s.display_name}...[/cyan]")
        self.post_message(AttachSession(s.name, target))

    def action_start_agent(self) -> None:
        agents = list_available_agents()
        if not agents:
            log = self.query_one("#activity-log", Log)
            self.log_msg("[red]No agents. Run 'agency init' first.[/red]")
            return
        log = self.query_one("#activity-log", Log)
        self.log_msg(f"[cyan]Starting agent '{agents[0]}'...[/cyan]")
        self.post_message(StartAgent(agents[0], os.getcwd()))

    def action_start_manager(self) -> None:
        managers = list_available_managers()
        if not managers:
            log = self.query_one("#activity-log", Log)
            self.log_msg("[red]No managers. Run 'agency init' first.[/red]")
            return
        log = self.query_one("#activity-log", Log)
        self.log_msg(f"[cyan]Starting manager '{managers[0]}'...[/cyan]")
        self.post_message(StartManager(managers[0], os.getcwd()))

    def action_stop_agent(self) -> None:
        if not self._sessions:
            return
        s = self._sessions[self._selected_session_index]
        if self._selected_agent_index is None or self._selected_agent_index >= len(s.windows):
            return
        agent = s.windows[self._selected_agent_index]
        log = self.query_one("#activity-log", Log)
        self.log_msg(f"[yellow]Stopping {agent}...[/yellow]")
        self.post_message(StopAgent(s.name, agent))

    def _get_tasks_file(self) -> Path:
        """Get tasks file path."""
        tasks_file = Path.home() / ".config" / "agency" / "sessions" / "tasks.json"
        tasks_file.parent.mkdir(parents=True, exist_ok=True)
        return tasks_file

    def _load_tasks(self) -> dict:
        """Load tasks from file."""
        tasks_file = self._get_tasks_file()
        if not tasks_file.exists():
            return {}
        with open(tasks_file) as f:
            return json.load(f)

    def _save_tasks(self, tasks: dict) -> None:
        """Save tasks to file."""
        tasks_file = self._get_tasks_file()
        with open(tasks_file, 'w') as f:
            json.dump(tasks, f, indent=2)

    def _generate_task_id(self, tasks: dict) -> str:
        """Generate next task ID."""
        max_num = 0
        for tid in tasks.keys():
            if tid.startswith("TASK"):
                try:
                    num = int(tid[4:])
                    max_num = max(max_num, num)
                except ValueError:
                    pass
        return f"TASK{max_num + 1:03d}"

    def action_create_task(self) -> None:
        """Create a new task (uses current session/agent as assignee)."""
        log = self.query_one("#activity-log", Log)
        
        tasks = self._load_tasks()
        task_id = self._generate_task_id(tasks)
        
        # Use selected agent if in sessions panel
        assigned_to = None
        if self._sessions:
            s = self._sessions[self._selected_session_index]
            if self._selected_agent_index is not None and self._selected_agent_index < len(s.windows):
                assigned_to = s.windows[self._selected_agent_index]
        
        task = {
            "task_id": task_id,
            "description": "New task",
            "status": "pending",
            "assigned_to": assigned_to,
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            "result": None
        }
        
        tasks[task_id] = task
        self._save_tasks(tasks)
        
        self.log_msg(f"[green]Created task:[/green] {task_id}")
        if assigned_to:
            self.log_msg(f"  Assigned to: {assigned_to}")
        
        self.refresh_tasks()

    def action_update_task(self) -> None:
        """Update status of selected task (cycles through statuses)."""
        
        if not self._tasks:
            self.log_msg("[yellow]No tasks to update[/yellow]")
            return
        
        task = self._tasks[self._selected_task_index]
        status_order = ["pending", "in_progress", "completed", "failed"]
        current_idx = status_order.index(task.status) if task.status in status_order else 0
        next_idx = (current_idx + 1) % len(status_order)
        new_status = status_order[next_idx]
        
        tasks = self._load_tasks()
        if task.task_id in tasks:
            tasks[task.task_id]["status"] = new_status
            if new_status == "completed":
                tasks[task.task_id]["completed_at"] = datetime.now().isoformat()
            else:
                tasks[task.task_id]["completed_at"] = None
            self._save_tasks(tasks)
        
        self.log_msg(f"[cyan]Updated:[/cyan] {task.task_id} -> {new_status}")
        self.refresh_tasks()

    def action_delete_task(self) -> None:
        """Delete selected task."""
        log = self.query_one("#activity-log", Log)
        
        if not self._tasks:
            self.log_msg("[yellow]No tasks to delete[/yellow]")
            return
        
        task = self._tasks[self._selected_task_index]
        tasks = self._load_tasks()
        
        if task.task_id in tasks:
            del tasks[task.task_id]
            self._save_tasks(tasks)
            self.log_msg(f"[red]Deleted task:[/red] {task.task_id}")
        
        # Adjust index if needed
        if self._selected_task_index >= len(self._tasks) - 1:
            self._selected_task_index = max(0, len(self._tasks) - 2)
        
        self.refresh_tasks()

    def action_toggle_help(self) -> None:
        self.log_msg("""[bold]Agency TUI - Keyboard Shortcuts[/bold]
─────────────────────────────────────
[cyan]←/→[/cyan]    Switch panels (Sessions/Tasks/Main)
[cyan]↑/↓[/cyan]    Navigate sessions & tasks
[cyan]Enter[/cyan]  Select/expand or show task details
[cyan]a[/cyan]      Attach to session
[cyan]s[/cyan]      Focus message input
[cyan]n[/cyan]      New agent
[cyan]m[/cyan]      New manager
[cyan]x[/cyan]      Stop agent
[cyan]c[/cyan]      Create task
[cyan]u[/cyan]      Update task status
[cyan]d[/cyan]      Delete task
[cyan]r[/cyan]      Refresh
[cyan]?[/cyan]      Help
[cyan]q[/cyan]      Quit""")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if not self._sessions or not event.value.strip():
            return
        s = self._sessions[self._selected_session_index]
        agent = None
        if self._selected_agent_index is not None and self._selected_agent_index < len(s.windows):
            agent = s.windows[self._selected_agent_index]
        msg = event.value.strip()
        log = self.query_one("#activity-log", Log)
        target = agent if agent else s.display_name
        self.log_msg(f"[cyan]→ {target}:[/cyan] {msg}")
        self.post_message(SendMessage(s.name, agent, msg))
        event.input.value = ""

    def on_send_message(self, event: SendMessage) -> None:
        from datetime import datetime
        save_message(event.session, event.agent, event.message, "out", datetime.now().isoformat())
        if event.agent:
            send_keys(event.session, event.agent, event.message)
        else:
            sess = next((x for x in list_agency_sessions() if x.name == event.session), None)
            if sess and sess.windows:
                send_keys(event.session, sess.windows[0], event.message)
        log = self.query_one("#activity-log", Log)
        self.log_msg(f"[green]✓ Sent to {event.session}[/green]")

    def on_attach_session(self, event: AttachSession) -> None:
        if event.target:
            os.execvp("tmux", ["tmux", "-L", TMUX_SOCKET, "select-window", "-t", f"{event.session}:{event.target}"])
        os.execvp("tmux", ["tmux", "-L", TMUX_SOCKET, "attach-session", "-t", event.session])

    def on_start_agent(self, event: StartAgent) -> None:
        from agency.tui.commands import start_agent
        try:
            start_agent(event.agent_name, event.work_dir)
            self.log_msg(f"[green]✓ Started {event.agent_name}[/green]")
            self.refresh_sessions()
        except Exception as e:
            self.log_msg(f"[red]✗ {e}[/red]")

    def on_start_manager(self, event: StartManager) -> None:
        from agency.tui.commands import start_manager
        try:
            start_manager(event.manager_name, event.work_dir)
            self.log_msg(f"[green]✓ Manager {event.manager_name} started[/green]")
            self.refresh_sessions()
        except Exception as e:
            self.log_msg(f"[red]✗ {e}[/red]")

    def on_stop_agent(self, event: StopAgent) -> None:
        from agency.tui.commands import stop_agent
        try:
            stop_agent(event.session, event.agent)
            self.log_msg(f"[green]✓ {event.agent} stopped[/green]")
            self.refresh_sessions()
        except Exception as e:
            self.log_msg(f"[red]✗ {e}[/red]")

    def action_quit(self) -> None:
        self.exit()

    def log_msg(self, message: str) -> None:
        """Write a message with Rich markup to the activity log."""
        log_widget = self.query_one("#activity-log", Log)
        log_widget.write_line(Text.from_markup(message))


def save_message(session: str, agent: str | None, content: str, direction: str, timestamp: str) -> None:
    import json
    messages_path = Path.home() / ".config" / "agency" / MESSAGES_FILE
    messages_path.parent.mkdir(parents=True, exist_ok=True)
    messages = []
    if messages_path.exists():
        with open(messages_path) as f:
            messages = json.load(f)
    messages.append({"session": session, "agent": agent, "content": content, "direction": direction, "timestamp": timestamp})
    if len(messages) > 1000:
        messages = messages[-1000:]
    with open(messages_path, 'w') as f:
        json.dump(messages, f, indent=2)


def run_tui() -> None:
    app = AgencyTUI()
    app.run()
