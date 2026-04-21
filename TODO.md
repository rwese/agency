# TODO: Agency End-to-End Integration Test

## Status: In Progress

## Tasks

### Stage 1: Test Infrastructure
- [x] 1.1 Create test directory structure
- [x] 1.2 Create manager config with communication protocol
- [x] 1.3 Create coder agent config
- [x] 1.4 Create tester agent config

### Stage 2: Test Execution
- [x] 2.1 Create justfile recipes for test execution
- [x] 2.2 Create test runner script
- [x] 2.3 Document test procedure in TESTING.md

### Stage 3: Execution & Validation
- [x] 3.1 Run initial test with real pi agents (manager started)
- [ ] 3.2 Verify manager → agent communication (needs attach)
- [ ] 3.3 Verify task completion
- [ ] 3.4 Document findings and blindspots

---

## Test Scenario
- Task: Create a simple CLI todo app
- Manager: Orchestrates task delegation
- Agents: coder (implements), tester (verifies)
- Expected: Working todo CLI in test-todo-app/

## Blind Spots to Watch
1. Pi startup timing
2. Session directory sharing
3. Personality injection
4. Message delivery order
5. Error propagation
