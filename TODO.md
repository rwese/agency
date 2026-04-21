# Task: Task Management Integration

## Status

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
| 9 | Document task format | [ ] |
| 10 | Remove demo data | [x] |

## Notes
- Task data: `~/.config/agency/sessions/tasks.json`
- Status values: `pending`, `in_progress`, `completed`, `failed`

## TUI Keybindings for Tasks
- `c` - Create task (uses selected agent as assignee)
- `u` - Update task status (cycles: pending → in_progress → completed → failed)
- `d` - Delete selected task

## CLI Commands
```bash
agency tasks list                    # List all tasks
agency tasks add -d "Description"   # Create task
agency tasks add -d "..." -a coder # Create with assignee
agency tasks update <id> --status in_progress
agency tasks update <id> --assignee tester
agency tasks show <id>              # Show task details
agency tasks delete <id>            # Delete task
```
