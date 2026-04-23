# Agency Evaluation Projects

Demo projects for testing and validating agency orchestration capabilities.

## Purpose

These projects serve as **evaluation benchmarks** to:

1. **Test orchestration workflows** - Verify task assignment, review, approval flows
2. **Validate agent outputs** - Ensure produced code meets specifications
3. **Measure agency effectiveness** - Track completion rates, review cycles, rejection rates
4. **Benchmark different scenarios** - CLI tools, libraries, web services, data processing

## Project Structure

```
demo/
├── README.md              # This file
└── projects/
    ├── 01-markdown-to-html/       # CLI: text transformation
    ├── 02-json-schema-validator/  # Library: validation
    ├── 03-image-metadata-extractor/  # CLI: file processing
    ├── 04-cron-parser/            # Library: parsing
    ├── 05-csv-sqlite-importer/    # CLI: data import
    ├── 06-api-rate-limiter/        # Library: middleware
    ├── 07-password-strength-checker/  # Library: security
    ├── 08-git-hook-installer/     # Developer tool
    ├── 09-env-validator/          # Library: config
    └── 10-text-diff-viewer/       # CLI: text processing
```

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

| Level | Description | Examples |
|-------|-------------|----------|
| Low | Single file, simple logic | Parser, converter |
| Medium | Multiple modules, some deps | CLI tools, libraries |
| Medium-High | Multiple components, integration | API middleware, web |
| High | Full systems, multiple tiers | Web services, databases |

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
