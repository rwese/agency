# Layout Patterns

## Grid Layouts

### Three-Column Dashboard

```
┌─────────────────────────────────────────────────────────────────────┐
│ Header: Agency TUI                              [status indicators] │
├───────────────┬─────────────────────────────┬───────────────────────┤
│               │                             │                       │
│  Sessions     │     Activity Feed           │    Task Board         │
│  Panel        │     (scrollable log)         │    (kanban-style)     │
│  (narrow)     │                             │                       │
│               │                             │                       │
│  - session1   │     [timestamp] Action      │    To Do │ Done      │
│  - session2   │     [timestamp] Action       │    ─────│─────       │
│  - manager    │                             │    task1 │ task3      │
│               │                             │    task2 │            │
│               │                             │                       │
├───────────────┴─────────────────────────────┴───────────────────────┤
│ Input: [message box                                          ] [→] │
├─────────────────────────────────────────────────────────────────────┤
│ Footer: q=quit r=refresh a=attach s=send n=new m=manager ?=help    │
└─────────────────────────────────────────────────────────────────────┘
```

### Split Panel with Tabs

```
┌─────────────────────────────────────────────────────────────────────┐
│ Agency  │ Sessions │ Tasks │ Chat │ [+]                            │
├─────────┴──────────┴───────┴──────┴─────────────────────────────────┤
│                                                                     │
│  ┌─ Sessions ──────────────────────────────────────────────────┐    │
│  │  🤖 project-api          👑 coordinator                    │    │
│  │     └ coder                 └ orchestrator                 │    │
│  │     └ tester                                            │    │
│  │                                                           │    │
│  └───────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─ Details ───────────────────────────────────────────────────┐   │
│  │  Selected: agency-project-api / coder                      │   │
│  │  Status: Running | Uptime: 2h 34m | Memory: 128MB          │   │
│  │                                                           │   │
│  │  Recent:                                                   │   │
│  │  > 14:32 Fixed authentication bug in login.py              │   │
│  │  > 14:28 Running tests for auth module...                   │   │
│  │  > 14:25 Starting work on session management                │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│ [message input...]                                                  │
└─────────────────────────────────────────────────────────────────────┘
```

### Master-Detail View

```
┌─────────────────────────────────────────────────────────────────────┐
│ ╔═══════════════════════════════════════════════════════════════╗ │
│ ║  Agency - AI Agent Manager                               [─][□][×]║ │
│ ╠═══════════════════════════════════════════════════════════════╣ │
│ ║ ┌─────────────┐ ┌───────────────────────────────────────────┐ ║ │
│ ║ │ SESSIONS    │ │ DETAILS                                   │ ║ │
│ ║ ├─────────────┤ │                                           │ ║ │
│ ║ │ ▶ coder     │ │ Session: agency-demo                       │ ║ │
│ ║ │   └ dev     │ │ Agent: coder                              │ ║ │
│ ║ │   └ test    │ │ Status: ● Running                         │ ║ │
│ ║ │             │ │                                           │ ║ │
│ ║ │ 👑 manager  │ │ ┌─────────────────────────────────────┐   │ ║ │
│ ║ │   └ coord   │ │ │  Terminal Output (scrollable)       │   │ ║ │
│ ║ │             │ │ │                                     │   │ ║ │
│ ║ ├─────────────┤ │ │  $ Working on auth module...        │   │ ║ │
│ ║ │ TASKS       │ │ │  $ Tests passed: 12/12               │   │ ║ │
│ ║ ├─────────────┤ │ │  $ Committing changes...             │   │ ║ │
│ ║ │ ⏳ TASK001  │ │ │                                     │   │ ║ │
│ ║ │ ✅ TASK002  │ │ └─────────────────────────────────────┘   │ ║ │
│ ║ │ 🔄 TASK003  │ │                                           │ ║ │
│ ║ └─────────────┘ └───────────────────────────────────────────┘ ║ │
│ ╠═══════════════════════════════════════════════════════════════╣ │
│ ║ > Type message to coder...                              [Send] ║ │
│ ╚═══════════════════════════════════════════════════════════════╝ │
└─────────────────────────────────────────────────────────────────────┘
```

### Card-Based Dashboard

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AGENCY DASHBOARD                              │
│                     ═══════════════════════                          │
├─────────────────┬─────────────────┬─────────────────────────────────┤
│                 │                 │                                  │
│  ┌───────────┐  │  ┌───────────┐  │  ┌────────────────────────┐    │
│  │ Sessions  │  │  │  Tasks    │  │  │   Activity Feed       │    │
│  │   ─────   │  │  │  ─────    │  │  │   ──────────────      │    │
│  │  3 active │  │  │  12 total │  │  │                       │    │
│  │           │  │  │           │  │  │  • coder committed    │    │
│  │  ◉ api    │  │  │  ⏳ 3      │  │  │  • tester ready       │    │
│  │  ◉ web    │  │  │  🔄 5      │  │  │  • manager assigned  │    │
│  │  ◉ docs   │  │  │  ✅ 4      │  │  │                       │    │
│  │           │  │  │  ❌ 0      │  │  │                       │    │
│  └───────────┘  │  └───────────┘  │  └────────────────────────┘    │
│                 │                 │                                  │
├─────────────────┴─────────────────┴─────────────────────────────────┤
│  [message input...]                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

## Navigation Patterns

### Tab Bar

```
┌─────────────────────────────────────────────────────────────────────┐
│  [SESSIONS]  [TASKS]  [CHAT]  [SETTINGS]                [?] [×]   │
└─────────────────────────────────────────────────────────────────────┘
```

### Breadcrumb Navigation

```
Sessions  >  agency-demo  >  coder
────────────────────────────────────────────
│ Selected: coder                              │
│ Path: /projects/demo                         │
└─────────────────────────────────────────────┘
```

### Tree View (Collapsible)

```
📁 Sessions
├── 📁 agency-demo
│   ├── 🤖 coder
│   └── 🤖 tester
├── 📁 agency-web
│   ├── 🤖 frontend
│   └── 🤖 backend
└── 👑 coordinator
    └── 🤖 orchestrator
```

## Responsive Considerations

### Narrow Terminal (< 80 cols)

```
┌──────────────────────┐
│ Agency    [≡] [q]    │
├──────────────────────┤
│ Sessions │ Tasks     │
│ ──────── │ ────────  │
│ ● api    │ ⏳ T001   │
│ ○ web    │ ✅ T002   │
│ 👑 mgr   │ 🔄 T003   │
├──────────────────────┤
│ > message...    [→]  │
├──────────────────────┤
│ q=quit r=refresh     │
└──────────────────────┘
```

### Wide Terminal (> 120 cols)

```
┌───────────────┬───────────────────────────────┬─────────────────────────────────────┐
│ Sessions      │ Tasks                    │ Activity                                │
│ ───────────── ├─────────────────────────────┼─────────────────────────────────────│
│ ● api         │ ⏳ TASK001: Auth API    │ [14:32] coder: Running tests...         │
│   ├ coder     │ 🔄 TASK002: UI Fix     │ [14:30] tester: All tests passed        │
│   └ tester    │ ✅ TASK003: Setup CI   │ [14:28] manager: Task assigned to coder │
│ ○ web         │                         │                                         │
│               │                         │                                         │
├───────────────┴─────────────────────────────┴─────────────────────────────────────│
│ > Type message to coder...                                                          │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Layout Principles

1. **Hierarchy**: Most important info (sessions, current target) at top-left
2. **Density**: Compact but readable; use abbreviations for secondary info
3. **Grouping**: Related items together; clear separation between sections
4. **Affordance**: Visual indicators for interactive elements (▶ ● ◎)
5. **Scrolling**: Long content in scrollable containers with scrollbars
6. **Empty states**: Show helpful messages when lists are empty
