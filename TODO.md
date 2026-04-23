# Agency - Known Issues and Fixes

## Completed Fixes

| # | Issue | Fix | Status |
|---|-------|-----|--------|
| 1 | Developer bypassed `pending_approval` status | Added status transition validation | ✅ |
| 2 | Developer used wrong commands | Updated personality with correct workflow | ✅ |
| 3 | Task ID injection with spaces | Documented as tmux behavior | ✅ |
| 4 | Manager didn't auto-review | Updated manager personality + v2 heartbeat | ✅ |
| 5 | Manager heartbeat v1 not auto-assigning | Switched to v2 heartbeat with `assign_tasks_to_agents()` | ✅ |
| 6 | Auto-approval only on count change | Check every cycle for pending tasks | ✅ |

## Known Issues

1. **Heartbeat v2 not starting from `agency session start`** - Was defined after `__main__` block
2. **Test fixtures use wrong directory structure** - Fixed to use `var/tasks` and `var/pending`

## Demo Projects Status

| Demo | Status |
|------|--------|
| **Log Parser** | ✅ Complete |
| **URL Shortener** | ✅ Complete (backend + frontend) |
| **Bookmarks Vault** | ✅ Complete |
| **Secret Scanner** | ✅ Complete |

---

# Schema Implementation (Completed)

## Phase 1: Schema Consolidation ✅
- [x] 1.1 Audit existing schemas in `src/agency/schemas/`
- [x] 1.2 Consolidate into unified schema structure
- [x] 1.3 Add missing schemas (tasks, notifications, signals)
- [x] 1.4 Add JSON Schema `$id` URLs for all schemas
- [x] 1.5 Create schema index (_index.json)

## Phase 2: SPEC.md Creation ✅
- [x] 2.1 Create root SPEC.md with frontmatter
- [x] 2.2 Document all entities (Project, Manager, Agent, Task)
- [x] 2.3 Embed schema references with `json:schema` or include syntax
- [x] 2.4 Add task lifecycle diagrams

## Phase 3: Pydantic Model Generation ✅
- [x] 3.1 Add `datamodel-code-generator` to dependencies (skipped - custom generator)
- [x] 3.2 Create `scripts/generate_models.py`
- [x] 3.3 Generate Pydantic models from schemas
- [x] 3.4 Verify generated models match existing dataclasses (config tests pass)

## Phase 4: Validation Pipeline ✅
- [x] 4.1 Add JSON Schema validation to config loading (already exists in config.py)
- [x] 4.2 Create `scripts/validate_schemas.py`
- [x] 4.3 Add CI step for schema validation

## Phase 5: Documentation Generation ✅
- [x] 5.1 Add schema extraction script (included in generate_models.py)
- [x] 5.2 Update README with schema references
- [x] 5.3 Document migration path (in SPEC.md)

## Acceptance Criteria ✅
- [x] All schemas have valid JSON Schema draft-2020-12 syntax
- [x] Pydantic models generated from schemas match existing code
- [x] Config files validate against schemas at runtime
- [x] SPEC.md serves as single source of truth
- [x] CI validates schemas on push

## Completed Features

### Schema Files (12 total)
- `config.json` - Project configuration
- `manager.json` - Coordinator config
- `agent.json` - Individual agent
- `agents.json` - Agent registry
- `task.json` - Work unit
- `tasks_store.json` - Task registry
- `result.json` - Task result
- `pending_task.json` - Pending approval
- `notification.json` - Event notification
- `notifications_store.json` - Notification registry
- `slots_available.json` - Task slot tracking
- `halted.json` - Halt state

### Generated Models (12 total)
Auto-generated Pydantic models in `src/agency/models/`

### Scripts
- `scripts/generate_models.py` - Generate Pydantic from schemas
- `scripts/validate_schemas.py` - Validate schema syntax

### Documentation
- `SPEC.md` - Complete specification with embedded schemas
- Updated `README.md` with schema references
- Updated `.github/workflows/ci.yml` with validation step

## Usage

```bash
# Validate schemas
uv run python scripts/validate_schemas.py

# Generate/update Pydantic models
uv run python scripts/generate_models.py

# Commit schema changes
git add src/agency/schemas/ && git commit -m "chore: update schemas"
```
