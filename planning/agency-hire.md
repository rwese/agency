# Agency Hire — Project-Driven Agency Generation

## Problem

When starting a new project, creating agency configuration is manual:
- Writing manager personality
- Defining agent roles and personalities
- Setting up task templates
- Configuring workflows

This is repetitive and requires deep knowledge of the agency system.

## Solution

A `agency hire` command that:

1. **Interviews** the user about the project (interactive prompts)
2. **Generates** appropriate manager/agent configurations
3. **Customizes** personalities for project type
4. **Creates** initial task templates

## Concept: Hiring an Agency

```bash
# Interactive hiring process
agency hire --project "Build a REST API"

# Questions asked:
# - Project type (API, CLI, Web, Library)
# - Language preferences
# - Team size (solo, pair, team)
# - Review requirements
# - Special considerations

# Output: .agency/ configured with hired team
```

## Interview Questions

### Phase 1: Project Profile

| Question | Options | Default |
|----------|---------|---------|
| Project type | API, CLI, Library, Web, Full-stack, Other | Ask |
| Primary language | Python, Go, Rust, TypeScript, JavaScript | - |
| Framework | FastAPI, Flask, Gin, Express, etc. | None |
| Database | PostgreSQL, SQLite, Redis, None | None |

### Phase 2: Team Structure

| Question | Options | Default |
|----------|---------|---------|
| Team size | Solo, Pair, Team | Solo |
| Agents needed | Coder, Tester, DevOps, Reviewer | Based on size |
| Manager style | Coordinator, Director, Facilitator | Coordinator |

### Phase 3: Workflow

| Question | Options | Default |
|----------|---------|---------|
| Review process | Mandatory review, Optional, Self-review | Mandatory |
| Test requirements | TDD, Tests required, Tests optional | Tests required |
| CI/CD | Yes, No | Ask |

## Generated Outputs

### 1. Manager Personality

```yaml
# .agency/manager.yaml
name: coordinator
personality: |
  You are the project coordinator for a FastAPI REST API project.

  ## Project Context
  - Language: Python
  - Framework: FastAPI
  - Database: PostgreSQL
  - Testing: pytest

  ## Your Approach
  - Break features into small, reviewable tasks
  - Ensure tests are written with code
  - Coordinate between coder and tester agents

  ## Task Priorities
  1. API endpoints with tests
  2. Database models
  3. Documentation
```

### 2. Agent Personalities

#### Coder
```yaml
# .agency/agents/coder.yaml
name: coder
personality: |
  You are a senior Python developer specializing in FastAPI.

  ## Code Standards
  - Follow PEP 8
  - Type hints on all functions
  - Docstrings on public functions
  - Error handling with proper exceptions

  ## Testing
  - pytest for unit tests
  - pytest-asyncio for async tests
  - 80% coverage minimum

  ## Your Task
  - Implement features from pending tasks
  - Write tests alongside code
  - Update documentation
```

#### Tester
```yaml
# .agency/agents/tester.yaml
name: tester
personality: |
  You are a QA engineer focused on API testing.

  ## Testing Approach
  - Test edge cases first
  - Verify error handling
  - Check API contract compliance

  ## Tools
  - pytest for unit tests
  - httpx for API testing
  - pytest-cov for coverage
```

### 3. Task Templates

```yaml
# .agency/templates/feature.yaml
name: Add API Feature
steps:
  - Create feature branch
  - Write tests first (TDD)
  - Implement feature
  - Run full test suite
  - Update OpenAPI docs
  - Create PR description
acceptance:
  - Tests pass
  - Coverage maintained
  - Docs updated
```

## Implementation Plan

### Phase 1: CLI Interface
- [ ] Create `agency hire` command
- [ ] Define interview questions in YAML
- [ ] Implement interactive prompts with Click
- [ ] Generate config files from templates

### Phase 2: Templates
- [ ] Create manager personality templates per project type
- [ ] Create agent personality templates
- [ ] Create task templates

### Phase 3: Intelligence
- [ ] Detect project type from existing files
- [ ] Suggest sensible defaults
- [ ] Generate from project scan

### Phase 4: Persistence
- [ ] Save "hired" agencies as reusable templates
- [ ] `agency hire --from-template my-team`
- [ ] Share agency configurations

## File Structure

```
agency-hire/
├── cli.py                 # agency hire command
├── questions.py           # Interview question definitions
├── generators/
│   ├── __init__.py
│   ├── manager.py         # Generate manager personality
│   ├── agent.py           # Generate agent personalities
│   └── template.py        # Generate task templates
├── templates/
│   ├── manager/
│   │   ├── api.yaml
│   │   ├── cli.yaml
│   │   ├── library.yaml
│   │   └── fullstack.yaml
│   ├── agent/
│   │   ├── coder-python.yaml
│   │   ├── coder-go.yaml
│   │   ├── tester.yaml
│   │   └── devops.yaml
│   └── task/
│       ├── feature.yaml
│       ├── bugfix.yaml
│       └── refactor.yaml
└── config.py             # Hire configuration
```

## Commands

```bash
# Interactive hiring
agency hire

# With project type
agency hire --type api --language python

# Preview before applying
agency hire --preview

# Apply to existing .agency
agency hire --update

# Save as reusable template
agency hire --save-as my-api-team

# Use saved template
agency hire --from-template my-api-team
```

## Example Session

```bash
$ agency hire

🚀 Agency Hire — Let's build your team!

📋 Project Profile
? Project type: (api)
   1 - API
   2 - CLI tool
   3 - Library/Package
   4 - Web application
   5 - Full-stack application
   6 - Other
   (Use arrow keys)
▶ API

? Primary language: Python
? Framework: FastAPI

👥 Team Setup
? Team size: (solo)
   1 - Solo (1 developer)
   2 - Pair (2 developers)
   3 - Team (3+ developers)
▶ Solo

? Which agents do you need?
   ◉ Coder (required)
   ○ Tester
   ○ DevOps
   ○ Reviewer

⚙️ Workflow
? Review process: (mandatory)
   1 - Mandatory review
   2 - Optional review
   3 - Self-review only
▶ Mandatory

? Require tests: (yes)
   1 - Yes, TDD style
   2 - Yes, tests after
   3 - No
▶ Yes, TDD style

📝 Generating your agency...
✓ Created .agency/manager.yaml
✓ Created .agency/agents.yaml
✓ Created .agency/agents/coder.yaml
✓ Created .agency/agents/tester.yaml
✓ Created .agency/templates/

🎉 Your agency is ready!

To start working:
  agency session start
```
