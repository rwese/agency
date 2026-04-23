# Demo Project 16: Static Site Generator

**Type:** Build Tool
**Complexity:** Medium
**Purpose:** Test file processing, templating, asset handling, build pipelines

## Overview

A simple static site generator that converts Markdown files to HTML with layouts and assets.

## Features

- [ ] Parse Markdown to HTML
- [ ] Layout system (base + page templates)
- [ ] Include/partial system
- [ ] Frontmatter parsing (YAML)
- [ ] Asset copying (CSS, JS, images)
- [ ] Markdown extensions (tables, code blocks)
- [ ] Config file (site.yaml)
- [ ] Live reload during development
- [ ] Build optimization (minify CSS/JS)
- [ ] Sitemap generation
- [ ] RSS feed generation

## Project Structure

```
site/
├── content/
│   ├── _layouts/
│   │   ├── base.html
│   │   └── post.html
│   ├── _includes/
│   │   ├── header.html
│   │   └── footer.html
│   ├── index.md
│   ├── about.md
│   └── posts/
│       ├── 2024-01-15-welcome.md
│       └── 2024-01-20-features.md
├── assets/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── static/
│   └── images/
│       └── logo.png
├── site.yaml
└── _config.yml
```

## Configuration

### site.yaml

```yaml
site:
  title: "My Blog"
  description: "A simple blog"
  url: "https://example.com"
  author: "John Doe"

build:
  output_dir: "_site"
  markdown_ext:
    - tables
    - fenced_code
    - autolink
  minify: true

plugins:
  - sitemap
  - rss
```

## Frontmatter

```markdown
---
title: "Welcome to My Blog"
date: 2024-01-15
author: "John Doe"
tags: ["welcome", "intro"]
layout: post
draft: false
---

# Welcome

This is the content...
```

## Layouts

### base.html

```html
<!DOCTYPE html>
<html>
<head>
  <title>{{ page.title }} - {{ site.title }}</title>
  <link rel="stylesheet" href="/assets/css/style.css">
</head>
<body>
  {% include header.html %}
  <main>
    {{ content | safe }}
  </main>
  {% include footer.html %}
</body>
</html>
```

### post.html

```html
---
layout: base
---

<article class="post">
  <header>
    <h1>{{ page.title }}</h1>
    <time>{{ page.date | date: "%B %d, %Y" }}</time>
  </header>
  <div class="content">
    {{ content | safe }}
  </div>
</article>
```

## CLI Interface

```bash
# Build site
ssg build

# Development server with live reload
ssg serve --port 8000

# Clean output directory
ssg clean

# Initialize new site
ssg init my-site

# Generate sitemap
ssg sitemap

# Generate RSS feed
ssg feed
```

## Filters

| Filter | Usage | Description |
|--------|-------|-------------|
| `date` | `{{ page.date \| date: "%Y-%m-%d" }}` | Format date |
| `markdown` | `{{ content \| markdown }}` | Render markdown |
| `slugify` | `{{ title \| slugify }}` | Convert to URL slug |
| `strip_html` | `{{ html \| strip_html }}` | Remove HTML tags |

## Test Cases

| ID | Test | Description |
|----|------|-------------|
| TC01 | Parse markdown | Basic MD renders correctly |
| TC02 | Frontmatter | YAML parsed correctly |
| TC03 | Layout inheritance | Base layout applied |
| TC04 | Include partials | Partials included |
| TC05 | Asset copy | CSS/JS copied to output |
| TC06 | Static copy | Images copied correctly |
| TC07 | Build output | HTML files generated |
| TC08 | Live reload | Changes trigger rebuild |
| TC09 | Sitemap | Valid sitemap.xml |
| TC10 | RSS feed | Valid feed.xml |
| TC11 | Minification | CSS/JS minified |
| TC12 | Draft skip | Draft pages skipped |

## Task Breakdown

1. Setup project structure
2. Create config parser
3. Implement frontmatter parser
4. Implement Markdown renderer
5. Create layout system
6. Implement include system
7. Add filter system
8. Create asset pipeline
9. Implement development server
10. Add live reload
11. Implement minification
12. Add sitemap plugin
13. Add RSS plugin
14. Write unit tests
15. Write integration tests
16. Create e2e test report

## Success Criteria

- All markdown files converted to HTML
- Layouts applied correctly
- Includes work in layouts
- Assets copied to output
- Sitemap is valid XML
- RSS feed is valid XML
- Minification reduces file size
- Live reload detects changes < 1s
- Draft pages not in output
- Output is valid HTML5
