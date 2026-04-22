# agency-web E2E Test Plan

## Objective
Validate that the Agency v2.0 tooling can successfully orchestrate a team of AI agents to build a complete full-stack web application from planning to deployment.

## Success Criteria
1. ✅ All 6 phases complete with working code
2. ✅ Backend starts and responds to health check
3. ✅ Frontend builds and loads without errors
4. ✅ Docker Compose runs all services
5. ✅ CI/CD pipeline executes successfully
6. ✅ No critical bugs in agency tooling exposed

## Test Environment
- **Location**: `agency-web/` directory
- **Template**: fullstack-ts
- **Team**: backend, frontend, devops, architect, security, qa
- **parallel_limit**: 2

## Test Phases

### Phase 0: Setup (Manual)
- [ ] Delete existing `agency-web/` directory
- [ ] Create fresh `agency-web/` with git init
- [ ] Run `agency init --template fullstack-ts`
- [ ] Copy planning docs: PRD.md, API.md, DATA_MODEL.md, TODO.md, UI_WIREFRAMES.md
- [ ] Run `agency start`
- [ ] Verify all 7 members running (manager + 6 agents)

### Phase 1: Infrastructure
| Task | Agent | Verification |
|------|-------|--------------|
| 1.1 Backend scaffolding | backend | `backend/src/index.ts` exists, `npm install` works |
| 1.2 Frontend scaffolding | frontend | `frontend/src/App.tsx` exists, `npm install` works |
| 1.3 Docker Compose | devops | `docker compose config` passes |
| 1.4 CI/CD pipeline | devops | `.github/workflows/ci.yml` runs on push |

**Verification Commands:**
```bash
cd agency-web
ls backend/src/index.ts
ls frontend/src/App.tsx
docker compose config
```

### Phase 2: Backend Core
| Task | Agent | Verification |
|------|-------|--------------|
| 2.1 Prisma schema | backend | `prisma/schema.prisma` parses, migrations run |
| 2.2 Database migrations | backend | `prisma migrate dev` succeeds |
| 2.3 Auth endpoints | backend | POST /api/auth/login returns 200 |
| 2.4 User endpoints | backend | GET /api/users returns 200 |
| 2.5 Team endpoints | backend | GET /api/teams returns 200 |

**Verification Commands:**
```bash
cd agency-web/backend
npx prisma validate
npx prisma migrate status
curl -s http://localhost:3000/api/health | jq .status
```

### Phase 3: Backend Features
| Task | Agent | Verification |
|------|-------|--------------|
| 3.1 Epic CRUD | backend | Full REST operations work |
| 3.2 Task CRUD | backend | Full REST operations work |
| 3.3 Comments | backend | POST /api/tasks/:id/comments works |
| 3.4 Search | backend | GET /api/search?q=test returns results |
| 3.5 Webhooks | backend | POST /api/webhooks/github works |

### Phase 4: Frontend Core
| Task | Agent | Verification |
|------|-------|--------------|
| 4.1 Layout | frontend | Sidebar navigation renders |
| 4.2 Auth pages | frontend | Login form submits successfully |
| 4.3 Dashboard | frontend | Widgets load on dashboard |
| 4.4 Epics list | frontend | Epics display from API |
| 4.5 Tasks list | frontend | Tasks display with status badges |
| 4.6 Kanban | frontend | Drag-drop between columns works |

**Verification Commands:**
```bash
cd agency-web/frontend
npm run build  # Should complete without errors
npm run dev    # Should start on port 5173
```

### Phase 5: Frontend Features
| Task | Agent | Verification |
|------|-------|--------------|
| 5.1 Inline editing | frontend | Click-to-edit works |
| 5.2 Bulk actions | frontend | Multi-select and bulk edit works |
| 5.3 Keyboard shortcuts | frontend | J/K navigation, E to edit |
| 5.4 Mobile | frontend | Responsive at 375px width |
| 5.5 Accessibility | frontend | axe-core reports 0 violations |

### Phase 6: Integration
| Task | Agent | Verification |
|------|-------|--------------|
| 6.1 E2E tests | qa | Playwright tests pass |
| 6.2 Health check | backend | /api/health returns 200 |
| 6.3 Docker images | devops | Images push to GHCR |
| 6.4 Documentation | qa | README, API docs complete |

## Agency Tooling Validation

### Heartbeat Functionality
- [ ] Manager receives task notifications
- [ ] Agents receive task assignments
- [ ] Idle agents receive ping after 2 min
- [ ] parallel_limit respected (max 2 concurrent)

### Task Management
- [ ] `agency tasks add` creates tasks
- [ ] `agency tasks assign` distributes work
- [ ] `agency tasks list` shows correct status
- [ ] `agency tasks complete` archives work

### Session Management
- [ ] `agency start` launches all members
- [ ] `agency stop` gracefully shuts down
- [ ] `agency attach` connects to session
- [ ] `agency members` shows active agents

## Test Execution Log

| Date | Phase | Result | Notes |
|------|-------|--------|-------|
| 2026-04-22 | 0 | ⏳ | Setup in progress |

## Known Issues
- [ ] Task ID parsing bug (contains "orb" splits incorrectly)
- [ ] Agents sometimes show wrong personality
- [ ] Heartbeat may not send notifications reliably

## Defects Found
| ID | Description | Severity | Status |
|----|-------------|----------|--------|
| | | | |

## Attachments
- Planning docs: `planning/agency-web/`
- Screenshot evidence: (capture during test)
- Logs: `.agency/audit.db`
