## Plan: Agency Skill - Templates & Assets Update

### Research Summary

**Existing structure:**
- Skill: `.agents/skills/agency/SKILL.md` + `references/{commands,config}.md`
- Templates: `templates/{basic, api, fullstack}/.agency/` (ready-to-copy project structures)
- Templates contain: `agents.yaml`, `config.yaml`, `manager.yaml`, `agents/*.yaml`, `agents/*/personality.md`

**Gap identified:** No guidance on *creating* custom agencies/agents, no starter personality snippets, no guides.

---

### Scope

**Goals:**
- Add reusable agent personality snippets (coder, reviewer, devops, tester, architect)
- Create a `solo` template (minimal single-agent for personal projects)
- Create a `team` template (multi-agent with distinct roles)
- Add creation guide in `references/` explaining how to build custom agencies
- Document template selection guidance in skill

**Non-Goals:**
- Not modifying core agency CLI behavior
- Not adding agent runtime logic
- Not creating documentation outside skill

**Assumptions:**
- Users clone/copy templates into their own projects
- Templates use existing schema (config.yaml, manager.yaml, agents.yaml)
- Agent personality snippets are `.md` files referenced by agent configs

---

### Tech Stack

- **Language:** Markdown (templates), YAML (configs)
- **Framework:** N/A
- **Database:** N/A
- **Hosting:** N/A
- **Tools:** Standard agency template structure

---

### Milestones

## M1 - Personality snippets

### M1.1 Create agent personality snippets
- Criteria: 5 personality .md files in `assets/personalities/` covering: coder, reviewer, devops, tester, architect
- Each file: ~30-50 lines with strengths, guidelines, task workflow

### M1.2 Update SKILL.md with personality snippet usage
- Criteria: Document how to reference snippets, link to `assets/personalities/`

**Priority:** high

---

## M2 - New templates

### M2.1 Create `templates/solo/.agency/` template
- Criteria: Minimal single-agent setup with 1 manager + 1 coder, simple config
- Contains: config.yaml, manager.yaml, agents.yaml, agents/developer.yaml, agents/developer/personality.md, README.md

### M2.2 Create `templates/team/.agency/` template
- Criteria: Multi-agent setup with manager + 3 roles (coder, reviewer, tester)
- Contains: Full structure with separate agent configs and distinct personalities

### M2.3 Add template selection guidance to SKILL.md
- Criteria: Table comparing templates by use case (solo, api, fullstack, team)

**Priority:** high

---

## M3 - Creation guide

### M3.1 Create `references/creating-agencies.md`
- Criteria: Step-by-step guide covering: 1) Planning agents, 2) Writing personality, 3) Configuring agents.yaml, 4) Testing template

### M3.2 Add reference links to SKILL.md
- Criteria: SKILL.md references `references/creating-agencies.md` for custom agency creation

**Priority:** med

---

### Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| Templates become stale as agency evolves | Version templates with agency release, note schema URL |
| Personality snippets too generic | Include placeholders for customization (`${{project_name}}`) |

### Decision Log

- **Chose `assets/personalities/` over inline content** — Snippets are reusable across templates, single source of truth
- **Chose `solo` + `team` over `minimal` + `saas`** — Clearer differentiation for primary audience (solo developers, small teams)
- **Chose markdown personalities over YAML** — More expressive for guidelines/strengths sections

---

### Definition of Done

A task is **done** when:
- Code/files written and match schema (validated against existing templates)
- Files referenced from SKILL.md or included in expected locations
- No debug code, TODOs, or dead files
- Changes documented in skill updates

---

### Self-Review Checklist

- [x] Every task has acceptance criteria
- [x] Tasks are atomic (one logical unit)
- [x] Tasks respect dependencies (M1 before M3)
- [x] Blockers are identified, not hidden
- [x] Scope is bounded (non-goals clear)
