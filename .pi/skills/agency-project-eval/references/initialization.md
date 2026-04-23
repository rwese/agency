# Project Initialization Reference

Quick reference for initializing demo projects with agency.

## CLI Projects (01, 03, 05, 10)

```bash
cd demo/projects/01-markdown-to-html
agency hire --dir . --type cli --language python --team solo
agency session start
agency session attach
```

## Library Projects (02, 04, 06, 07, 09)

```bash
cd demo/projects/02-json-schema-validator
agency hire --dir . --type library --language python --team solo
agency session start
agency session attach
```

## Developer Tools (08)

```bash
cd demo/projects/08-git-hook-installer
agency hire --dir . --type cli --language python --team solo
agency session start
agency session attach
```

## Static Web (11)

```bash
cd demo/projects/11-notes-app-static
agency hire --dir . --type web --language javascript --team solo
agency session start
agency session attach
```

## API Projects (12)

```bash
cd demo/projects/12-todo-api
agency hire --dir . --type api --language python --team solo
agency session start
agency session attach
```

## Full-Stack (13)

```bash
cd demo/projects/13-contacts-sqlite
agency hire --dir . --type fullstack --language python --team pair
agency session start
agency session attach
```

## Microservices (14)

```bash
cd demo/projects/14-url-shortener-docker
agency hire --dir . --type fullstack --language python --team team
agency session start
agency session attach
```

## Real-time (15)

```bash
cd demo/projects/15-chat-realtime
agency hire --dir . --type fullstack --language python --team team
agency session start
agency session attach
```

## Static Site Generator (16)

```bash
cd demo/projects/16-static-site-generator
agency hire --dir . --type library --language python --team solo
agency session start
agency session attach
```

## Common Commands

```bash
# View tasks
agency tasks list

# View completed tasks
agency tasks history

# Stop gracefully
agency session stop

# Kill if stuck
agency session kill

# Reattach
agency session attach
```

## Project-Specific Test Commands

### Python Projects

```bash
# Install deps
uv pip install -e .

# Run tests
uv run pytest tests/ -v

# Coverage
uv run pytest --cov=src --cov-report=html

# Lint
uv run ruff check src/
uv run ruff format src/
```

### JavaScript Projects

```bash
# Install deps
npm install

# Run tests
npm test

# Build
npm run build
```

### Go Projects

```bash
# Build
go build ./...

# Test
go test ./...

# Lint
golangci-lint run
```

## Cleanup

```bash
# Remove agency artifacts, keep code
rm -rf .agency/var/
rm -rf .agency/pi/

# Keep .agency but remove logs
rm -rf .agency/var/tasks/
rm -f .agency/var/audit.db
```
