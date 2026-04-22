# pi-status

Unix socket server providing read-only access to pi agent state for external monitoring and integration.

## Socket Path

Default: `~/.pi/status.sock`

Configure via environment variable:
```bash
export PI_STATUS_SOCKET=/path/to/socket.sock
```

## API

Connect to the socket and send JSON messages. Each request returns a JSON response.

### Actions

| Action | Description |
|--------|-------------|
| `ping` | Connection check → `{"type":"pong"}` |
| `health` | Quick health snapshot |
| `status` / `get` | Full state |

### Examples

**Health check:**
```bash
echo '{"action":"health"}' | socat - UNIX-CONNECT:~/.pi/status.sock
```

**Full status:**
```bash
echo '{"action":"status"}' | socat - UNIX-CONNECT:~/.pi/status.sock
```

**Using node:**
```bash
node --input-type=module <<'EOF'
import { createConnection } from "node:net";
const s = createConnection("/~/.pi/status.sock");
s.write(JSON.stringify({action:"status"}) + "\n");
s.on("data", d => { console.log(JSON.stringify(JSON.parse(d), null, 2)); s.end(); });
EOF
```

## Response Shape

```json
{
  "type": "ok",
  "data": {
    "running": true,
    "idle": true,
    "sessionActive": true,
    "sessionFile": "/path/to/session.jsonl",
    "cwd": "/current/working/dir",
    "model": { "id": "claude-sonnet", "provider": "anthropic" },
    "currentTurn": { "index": 3, "startTime": 123, "durationMs": 5000 },
    "messageCount": 15,
    "userMessageCount": 5,
    "assistantMessageCount": 7,
    "toolResultCount": 3,
    "currentToolCalls": [{ "toolCallId": "abc", "toolName": "bash", "startTime": 123 }],
    "completedToolCalls": 12,
    "startedAt": 1234567890,
    "lastActivityAt": 1234567890
  }
}
```

## Install

```bash
ln -sf /path/to/pi-status ~/.pi/agent/extensions/pi-status
```

Or via just:
```bash
just pi-status-link
```
