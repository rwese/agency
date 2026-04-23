# Demo Project 04: Cron Expression Parser

**Type:** Library + CLI
**Complexity:** Medium
**Purpose:** Test parsing, validation, human-readable output, scheduling

## Overview

Parse, validate, and explain cron expressions. Calculate next run times.

## Features

- [ ] Parse standard 5-field cron expressions
- [ ] Support extended cron (6th field for seconds)
- [ ] Support predefined schedules (@hourly, @daily, @weekly, etc.)
- [ ] Validate cron expressions with clear errors
- [ ] Human-readable explanation of schedule
- [ ] Calculate next N run times
- [ ] Calculate previous run time
- [ ] Library API for programmatic use

## Tech Stack

- **Language:** Python or Go
- **Dependencies:** None (pure implementation)

## CLI Interface

```bash
# Explain cron expression
cron parse "0 9 * * 1-5"

# Calculate next runs
cron next "0 9 * * 1-5" --count 5

# Previous run
cron prev "0 9 * * 1-5"

# Validate
cron validate "0 9 * * *"

# Predefined schedules
cron parse "@daily"
cron next "@hourly" --count 3
```

## Test Cases

| ID | Test | Description |
|----|------|-------------|
| TC01 | Parse standard | 5-field cron works |
| TC02 | Parse extended | 6-field with seconds |
| TC03 | Parse predefined | @daily, @hourly, etc. |
| TC04 | Validate valid | Valid expression passes |
| TC05 | Validate invalid | Invalid expression fails |
| TC06 | Explain output | Human-readable description |
| TC07 | Next runs | Correct future dates |
| TC08 | Prev run | Correct past date |
| TC09 | Range parsing | 1-5, */2, 1,3,5 |

## Task Breakdown

1. Create cron expression parser
2. Implement field validation
3. Add predefined schedule support
4. Create human-readable explainer
5. Implement next/previous run calculator
6. Build CLI interface
7. Write comprehensive unit tests
8. Write integration tests
9. Create e2e test report

## Success Criteria

- Parses all standard cron formats
- Explains schedule in plain English
- Next/previous times are accurate
- Invalid expressions rejected with clear error
- Handles edge cases (Feb 30, etc.)
