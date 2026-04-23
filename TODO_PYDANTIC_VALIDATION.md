## Pydantic Validation — Full Wiring Plan

### Goal
Replace all dataclasses with generated Pydantic models, enabling schema-driven validation throughout the codebase.

---

## In Progress

- [ ] *(none)*

### Ready

#### 1. Fix Generator `from_dict` Return Type
- **File**: `scripts/generate_models.py`
- **Issue**: All generated models use `-> "Task"` in `from_dict()` instead of their actual class name
- **Fix**: Use `class_name` parameter for return type annotation
- **Test**: Verify each model's `from_dict()` returns correct type

#### 2. Replace Config Dataclasses with Pydantic
- **File**: `src/agency/config.py`
- **Classes**: `AgencyConfig`, `ManagerConfig`, `AgentConfig`
- **Models**: `Config`, `Manager`, `Agent` (from `models/config.py`, `models/manager.py`, `models/agent.py`)
- **Changes**:
  - Import from `agency.models`
  - Replace `@dataclass` with `BaseModel`
  - Use `Config.model_validate(data)` in load functions
  - Remove `_validate_with_schema()` (Pydantic handles it)
- **Test**: `pytest tests/test_config.py` (if exists) or manual validation

#### 3. Wire Audit Events to Pydantic
- **File**: `src/agency/audit.py`
- **Classes**: `AuditEvent`
- **Schema**: Create `schemas/audit_event.json` if not exists
- **Changes**:
  - Replace `@dataclass AuditEvent` with Pydantic model
  - Validate event data on creation
- **Test**: `pytest tests/test_audit.py`

#### 4. Replace pi_inject Dataclasses with Pydantic
- **File**: `src/agency/pi_inject.py`
- **Classes**: `InjectResponse`
- **Changes**: Replace with Pydantic model
- **Test**: Integration test with pi-inject

#### 5. Replace template_inject Dataclasses with Pydantic
- **File**: `src/agency/template_inject.py`
- **Classes**: `InjectionResult`, `InjectionOptions`
- **Changes**: Replace with Pydantic models
- **Test**: `pytest tests/test_template_inject.py`

#### 6. Replace __main__ Dataclasses with Pydantic
- **File**: `src/agency/__main__.py`
- **Classes**: `AgentEntry`, `InitConfig`
- **Changes**: Replace with Pydantic models
- **Test**: `agency init` still works

#### 7. Add Tests for Validation
- **File**: `tests/test_validation.py` (new)
- **Tests**:
  - Invalid config raises ValidationError
  - Invalid manager config raises ValidationError
  - Invalid agent config raises ValidationError
  - Audit event with bad data raises ValidationError

#### 8. Add Schema for Audit Events
- **File**: `schemas/audit_event.json` (if not exists)
- **Properties**: action, task_id, agent, timestamp, details

#### 9. Remove jsonschema Dependency
- **File**: `pyproject.toml`, `src/agency/config.py`
- **Reason**: Pydantic replaces jsonschema validation
- **Changes**:
  - Remove `jsonschema` from dependencies
  - Remove `_validate_with_schema()` function from config.py

---

## Blocked

- [ ] *(none)*

---

## Done

- [x] **Task model**: Schema → Pydantic with validators (status, priority, task_id pattern)
- [x] **Generator**: Auto-generates pattern validators from schema regex
- [x] **Test fixes**: Update test task_ids to match pattern

---

## File Summary

| File | Current | Target | Status |
|------|---------|--------|--------|
| `src/agency/models/task.py` | Pydantic + validators | Done | ✅ |
| `src/agency/models/config.py` | Pydantic (wrong from_dict) | Wire to config.py | ⬜ |
| `src/agency/models/manager.py` | Pydantic | Wire to config.py | ⬜ |
| `src/agency/models/agent.py` | Pydantic (wrong from_dict) | Wire to config.py | ⬜ |
| `src/agency/models/notification.py` | Pydantic (wrong from_dict) | Wire to notifications.py | ⬜ |
| `src/agency/models/audit_event.py` | Missing | Create schema + wire | ⬜ |
| `src/agency/config.py` | dataclass | Use Pydantic models | ⬜ |
| `src/agency/audit.py` | dataclass | Use Pydantic model | ⬜ |
| `src/agency/pi_inject.py` | dataclass | Use Pydantic model | ⬜ |
| `src/agency/template_inject.py` | dataclass | Use Pydantic models | ⬜ |
| `src/agency/__main__.py` | dataclass | Use Pydantic models | ⬜ |
| `scripts/generate_models.py` | Missing return type fix | Fix class name | ⬜ |

---

## Validation Points

Once complete, data will be validated at:

| Component | Load Point | Validation |
|-----------|-----------|-----------|
| AgencyConfig | `load_agency_config()` | `Config.model_validate()` |
| ManagerConfig | `load_manager_config()` | `Manager.model_validate()` |
| AgentConfig | `load_agents_config()` | `Agent.model_validate()` |
| AuditEvent | `AuditStore.log_*()` | `AuditEvent.model_validate()` |
| Notification | `NotificationStore.add()` | `Notification.model_validate()` |
| Task | `add_task()`, `get_task()` | `Task.model_validate()` |

---

## Commands

```bash
# Generate models (after schema changes)
python3 scripts/generate_models.py

# Run tests
uv run pytest tests/ -q --timeout=60

# Check lint
uv run ruff check src/agency/
uv run ruff format src/agency/
```
