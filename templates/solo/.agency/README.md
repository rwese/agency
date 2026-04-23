# Solo Agency Template

Minimal single-developer template for personal projects.

## Structure

```
.agency/
├── config.yaml     # Project configuration
├── manager.yaml   # Manager personality
├── agents.yaml    # Agent definitions
└── agents/
    └── developer/
        └── personality.md
```

## Usage

```bash
agency init --dir ~/projects/myproject --template solo
agency session start
agency session attach
```

## Customization

1. Update `config.yaml` with your project name
2. Adjust `agents/developer/personality.md` if needed
3. Modify `manager.yaml` for your workflow preferences

## Use Cases

- Personal side projects
- Learning new technologies
- Quick prototyping
- Solo development workflow
