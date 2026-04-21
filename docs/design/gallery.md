# Inspiration Gallery

## Screenshots & Visual References

### Textual Widget Gallery

![Textual Widgets](https://textual.textualize.io/assets/images/widget-gallery.png)

- **Source**: [Reddit r/programming](https://www.reddit.com/r/programming/comments/11kw98o/textual_tui_framework_widget_gallery/)
- **Features**: Buttons, inputs, checkboxes, switches, progress bars

### Beautiful TUI Apps

**1. Lazygit**
```
┌─────────────────────────────────────────────────────────────┐
│  repos  │  files  │  status                    │  main      │
├─────────┼─────────┼────────────────────────────┼────────────┤
│         │         │                           │            │
│  ✓ agency    │  app.py         │ M app.py         │            │
│  ✓ web-ui     │  config.py     │ A new.py         │            │
│  ✓ api        │  utils.py       │                  │            │
│  ○ docs       │                 │                  │            │
│               │                 │                  │            │
│               │                 │                  │            │
├───────────────┴─────────────────┴──────────────────┴────────────┤
│ > git status                                                    │
└─────────────────────────────────────────────────────────────────┘
```
- **Repo**: [jesseduffield/lazygit](https://github.com/jesseduffield/lazygit)
- **Style**: Split panes, vim-like navigation, syntax highlighting

**2. GitUI**
- **Repo**: [Extrawurst/gitui](https://github.com/Extrawurst/gitui)
- **Style**: Dark theme, table layouts, modal dialogs

**3. Yazi**
```
┌─────────────────────────────────────────────────────────────┐
│  media  │  Pictures  │  📁 vacation                    │
├─────────┴───────────┴──────────────────────────────────────┤
│                                                           │
│   📁 2024                    📁 beach                      │
│   📁 2025                    📁 mountains                 │
│                                📁 city                     │
│   📄 notes.txt                                          │
│   📄 todos.md                                            │
│                                                           │
├─────────────────────────────────────────────────────────────┤
│  12 items  │  2.3GB  │  /home/user/Pictures              │
└─────────────────────────────────────────────────────────────┘
```
- **Repo**: [sxyazi/yazi](https://github.com/sxyazi/yazi)
- **Style**: Clean file browser, preview pane, status bar

**4. Wtftis (chess-tui)**
```
┌─────────────────────────────────────────────────────────────┐
│                    ♜ ♞ ♝ ♛ ♚ ♝ ♞ ♜                        │
│                    ♟ ♟ ♟ ♟ ♟ ♟ ♟ ♟                        │
│                                                           │
│                    ♙ ♙ ♙ ♙ ♙ ♙ ♙ ♙                        │
│                    ♖ ♘ ♗ ♕ ♔ ♗ ♘ ♖                        │
│                                                           │
├─────────────────────────────────────────────────────────────┤
│  White to move  │  Move 15/40  │  ♟ x2  ♙ x3  │  05:32   │
└─────────────────────────────────────────────────────────────┘
```
- **Style**: ASCII chess, clean board rendering

**5. Gum CLI Prompts**
```bash
╭──────────────────────────────────────────────────────────────╮
│  What would you like to do today?                           │
│                                                            │
│    ◉ Build a new feature                                    │
│    ○ Fix a bug                                             │
│    ○ Write documentation                                    │
│    ○ Review pull requests                                   │
│                                                            │
│                            [ Select ]  [ Cancel ]           │
╰──────────────────────────────────────────────────────────────╯
```
- **Repo**: [charmbracelet/gum](https://github.com/charmbracelet/gum)
- **Style**: Interactive prompts, spinner animations

## Screenshot Resources

### Curated TUI Screenshots

| Source | Description |
|--------|-------------|
| [Terminal Trove](https://terminaltrove.com/) | New terminal apps with screenshots |
| [r/unixporn](https://reddit.com/r/unixporn) | Desktop/window themes (rice) |
| [r/programming](https://reddit.com/r/programming) | TUI framework showcases |
| [awesome-tuis](https://github.com/rothgar/awesome-tuis) | List with many screenshots |

### Textual Projects Gallery

| Project | Description |
|---------|------------|
| [textual-timeclock](https://github.com/leonardops timeclock) | Time tracking app |
| [cotton](https://github.com/mikepartelow/cotton) | HTTP testing |
| [textual-paint](https://github.com/ofk/textual-paint) | MS Paint clone |

## Design Pattern References

### Terminal Chat Interfaces

```
┌─────────────────────────────────────────────────────────────────────┐
│  Agency Chat                                                    [─][□][×]│
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [14:32] 👑 coordinator                                           │
│           Delegating TASK001 to coder                              │
│                                                                     │
│  [14:33] 🤖 coder                                                 │
│           Working on authentication module...                      │
│                                                                     │
│  [14:34] 🤖 coder                                                 │
│           Found issue in JWT handling                             │
│                                                                     │
│  [14:35] 👑 coordinator                                           │
│           Please prioritize auth fixes                             │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  > Type message...                                    [Send]       │
└─────────────────────────────────────────────────────────────────────┘
```

**Similar Projects:**
- [Slack-term](https://github.com/erroneousboat/slack-term)
- [Discord TUI clients](https://github.com/chatta/rainbow)

### Task/Kanban Boards

```
┌─────────────────────────────────────────────────────────────────────┐
│  Agency Tasks                                                       │
├─────────────┬─────────────┬─────────────┬───────────────────────────┤
│  To Do      │  In Progress│  Review    │  Done                      │
├─────────────┼─────────────┼─────────────┼───────────────────────────┤
│             │             │             │                           │
│ ┌─────────┐ │ ┌─────────┐ │ ┌─────────┐ │ ┌─────────┐               │
│ │ TASK001 │ │ │ TASK003 │ │ │ TASK005 │ │ │ TASK002 │               │
│ │ Auth    │ │ │ UI Fix  │ │ │ Tests   │ │ │ Setup   │               │
│ │ @coder  │ │ │ @designer│ │ │ @tester │ │ │ @coordinator│         │
│ └─────────┘ │ └─────────┘ │ └─────────┘ │ └─────────┘               │
│             │             │             │                           │
│ ┌─────────┐ │             │             │                           │
│ │ TASK006 │ │             │             │                           │
│ │ Docs    │ │             │             │                           │
│ │ @writer │ │             │             │                           │
│ └─────────┘ │             │             │                           │
│             │             │             │                           │
├─────────────┴─────────────┴─────────────┴───────────────────────────┤
│  6 tasks  │  1 completed                                            │
└─────────────────────────────────────────────────────────────────────┘
```

**Inspiration:**
- [copilot-cli-board](https://github.com/likamrat/copilot-cli-board) - Agent Kanban

### Dashboard with Cards

```
┌─────────────────────────────────────────────────────────────────────┐
│  AGENCY DASHBOARD                                                   │
├─────────────────────┬─────────────────────┬─────────────────────────┤
│                     │                     │                         │
│   ┌─────────────┐   │   ┌─────────────┐   │   ┌─────────────────┐  │
│   │  Sessions   │   │   │    Tasks    │   │   │    Activity     │  │
│   │  ─────────  │   │   │  ─────────  │   │   │  ─────────────  │  │
│   │             │   │   │             │   │   │                 │  │
│   │  ● demo     │   │   │  ⏳ 3       │   │   │  • coder: started│  │
│   │  ○ web      │   │   │  🔄 2       │   │   │  • tester: done │  │
│   │  👑 mgr     │   │   │  ✅ 5       │   │   │  • mgr: assigned│  │
│   │             │   │   │  ❌ 0       │   │   │                 │  │
│   │  3 active   │   │   │  10 total   │   │   │  Recent 5      │  │
│   └─────────────┘   │   └─────────────┘   │   └─────────────────┘  │
│                     │                     │                         │
├─────────────────────┴─────────────────────┴─────────────────────────┤
│  System Status: ● Connected  │  Memory: 256MB  │  Uptime: 4h 23m     │
└─────────────────────────────────────────────────────────────────────┘
```

## Typography References

### Monospace Fonts for Terminal

| Font | Style | Best For |
|------|-------|----------|
| [JetBrains Mono](https://www.jetbrains.com/lp/mono/) | Modern, ligatures | General coding |
| [Fira Code](https://github.com/tonsky/FiraCode) | Programming ligatures | Code readability |
| [Source Code Pro](https://adobe-fonts.github.io/source-code-pro/) | Clean, neutral | Long sessions |
| [Hack](https://sourcefoundry.org/hack/) | Bitstream Vera | Traditional |
| [Iosevka](https://github.com/be5invis/Iosevka) | Customizable | Power users |

### Font Settings for TUI

```python
# Terminal font recommendations
FONT_CONFIG = {
    "family": "JetBrains Mono",
    "size": 14,  # or 12 for denser layouts
    "line_height": 1.2,
    "ligatures": True,  # if supported
}
```

## Color Harmony

### Analogous Colors

```
Tokyonight Purple: #9D7CD8
                 ↓
Blue: #7AA2F7 ← Cyan: #7DCFFF
                 ↑
       Green: #9ECE6A
```

### Complementary Accents

```
Primary: #7AA2F7 (Blue)
     ↓
Complement: #F7768E (Red/Pink)
     ↓
Success: #9ECE6A (Green)
```

## Animation Ideas

### Loading States

```
⠋ Loading      ⠙ Loading      ⠹ Loading
⠸ Loading  →   ⠴ Loading  →   ⠦ Loading
⠧ Loading      ⠇ Loading      ⠏ Loading
```

### Progress Indicators

```
[████░░░░░░] 50%
[██████░░░░] 60%
[████████░░] 80%
[██████████] 100% ✓
```

### Typing Indicator

```
Agent is typing...
⠋
⠙
⠹
⠸
⠼  ← cycling
```
