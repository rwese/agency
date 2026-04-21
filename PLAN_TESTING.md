# Plan: TUI E2E Testing

## Overview

Create end-to-end tests for the Agency TUI using expect scripts. Tests will verify:
- Panel navigation
- Session management
- Task management
- Messaging
- Full workflow

## Research Summary

- `expect` available at `/usr/bin/expect`
- Current `test_agency.sh` covers CLI only, no TUI tests
- TUI keybindings:
  - `←/→` - Switch panels
  - `↑/↓` - Navigate within panel
  - `Enter` - Select/expand
  - `a` - Attach to session
  - `s` - Focus message input
  - `n` - Start new agent
  - `m` - Start new manager
  - `x` - Stop agent
  - `c` - Create task
  - `u` - Update task status
  - `d` - Delete task
  - `?` - Help
  - `q` - Quit

## Requirements

| Requirement | Answer |
|-------------|--------|
| Coverage | Navigation, Sessions, Tasks, Messaging, Full Workflow |
| Format | Expect scripts |
| Cleanup | Bash trap for cleanup |

## File Structure

```
test_tui/
├── expect_helpers.exp     # Reusable expect functions
├── test_tui_nav.exp       # Panel navigation
├── test_tui_tasks.exp     # Task CRUD
├── test_tui_sessions.exp   # Session management
└── test_tui_full.exp      # Full workflow
```

## TODO Tasks

| # | Task | Acceptance Criteria | Priority |
|---|------|---------------------|----------|
| 1 | Create expect helper library | `expect_helpers.exp` with send_key, wait_for, cleanup | high |
| 2 | Test panel navigation | `←/→` switches panels, `↑/↓` navigates | high |
| 3 | Test task creation | Press `c` creates new task | high |
| 4 | Test task update | Press `u` cycles status | high |
| 5 | Test task deletion | Press `d` deletes selected task | high |
| 6 | Test message sending | Type message, send to agent | med |
| 7 | Test start/stop agent | `n` starts, `x` stops | med |
| 8 | Full workflow test | Create session → start agent → create task → send message → cleanup | high |
| 9 | Integrate with test_agency.sh | Run TUI tests after CLI tests | high |

## Test Scenarios

### 1. Launch TUI
```bash
agency tui
# Verify: Sessions panel visible, Tasks panel visible, Activity Log visible
```

### 2. Panel Navigation
```bash
# Press → → Tasks panel active (◀ indicator moves)
# Press ↓ → Navigate tasks
# Press ← → Sessions panel active
# Press ↓ → Navigate sessions
```

### 3. Task Management
```bash
# In Tasks panel:
# Press c → new task created, shown in list
# Press u → task status cycles (pending → in_progress → completed → failed)
# Press d → task deleted
```

### 4. Session Management
```bash
# In Sessions panel:
# Select session → press Enter → expand agents
# Select agent → press a → tmux attach (timeout/exit)
```

### 5. Full Workflow
```bash
# 1. Start session: agency start coder --dir /tmp/test-e2e
# 2. Launch TUI
# 3. Navigate to Tasks panel
# 4. Create task: press c
# 5. Navigate to Sessions panel
# 6. Select session/agent
# 7. Send message: press s, type "do the task", Enter
# 8. Update task status: navigate to task, press u
# 9. Cleanup: press x to stop agent, agency kill
```

## Helper Library API

### expect_helpers.exp
```tcl
proc launch_tui {}          # Launch agency tui in tmux
proc send_key {key}         # Send a key
proc send_text {text}       # Type text
proc wait_for {pattern}      # Wait for text pattern
proc press_enter {}         # Send Enter key
proc cleanup {}             # Kill tmux sessions
proc assert_visible {text}  # Assert text visible
```

## Cleanup Strategy

```bash
trap cleanup EXIT INT TERM
cleanup() {
    tmux -L agency kill-session -t agency-* 2>/dev/null
    rm -rf /tmp/test-e2e-* 2>/dev/null
}
```

## Success Criteria

- [ ] All expect scripts exit with code 0
- [ ] tmux sessions cleaned up after each test
- [ ] Tests run headless (no visible window)
- [ ] Tests integrate with `test_agency.sh`
- [ ] Tests timeout after 30s if stuck

## Example Test Template

```tcl
#!/usr/bin/expect -f
source expect_helpers.exp

set test_name "Panel Navigation"
puts "Testing: $test_name"

launch_tui

# Test: Sessions panel active by default
assert_visible "Sessions"
assert_visible "◀"

# Test: Press → to switch to Tasks
send_key "→"
wait_for "Tasks ◀"

# Test: Press ↓ to navigate tasks
send_key "↓"
assert_visible "TASK"

cleanup
puts "PASS: $test_name"
exit 0
```
