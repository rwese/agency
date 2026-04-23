---
name: agency-project-eval
description: "Build, run, and evaluate demo projects using agency. Use when: (1) running evaluation projects from demo/projects, (2) validating project outputs, (3) reviewing agency session results, (4) generating evaluation reports. Covers project initialization, session management, test execution, and result validation."
---

# Agency Project Evaluation

Build, evaluate, and review agency project implementations from the demo collection.

## Purpose

Run evaluation projects through agency to:
- Test orchestration workflows
- Validate agent outputs
- Measure agency effectiveness
- Track completion rates and quality

**Results are stored locally, not committed to git.**

## Project Collection

Projects are in `demo/projects/`:
- `01-10`: CLI tools, libraries, developer tools
- `11-16`: Web-based (static, API, fullstack, microservices)

See `demo/README.md` for full list.

## Commands

### List Projects

```bash
ls demo/projects/
```

### Initialize Project

```bash
# Use agency hire for custom agency
agency hire --dir demo/projects/01-markdown-to-html --type cli --language python --team solo

# Or use template
agency init --dir demo/projects/01-markdown-to-html --template basic
```

### Run Evaluation

```bash
# Start session
agency session start

# Attach to work with agency
agency session attach
# Detach: Ctrl+B D

# View results
agency tasks history

# Stop session
agency session stop
```

### Validate Results

After completion, validate against `TEST_REPORT.md`:

```bash
# Run project tests
cd demo/projects/01-markdown-to-html
uv run pytest tests/ -v

# Check coverage
uv run pytest --cov=src --cov-report=html

# Run linter
uv run ruff check src/
```

## Result Storage

Results are stored in:

```
demo/projects/01-markdown-to-html/
├── TEST_REPORT.md          # Evaluation results
├── .agency/var/           # Session artifacts
│   ├── audit.db           # Audit log
│   ├── tasks.json         # Task history
│   └── notifications.json  # Notifications
└── results/               # Optional: test outputs
    ├── test-results.xml
    └── coverage/
```

## Evaluation Workflow

### 1. Select Project

Choose project based on complexity and type:
- Low complexity: 01, 09, 11
- Medium: 02, 03, 04, 05, 08, 10, 12, 16
- Medium-High: 06, 07, 13
- High: 14, 15

### 2. Initialize

```bash
cd demo/projects/<project>
agency hire --dir . --type <type> --language <lang> --team <size>
```

### 3. Execute

```bash
agency session start
# Work through tasks...
agency session stop
```

### 4. Validate

```bash
# Check implementation matches spec
# Run tests
# Verify acceptance criteria
```

### 5. Document

Create `TEST_REPORT.md`:

```markdown
# Test Report: Project Name

## Environment
- OS: macOS 14.0
- Python: 3.11
- Agency: v2.0.0

## Execution
- Session start: 2024-01-15 10:00:00
- Session stop: 2024-01-15 12:30:00
- Duration: 2h 30m

## Tasks
| ID | Subject | Status | Duration | Reviews |
|----|---------|--------|----------|---------|
| abc-123 | Feature 1 | completed | 45m | 1 |
| def-456 | Feature 2 | completed | 30m | 2 |

## Test Results
- Unit tests: 15 passed
- Integration tests: 8 passed
- Coverage: 85%

## Issues
- None

## Summary
- Tasks completed: 2/2
- Average review cycles: 1.5
- Quality: Good
```

## Metrics

Track these per project:

| Metric | Description |
|--------|-------------|
| Tasks completed | vs created |
| Review cycles | avg per task |
| Rejection rate | % tasks rejected |
| Time to complete | avg duration |
| Test pass rate | % tests passing |
| Coverage | % code covered |

## Cleanup

```bash
# Remove agency config (keep source)
rm -rf demo/projects/01-markdown-to-html/.agency

# Keep results only
mv demo/projects/01-markdown-to-html/TEST_REPORT.md /path/to/results/
```
