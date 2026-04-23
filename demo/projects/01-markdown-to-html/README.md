# Demo Project 01: Markdown to HTML Converter

**Type:** CLI Tool
**Complexity:** Low
**Purpose:** Test CLI parsing, file I/O, text transformation

## Overview

A command-line tool that converts Markdown files to HTML with syntax highlighting and configurable output.

## Features

- [ ] Parse standard Markdown (headings, lists, links, images, code blocks)
- [ ] Support GFM (GitHub Flavored Markdown) extensions
- [ ] Syntax highlighting for code blocks (using a library like `pygments` or `highlight.js`)
- [ ] Table support
- [ ] Custom CSS template option
- [ ] Standalone HTML output (embedded CSS)
- [ ] Watch mode for development

## Tech Stack

- **Language:** Python
- **Dependencies:** `markdown-it-py` or `mistune`, `pygments` (optional)
- **Output:** Single HTML file or HTML fragment

## CLI Interface

```bash
# Basic usage
md2html input.md -o output.html

# With embedded CSS
md2html input.md --standalone -o output.html

# Watch mode
md2html input.md --watch

# Custom template
md2html input.md --template custom.css -o output.html
```

## Test Cases

| ID | Test | Description |
|----|------|-------------|
| TC01 | Parse heading | H1-H6 rendered correctly |
| TC02 | Parse lists | Ordered/unordered lists |
| TC03 | Parse code block | Syntax highlighting applied |
| TC04 | Parse table | Table with header and rows |
| TC05 | Parse link/image | Links work, images show |
| TC06 | Standalone output | CSS embedded in output |
| TC07 | Watch mode | Changes trigger rebuild |

## Task Breakdown

1. Create parser module for Markdown
2. Implement HTML renderer with templates
3. Add syntax highlighting for code blocks
4. Implement CLI with argparse/click
5. Add watch mode with file monitoring
6. Write unit tests for parser
7. Write integration tests for CLI
8. Create e2e test report

## Success Criteria

- All Markdown elements render correctly
- Syntax highlighting works for 3+ languages
- Standalone output is self-contained
- Watch mode detects file changes < 1s
- No external dependencies in output HTML (when standalone)
