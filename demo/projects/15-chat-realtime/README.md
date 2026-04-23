# Demo Project 15: Chat Room (WebSockets)

**Type:** Real-time Web App
**Complexity:** High
**Purpose:** Test WebSockets, real-time updates, room management, presence

## Overview

A real-time chat application with rooms, typing indicators, and user presence.

## Features

- [ ] User registration/login (simple)
- [ ] Create/join chat rooms
- [ ] Send/receive messages in real-time
- [ ] Typing indicators
- [ ] Online user presence
- [ ] Message history (last 100)
- [ ] System messages (user joined/left)
- [ ] Unread message count
- [ ] WebSocket connection status
- [ ] Auto-reconnect on disconnect

## Architecture

```
┌─────────────┐     WebSocket     ┌─────────────┐
│   Client    │◀──────────────────▶│   Server    │
│  (Browser)  │                    │  (FastAPI)  │
└─────────────┘                    └──────┬──────┘
                                         │
                              ┌──────────┴──────────┐
                              │                     │
                         ┌────▼────┐          ┌────▼────┐
                         │  Redis   │          │   JWT   │
                         │  (Pub/   │          │  Auth   │
                         │  Sub)    │          │         │
                         └──────────┘          └─────────┘
```

## Tech Stack

- **Backend:** Python + FastAPI + WebSockets
- **Frontend:** Vanilla JS + HTML/CSS
- **Message Broker:** Redis (Pub/Sub)
- **Auth:** JWT tokens
- **Storage:** Redis (messages, presence)

## Data Model

### Room

```python
{
    "id": "room-uuid",
    "name": "General",
    "created_at": "ISO8601",
    "members": ["user1", "user2"]
}
```

### Message

```python
{
    "id": "msg-uuid",
    "room_id": "room-uuid",
    "user_id": "user-id",
    "username": "john",
    "content": "Hello!",
    "type": "message|system|typing",
    "timestamp": "ISO8601"
}
```

### Presence

```python
{
    "user_id": "user-id",
    "username": "john",
    "room_id": "room-uuid",
    "status": "online|away|offline",
    "last_seen": "ISO8601"
}
```

## API Endpoints

### REST (Authentication)

```bash
# Register
POST /api/auth/register
{"username": "john", "password": "secret"}

# Login
POST /api/auth/login
{"username": "john", "password": "secret"}
# Returns: {"access_token": "...", "token_type": "bearer"}

# Get rooms
GET /api/rooms

# Create room
POST /api/rooms
{"name": "General Chat"}

# Get room messages
GET /api/rooms/{room_id}/messages?limit=50

# Get room members
GET /api/rooms/{room_id}/members
```

### WebSocket

```javascript
// Connect
const ws = new WebSocket("ws://localhost:8000/ws/{room_id}?token={jwt}");

// Send message
ws.send(JSON.stringify({
  type: "message",
  content: "Hello!"
}));

// Send typing indicator
ws.send(JSON.stringify({
  type: "typing",
  is_typing: true
}));

// Receive messages
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  // {type: "message", data: {...}}
};
```

### WebSocket Message Types

```json
// Incoming (server -> client)
{"type": "message", "data": {"id": "...", "content": "...", "user": "..."}}
{"type": "typing", "data": {"user_id": "...", "username": "...", "is_typing": true}}
{"type": "presence", "data": {"user_id": "...", "status": "online"}}
{"type": "system", "data": {"content": "User joined"}}

// Outgoing (client -> server)
{"type": "message", "content": "Hello"}
{"type": "typing", "is_typing": true}
{"type": "leave"}
```

## File Structure

```
chat-realtime/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── auth.py
│   │   ├── models.py
│   │   ├── rooms.py
│   │   ├── messages.py
│   │   └── websocket.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html
│   ├── chat.js
│   └── style.css
├── docker-compose.yml
└── TEST_REPORT.md
```

## Test Cases

| ID | Test | Description |
|----|------|-------------|
| TC01 | User registration | User created, token returned |
| TC02 | User login | JWT token returned |
| TC03 | Create room | Room appears in list |
| TC04 | Join room | User can join via WS |
| TC05 | Send message | Message appears for others |
| TC06 | Receive message | Real-time delivery < 100ms |
| TC07 | Typing indicator | Shows when typing |
| TC08 | User presence | Online status shown |
| TC09 | User join/leave | System message shown |
| TC10 | Reconnect | Auto-reconnects on disconnect |
| TC11 | Auth required | WS rejected without token |
| TC12 | Message history | Last messages loaded |

## Task Breakdown

1. Setup FastAPI project
2. Implement JWT authentication
3. Create room CRUD endpoints
4. Implement WebSocket handler
5. Add Redis Pub/Sub for broadcasting
6. Create message storage
7. Implement presence tracking
8. Build frontend UI
9. Implement WebSocket client
10. Add typing indicators
11. Add reconnection logic
12. Write backend unit tests
13. Write WebSocket integration tests
14. Create e2e test report

## Success Criteria

- WebSocket connects with valid JWT
- Messages delivered in < 100ms
- Typing indicators show correctly
- Presence updates on join/leave
- Auto-reconnect works on disconnect
- Messages persist after reload
- Multiple users see same messages
- System messages appear on join/leave
