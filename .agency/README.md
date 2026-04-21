# Basic Agency Template

Minimal template for any project.

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
agency init-project --dir ~/projects/myapp \
  --template https://github.com/rwese/agency-templates/tree/main/basic \
  --start-manager coordinator
```
