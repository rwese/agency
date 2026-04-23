# Agency v2.0 - Agent Configuration

Tmux-based AI agent orchestration with project-centric model.

See `skill:agency` for usage instructions.

## Architecture

```
agency-<project>                    # tmux session + socket
├── [MGR] coordinator              # Manager (index 0)
├── coder                           # Agent (index 1+)
└── tester                          # Agent
```

**Relationships:**
- Project 1:1 Manager
- Project 1:N Agents
- Manager 1:N Tasks
- Agent 1:1 Task (active)

## Task Lifecycle

```
pending → in_progress → pending_approval → completed
                     ↓
                  failed (on reject)
```

## File Structure

```
<project-root>/
├── .agency/
│   ├── config.yaml           # Project settings
│   ├── manager.yaml          # Manager personality
│   ├── agents.yaml           # Agent registry
│   ├── var/                  # Session artifacts (for review)
│   │   ├── audit.db          # Audit log of all actions
│   │   ├── notifications.json # All notifications sent
│   │   ├── tasks.json        # Final task state
│   │   └── tasks/            # Per-task details
│   └── agents/               # Agent configs
└── src/
```

## Session Review

After a session ends, review session artifacts in `.agency/var/`:

```bash
# Review notification history (who was notified of what)
cat .agency/var/notifications.json | jq .

# Review audit trail
sqlite3 .agency/var/audit.db "SELECT * FROM events ORDER BY ts DESC LIMIT 50;"

# Review task completion states
cat .agency/var/tasks.json | jq '.tasks | to_entries[] | {id: .key, status: .value.status, agent: .value.assigned_to}'

# Check for manager review
cat .agency/var/tasks.json | jq '.tasks[].reviewer_assigned'
```

**Key session metrics:**
- Did manager review tasks? (`reviewer_assigned` should not be null)
- Did agents update status to `in_progress`? (`started_at` should be set)
- Were notifications sent? (check `notifications.json`)

## Configuration

### config.yaml

```yaml
$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/config.json
project: api
shell: bash
audit_enabled: true  # Set to false to disable audit logging
```

### manager.yaml

```yaml
$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/manager.json
name: coordinator
personality: |
  You are the project coordinator.

  ## Task Management
  - agency tasks list  # See pending
  - agency tasks assign <id> <agent>  # Assign
  - agency tasks add -d "..."  # Create

poll_interval: 30
auto_approve: false
```

### agents.yaml

```yaml
$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/agents.json
agents:
  - name: coder
    config: agents/coder.yaml
```

## Template Injection

Personality files support dynamic placeholders:

```
${{file:path}}      → Read file at path, inject contents
${{shell:cmd}}       → Execute command, inject stdout
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AGENCY_DIR` | Path to `.agency/` |
| `AGENCY_AGENT` | Agent name (set for agents) |
| `AGENCY_MANAGER` | Manager name (set for manager) |
| `AGENCY_ROLE` | `MANAGER` or `AGENT` |

## Development

```bash
# Install
uv pip install -e .

# Test
./test_agency.sh
uv run pytest

# Lint
uv run ruff check src/
uv run ruff format src/
```

## Design Documents

See `docs/design/` for complete specification:
- `v2.0-cli.md` - CLI reference
- `v2.0-workflows.md` - Workflows
- **`v2.0-requirements.md`** - **Operational rules (heartbeat, notifications, dos/don'ts, edge cases)**

## Boundaries

**ALWAYS**
- Run `./test_agency.sh` before committing
- Use `uv run agency` or `agency` (after install)

**NEVER**
- Commit with untested changes
- Leave running tmux sessions
- Store secrets in `.agency/`
