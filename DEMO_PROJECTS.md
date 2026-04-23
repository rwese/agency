# Agency Demo Projects

Build these demo projects to test and showcase agency capabilities.

## Requirements for All Projects

Every demo project must include:

### 1. Reviewer Agent
Each project should demonstrate the reviewer workflow:
- Reviewer agent spawned when task enters `pending_approval`
- Reviewer checks code quality, tests, documentation
- Reviewer approves or rejects with feedback
- Manual override: `agency tasks approve <task-id>` or `agency tasks reject <task-id> --reason "..."`

### 2. End-to-End Test Report
Each project must produce an e2e test report documenting:
- **Test environment** (OS, versions, runtime)
- **Test execution** (commands run, output)
- **Results** (pass/fail for each test case)
- **Evidence** (screenshots, logs, error traces)
- **Summary** (total tests, passed, failed, coverage %)

Report format: Markdown file `TEST_REPORT.md` in project root.

---

## Projects

| # | Project | Type | Complexity | Status |
|---|---------|------|------------|--------|
| 1 | Log Parser | CLI | Low | ✅ Complete |
| 2 | URL Shortener | API | Medium | ✅ Complete |
| 3 | Bookmarks Vault | Web | Medium | ✅ Complete |
| 4 | Secret Scanner | CLI | Medium | ⬜ Not started |

---

## 1. Log Parser (CLI)

**Location:** `~/sandpit/log-parser`

**Description:** CLI tool to parse and analyze log files.

**Features:**
- Parse common log formats (Apache, Nginx, syslog, JSON)
- Filter by level (ERROR, WARN, INFO, DEBUG)
- Aggregate statistics (error count, top IPs, etc.)
- Export to JSON or CSV
- Colorized terminal output

**Tech:** Python or Go (single binary)

**Testing:**
- Unit tests for parsers
- Integration tests with sample logs
- E2E: Run CLI on sample log file, verify output

**TEST_REPORT.md sections:**
```markdown
## Test Environment
- OS: macOS 14.x
- Runtime: Python 3.12 / Go 1.22

## Test Cases
| ID | Test | Command | Expected | Actual | Status |
|----|------|---------|---------|--------|--------|
| TC01 | Parse Apache log | `log-parser parse access.log` | Count > 0 | 1,234 | ✅ PASS |

## Evidence
[Screenshots of CLI output]
```

---

## 2. URL Shortener (API)

**Location:** `~/sandpit/url-shortener`

**Description:** Simple URL shortening service with storage backend.

**Features:**
- Create short URLs (POST /links)
- Redirect by short code (GET /{code})
- View stats (GET /{code}/stats)
- Delete links (DELETE /{code})
- Optional expiration
- Click analytics

**Tech:**
- API: Python FastAPI or Go
- Storage: Garage (S3-compatible) or SQLite
- No auth needed for MVP

**Testing:**
- Unit tests
- API integration tests (start server, curl endpoints)
- E2E: Full flow from create → redirect → stats → delete

**TEST_REPORT.md sections:**
```markdown
## Test Environment
- OS: macOS 14.x
- API Runtime: Python 3.12 / FastAPI
- Storage: SQLite

## API Test Cases
| ID | Endpoint | Method | Status | Response |
|----|----------|--------|--------|----------|
| API01 | /links | POST | 201 | `{"code": "abc123"}` |

## E2E Flow
1. Create link → 201
2. Redirect → 302 to original URL
3. Check stats → 200 with click count
```

---

## 3. Bookmarks Vault (Web)

**Location:** `~/sandpit/bookmarks-vault`

**Description:** Local-first bookmark manager with tagging.

**Features:**
- Add/edit/delete bookmarks
- Tag-based organization
- Search by title, URL, tags
- Import from browser (HTML export)
- Export to JSON
- Drag-and-drop ordering
- Dark/light themes

**Tech:** Single HTML file, vanilla JS, localStorage

**Testing:**
- Unit tests for data layer
- Browser testing with Playwright
- E2E: User flow add → search → delete

**TEST_REPORT.md sections:**
```markdown
## Test Environment
- OS: macOS 14.x
- Browser: Chrome 124 / Firefox 125

## Playwright Tests
| ID | Test | Status | Duration |
|----|------|--------|----------|
| E2E01 | Add bookmark | ✅ PASS | 1.2s |
| E2E02 | Search by tag | ✅ PASS | 0.8s |

## Screenshots
[Playwright screenshots on failure]
```

---

## 4. Secret Scanner (CLI)

**Location:** `~/sandpit/secret-scanner`

**Description:** Scan directories for exposed secrets (API keys, tokens, etc.).

**Features:**
- Detect common secret patterns (AWS keys, GitHub tokens, API keys)
- Support multiple patterns (regex + entropy)
- Output format: JSON, SARIF, human-readable
- Configurable severity levels
- Ignore false positives (.gitignore style)
- Pre-commit hook integration

**Tech:** Python with patterns library or Go

**Testing:**
- Test against sample files with seeded secrets
- Verify no false negatives on known patterns
- E2E: Scan test directory, verify secrets detected

**TEST_REPORT.md sections:**
```markdown
## Test Environment
- OS: macOS 14.x
- Runtime: Python 3.12 / Go 1.22

## Detection Tests
| Pattern | Sample | Detected | Confidence |
|---------|--------|----------|------------|
| AWS Key | `AKIAIOSFODNN7EXAMPLE` | ✅ | High |
| GitHub Token | `ghp_xxxxxxxxxxxx` | ✅ | High |

## E2E Scan
```bash
secret-scanner scan ./test-files --format json
# Expected: 5 secrets found, 0 false positives
```
```

---

## Agency Usage

For each project:

```bash
cd ~/sandpit/<project>
agency init --dir . --template basic  # or api/fullstack
agency session start
# Work with manager to create tasks...
agency session stop
```

### Required Task Flow

```
┌─────────────┐    ┌───────────────┐    ┌────────────────┐
│   pending   │───▶│ in_progress   │───▶│ pending_approval│
│  (unassigned)│   │  (assigned)   │    │   (reviewer)   │
└─────────────┘    └───────────────┘    └────────────────┘
                                                  │
                              ┌───────────────────┴───────────────────┐
                              ▼                                       ▼
                      ┌───────────────┐                        ┌──────────────┐
                      │  completed    │                        │   rejected   │
                      │  (archived)   │                        │  (retry)     │
                      └───────────────┘                        └──────────────┘
```

### Example Task Breakdown (Log Parser)

```bash
# Core implementation
agency tasks add -s "Implement log parser core" -d "Create parser classes for Apache, Nginx, syslog formats"
agency tasks add -s "Add CLI interface" -d "Argparse/click CLI with filter options"
agency tasks add -s "Add export functionality" -d "JSON and CSV export options"

# Testing & Review
agency tasks add -s "Add unit tests" -d "Unit tests for parsers, integration tests"
agency tasks add -s "Add e2e tests" -d "End-to-end test with sample logs"

# Review & Report
agency tasks add -s "Review code" -d "Review implementation, tests, and documentation"
agency tasks add -s "Create test report" -d "Document test execution and results in TEST_REPORT.md"
```

### Verification Checklist

Before marking project complete, verify:

- [ ] All tasks approved by reviewer
- [ ] `TEST_REPORT.md` exists with:
  - [ ] Test environment section
  - [ ] Test cases table with pass/fail
  - [ ] Evidence (logs, screenshots)
  - [ ] Summary statistics
- [ ] Code passes linter
- [ ] Tests pass locally
