# UI Components

## Cards

### Session Card

```python
class SessionCard(Static):
    """Card displaying session with agents."""
    
    DEFAULT_CSS = """
    SessionCard {
        height: auto;
        background: $panel;
        border: solid $border;
        padding: 1 2;
        margin: 0 1;
    }
    
    SessionCard:focus {
        border: solid $accent;
        background: $accent 10%;
    }
    
    .session-icon {
        color: $accent;
    }
    
    .session-name {
        text-style: bold;
        color: $text;
    }
    
    .agent-list {
        color: $text-muted;
    }
    """
    
    def __init__(self, session: SessionInfo):
        self.session = session
        super().__init__()
    
    def compose(self) -> ComposeResult:
        icon = "👑" if self.session.is_manager else "🤖"
        name = self.session.display_name
        
        yield Static(f"{icon} {name}", classes="session-name")
        
        if self.session.windows:
            with Vertical(classes="agent-list"):
                for agent in self.session.windows:
                    yield Static(f"   └ {agent}")
```

### Task Card

```python
class TaskCard(Static):
    """Card displaying task with status and assignee."""
    
    STATUS_ICONS = {
        "pending": "⏳",
        "in_progress": "🔄",
        "completed": "✅",
        "failed": "❌",
    }
    
    STATUS_COLORS = {
        "pending": "yellow",
        "in_progress": "cyan",
        "completed": "green",
        "failed": "red",
    }
    
    def __init__(self, task: TaskInfo):
        self.task = task
        super().__init__()
    
    def compose(self) -> ComposeResult:
        icon = self.STATUS_ICONS.get(self.task.status, "❓")
        color = self.STATUS_COLORS.get(self.task.status, "white")
        
        with Horizontal():
            yield Static(icon)
            yield Static(self.task.task_id, styles=f"color: {color}; text-style: bold;")
        
        yield Static(self.task.description[:50], classes="task-desc")
        
        if self.task.assigned_to:
            yield Static(f"→ {self.task.assigned_to}", classes="task-assignee")
```

### Status Badge

```python
class StatusBadge(Static):
    """Small badge showing status with color."""
    
    BADGE_STYLES = {
        "online": ("● Online", "green"),
        "offline": ("○ Offline", "dim"),
        "busy": ("◉ Busy", "yellow"),
        "error": ("✗ Error", "red"),
    }
    
    def __init__(self, status: str):
        label, color = self.BADGE_STYLES.get(status, ("?", "white"))
        super().__init__(label)
        self.styles.color = color
```

## Lists

### Selectable List

```python
class SelectableList(Static):
    """List with keyboard navigation and selection."""
    
    def __init__(self, items: list[str]):
        self.items = items
        self.selected_index = 0
        super().__init__()
    
    def render(self) -> Text:
        lines = []
        for i, item in enumerate(self.items):
            if i == self.selected_index:
                prefix = "▶ "
                style = "bold cyan"
            else:
                prefix = "  "
                style = ""
            lines.append(Text(f"{prefix}{item}", style=style))
        return Text("\n").join(lines)
```

### Tree View

```python
def render_tree(data: dict, prefix: str = "", is_last: bool = True) -> list[str]:
    """Render a nested dict as tree lines."""
    lines = []
    connector = "└── " if is_last else "├── "
    
    for i, (key, value) in enumerate(data.items()):
        is_last_item = i == len(data) - 1
        
        if isinstance(value, dict):
            lines.append(f"{prefix}{connector}{key}")
            extension = "    " if is_last_item else "│   "
            lines.extend(render_tree(value, prefix + extension, True))
        else:
            lines.append(f"{prefix}{connector}{key}: {value}")
    
    return lines

# Example:
# tree = {
#     "Sessions": {
#         "agency-demo": {"coder": None, "tester": None},
#         "agency-web": {"frontend": None, "backend": None},
#     }
# }
# for line in render_tree(tree):
#     print(line)
```

## Inputs

### Message Input

```python
class MessageInput(Input):
    """Styled input for sending messages."""
    
    DEFAULT_CSS = """
    MessageInput {
        border: solid $border;
        background: $surface;
        padding: 0 1;
        height: 3;
    }
    
    MessageInput:focus {
        border: solid $accent;
    }
    
    MessageInput::-placeholder {
        color: $text-muted;
    }
    """
    
    def __init__(self):
        super().__init__(
            placeholder="Type message...",
            id="message-input"
        )
```

### Command Picker

```python
class CommandPicker(Static):
    """Dropdown-style command selector."""
    
    COMMANDS = [
        ("start", "Start new agent"),
        ("stop", "Stop agent"),
        ("attach", "Attach to session"),
        ("send", "Send message"),
        ("tasks", "Manage tasks"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Static("Commands:", classes="picker-label")
        for cmd, desc in self.COMMANDS:
            yield Static(f"  {cmd:<10} {desc}", classes="command-item")
```

## Panels

### Collapsible Section

```python
class CollapsiblePanel(Static):
    """Panel that can expand/collapse."""
    
    def __init__(self, title: str, content: str, collapsed: bool = False):
        self.title = title
        self.content = content
        self.collapsed = collapsed
        super().__init__()
    
    def render(self) -> Text:
        icon = "▶" if self.collapsed else "▼"
        lines = [Text(f"{icon} {self.title}", style="bold")]
        
        if not self.collapsed:
            lines.append(Text(self.content, style="dim"))
        
        return Text("\n").join(lines)
```

### Tab Container

```python
class TabBar(Static):
    """Horizontal tab navigation."""
    
    TABS = ["Sessions", "Tasks", "Activity"]
    
    DEFAULT_CSS = """
    TabBar {
        height: 1;
        background: $panel;
        dock: top;
    }
    
    Tab {
        padding: 0 2;
        background: $panel;
    }
    
    Tab.active {
        background: $accent 20%;
        text-style: bold;
    }
    
    Tab:hover {
        background: $accent 10%;
    }
    """
    
    def compose(self) -> ComposeResult:
        for i, tab in enumerate(self.TABS):
            classes = "active" if i == 0 else ""
            yield Static(tab, classes=f"Tab {classes}")
```

## Progress Indicators

### Loading Spinner

```python
class LoadingSpinner(Static):
    """Animated loading indicator."""
    
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    def __init__(self):
        self.frame = 0
        super().__init__(self.FRAMES[0])
    
    def on_mount(self) -> None:
        self.update_timer = self.set_interval(0.1, self.next_frame)
    
    def next_frame(self) -> None:
        self.frame = (self.frame + 1) % len(self.FRAMES)
        self.update(self.FRAMES[self.frame])
```

### Progress Bar

```python
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn

def create_progress() -> Progress:
    return Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=20),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
    )

# Usage:
with create_progress() as progress:
    task = progress.add_task("Processing...", total=100)
    for i in range(100):
        progress.update(task, advance=1)
```

## Status Indicators

### Connection Status

```python
class ConnectionIndicator(Static):
    """Shows tmux connection status."""
    
    CONNECTED_COLOR = "green"
    DISCONNECTED_COLOR = "red"
    
    def __init__(self):
        super().__init__("● Disconnected")
        self.styles.color = self.DISCONNECTED_COLOR
    
    def set_connected(self) -> None:
        self.update("● Connected")
        self.styles.color = self.CONNECTED_COLOR
    
    def set_disconnected(self) -> None:
        self.update("● Disconnected")
        self.styles.color = self.DISCONNECTED_COLOR
```

### Activity Pulse

```python
class ActivityPulse(Static):
    """Shows recent activity with pulse effect."""
    
    def __init__(self):
        self.pulse = False
        super().__init__("●")
        self.styles.color = "green"
    
    def on_mount(self) -> None:
        self.pulse_timer = self.set_interval(1.0, self.pulse_toggle)
    
    def pulse_toggle(self) -> None:
        self.pulse = not self.pulse
        self.styles.color = "brightgreen" if self.pulse else "green"
```

## Notifications

### Toast Notification

```python
class Toast(Static):
    """Temporary notification popup."""
    
    TYPES = {
        "info": ("ℹ", "blue"),
        "success": ("✓", "green"),
        "warning": ("⚠", "yellow"),
        "error": ("✗", "red"),
    }
    
    DEFAULT_CSS = """
    Toast {
        width: 40;
        height: 3;
        background: $surface;
        border: solid $accent;
        padding: 1 2;
        opacity: 0;
    }
    
    Toast.visible {
        opacity: 1;
    }
    """
    
    def __init__(self, message: str, type_: str = "info"):
        icon, color = self.TYPES.get(type_, ("?", "white"))
        super().__init__(f"{icon} {message}")
        self.styles.color = color
```

### Status Bar

```python
class StatusBar(Static):
    """Bottom status bar with key info."""
    
    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        background: $panel;
        dock: bottom;
        padding: 0 2;
    }
    
    StatusBar > .status-item {
        color: $text-muted;
        margin-right: 2;
    }
    
    StatusBar > .status-item.current {
        color: $accent;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield Static("Sessions: 3", classes="status-item")
        yield Static("Tasks: 5", classes="status-item")
        yield Static("12:34:56", classes="status-item current")
```

## Emoji & Icons

```python
# Status icons
STATUS_ICONS = {
    "pending": "⏳",      # Hourglass
    "in_progress": "🔄",  # Arrows
    "completed": "✅",     # Checkmark
    "failed": "❌",        # X mark
    "stopped": "⏹",      # Stop button
    "waiting": "⏸",      # Pause
}

# Agent type icons
AGENT_ICONS = {
    "coordinator": "👑",  # Crown
    "coder": "💻",        # Laptop
    "tester": "🧪",      # Test tube
    "reviewer": "🔍",     # Magnifying glass
    "docs": "📝",         # Memo
    "default": "🤖",      # Robot
}

# Action icons
ACTION_ICONS = {
    "send": "📤",
    "receive": "📥",
    "attach": "🔗",
    "detach": "⛓",
    "start": "▶",
    "stop": "■",
    "refresh": "🔄",
    "settings": "⚙",
    "help": "?",
}

# Connection indicators
CONNECTION_ICONS = {
    "connected": "●",     # Filled circle
    "disconnected": "○",  # Empty circle
    "error": "✗",
    "warning": "⚠",
}
```

## Empty States

```python
EMPTY_STATES = {
    "no_sessions": """
    ┌─────────────────────────┐
    │    No Active Sessions   │
    │                         │
    │   Start an agent with:  │
    │   $ agency start <name> │
    └─────────────────────────┘
    """,
    
    "no_tasks": """
    ┌─────────────────────────┐
    │      No Tasks Yet       │
    │                         │
    │   Create a task with:   │
    │   $ agency tasks add    │
    └─────────────────────────┘
    """,
    
    "no_messages": """
    ┌─────────────────────────┐
    │   No Messages Yet       │
    │                         │
    │   Send a message to     │
    │   start a conversation  │
    └─────────────────────────┘
    """,
}
```
