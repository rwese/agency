# Implementation TODO

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

## Acceptance Criteria
- [x] All schemas have valid JSON Schema draft-2020-12 syntax
- [x] Pydantic models generated from schemas match existing code
- [x] Config files validate against schemas at runtime
- [x] SPEC.md serves as single source of truth
- [x] CI validates schemas on push

## Files Added/Modified

### New Files
- `SPEC.md` - Complete specification with embedded schemas
- `src/agency/schemas/task.json` - Task entity schema
- `src/agency/schemas/tasks_store.json` - Task registry schema
- `src/agency/schemas/result.json` - Task result schema
- `src/agency/schemas/pending_task.json` - Pending approval schema
- `src/agency/schemas/notification.json` - Notification event schema
- `src/agency/schemas/notifications_store.json` - Notification registry schema
- `src/agency/schemas/slots_available.json` - Slot tracking schema
- `src/agency/schemas/halted.json` - Halt state schema
- `src/agency/schemas/_index.json` - Schema index
- `scripts/generate_models.py` - Pydantic model generator
- `scripts/validate_schemas.py` - Schema validator

### Modified Files
- `src/agency/schemas/config.json` - Updated to draft-2020-12
- `src/agency/schemas/manager.json` - Updated to draft-2020-12
- `src/agency/schemas/agent.json` - Updated to draft-2020-12
- `src/agency/schemas/agents.json` - Updated to draft-2020-12
- `.github/workflows/ci.yml` - Added schema validation steps
- `README.md` - Added schema references
