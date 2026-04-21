# Code Examples

## Textual Components

### Basic Panel with Border

```python
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Static

class PanelExample(App):
    CSS = """
    Screen { background: #1A1B26; }
    
    #main-panel {
        width: 60;
        height: 20;
        border: solid #7AA2F7;
        background: #16161E;
        padding: 1 2;
    }
    
    .panel-title {
        text-style: bold;
        color: #7AA2F7;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Container(id="main-panel"):
            yield Static("┌─ Sessions ─┐", classes="panel-title")
            yield Static("│ 👑 coordinator │")
            yield Static("│ 🤖 coder      │")
            yield Static("│ 🤖 tester     │")
            yield Static("└─────────────┘")

if __name__ == "__main__":
    app = PanelExample()
    app.run()
```

### DataTable with Selection

```python
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import DataTable

class DataTableExample(App):
    CSS = """
    Screen { background: #1A1B26; }
    
    DataTable {
        background: #16161E;
        border: solid #3B3B5C;
    }
    
    DataTable > .datatable--cursor {
        background: #7AA2F7 30%;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield DataTable()
    
    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Session", "Agents", "Status")
        table.add_rows([
            ["agency-demo", "coder, tester", "Running"],
            ["agency-web", "frontend, backend", "Running"],
            ["agency-docs", "writer", "Stopped"],
        ])
```

### Log Viewer with Auto-scroll

```python
from textual.app import App, ComposeResult
from textual.widgets import Log, Button
from textual.containers import Container, Horizontal

class LogExample(App):
    CSS = """
    Screen { background: #1A1B26; }
    
    #log-container {
        height: 1fr;
        border: solid #3B3B5C;
        background: #16161E;
        padding: 1;
    }
    
    Log {
        background: #16161E;
    }
    
    #button-row {
        height: 3;
        background: #24253A;
        padding: 1;
        align: right;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Container():
            with Horizontal(id="button-row"):
                yield Button("Clear", id="clear-btn")
                yield Button("Auto-scroll: ON", id="toggle-btn")
            with Container(id="log-container"):
                yield Log(id="activity-log", auto_scroll=True)
    
    def on_mount(self) -> None:
        self.log_widget = self.query_one("#activity-log", Log)
        self.log_widget.write_line("[14:32:01] [INFO] Application started")
        self.log_widget.write_line("[14:32:02] [INFO] Connecting to tmux...")
        self.log_widget.write_line("[14:32:03] [INFO] Ready!")
```

### Progress Dashboard

```python
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

def create_dashboard() -> Layout:
    layout = Layout()
    
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3),
    )
    
    layout["main"].split_row(
        Layout(name="sessions", ratio=1),
        Layout(name="tasks", ratio=2),
        Layout(name="activity", ratio=2),
    )
    
    return layout

def render_header() -> Panel:
    return Panel(
        "[bold cyan]AGENCY TUI[/bold cyan]  [dim]v0.3.0[/dim]     "
        "[green]●[/green] Connected to tmux",
        border_style="cyan",
    )

def render_sessions() -> Panel:
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Session", style="cyan")
    table.add_column("Agents")
    table.add_column("Status")
    
    table.add_row("agency-demo", "coder, tester", "[green]●[/green]")
    table.add_row("agency-web", "frontend", "[green]●[/green]")
    
    return Panel(table, title="Sessions", border_style="blue")

def render_tasks() -> Panel:
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    )
    
    t1 = progress.add_task("Authentication", total=100)
    t2 = progress.add_task("Testing", total=100)
    t3 = progress.add_task("Documentation", total=100)
    
    progress.update(t1, completed=75)
    progress.update(t2, completed=50)
    progress.update(t3, completed=25)
    
    return Panel(progress, title="Tasks", border_style="purple")

console = Console()
layout = create_dashboard()

layout["header"].update(render_header())
layout["sessions"].update(render_sessions())
layout["tasks"].update(render_tasks())
layout["activity"].update(Panel("[dim]Activity log...[/dim]", title="Activity"))
layout["footer"].update(Panel("[dim]Press ? for help[/dim]"))

console.print(layout)
```

## Rich Library Examples

### Styled Text

```python
from rich.console import Console
from rich.text import Text
from rich.style import Style

console = Console()

# Gradient-like effect
gradient = Text()
for i, char in enumerate("AGENCY"):
    colors = ["#F7768E", "#E0AF68", "#9ECE6A", "#7DCFFF", "#BB9AF7"]
    gradient.append(char, Style(color=colors[i % len(colors)], bold=True))

console.print(gradient)

# Highlighted text
console.print("[bold]Bold[/bold] [italic]Italic[/italic] [bold italic]Both[/bold italic]")
console.print("[link=https://github.com]GitHub Link[/link]")
console.print("[cyan]Cyan[/cyan] [on red]On Red[/on red] [reverse]Reverse[/reverse]")
```

### Tables

```python
from rich.table import Table

table = Table(title="Agent Status", show_header=True, header_style="bold magenta")
table.add_column("Name", style="cyan", no_wrap=True)
table.add_column("Type", style="green")
table.add_column("Status", justify="center")
table.add_column("Uptime", justify="right")

table.add_row("coordinator", "Manager", "[green]●[/green] Active", "2h 34m")
table.add_row("coder", "Agent", "[cyan]●[/cyan] Running", "1h 12m")
table.add_row("tester", "Agent", "[yellow]◐[/yellow] Idle", "45m")

console.print(table)
```

### Boxes and Borders

```python
from rich.box import BOX_STYLES

# Different border styles
for box_name in ["ASCII", "ROUNDED", "HEAVY", "DOUBLE", "SIMPLE"]:
    box = getattr(Box, box_name)
    console.print(Panel("Content", box=box, title=box_name))
```

## Animation Examples

### Typing Effect

```python
import asyncio
from textual.app import App, ComposeResult
from textual.widgets import Static

class TypingEffect(App):
    async def on_mount(self) -> None:
        text = "Hello, Agent!"
        widget = Static()
        yield widget
        
        for i in range(len(text) + 1):
            widget.update(text[:i] + "█")
            await asyncio.sleep(0.1)
        
        widget.update(text)
```

### Pulse Animation

```python
from textual.app import App, ComposeResult
from textual.widgets import Static
from textual.timer import Timer

class PulseExample(App):
    CSS = """
    Screen { background: #1A1B26; }
    #pulse { width: 100%; height: 100%; content-align: center middle; }
    """
    
    def __init__(self) -> None:
        super().__init__()
        self._intensity = 0.0
        self._direction = 1
    
    def compose(self) -> ComposeResult:
        yield Static("●", id="pulse")
    
    def on_mount(self) -> None:
        self._timer = self.set_interval(0.1, self.pulse)
    
    def pulse(self) -> None:
        self._intensity += 0.1 * self._direction
        if self._intensity >= 1.0:
            self._direction = -1
        elif self._intensity <= 0.0:
            self._direction = 1
        
        intensity = int(255 * self._intensity)
        color = f"rgb({intensity},{255-intensity},{0})"
        self.query_one("#pulse").styles.color = color
```

## Layout Snippets

### Three-Column Layout

```python
from textual.containers import Horizontal, Vertical

class ThreeColumnLayout:
    CSS = """
    #left-panel { width: 25; dock: left; background: $panel; }
    #center-panel { width: 1fr; }
    #right-panel { width: 30; dock: right; background: $panel; }
    """
    
    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="left-panel"):
                yield Static("SESSIONS", classes="header")
                # session list
            with Vertical(id="center-panel"):
                yield Static("ACTIVITY", classes="header")
                # activity feed
            with Vertical(id="right-panel"):
                yield Static("TASKS", classes="header")
                # task list
```

### Header with Breadcrumbs

```python
class HeaderWithBreadcrumb(Static):
    CSS = """
    Header {
        height: 3;
        background: $surface;
        dock: top;
    }
    
    #breadcrumb {
        width: 100%;
        height: 1;
        content-align: center middle;
        color: $text-muted;
    }
    
    #title {
        width: 100%;
        height: 2;
        content-align: center middle;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield Static("Sessions > agency-demo > coder", id="breadcrumb")
        yield Static("[bold cyan]Agency TUI[/bold cyan]", id="title")
```

### Sidebar Navigation

```python
class SidebarNav(Static):
    CSS = """
    #sidebar {
        width: 20;
        dock: left;
        background: $panel;
    }
    
    NavItem {
        height: 3;
        padding: 1 2;
    }
    
    NavItem:hover {
        background: $accent 10%;
    }
    
    NavItem.active {
        background: $accent 20%;
        text-style: bold;
    }
    """
    
    NAV_ITEMS = [
        ("🏠", "Dashboard"),
        ("💻", "Sessions"),
        ("📋", "Tasks"),
        ("💬", "Messages"),
        ("⚙", "Settings"),
    ]
    
    def compose(self) -> ComposeResult:
        for icon, label in self.NAV_ITEMS:
            yield Static(f"{icon} {label}", classes="NavItem")
```

## Color Utility Functions

```python
def hex_to_ansi(hex_color: str) -> str:
    """Convert hex color to ANSI 256 color code."""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    
    # ANSI 256 approximation
    if r == g == b:
        gray = round(r / 255 * 24 + 232)
        return f"238"  # Use standard gray
    
    return f"16;{r};{g};{b}"  # True color

def blend_colors(color1: str, color2: str, ratio: float = 0.5) -> str:
    """Blend two hex colors."""
    def hex_to_rgb(c):
        c = c.lstrip("#")
        return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
    
    r1, g1, b1 = hex_to_rgb(color1)
    r2, g2, b2 = hex_to_rgb(color2)
    
    r = int(r1 + (r2 - r1) * ratio)
    g = int(g1 + (g2 - g1) * ratio)
    b = int(b1 + (b2 - b1) * ratio)
    
    return f"#{r:02x}{g:02x}{b:02x}"

def darken(hex_color: str, amount: float = 0.1) -> str:
    """Darken a hex color."""
    return blend_colors(hex_color, "#000000", amount)

def lighten(hex_color: str, amount: float = 0.1) -> str:
    """Lighten a hex color."""
    return blend_colors(hex_color, "#FFFFFF", amount)
```

## tmux Integration

```python
import subprocess
from dataclasses import dataclass

@dataclass
class TmuxSession:
    name: str
    windows: list[str]
    created: str

def list_sessions_detailed() -> list[TmuxSession]:
    """List tmux sessions with detailed info."""
    result = subprocess.run(
        ["tmux", "-L", "agency", "list-sessions", "-F", "#{session_name}|#{session_created_string}|#{session_windows}"],
        capture_output=True, text=True
    )
    
    sessions = []
    for line in result.stdout.strip().split("\n"):
        if line:
            name, created, windows = line.split("|")
            sessions.append(TmuxSession(
                name=name,
                created=created,
                windows=windows.split()
            ))
    
    return sessions
```

## Internationalization

```python
from enum import Enum

class T_(str, Enum):
    """Translation helper for i18n."""
    
    SESSIONS = "Sessions"
    TASKS = "Tasks"
    SEND_MESSAGE = "Send message"
    NO_SESSIONS = "No active sessions"
    NO_TASKS = "No tasks"
    
    # Status
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    FAILED = "Failed"
    
    # Actions
    START = "Start"
    STOP = "Stop"
    ATTACH = "Attach"
    REFRESH = "Refresh"
    QUIT = "Quit"
    
    @property
    def _(self):
        """Placeholder for translation lookup."""
        return self.value

# Usage
print(T_.SESSIONS)  # "Sessions"
```
