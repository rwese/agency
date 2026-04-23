# Agency Configuration Schemas

## File Structure

```
project/
├── .agency/
│   ├── config.yaml         # Project settings
│   ├── manager.yaml        # Manager personality
│   ├── agents.yaml         # Agent registry
│   ├── tasks/              # Task data
│   └── agents/             # Agent configs
└── src/                    # Project code
```

## config.yaml

```yaml
$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/config.json
project: myproject
shell: bash
parallel_limit: 3
audit_enabled: true  # Set to false to disable audit logging
```

## manager.yaml

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

## agents.yaml

```yaml
$schema: https://raw.githubusercontent.com/rwese/agency/main/src/agency/schemas/agents.json
agents:
  - name: coder
    config: agents/coder.yaml
```

## Template Injection

Personality files support dynamic placeholders:

| Placeholder | Result |
|-------------|--------|
| `${{file:path}}` | Read file at path, inject contents |
| `${{shell:cmd}}` | Execute command, inject stdout |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AGENCY_DIR` | Path to `.agency/` |
| `AGENCY_AGENT` | Current agent name |
| `AGENCY_MANAGER` | Manager name |
| `AGENCY_ROLE` | MANAGER or AGENT |
