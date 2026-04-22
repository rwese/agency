# Agency Development TODO

## Status: In Progress

## Tasks

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Create `template_inject.py` module | [x] | Module with `TemplateInjector` class |
| 2 | Add custom delimiter support | [x] | Configurable placeholder pattern |
| 3 | Integrate into personality loading | [x] | Hook into session.py manager/agent launch |
| 4 | Integrate into context file processing | [x] | Process context files before append |
| 5 | Add tests | [x] | Unit tests for TemplateInjector |
| 6 | Update AGENTS.md documentation | [x] | Document placeholder syntax |

## Progress Log

- [2026-04-22] Plan approved, starting implementation
- [2026-04-22] Created `template_inject.py` with `TemplateInjector`, custom delimiter support
- [2026-04-22] Integrated template injection into session.py (manager + agent personality + context files)
- [2026-04-22] Added 23 unit tests for TemplateInjector, all passing
- [2026-04-22] Updated AGENTS.md with template injection documentation
- [2026-04-22] Added `template_delimiter` config option

---

## agency-web Testing (Greenfield Project)

### Bugs Found & Fixed

| # | Bug | Root Cause | Fix |
|---|-----|------------|-----|
| 1 | YAML multiline block parsing | `\|` literal blocks end at blank lines | Indent all content (headers, lists) inside multiline blocks |
| 2 | `.agency` deleted accidentally | `rm -rf agency-web/.agency` ran from wrong dir | Use absolute paths |
| 3 | Only default `developer` agent loaded | `agency_dir = git_root / ".agency"` assumes `.agency` at git root | Use `work_dir / ".agency"` |

### Key Learnings

1. **YAML multiline blocks**: When using `|` literal blocks, blank lines end the block. All subsequent content must be indented 2+ spaces.

2. **Project structure**: When creating a subdirectory project within a git repo, `.agency/` must be in the subdirectory, not at the git root.

3. **Template generation**: The `agency init --template` command downloads templates but doesn't properly override existing `.agency/` configs.

### Next Steps for agency-web

1. Assign tasks to agents (backend, frontend, devops, etc.)
2. Implement core features from PRD.md
3. Test agency coordination with parallel agent work

### Related Commits

- `fix(agency): use work_dir for .agency, not git_root`
- `feat(agency-web): add project scaffold and agency configuration`
