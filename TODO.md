# TODO: agency init Local Project Support

## Status: In Progress

## Tasks

### Stage 1: Core Infrastructure
- [x] 1.1 Define paths module - Add LOCAL_AGENCY_DIR constant and helper functions
- [x] 1.2 Add git root detection helper function

### Stage 2: CLI Changes
- [x] 2.1 Add arg parsing for init - --global, --local, --force flags
- [x] 2.2 Implement interactive detection
- [x] 2.3 Implement cmd_init_interactive() with prompts

### Stage 3: Local Init Implementation
- [x] 3.1 Implement cmd_init_local() - Create .agency/ structure in git root
- [x] 3.2 Create local template files (agents/, managers/, README.md)

### Stage 4: Documentation & Testing
- [x] 4.1 Update shell completions - Add new flags to bash/zsh/fish
- [x] 4.2 Update AGENTS.md and README.md
- [x] 4.3 Add test cases to test_agency.sh

---

## Notes

- Local directory: `.agency/` in git root
- Interactive mode prompts for: scope, sample agents, sample managers
- Git detection auto-suggests --local in git repos
- Non-interactive requires explicit --global or --local
