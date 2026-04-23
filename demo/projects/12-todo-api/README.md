# Demo Project 12: Todo API (REST)

**Type:** REST API
**Complexity:** Medium
**Purpose:** Test API design, HTTP handling, request/response validation

## Overview

A RESTful todo API with in-memory storage. No database required.

## Features

- [ ] Create todo (POST /todos)
- [ ] List todos (GET /todos)
- [ ] Get single todo (GET /todos/{id})
- [ ] Update todo (PUT /todos/{id})
- [ ] Delete todo (DELETE /todos/{id})
- [ ] Mark complete (PATCH /todos/{id}/complete)
- [ ] Filter by status (GET /todos?status=pending)
- [ ] Filter by priority (GET /todos?priority=high)
- [ ] Pagination (GET /todos?page=1&limit=20)
- [ ] Health check endpoint (GET /health)

## Data Model

```json
{
  "id": "uuid",
  "title": "string (required)",
  "description": "string (optional)",
  "status": "pending|in_progress|completed",
  "priority": "low|normal|high",
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

## Tech Stack

- **Language:** Python
- **Framework:** FastAPI or Flask
- **Storage:** In-memory (dict)

## API Endpoints

```bash
# Create todo
POST /todos
Content-Type: application/json
{"title": "Buy groceries", "priority": "normal"}

# List todos
GET /todos
GET /todos?status=pending&priority=high&page=1&limit=10

# Get todo
GET /todos/{id}

# Update todo
PUT /todos/{id}
Content-Type: application/json
{"title": "Updated title", "status": "completed"}

# Delete todo
DELETE /todos/{id}

# Mark complete
PATCH /todos/{id}/complete

# Health check
GET /health
```

## Response Formats

### Todo Object
```json
{
  "id": "abc123",
  "title": "Buy groceries",
  "description": "Get milk, eggs, bread",
  "status": "pending",
  "priority": "normal",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### List Response
```json
{
  "items": [...],
  "total": 42,
  "page": 1,
  "limit": 20,
  "pages": 3
}
```

### Error Response
```json
{
  "error": "not_found",
  "message": "Todo with id 'abc123' not found"
}
```

## Test Cases

| ID | Test | Description |
|----|------|-------------|
| TC01 | Create todo | 201 response, todo returned |
| TC02 | List todos | 200 with array |
| TC03 | Get todo | 200 with todo object |
| TC04 | Update todo | 200 with updated todo |
| TC05 | Delete todo | 204 no content |
| TC06 | Mark complete | Status changes to completed |
| TC07 | Filter status | Only matching returned |
| TC08 | Filter priority | Only matching returned |
| TC09 | Pagination | Correct page returned |
| TC10 | Not found | 404 for missing id |
| TC11 | Validation | 422 for invalid data |
| TC12 | Health check | 200 with status |

## Task Breakdown

1. Setup FastAPI/Flask project
2. Define data models
3. Implement CRUD endpoints
4. Add filtering
5. Add pagination
6. Add validation
7. Implement error handling
8. Add health check
9. Write unit tests
10. Write integration tests (with TestClient)
11. Create e2e test report

## Success Criteria

- All endpoints return correct status codes
- Validation rejects invalid data with 422
- Filtering works for status and priority
- Pagination returns correct slices
- Error responses are consistent
- Health endpoint returns 200
- Unit tests cover core logic
- Integration tests hit actual endpoints
