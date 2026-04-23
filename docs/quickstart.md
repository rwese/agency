# Agency Quickstart

Build projects with AI agents using tmux-based orchestration.

## Prerequisites

```bash
# Install Agency
uv pip install -e ~/Repos/github.com/rwese/agency

# Verify
agency --version
```

## 5-Minute Project Setup

### 1. Create Project Directory

```bash
mkdir ~/projects/my-new-project
cd ~/projects/my-new-project
git init
```

### 2. Initialize Agency

```bash
agency init --template minimal
```

**Templates:**
| Template | Agents | Use Case |
|----------|--------|----------|
| `minimal` | 1 (coder) | Simple projects, single-file apps |
| `fullstack-ts` | 6 | Full-stack web apps |

### 3. Copy Extensions (If Missing)

If extensions fail to copy during init:

```bash
mkdir -p .agency/pi/extensions
cp -r ~/Repos/github.com/rwese/agency/extras/pi/extensions/* .agency/pi/extensions/
```

### 4. Configure Manager

Edit `.agency/manager.yaml`:

```yaml
name: coordinator
personality: |
  You are the project coordinator for [PROJECT NAME].

  ## Your Task
  Manage a single coder agent.

  ## Workflow
  1. Create tasks: agency tasks add -d "description"
  2. Assign: agency tasks assign <id> coder
  3. Review: agency tasks show <id>
  4. Approve: agency tasks update <id> --status completed

  ## Context
  See PLAN.md for project specification.

poll_interval: 30
auto_approve: false
```

### 5. Write PLAN.md

```markdown
# Project Plan: [Name]

## Scope
**Goals:**
- Feature A
- Feature B

**Non-Goals:**
- Cloud sync
- User auth

## Tech Stack
- **Language:** Python
- **Framework:** Flask
- **Storage:** SQLite

## Milestones

### M1 - Foundation
#### M1.1 Task - Criteria: ...

### M2 - Features
#### M2.1 Task - Criteria: ...

## Definition of Done
A task is **done** when:
- Code written and runs
- No debug code or TODOs
```

## Running the Session

### Start

```bash
agency session start
```

### Attach/Detach

```bash
agency session attach
# Ctrl+b d to detach
```

### Monitor Progress

```bash
# In another terminal
tmux -L agency-[project] capture-pane -t agency-[project]:coder -p | tail -30
```

### Stop

```bash
agency session stop agency-[project]
```

## Task Management

```bash
# Create tasks
agency tasks add -d "Implement feature X"
agency tasks add -d "Create UI components"

# Assign to coder
agency tasks assign <task-id> coder

# Track progress
agency tasks list
agency tasks show <task-id>

# Mark complete
agency tasks update <task-id> --status completed
```

## Typical Workflow

```
┌─────────────────────────────────────────────────────────┐
│ 1. mkdir ~/projects/my-app && cd $_ && git init         │
│ 2. agency init --template minimal                      │
│ 3. Edit .agency/manager.yaml                          │
│ 4. Write PLAN.md                                      │
│ 5. agency session start                                │
│ 6. agency tasks add -d "..."                           │
│ 7. agency tasks assign <id> coder                      │
│ 8. Monitor via tmux capture                            │
│ 9. Review completed tasks                              │
│ 10. agency session stop                                │
└─────────────────────────────────────────────────────────┘
```

## Task Design

| Complexity | Tasks | Example |
|------------|-------|---------|
| Simple | 3-5 | Single HTML file, CLI tool |
| Medium | 8-10 | Frontend + backend |
| Complex | 10+ | Full-stack, microservices |

**Each task needs:**
- Clear description
- Acceptance criteria
- Implicit order via creation sequence

## Gitignore

```bash
cat >> .gitignore << 'EOF'

# Agency runtime
.agency/run/
.agency/var/notifications.json
.agency/var/*.db
.agency/var/*.db-shm
.agency/var/*.db-wal
.agency/pi/sessions/
.agency/.heartbeat-*.pid
.agency/.heartbeat-*.log
.agency/var/pending/
.agency/var/system_hint.txt
EOF
```

## Known Issues

### Issue: `readonly AGENCY_DIR` error

**Cause:** Script declares `readonly` then tries `export AGENCY_DIR`

**Fix:**
```bash
sed -i '' 's/readonly AGENCY_DIR=/AGENCY_DIR=/' \
  ~/Repos/github.com/rwese/agency/src/agency/session.py
```

### Issue: `tasks-agent` command not found

**Fix:**
```bash
sed -i '' 's/agency tasks-agent/agency tasks/g' \
  ~/Repos/github.com/rwese/agency/src/agency/session.py
```

### Issue: Extensions not copied

**Cause:** Path resolution bug in `__main__.py`

**Fix:** Manually copy (see Step 3 above)

## File Structure

```
.agency/
├── config.yaml           # Project settings
├── manager.yaml          # Coordinator personality
├── agents.yaml           # Agent registry
├── agents/
│   └── coder.yaml        # Coder personality
├── pi/                   # Extensions
│   └── extensions/
├── var/
│   ├── tasks.json        # Task definitions
│   └── tasks/            # Task results
└── run/                  # Runtime (gitignore)
```

## Next Steps

- See [examples/demo-brutal-notes](./examples/demo-brutal-notes/) for a complete walkthrough
- Read [AGENTS.md](../AGENTS.md) for agent configuration
- Check [design/](../design/) for architecture docs
