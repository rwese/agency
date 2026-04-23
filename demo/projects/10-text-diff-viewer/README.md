# Demo Project 10: Text Diff Viewer

**Type:** CLI Tool
**Complexity:** Medium
**Purpose:** Test text processing, diff algorithms, terminal output

## Overview

A terminal-based diff viewer with side-by-side view, syntax highlighting, and navigation.

## Features

- [ ] Unified diff format output
- [ ] Side-by-side diff view
- [ ] Inline diff (within line)
- [ ] Syntax highlighting (for code)
- [ ] Word-level diff highlighting
- [ ] Directory diff (recursive)
- [ ] Ignore whitespace option
- [ ] Ignore case option
- [ ] Color output (with --color)
- [ ] Exit codes for scripting (0=same, 1=different)

## Tech Stack

- **Language:** Python
- **Dependencies:** `difflib` (stdlib), `pygments` (optional for syntax)

## CLI Interface

```bash
# Compare two files
diffview file1.txt file2.txt

# Side-by-side view
diffview file1.txt file2.txt --side-by-side

# Unified diff (git style)
diffview file1.txt file2.txt --unified

# Directory diff
diffview dir1/ dir2/ --recursive

# Ignore whitespace
diffview file1.txt file2.txt --ignore-whitespace

# Word diff
diffview file1.txt file2.txt --word-diff

# With syntax highlighting
diffview file1.py file2.py --highlight

# Color output (auto-detected)
diffview file1.txt file2.txt --color=always
```

## Output Examples

### Side-by-side
```
file1.txt              | file2.txt
------------------------+------------------------
Hello world            | Hello universe
This is line 3         | This is line 3
- removed line         | + added line
```

### Unified
```
--- file1.txt
+++ file2.txt
@@ -1,3 +1,3 @@
 Hello world
-removed line
+added line
```

## Test Cases

| ID | Test | Description |
|----|------|-------------|
| TC01 | No changes | Identical files show no diff |
| TC02 | Added lines | New lines highlighted |
| TC03 | Removed lines | Removed lines highlighted |
| TC04 | Modified lines | Changed lines highlighted |
| TC05 | Side-by-side | Two columns displayed |
| TC06 | Word diff | Word-level changes shown |
| TC07 | Directory diff | Recursive comparison |
| TC08 | Ignore space | Whitespace ignored |
| TC09 | Ignore case | Case differences ignored |
| TC10 | Exit code | 0=same, 1=different |
| TC11 | Syntax highlight | Code highlighted |

## Task Breakdown

1. Implement unified diff generation
2. Create side-by-side renderer
3. Implement word-level diff
4. Add syntax highlighting with pygments
5. Implement directory diff
6. Add ignore whitespace/case options
7. Create color output (ANSI)
8. Set correct exit codes
9. Write unit tests for diff algorithms
10. Write integration tests
11. Create e2e test report

## Success Criteria

- Correctly identifies added/removed/modified lines
- Side-by-side view aligns correctly
- Word diff highlights exact changes
- Directory diff compares recursively
- Exit codes work for scripting
- Color output is readable
- Syntax highlighting works for common languages
