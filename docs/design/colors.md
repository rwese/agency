# Color Schemes

## Terminal Color Basics

Terminals typically support:
- **8 ANSI colors** (standard)
- **16 ANSI colors** (bright variants)
- **256 palette** (216 RGB + 24 grayscale)
- **True color** (16.7 million - RGB hex)

## Popular Dark Themes

### Tokyonight

```python
TOKYONIGHT = {
    "black": "#15161E",
    "red": "#F7768E",
    "orange": "#FF9E64",
    "yellow": "#E0AF68",
    "green": "#9ECE6A",
    "cyan": "#7DCFFF",
    "blue": "#7AA2F7",
    "purple": "#BB9AF7",
    "white": "#C0CAF5",
    "foreground": "#C0CAF5",
    "background": "#1A1B26",
}
```

### Catppuccin Mocha

```python
CATPPUCCIN_MOCHA = {
    "rosewater": "#F5E0DC",
    "flamingo": "#F2CDCD",
    "pink": "#F5C2E7",
    "mauve": "#CBA6F7",
    "red": "#F38BA8",
    "maroon": "#EBA0AC",
    "peach": "#FAB387",
    "yellow": "#F9E2AF",
    "green": "#A6E3A1",
    "teal": "#94E2D5",
    "sky": "#89DCEB",
    "sapphire": "#74C7EC",
    "blue": "#89B4FA",
    "lavender": "#B4BEFE",
    "text": "#CDD6F4",
    "subtext": "#BAC2DE",
    "surface0": "#313244",
    "surface1": "#45475A",
    "surface2": "#585B70",
    "overlay0": "#6C7086",
    "overlay1": "#7F849C",
    "overlay2": "#9399B2",
    "base": "#1E1E2E",
    "mantle": "#181825",
    "crust": "#11111B",
}
```

### Nord

```python
NORD = {
    "polar_night_1": "#2E3440",
    "polar_night_2": "#3B4252",
    "polar_night_3": "#434C5E",
    "polar_night_4": "#4C566A",
    "snow_storm_1": "#D8DEE9",
    "snow_storm_2": "#E5E9F0",
    "snow_storm_3": "#ECEFF4",
    "frost_1": "#8FBCBB",
    "frost_2": "#88C0D0",
    "frost_3": "#81A1C1",
    "frost_4": "#5E81AC",
    "aurora_1": "#BF616A",
    "aurora_2": "#D08770",
    "aurora_3": "#EBCB8B",
    "aurora_4": "#A3BE8C",
    "aurora_5": "#B48EAD",
}
```

### Kanagawa

```python
KANAGAWA = {
    "wave_1": "#1F1F28",
    "wave_2": "#2A2A37",
    "dragon_1": "#545795",
    "dragon_2": "#6E6A97",
    "fuji_white": "#EFF1F5",
    "fuji_gray": "#A6A6B8",
    "spring_blue": "#7AA2F7",
    "sakura_pink": "#DCA4E0",
    "mount_gray": "#5B6078",
    "oni_violet": "#957FB8",
    "lotus_pink": "#F2A7B0",
    "peach": "#FFAD66",
    "spring_green": "#98C379",
    "boat_yellow": "#E0C070",
    "pine_green": "#89B58C",
    "winter_green": "#2A2A37",
    "autumn_yellow": "#D19A66",
    "winter_red": "#F76D6D",
    "autumn_green": "#769B6B",
}
```

### Rose Pine

```python
ROSEPINE = {
    "base": "#191724",
    "surface": "#1f1d2b",
    "overlay": "#26233a",
    "muted": "#6e6a97",
    "subtle": "#908caa",
    "text": "#e0def4",
    "love": "#eb6f92",
    "gold": "#f6c177",
    "rose": "#ebbcba",
    "pine": "#9ccfd8",
    "foam": "#c4a7e7",
    "iris": "#f6c177",
    "highlight_low": "#21202e",
    "highlight_med": "#403d52",
    "highlight_high": "#524f67",
}
```

## Semantic Color Assignments

### Status Colors

```python
STATUS_COLORS = {
    "pending": "yellow",      # ⏳ Yellow indicates waiting
    "in_progress": "cyan",    # 🔄 Cyan for active/running
    "completed": "green",     # ✅ Green for success
    "failed": "red",          # ❌ Red for errors
    "stopped": "dim",         # ⏹ Gray for inactive
}
```

### Panel Colors

```python
PANEL_COLORS = {
    "sessions": "blue",        # Primary navigation
    "tasks": "purple",        # Secondary information
    "chat": "green",          # Communication
    "activity": "yellow",     # Logs and updates
    "details": "cyan",        # Selected item details
}
```

### Agent Types

```python
AGENT_COLORS = {
    "coordinator": "brightmagenta",  # 👑 Manager
    "coder": "blue",                   # 💻 Development
    "tester": "green",                 # 🧪 Quality
    "reviewer": "yellow",              # 🔍 Code review
    "docs": "cyan",                   # 📝 Documentation
}
```

## Textual Theme Example

```python
from textual.theme import Theme

AGENCY_THEME = Theme(
    name="agency-dark",
    primary="#7AA2F7",           # Blue accent
    secondary="#BB9AF7",          # Purple
    accent="#7DCFFF",             # Cyan
    success="#9ECE6A",            # Green
    warning="#E0AF68",            # Yellow
    error="#F7768E",              # Red
    background="#1A1B26",         # Dark background
    surface="#16161E",            # Slightly lighter
    panel="#24253A",              # Panel background
    border="#3B3B5C",             # Subtle borders
    text="#C0CAF5",               # Primary text
    text_muted="#565F89",         # Secondary text
    bright=True,
)
```

## Gradient Text Effect

```python
from rich.text import Text
from rich.style import Style

# Gradient-like effect using multiple colors
def gradient_text(text: str) -> Text:
    colors = ["#F7768E", "#E0AF68", "#9ECE6A", "#7DCFFF", "#BB9AF7"]
    result = Text()
    for i, char in enumerate(text):
        color = colors[i % len(colors)]
        result.append(char, Style(color=color))
    return result

# Usage
console.print(gradient_text("AGENCY"))
```

## Contrast Guidelines

### Minimum Contrast Ratios

| Context | Minimum Ratio |
|---------|---------------|
| Body text | 4.5:1 |
| Large text | 3:1 |
| UI components | 3:1 |
| Decorative | No requirement |

### Color Blind Safe Palettes

```python
# Alternative colors for colorblind users
COLORBLIND_SAFE = {
    "orange": "#FFA500",   # Instead of red/green
    "blue": "#0077BB",     # Instead of green
    "shape_circle": "●",    # Add shapes
    "shape_square": "■",
    "shape_triangle": "▲",
}
```

## Box Drawing Characters

```python
BOX_CHARS = {
    "light": {
        "horizontal": "─",
        "vertical": "│",
        "top_left": "┌",
        "top_right": "┐",
        "bottom_left": "└",
        "bottom_right": "┘",
        "cross": "┼",
        "tee_down": "┬",
        "tee_up": "┴",
    },
    "heavy": {
        "horizontal": "━",
        "vertical": "┃",
        "top_left": "┏",
        "top_right": "┓",
        "bottom_left": "┗",
        "bottom_right": "┛",
        "cross": "╋",
    },
    "rounded": {
        "top_left": "╭",
        "top_right": "╮",
        "bottom_left": "╰",
        "bottom_right": "╯",
    },
    "double": {
        "horizontal": "═",
        "vertical": "║",
        "top_left": "╔",
        "top_right": "╗",
        "bottom_left": "╚",
        "bottom_right": "╝",
    },
}
```

## Border Styles

```python
from rich.style import Style
from rich.border import Border, Box

# Standard panel border
PANEL_BORDER = Border(
    left=Style(color="#3B3B5C"),
    right=Style(color="#3B3B5C"),
    top=Style(color="#3B3B5C"),
    bottom=Style(color="#3B3B5C"),
)

# Highlighted/active panel
ACTIVE_BORDER = Border(
    left=Style(color="#7AA2F7", bold=True),
    right=Style(color="#3B3B5C"),
    top=Style(color="#7AA2F7", bold=True),
    bottom=Style(color="#3B3B5C"),
)

# Error/focused border
ERROR_BORDER = Border(
    left=Style(color="#F7768E", bold=True),
    right=Style(color="#F7768E"),
    top=Style(color="#F7768E", bold=True),
    bottom=Style(color="#F7768E"),
)
```
