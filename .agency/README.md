# Agency - Local Configuration

This directory contains project-specific agency configuration.

## Structure

```
.agency/
├── agents/         # Agent configurations
│   └── example.yaml
├── managers/       # Manager configurations
│   └── coordinator.yaml
└── README.md       # This file
```

## Usage

```bash
# Start an agent
agency start example --dir .

# Start the coordinator manager
agency start-manager coordinator --dir .
```

## Notes

- Local configs take precedence over global configs
- This directory should be committed to version control
- See ~/.config/agency/ for global configuration
