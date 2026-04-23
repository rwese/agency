# Demo Project 09: Environment Variable Validator

**Type:** Library + CLI
**Complexity:** Low-Medium
**Purpose:** Test config validation, schema definitions, error reporting

## Overview

Validate environment variables against a schema definition with clear error messages.

## Features

- [ ] Define required variables
- [ ] Define optional variables with defaults
- [ ] Type validation (string, integer, boolean, URL, email, path)
- [ ] Regex pattern matching
- [ ] Custom validators
- [ ] Cross-variable validation (e.g., PORT must be > 0 if defined)
- [ ] Load from .env file
- [ ] Load from environment
- [ ] Generate sample .env file
- [ ] Auto-document variables

## Tech Stack

- **Language:** Python
- **Dependencies:** `python-dotenv` (optional)

## CLI Interface

```bash
# Validate from environment
env-validate --schema schema.yaml

# Validate from .env file
env-validate --schema schema.yaml --env-file .env

# Generate sample .env
env-validate --schema schema.yaml --generate-sample

# Show documentation
env-validate --schema schema.yaml --docs

# Validate and export
env-validate --schema schema.yaml --export validated.env
```

## Schema Format (YAML)

```yaml
variables:
  DATABASE_URL:
    type: string
    required: true
    description: "PostgreSQL connection string"

  PORT:
    type: integer
    default: 8080
    description: "Server port"
    validator: "value > 0 and value < 65536"

  DEBUG:
    type: boolean
    default: false
    description: "Enable debug mode"

  ALLOWED_HOSTS:
    type: list
    separator: ","
    description: "Allowed HTTP hosts"
```

## Test Cases

| ID | Test | Description |
|----|------|-------------|
| TC01 | Required missing | Error when required not set |
| TC02 | Type mismatch | String where int expected |
| TC03 | Default value | Optional with default works |
| TC04 | Boolean parsing | "true", "false", "1", "0" |
| TC05 | URL validation | Valid URL passes |
| TC06 | Email validation | Valid email passes |
| TC07 | Regex match | Pattern validation |
| TC08 | Cross-var | PORT > 0 when defined |
| TC09 | Dotenv file | Load from .env works |
| TC10 | Generate sample | Sample .env generated |

## Task Breakdown

1. Create schema parser
2. Implement type validators
3. Add regex pattern support
4. Implement custom validators
5. Add cross-variable validation
6. Implement dotenv loading
7. Add sample generation
8. Create documentation output
9. Build CLI interface
10. Write unit tests
11. Write integration tests
12. Create e2e test report

## Success Criteria

- All type validations work correctly
- Clear error messages for failures
- Default values applied correctly
- Cross-variable validation works
- Dotenv file parsing handles edge cases
- Generated sample matches schema
