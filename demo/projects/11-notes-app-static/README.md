# Demo Project 11: Notes App (Static)

**Type:** Single Page Application (SPA)
**Complexity:** Low
**Purpose:** Test frontend-only web app, localStorage, vanilla JS

## Overview

A simple notes application with localStorage persistence. No backend required.

## Features

- [ ] Create notes with title and content
- [ ] Edit existing notes
- [ ] Delete notes with confirmation
- [ ] Search notes by title/content
- [ ] Sort by date created/modified
- [ ] Markdown preview toggle
- [ ] Dark/light theme toggle
- [ ] Export notes to JSON
- [ ] Import notes from JSON
- [ ] Responsive design (mobile-friendly)

## Tech Stack

- **Language:** HTML, CSS, JavaScript
- **Storage:** localStorage
- **No build step required**

## File Structure

```
notes-static/
├── index.html      # Single HTML file with embedded CSS/JS
├── SPEC.md         # This specification
└── TEST_REPORT.md  # Test results (to be generated)
```

## User Interface

```
┌─────────────────────────────────────────────┐
│ Notes App          [Search...] [+] [☀/🌙]  │
├──────────────┬──────────────────────────────┤
│ Notes List   │  Editor                      │
│              │                              │
│ ○ Note 1     │  Title: ___________         │
│ ○ Note 2     │                              │
│ ○ Note 3     │  Content:                   │
│              │  ┌──────────────────────────┐│
│              │  │                          ││
│              │  │                          ││
│              │  └──────────────────────────┘│
│              │                              │
│              │  [Save] [Delete] [Preview]   │
└──────────────┴──────────────────────────────┘
```

## Test Cases

| ID | Test | Description |
|----|------|-------------|
| TC01 | Create note | New note appears in list |
| TC02 | Edit note | Changes persist after reload |
| TC03 | Delete note | Note removed from list |
| TC04 | Search | Filtered results shown |
| TC05 | Sort by date | Notes ordered correctly |
| TC06 | Dark mode | Theme toggles correctly |
| TC07 | Export JSON | Valid JSON downloaded |
| TC08 | Import JSON | Notes loaded correctly |
| TC09 | Responsive | Works on mobile viewport |
| TC10 | Persistence | Data survives page reload |

## Task Breakdown

1. Create HTML structure
2. Implement note data model
3. Add localStorage persistence
4. Build note list UI
5. Build editor UI
6. Implement CRUD operations
7. Add search functionality
8. Add sorting
9. Add theme toggle
10. Add import/export
11. Add responsive CSS
12. Write Playwright tests
13. Create e2e test report

## Success Criteria

- All CRUD operations work correctly
- Data persists across page reloads
- Search filters in real-time
- Theme preference persists
- Export produces valid JSON
- Import loads notes correctly
- Works on mobile viewport (375px+)
- No console errors
