# Agency Development TODO

## Status: In Progress

## Tasks

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Create `template_inject.py` module | [x] | Module with `TemplateInjector` class |
| 2 | Add custom delimiter support | [x] | Configurable placeholder pattern |
| 3 | Integrate into personality loading | [x] | Hook into session.py manager/agent launch |
| 4 | Integrate into context file processing | [x] | Process context files before append |
| 5 | Add tests | [x] | Unit tests for TemplateInjector |
| 6 | Update AGENTS.md documentation | [x] | Document placeholder syntax |

## Progress Log

- [2026-04-22] Plan approved, starting implementation
- [2026-04-22] Created `template_inject.py` with `TemplateInjector`, custom delimiter support
- [2026-04-22] Integrated template injection into session.py (manager + agent personality + context files)
- [2026-04-22] Added 23 unit tests for TemplateInjector, all passing
- [2026-04-22] Updated AGENTS.md with template injection documentation
- [2026-04-22] Added `template_delimiter` config option

---

## agency-web Testing (Greenfield Project)

### Bugs Found & Fixed

| # | Bug | Root Cause | Fix |
|---|-----|------------|-----|
| 1 | YAML multiline block parsing | `\|` literal blocks end at blank lines | Indent all content (headers, lists) inside multiline blocks |
| 2 | `.agency` deleted accidentally | `rm -rf agency-web/.agency` ran from wrong dir | Use absolute paths |
| 3 | Only default `developer` agent loaded | `agency_dir = git_root / ".agency"` assumes `.agency` at git root | Use `work_dir / ".agency"` |
| 4 | Tasks assigned to `developer` | Task assign used wrong agent name | Tasks assigned to `developer` instead of correct agent |

### Idle Detection for Stop

Implemented scrollback-based idle detection:
- `get_scrollback_hash()`: Get line count + MD5 hash of pane content
- `get_window_activity()`: Track last time scrollback changed  
- `is_window_idle()`: Check if pane idle for N seconds
- `get_idle_windows()`: List all idle windows

New stop command behavior:
- Broadcasts shutdown message to all windows
- Waits for windows to become idle (no scrollback changes)
- Kills idle windows after --idle seconds (default 10)
- Force kills after --timeout (default 300s)

### Key Learnings

1. **YAML multiline blocks**: When using `|` literal blocks, blank lines end the block. All subsequent content must be indented 2+ spaces.

2. **Project structure**: When creating a subdirectory project within a git repo, `.agency/` must be in the subdirectory, not at the git root.

3. **Template generation**: The `agency init --template` command downloads templates but doesn't properly override existing `.agency/` configs.

4. **tmux activity tracking**: `pane_last_activity` and `pane_silence_time` don't work in all tmux versions. Scrollback content hashing is more reliable.

5. **pi process management**: When pi says "Goodbye" and exits, the tmux pane shell stays open. Need to kill the window to fully terminate.

### Related Commits

- `fix(agency): use work_dir for .agency, not git_root`
- `feat(agency-web): add project scaffold and agency configuration`
- `feat(session): add scrollback-based idle detection for graceful stop`

### Open Issues

1. Stop command sometimes times out even with idle detection (pi may be waiting on input)
2. Session may not fully exit after all windows killed
3. Task assignment bug needs investigation in tasks.py
