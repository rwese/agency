# Task: Task Management Integration ✅

## Completed

| # | Task | Status |
|---|------|--------|
| 1 | Add `agency tasks` CLI command group | [x] |
| 2 | Implement `agency tasks add` | [x] |
| 3 | Implement `agency tasks list` | [x] |
| 4 | Implement `agency tasks update` | [x] |
| 5 | Implement `agency tasks delete` | [x] |
| 6 | Wire TUI to create tasks | [x] |
| 7 | Wire TUI to update task status | [x] |
| 8 | Wire TUI to delete tasks | [x] |
| 9 | Document task format | [x] |
| 10 | Remove demo data | [x] |

## Usage

### CLI Commands
```bash
agency tasks list                    # List all tasks
agency tasks add -d "Description"   # Create task
agency tasks add -d "..." -a coder # Create with assignee
agency tasks update <id> --status in_progress
agency tasks update <id> --assignee tester
agency tasks show <id>              # Show task details
agency tasks delete <id>             # Delete task
```

### TUI Keybindings (in Tasks panel)
- `←/→` - Switch panels
- `↑/↓` - Navigate tasks
- `c` - Create task
- `u` - Update task status (cycles: pending → in_progress → completed → failed)
- `d` - Delete task
- `Enter` - Show task details

### Task Data Format
```json
{
  "TASK001": {
    "task_id": "TASK001",
    "description": "Implement user auth",
    "status": "pending|in_progress|completed|failed",
    "assigned_to": "coder",
    "created_at": "2026-04-21T10:00:00",
    "completed_at": null,
    "result": null
  }
}
```

### Storage
- Location: `~/.config/agency/sessions/tasks.json`
