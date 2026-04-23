# Demo Project 05: CSV to SQLite Importer

**Type:** CLI Tool
**Complexity:** Medium
**Purpose:** Test data import, schema inference, query capabilities

## Overview

Import CSV files into SQLite with automatic schema inference and SQL query capabilities.

## Features

- [ ] Auto-detect column types (string, integer, float, date)
- [ ] Handle quoted fields and escape characters
- [ ] Custom delimiter support (comma, tab, semicolon, pipe)
- [ ] Header row detection (or force no header)
- [ ] Create table with inferred schema
- [ ] Support for large files (streaming/chunked)
- [ ] Interactive SQL query mode
- [ ] Export query results to CSV/JSON
- [ ] Index creation on specified columns

## Tech Stack

- **Language:** Python
- **Dependencies:** `csv` (stdlib), `sqlite3` (stdlib)

## CLI Interface

```bash
# Import CSV
csv2sqlite import data.csv --db mydata.db --table people

# Auto-detect types
csv2sqlite import data.csv --db mydata.db

# Custom delimiter
csv2sqlite import data.csv --db mydata.db --delimiter "\t"

# Query mode
csv2sqlite query mydata.db "SELECT * FROM data LIMIT 10"

# Export results
csv2sqlite export mydata.db "SELECT * FROM data" --format csv --output out.csv

# Create index
csv2sqlite index mydata.db --table data --column email

# Show schema
csv2sqlite schema mydata.db
```

## Test Cases

| ID | Test | Description |
|----|------|-------------|
| TC01 | Import basic | CSV imports correctly |
| TC02 | Auto-types | Integers detected as int |
| TC03 | Quoted fields | "field,with,commas" works |
| TC04 | Delimiter tab | Tab-separated works |
| TC05 | Large file | 100k+ rows imports |
| TC06 | Query SELECT | SELECT works |
| TC07 | Query WHERE | WHERE filter works |
| TC08 | Export CSV | CSV export valid |
| TC09 | Export JSON | JSON export valid |

## Task Breakdown

1. Create CSV parser with streaming support
2. Implement type inference (sample-based)
3. Handle edge cases (quotes, escapes, newlines)
4. Create SQLite import functionality
5. Implement query interface
6. Add export formats (CSV, JSON)
7. Add index creation
8. Write unit tests for parser
9. Write integration tests for full flow
10. Create e2e test report

## Success Criteria

- Imports CSV with 100k+ rows without memory issues
- Type inference is correct (95%+ accuracy)
- Handles all standard CSV edge cases
- Query results are accurate
- Exports are valid CSV/JSON
