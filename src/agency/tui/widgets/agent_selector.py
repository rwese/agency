"""Agent selector widget for starting/stopping agents."""

from textual import on
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static, OptionList

from agency.tui.app import list_available_agents


class AgentSelected(Message):
    """Message sent when an agent is selected for starting."""
    def __init__(self, agent_name: str) -> None:
        self.agent_name = agent_name
        super().__init__()


class AgentSelector(Widget):
    """Widget for selecting an agent to start."""

    def __init__(self) -> None:
        super().__init__(id="agent-selector")
        self.agents: list[str] = []
        self._selected: str | None = None

    def compose(self):
        yield Static("Available Agents", id="agent-selector-header")
        agents = list_available_agents()
        self.agents = agents
        
        if agents:
            options = [f"{name}" for name in agents]
            yield OptionList(*options, id="agent-option-list")
            self._selected = agents[0] if agents else None
        else:
            yield Static("No agent configs found", id="no-agents")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle agent selection."""
        if 0 <= event.option_index < len(self.agents):
            self._selected = self.agents[event.option_index]
            self.post_message(AgentSelected(self._selected))
