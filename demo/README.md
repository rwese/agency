# Agency Evaluation Projects

Demo projects for testing and validating agency orchestration capabilities.

## Purpose

These projects serve as **evaluation benchmarks** to:

1. **Test orchestration workflows** - Verify task assignment, review, approval flows
2. **Validate agent outputs** - Ensure produced code meets specifications
3. **Measure agency effectiveness** - Track completion rates, review cycles, rejection rates
4. **Benchmark different scenarios** - CLI tools, libraries, web services, data processing

## Quick Start

```bash
# Hire an agency for a demo project
cd demo/projects/01-markdown-to-html
agency hire --dir . --type cli --language python --team solo

# Start working
agency session start
agency session attach
```

## Project Structure

```
demo/
├── README.md              # This file
└── projects/
    # CLI Tools
    ├── 01-markdown-to-html/       # CLI: text transformation
    ├── 03-image-metadata-extractor/  # CLI: file processing
    ├── 05-csv-sqlite-importer/    # CLI: data import
    ├── 10-text-diff-viewer/       # CLI: text processing
    
    # Libraries
    ├── 02-json-schema-validator/  # Library: validation
    ├── 04-cron-parser/            # Library: parsing
    ├── 06-api-rate-limiter/       # Library: middleware
    ├── 07-password-strength-checker/  # Library: security
    ├── 09-env-validator/          # Library: config
    
    # Developer Tools
    ├── 08-git-hook-installer/     # Developer tool
    
    # Web (Static/Frontend)
    ├── 11-notes-app-static/       # SPA: localStorage
    
    # Web (API/Backend)
    ├── 12-todo-api/               # REST API: in-memory
    
    # Web (Full-Stack)
    ├── 13-contacts-sqlite/        # Full-stack: SQLite
    ├── 14-url-shortener-docker/   # Microservices: Docker
    ├── 15-chat-realtime/          # Real-time: WebSockets
    
    # Build Tools
    └── 16-static-site-generator/  # Static site gen
```

## Complexity Levels

| Level | Description | Projects |
|-------|-------------|----------|
| Low | Single file, simple logic | 01, 09, 11 |
| Medium | Multiple modules, some deps | 02, 03, 04, 05, 08, 10, 12, 16 |
| Medium-High | Multiple components, integration | 06, 07, 13 |
| High | Full systems, multiple tiers | 14, 15 |

## Project Requirements

Each project must include:

### 1. Specification (README.md)
- Feature list with checkboxes
- CLI interface specification
- Test cases table
- Success criteria

### 2. Reviewer Workflow
- Reviewer agent spawned on `pending_approval`
- Checks: code quality, tests, documentation
- Approves or rejects with feedback

### 3. E2E Test Report (TEST_REPORT.md)
- Test environment (OS, runtime, versions)
- Test execution (commands, output)
- Results (pass/fail per test case)
- Evidence (logs, screenshots)
- Summary statistics

## Complexity Levels

| Level | Description | Projects |
|-------|-------------|----------|
| Low | Single file, simple logic | 01, 09, 11 |
| Medium | Multiple modules, some deps | 02, 03, 04, 05, 08, 10, 12, 16 |
| Medium-High | Multiple components, integration | 06, 07, 13 |
| High | Full systems, multiple tiers | 14, 15 |

## Complete Project Index

| # | Project | Type | Tech Stack | Complexity |
|---|---------|------|------------|------------|
| 01 | Markdown to HTML | CLI | Python | Low |
| 02 | JSON Schema Validator | Library | Python/Go | Medium |
| 03 | Image Metadata Extractor | CLI | Python | Medium |
| 04 | Cron Parser | Library | Python/Go | Medium |
| 05 | CSV SQLite Importer | CLI | Python | Medium |
| 06 | API Rate Limiter | Library | Python | Medium-High |
| 07 | Password Strength Checker | Library | Python | Medium-High |
| 08 | Git Hook Installer | Dev Tool | Python/Shell | Medium |
| 09 | Env Validator | Library | Python | Low |
| 10 | Text Diff Viewer | CLI | Python | Medium |
| 11 | Notes App (Static) | SPA | Vanilla JS | Low |
| 12 | Todo API | REST API | FastAPI | Medium |
| 13 | Contacts Manager | Full-Stack | FastAPI + SQLite | Medium-High |
| 14 | URL Shortener | Microservices | Docker + Redis | High |
| 15 | Chat Room | Real-time | WebSockets + Redis | High |
| 16 | Static Site Generator | Build Tool | Python | Medium |

## Running Projects

```bash
# Initialize agency in project directory
cd demo/projects/01-markdown-to-html
agency init --dir . --template basic

# Start session
agency session start

# Work with manager to create tasks
# Manager will assign to developer agent
# Reviewer spawned on completion

# View results
agency tasks history

# Stop session
agency session stop
```

## Evaluation Metrics

Track these metrics across projects:

| Metric | Description |
|--------|-------------|
| Task completion rate | Tasks completed vs created |
| Review cycles | Average reviews per task |
| Rejection rate | Tasks rejected by reviewer |
| Time to complete | Average task duration |
| Agent utilization | Busy vs idle time |
| E2E pass rate | Tests passing in final report |

## Adding New Projects

1. Create directory: `projects/XX-project-name/`
2. Add `README.md` with specification
3. Add `TEST_REPORT.md` template
4. Update this index

## Contributing

When completing a demo project:

1. Run full agency workflow (init → tasks → review → complete)
2. Document test execution in TEST_REPORT.md
3. Record metrics (completion rate, review cycles)
4. Update project status in this index
