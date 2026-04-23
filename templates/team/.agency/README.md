# Team Agency Template

Multi-agent template for small teams with distinct roles.

## Structure

```
.agency/
├── config.yaml     # Project configuration
├── manager.yaml   # Manager personality
├── agents.yaml    # Agent definitions
└── agents/
    ├── coder/
    │   └── personality.md
    ├── reviewer/
    │   └── personality.md
    └── tester/
        └── personality.md
```

## Pre-configured Agents

- **coder**: Implements features and fixes
- **reviewer**: Reviews code quality and security
- **tester**: Verifies functionality and catches bugs

## Workflow

```
Request → Coder → Reviewer → Tester → Approved
```

## Usage

```bash
agency init --dir ~/projects/myproject --template team
agency session start
agency session attach
```

## Customization

1. Update `config.yaml` with your project name
2. Adjust `parallel_limit` based on team size
3. Modify personalities as needed

## Use Cases

- Small team projects (2-5 developers)
- Quality-focused development
- Projects requiring code review gate
- Collaborative development workflows
