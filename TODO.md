# Agency TUI - v1.1 Fixes

## Critical Fixes

- [ ] Fix message targeting: send to selected agent, not first
- [ ] Add `m` keybinding to start managers
- [ ] Fix cursor navigation: ←/→ switch panels, ↑/↓ navigate within

## v2 (Deferred)

- [ ] Agent status indicators (idle/busy)
- [ ] Message history panel
- [ ] Session uptime display

## Fixed: Message Targeting

**Current behavior:** Always sends to first agent in session

**Desired behavior:**
1. User navigates session list with j/k
2. Each session shows its agents as sub-items
3. User selects specific agent/window
4. Press `s` to send message to that specific agent

## Fixed: Cursor Navigation

**Current:** j/k bindings conflict between SessionList and TaskBoard widgets

**Desired:**
- `←` / `→` - switch focus between panels
- `↑` / `↓` - navigate within focused panel
- `Enter` - select/confirm in focused panel

## Fixed: Start Manager

**Add:** `m` keybinding to start a manager (similar to `n` for agents)
