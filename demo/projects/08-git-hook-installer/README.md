# Demo Project 08: Git Hook Installer

**Type:** Developer Tool (CLI)
**Complexity:** Medium
**Purpose:** Test git integration, hook templates, file manipulation

## Overview

A CLI tool to install, manage, and share git hooks across projects with template support.

## Features

- [ ] Install pre-configured hooks (pre-commit, pre-push, etc.)
- [ ] Custom hook templates with variable interpolation
- [ ] Share hooks via git remote (hook registry)
- [ ] Per-project hook configuration
- [ ] Hook chaining (multiple hooks per event)
- [ ] Dry-run mode
- [ ] Hook enable/disable
- [ ] List installed hooks
- [ ] Hook validation

## Tech Stack

- **Language:** Python or Shell
- **Dependencies:** `git` (external)

## CLI Interface

```bash
# Install built-in hook
git-hook install pre-commit --template lint

# List available templates
git-hook list-templates

# Install custom hook
git-hook install pre-commit --file my-hook.sh

# Install from registry
git-hook install pre-commit --from registry@github:user/lint-hooks

# Dry run
git-hook install pre-commit --dry-run

# List installed hooks
git-hook list

# Disable hook
git-hook disable pre-commit

# Enable hook
git-hook enable pre-commit
```

## Hook Templates

### pre-commit (lint)
- Run linter (ruff, eslint, etc.)
- Run formatter check
- Check file sizes
- Prevent committing secrets

### pre-push (test)
- Run tests
- Check test coverage
- Block if coverage drops

### commit-msg (conventional commits)
- Validate commit message format
- Enforce conventional commits

## Test Cases

| ID | Test | Description |
|----|------|-------------|
| TC01 | Install hook | Hook file created correctly |
| TC02 | Hook executes | Pre-commit hook runs on commit |
| TC03 | Template vars | Variables interpolated |
| TC04 | Multiple hooks | Chained hooks run in order |
| TC05 | Dry run | No changes made |
| TC06 | Disable/enable | Hook can be toggled |
| TC07 | List hooks | Lists all installed |
| TC08 | Custom template | Custom file works |

## Task Breakdown

1. Create hook installer module
2. Implement built-in templates (pre-commit, pre-push, commit-msg)
3. Add variable interpolation
4. Implement hook chaining
5. Create registry support (git-based)
6. Build CLI interface
7. Add dry-run mode
8. Implement disable/enable
9. Write unit tests
10. Write integration tests (with actual git repos)
11. Create e2e test report

## Success Criteria

- Hooks are executable and run correctly
- Templates interpolate variables properly
- Multiple hooks run in correct order
- Dry-run makes no filesystem changes
- Hooks can be toggled on/off
- Works with git 2.x
