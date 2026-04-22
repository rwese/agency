# TODO: Init Command TUI Rewrite

## M1 - Wizard Structure

### M1.1 Extract wizard to separate module
- [x] Create `src/agency/wizard.py` with step functions
- [x] Define `WizardState` dataclass for passing data between steps
- [x] Include helper functions for common prompts

### M1.2 Create step functions
- [x] `step_project()` - Project name, shell selection
- [x] `step_agents()` - Agent name/personality prompts
- [x] `step_context()` - Context file selection (refactor from __main__)
- [x] `step_template()` - Template selection
- [x] `step_review()` - Show summary, confirm/edit

### M1.3 Add review step
- [x] Display all configured options
- [x] Confirm/Go back/Edit options

## M2 - Integrate with CLI

### M2.1 Refactor init_project command
- [x] Wire wizard into `init_project()`
- [x] Handle `--dir` and `--force` as CLI-only flags
- [x] Add `--yes` flag for non-interactive mode

### M2.2 Move file creation to separate function
- [x] `_create_project()` called only after wizard completes
- [x] Clear progress indicators during creation

## M3 - Polish

### M3.1 Progress feedback
- [x] "Creating X..." messages during file generation
- [x] Error handling with clear messages

### M3.2 Validation
- [x] Agent name validation (alphanumeric + hyphen)
- [x] Path validation when referenced

---

## Progress Log
