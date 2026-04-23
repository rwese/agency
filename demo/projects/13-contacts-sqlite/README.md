# Demo Project 13: Contacts Manager (SQLite)

**Type:** Full-Stack Web App
**Complexity:** Medium-High
**Purpose:** Test database integration, CRUD, form handling, server-side rendering

## Overview

A contact management application with SQLite database, server-side rendering, and basic search.

## Features

- [ ] List contacts with pagination
- [ ] View single contact details
- [ ] Create new contact (form)
- [ ] Edit existing contact
- [ ] Delete contact with confirmation
- [ ] Search by name/email
- [ ] Filter by tags
- [ ] Import contacts from CSV
- [ ] Export contacts to CSV
- [ ] Contact count display

## Data Model

### Contact (SQLite)

```sql
CREATE TABLE contacts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT UNIQUE,
  phone TEXT,
  company TEXT,
  notes TEXT,
  tags TEXT,  -- JSON array
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Contact API Response

```json
{
  "id": 1,
  "name": "Jane Doe",
  "email": "jane@example.com",
  "phone": "+1-555-0123",
  "company": "Acme Corp",
  "notes": "Met at conference",
  "tags": ["work", "vip"],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

## Tech Stack

- **Backend:** Python + FastAPI or Flask + Jinja2
- **Database:** SQLite
- **Frontend:** HTML + Tailwind CSS (CDN)
- **No JavaScript required** (progressive enhancement)

## File Structure

```
contacts-sqlite/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic schemas
│   ├── database.py      # DB connection
│   └── routers/
│       ├── contacts.py
│       └── import_export.py
├── templates/
│   ├── base.html
│   ├── contacts/
│   │   ├── list.html
│   │   ├── detail.html
│   │   ├── form.html
│   │   └── confirm_delete.html
│   └── import.html
├── static/
│   └── style.css
├── tests/
│   ├── test_api.py
│   └── test_db.py
├── requirements.txt
└── TEST_REPORT.md
```

## API Endpoints

```bash
# Web UI
GET  /                    # Contact list
GET  /contacts/{id}       # Contact detail
GET  /contacts/new        # New contact form
POST /contacts/new        # Create contact
GET  /contacts/{id}/edit # Edit form
POST /contacts/{id}/edit # Update contact
POST /contacts/{id}/delete # Delete contact

# API (JSON)
GET    /api/contacts           # List (with search/pagination)
POST   /api/contacts           # Create
GET    /api/contacts/{id}      # Get
PUT    /api/contacts/{id}      # Update
DELETE /api/contacts/{id}      # Delete
POST   /api/contacts/import   # Import CSV
GET    /api/contacts/export   # Export CSV
```

## Test Cases

| ID | Test | Description |
|----|------|-------------|
| TC01 | Create contact | Contact appears in list |
| TC02 | Edit contact | Changes persist |
| TC03 | Delete contact | Removed from database |
| TC04 | Search name | Results filtered |
| TC05 | Search email | Results filtered |
| TC06 | Filter tag | Matching contacts shown |
| TC07 | Pagination | Correct page displayed |
| TC08 | Import CSV | Contacts created |
| TC09 | Export CSV | Valid CSV downloaded |
| TC10 | Unique email | Duplicate rejected |
| TC11 | Form validation | Required fields enforced |

## Task Breakdown

1. Setup project structure
2. Configure SQLite database
3. Define SQLAlchemy models
4. Create database migrations
5. Build CRUD operations
6. Implement search
7. Add tag filtering
8. Create Jinja2 templates
9. Add form validation
10. Implement CSV import/export
11. Write unit tests for models
12. Write integration tests for API
13. Write e2e tests
14. Create e2e test report

## Success Criteria

- All CRUD operations work
- Search filters in real-time
- CSV import creates contacts correctly
- CSV export produces valid file
- Form validation prevents invalid data
- Pagination works correctly
- Database constraints enforced
- Tests pass for all endpoints
