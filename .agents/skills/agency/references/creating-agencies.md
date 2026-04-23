# Creating Custom Agencies

Guide for creating your own agency with custom agents and configuration.

## Overview

An agency consists of:

```
project/
└── .agency/
    ├── config.yaml       # Project settings
    ├── manager.yaml      # Manager personality
    ├── agents.yaml       # Agent registry
    └── agents/
        └── <agent>/
            └── personality.md
```

## Step 1: Plan Your Agents

Ask yourself:

- **How many agents do I need?**
  - Solo dev: 1 agent (coder)
  - Small team: 2-3 agents (coder, reviewer)
  - Full team: 4+ agents (coder, reviewer, tester, devops)

- **What roles are needed?**
  - Implementation (coders, developers)
  - Quality (reviewers, testers)
  - Infrastructure (devops, SRE)
  - Planning (architects, designers)

- **What personality traits?**
  - Technical focus (languages, frameworks)
  - Workflow preferences (TDD, agile)
  - Communication style (verbose, concise)

## Step 2: Write the Personality

Create `agents/<name>/personality.md`:

```markdown
# <Name> Personality

You are a [role description].

## Strengths
- [skill 1]
- [skill 2]

## Guidelines
1. [guideline 1]
2. [guideline 2]

## Task Workflow
[how this agent handles tasks]
```

**Tips:**
- Reference existing personalities in `assets/personalities/` as starting points
- Include `${{project_name}}` placeholders for customization
- Keep it focused (~50 lines max)

## Step 3: Configure agents.yaml

Create `agents.yaml`:

```yaml
agents:
  - name: <agent-name>
    config: agents/<agent-name>.yaml
  - name: <agent-name-2>
    config: agents/<agent-name-2>.yaml
```

## Step 4: Create Agent Config

Create `agents/<name>.yaml`:

```yaml
name: <name>
personality: personality.md
```

## Step 5: Configure Manager

Update `manager.yaml` with:

- Task assignment logic
- Review criteria
- Communication style

```yaml
name: coordinator
personality: |
  You are the project coordinator.

  ## Task Assignment
  - Feature work → assign to coder
  - Review → assign to reviewer

  ## Review Checklist
  Before approving:
  - [ ] Tests pass
  - [ ] Code quality checked
```

## Step 6: Test Your Template

```bash
# Create test project
cd /tmp
agency init --dir test-agency --template basic

# Copy your custom agency
cp -r my-agency/.agency /tmp/test-agency/

# Start session
cd /tmp/test-agency
agency session start
agency session attach
```

## Template Examples

### Minimal (1 Agent)

```
.agency/
├── config.yaml
├── manager.yaml
├── agents.yaml
└── agents/
    └── developer/
        └── personality.md
```

### Team (3 Agents)

```
.agency/
├── config.yaml
├── manager.yaml
├── agents.yaml
└── agents/
    ├── coder/
    │   └── personality.md
    ├── reviewer/
    │   └── personality.md
    └── tester/
        └── personality.md
```

## Common Patterns

### Workflow: Coder → Reviewer

```yaml
# manager.yaml
personality: |
  ## Task Flow
  1. Assign to coder
  2. After completion → assign to reviewer
  3. After review → approve
```

### Parallel Agents

```yaml
# config.yaml
parallel_limit: 3

# agents.yaml
agents:
  - name: coder-1
  - name: coder-2
  - name: coder-3
```

## Next Steps

- See [config.md](config.md) for schema details
- See `assets/personalities/` for reusable snippets
- Check `templates/` for complete examples
