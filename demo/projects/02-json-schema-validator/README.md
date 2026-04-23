# Demo Project 02: JSON Schema Validator

**Type:** Library + CLI
**Complexity:** Medium
**Purpose:** Test schema validation, error reporting, configuration

## Overview

A JSON Schema Draft-2020-12 validator with clear error messages and multiple output formats.

## Features

- [ ] Validate JSON against JSON Schema Draft-2020-12
- [ ] Support all core keywords (type, properties, items, etc.)
- [ ] Support `$ref` resolution (local and remote)
- [ ] Clear error messages with JSON path to error
- [ ] Multiple output formats: human, JSON, SARIF
- [ ] Validate schema itself (meta-schema validation)
- [ ] Library API for programmatic use

## Tech Stack

- **Language:** Python or Go
- **Dependencies:** `referencing` for `$ref` resolution
- **Standard:** JSON Schema Draft-2020-12

## CLI Interface

```bash
# Basic validation
jsv validate schema.json data.json

# With detailed output
jsv validate --format human schema.json data.json

# JSON output
jsv validate --format json schema.json data.json

# SARIF output (for CI)
jsv validate --format sarif schema.json data.json

# Validate schema itself
jsv validate-schema schema.json
```

## Test Cases

| ID | Test | Description |
|----|------|-------------|
| TC01 | Valid data | Valid data passes validation |
| TC02 | Type mismatch | Integer vs string detected |
| TC03 | Missing required | Required field missing |
| TC04 | Array items | Array item validation |
| TC05 | $ref local | Local $ref resolution |
| TC06 | $ref remote | Remote $ref via HTTP |
| TC07 | Format validation | email, uri, date-time |
| TC08 | Custom message | Error message is clear |

## Task Breakdown

1. Implement core validation engine
2. Add $ref resolution (local + remote)
3. Implement all JSON Schema keywords
4. Create error reporting with JSON paths
5. Add multiple output formats (human, JSON, SARIF)
6. Build CLI interface
7. Write comprehensive unit tests
8. Write integration tests
9. Create e2e test report

## Success Criteria

- Passes JSON Schema Test Suite (standard compliance)
- Error messages include JSON path
- Supports remote $ref via HTTP
- SARIF output is valid
- CLI returns exit code 1 on validation failure
