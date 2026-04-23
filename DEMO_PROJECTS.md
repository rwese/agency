# Agency Demo Projects

Build these demo projects to test and showcase agency capabilities.

## Projects

| # | Project | Type | Complexity | Status |
|---|---------|------|------------|--------|
| 1 | Log Parser | CLI | Low | ⬜ Not started |
| 2 | URL Shortener | API | Medium | ⬜ Not started |
| 3 | Bookmarks Vault | Web | Medium | ⬜ Not started |
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

**Testing:** Unit tests for parsers, integration tests with sample logs

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

**Testing:** Unit tests, API integration tests

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

**Testing:** Browser testing with Playwright

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

**Testing:** Test against sample files with seeded secrets

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

### Task Breakdown Example (Log Parser)

```bash
agency tasks add -s "Implement log parser core" -d "Create parser classes for Apache, Nginx, syslog formats"
agency tasks add -s "Add CLI interface" -d "Argparse/click CLI with filter options"
agency tasks add -s "Add export functionality" -d "JSON and CSV export options"
agency tasks add -s "Add tests" -d "Unit tests for parsers, integration tests"
```
