"""Start agent dialog screen."""

import os
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Static

import yaml


class StartAgentRequest(Message):
    """Message sent when user requests to start an agent."""
    def __init__(self, agent_name: str, work_dir: str) -> None:
        self.agent_name = agent_name
        self.work_dir = work_dir
        super().__init__()


class StartAgentDialog(Screen):
    """Dialog for starting a new agent."""

    CSS = """
    #dialog {
        width: 50;
        height: auto;
        background: $panel;
        border: solid $accent;
        padding: 2;
    }

    #title {
        text-style: bold;
        margin-bottom: 1;
    }

    #agent-list {
        height: 10;
        margin-bottom: 1;
    }

    #dir-input {
        margin-bottom: 1;
    }

    #buttons {
        height: 3;
    }
    """

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Cancel"),
        Binding("enter", "start_agent", "Start"),
    ]

    def __init__(self) -> None:
        super().__init__(id="start-agent-dialog")
        self._selected_agent: str | None = None

    def compose(self) -> ComposeResult:
        """Compose the dialog."""
        yield Container(
            Static("Start New Agent", id="title"),
            Static("Select Agent:", id="agent-label"),
            *self._build_agent_list(),
            Static("Working Directory:", id="dir-label"),
            Input(placeholder="~/projects/myapp", id="dir-input"),
            Horizontal(
                Button("Cancel", variant="error", id="cancel-btn"),
                Button("Start", variant="success", id="start-btn"),
                id="buttons",
            ),
            id="dialog",
        )

    def _build_agent_list(self) -> list:
        """Build agent list widgets."""
        from agency.tui.app import list_available_agents
        agents = list_available_agents()

        if not agents:
            return [Static("No agent configs found. Run 'agency init' first.", id="no-agents")]

        # Create options for selection
        options = []
        for name in agents:
            config = self._load_agent_config(name)
            desc = config.get("personality", "")[:50] if config else ""
            options.append(Static(f"• {name}: {desc}...", id=f"agent-{name}"))
        
        return options

    def _load_agent_config(self, agent_name: str) -> dict | None:
        """Load agent configuration."""
        config_path = Path.home() / ".config" / "agency" / "agents" / f"{agent_name}.yaml"
        if not config_path.exists():
            return None
        with open(config_path) as f:
            return yaml.safe_load(f)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "cancel-btn":
            self.app.pop_screen()
        elif event.button.id == "start-btn":
            self.action_start_agent()

    def on_mount(self) -> None:
        """Called when dialog is mounted."""
        # Focus the directory input
        dir_input = self.query_one("#dir-input", Input)
        dir_input.focus()

    def action_start_agent(self) -> None:
        """Start the agent."""
        from agency.tui.app import list_available_agents
        
        # Get selected agent (first one for now, could be enhanced with selection)
        agents = list_available_agents()
        if not agents:
            self.app.pop_screen()
            return

        agent_name = agents[0]  # Default to first agent

        # Get directory
        dir_input = self.query_one("#dir-input", Input)
        work_dir = dir_input.value.strip() or str(Path.cwd())

        # Expand tilde
        work_dir = os.path.expanduser(work_dir)

        self.post_message(StartAgentRequest(agent_name, work_dir))
        self.app.pop_screen()
