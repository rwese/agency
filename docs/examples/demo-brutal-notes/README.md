# Case Study: Demo Brutal Notes

A complete walkthrough of building a single-file brutalist note-taking app using Agency.

## Project Overview

**Goal:** Build a lightweight browser-based note-taking app with brutalist design.

**Result:** 504-line single HTML file with sidebar, editor, and localStorage persistence.

**Time:** ~20 minutes from setup to complete app.

## Timeline

| Time | Event |
|------|-------|
| +0:00 | Project directory created, git init |
| +1:00 | Plan created, Agency initialized |
| +2:00 | Tasks created (8 tasks) |
| +5:00 | Bug fixes applied |
| +7:00 | Extensions copied manually |
| +9:00 | Session started |
| +11:00 | HTML skeleton completed |
| +12:00 | All features implemented |
| +17:00 | Testing completed |
| +20:00 | Session stopped, commits made |

## Step-by-Step

### 1. Create Project

```bash
mkdir ~/projects/demo-brutal-notes
cd ~/projects/demo-brutal-notes
git init
```

### 2. Write PLAN.md

```markdown
# Project Plan: Demo Brutal Notes

## Scope
**Goals:**
- Sidebar listing all notes
- Center editor with title + content
- Create, edit, delete notes
- Persist to localStorage
- Brutalist visual design

**Non-Goals:**
- Cloud sync
- Rich text
- Search

## Tech Stack
- HTML, CSS, Vanilla JS
- No dependencies
- localStorage

## Design Direction: Brutalist
- Raw black/white palette + yellow accent
- 4px solid borders
- No rounded corners, no shadows
- Bold uppercase typography
```

### 3. Initialize Agency

```bash
agency init --template minimal
```

**Note:** The minimal template creates a single coder agent—perfect for this simple project.

### 4. Configure Manager

Edit `.agency/manager.yaml`:

```yaml
name: coordinator
personality: |
  You are the project coordinator for Demo Brutal Notes.

  Demo Brutal Notes is a simple single-file browser-based note-taking app.

  ## Your Task
  Manage a single coder agent who implements the app.

  ## Workflow
  1. Create tasks with agency tasks add -d "description"
  2. Assign to coder: agency tasks assign <id> coder
  3. Review completed tasks with agency tasks show <id>
  4. Approve with agency tasks update <id> --status completed
```

### 5. Configure Coder

Edit `.agency/agents/coder.yaml`:

```yaml
name: coder
personality: |
  You are the coder for Demo Brutal Notes.

  ## Project Context
  - Single HTML file: index.html
  - Brutalist design
  - localStorage for persistence

  ## Your Role
  1. Check assigned tasks: agency tasks list
  2. Read PLAN.md for requirements
  3. Implement the feature
  4. Mark task complete

parallel_limit: 1
```

### 6. Create Tasks

```bash
agency tasks add -d "Create index.html with HTML skeleton"
agency tasks add -d "Add CSS: grid layout, brutalist styling"
agency tasks add -d "Add localStorage helpers: getNotes(), saveNote()"
agency tasks add -d "Implement sidebar note list"
agency tasks add -d "Implement editor with auto-save"
agency tasks add -d "Add delete with confirmation"
agency tasks add -d "Final polish pass"
agency tasks add -d "Final testing"
```

### 7. Start Session

```bash
agency session start
```

### 8. Monitor Progress

In another terminal:

```bash
tmux -L agency-demo-brutal-notes capture-pane -t agency-demo-brutal-notes:coder -p | tail -30
```

### 9. Watch Tasks Complete

```
agency tasks list
## cache-json-5e1d
- status: completed ✅
- description: Create index.html with HTML skeleton

## crow-graph-275e
- status: completed ✅
- description: Add CSS: grid layout, brutalist styling

...
```

## What Worked

### 1. Pre-Created Tasks

Clear task breakdown made assignment easy. Each task had acceptance criteria.

### 2. PLAN.md Document

Gave coder context and acceptance criteria without constant clarification.

### 3. Single Coder Model

Simple projects don't need multiple agents. One coder was faster and simpler.

### 4. Minimal Template

The fullstack-ts template was overkill. Minimal was perfect.

## What to Improve

### 1. Task Count (8 → 3-4)

8 tasks was too granular for a single-file app. The coder completed 7 in one go.

**Better approach:** Create 3-5 larger milestones:
- `setup-foundation` - HTML structure + CSS
- `implement-storage` - localStorage CRUD
- `implement-ui` - Sidebar + editor
- `finalize` - Polish + testing

### 2. Extension Copying

Silent failure during init. Required manual workaround.

**Better:** Validate paths, show clear error if extensions missing.

### 3. Browser Testing

agent-browser click command hung (132s).

**Better:** Use simpler test approach:
- Manual verification
- Mock tests
- Console assertions

### 4. Task Auto-Assignment

Heartbeat didn't auto-assign. Manual assignment required.

**Better:** Let heartbeat poll for unassigned tasks and auto-assign.

## Bugs Found

| Bug | Fix |
|-----|-----|
| `readonly AGENCY_DIR` conflicts with `export` | Remove `readonly` |
| `$NOFRILLS_ENV` executed as command | Change to `eval $NOFRILLS_ENV` |
| Extension path goes to `src/` not repo root | Add one more `parent` level |
| `tasks-agent` command doesn't exist | Change to `agency tasks` |

## Files Created

```
~/projects/demo-brutal-notes/
├── index.html                    # The app (504 lines)
├── PLAN.md                       # Project specification
├── PROCESS_REVIEW.md             # Process learnings
├── AGENCY_QUICKSTART.md          # Quick reference
└── .agency/
    ├── config.yaml
    ├── manager.yaml
    ├── agents.yaml
    ├── agents/coder.yaml
    └── var/tasks/                # Task history
```

## Key Learnings

1. **Start simple** - Use `minimal` template unless you need multiple agents
2. **Git first** - Always `git init` before `agency init`
3. **Fewer tasks** - Better to have 5 medium tasks than 20 tiny ones
4. **Good context** - Better PLAN.md = better code with less back-and-forth
5. **Monitor first task** - Watch the first task completion closely
6. **Clean commits** - Commit after milestones, not after every task

## Commands Reference

```bash
# Setup
mkdir ~/projects/demo-brutal-notes && cd $_
git init
agency init --template minimal
mkdir -p .agency/pi/extensions
cp -r ~/Repos/github.com/rwese/agency/extras/pi/extensions/* .agency/pi/extensions/

# Session
agency session start
agency session attach        # Ctrl+b d to detach
agency session stop

# Monitoring
tmux -L agency-demo-brutal-notes capture-pane -t agency-demo-brutal-notes:coder -p | tail -30

# Tasks
agency tasks add -d "..."
agency tasks assign <id> coder
agency tasks list
agency tasks show <id>
agency tasks update <id> --status completed
```

## Related

- [Quickstart](../quickstart.md) - General quickstart guide
- [AGENTS.md](../../AGENTS.md) - Agent configuration
