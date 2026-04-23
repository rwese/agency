# Test Report: {{PROJECT_NAME}}

**Date:** {{DATE}}
**Project:** {{PROJECT_ID}} - {{PROJECT_NAME}}
**Type:** {{PROJECT_TYPE}}

---

## Environment

| Item | Value |
|------|-------|
| OS | {{OS}} |
| Python | {{PYTHON_VERSION}} |
| Agency | {{AGENCY_VERSION}} |
| Language | {{LANGUAGE}} |
| Framework | {{FRAMEWORK}} |

## Execution

| Item | Value |
|------|-------|
| Session start | {{START_TIME}} |
| Session stop | {{END_TIME}} |
| Duration | {{DURATION}} |

## Tasks

| Task ID | Subject | Status | Agent | Duration | Reviews |
|---------|---------|--------|-------|----------|---------|
| | | | | | |

## Test Results

### Unit Tests

```
$ uv run pytest tests/ -v
{{TEST_OUTPUT}}
```

**Result:** {{UNIT_TEST_PASSED}}/{{UNIT_TEST_TOTAL}} passed

### Integration Tests (if applicable)

```
$ uv run pytest tests/ -v
{{INTEGRATION_OUTPUT}}
```

**Result:** {{INTEGRATION_PASSED}}/{{INTEGRATION_TOTAL}} passed

### Coverage

```
$ uv run pytest --cov=src --cov-report=term-missing
{{COVERAGE_OUTPUT}}
```

**Coverage:** {{COVERAGE_PERCENT}}%

## Code Quality

### Linter

```
$ uv run ruff check src/
{{LINTER_OUTPUT}}
```

### Formatter

```
$ uv run ruff format --check src/
{{FORMAT_OUTPUT}}
```

## Acceptance Criteria

| Criterion | Status | Notes |
|-----------|--------|-------|
| | | |

## Issues

### Bugs Found

-

### Missing Features

-

### Code Quality Issues

-

## Summary

| Metric | Value |
|--------|-------|
| Tasks completed | {{COMPLETED}}/{{TOTAL}} |
| Review cycles (avg) | {{AVG_REVIEWS}} |
| Rejection rate | {{REJECTION_RATE}}% |
| Test pass rate | {{TEST_PASS_RATE}}% |
| Coverage | {{COVERAGE_PERCENT}}% |
| Quality | {{QUALITY_RATING}} |

## Observations

_Notes on agency behavior, workflow, agent performance_

## Recommendations

_Improvements for future evaluations_
