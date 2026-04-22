"""
Agency v2.0 - Audit Trail

SQLite-based audit logging for all agency operations.
"""

import json
import os
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Constants
AUDIT_FILE = "var/audit.db"
SCHEMA_VERSION = 1

# Event types
EVENT_CLI = "cli"
EVENT_TASK = "task"
EVENT_SESSION = "session"
EVENT_AGENT = "agent"

# Actions
ACTION_CREATE = "create"
ACTION_START = "start"
ACTION_STOP = "stop"
ACTION_ASSIGN = "assign"
ACTION_UPDATE = "update"
ACTION_COMPLETE = "complete"
ACTION_APPROVE = "approve"
ACTION_REJECT = "reject"
ACTION_DELETE = "delete"
ACTION_ATTACH = "attach"
ACTION_DETACH = "detach"
ACTION_HALT = "halt"
ACTION_RESUME = "resume"
ACTION_HEARTBEAT = "heartbeat"


@dataclass
class AuditEvent:
    """Represents an audit event."""

    event_type: str
    action: str
    os_user: str | None = None
    agency_session: str | None = None
    agency_role: str | None = None
    cli_command: str | None = None
    cli_args: dict | None = None
    cwd: str | None = None
    task_id: str | None = None
    details: dict | None = None
    timestamp: str | None = None
    id: int | None = None

    def to_dict(self) -> dict:
        """Convert to dict for SQLite insertion."""
        return {
            "event_type": self.event_type,
            "action": self.action,
            "os_user": self.os_user,
            "agency_session": self.agency_session,
            "agency_role": self.agency_role,
            "cli_command": self.cli_command,
            "cli_args": json.dumps(self.cli_args) if self.cli_args else None,
            "cwd": self.cwd,
            "task_id": self.task_id,
            "details": json.dumps(self.details) if self.details else None,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_row(cls, row: tuple) -> "AuditEvent":
        """Create from SQLite row."""
        return cls(
            id=row[0],
            timestamp=row[1],
            event_type=row[2],
            action=row[3],
            os_user=row[4],
            agency_session=row[5],
            agency_role=row[6],
            cli_command=row[7],
            cli_args=json.loads(row[8]) if row[8] else None,
            cwd=row[9],
            task_id=row[10],
            details=json.loads(row[11]) if row[11] else None,
        )


class AuditStore:
    """Manages audit trail with SQLite backend."""

    def __init__(self, agency_dir: Path):
        self.agency_dir = agency_dir
        self.db_path = agency_dir / AUDIT_FILE
        self._conn: sqlite3.Connection | None = None
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database and run migrations."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = self._get_conn()
        cursor = conn.cursor()

        # Create events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                event_type TEXT NOT NULL,
                action TEXT NOT NULL,
                os_user TEXT,
                agency_session TEXT,
                agency_role TEXT,
                cli_command TEXT,
                cli_args TEXT,
                cwd TEXT,
                task_id TEXT,
                details TEXT
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_task ON events(task_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_session ON events(agency_session)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_action ON events(action)")

        # Create metadata table for schema version
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Set schema version if not exists
        cursor.execute(
            "INSERT OR IGNORE INTO meta (key, value) VALUES ('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )

        conn.commit()

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create database connection with WAL mode."""
        if self._conn is None:
            self._conn = sqlite3.connect(
                str(self.db_path),
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            )
            self._conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")

        return self._conn

    @contextmanager
    def _transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for transactions."""
        conn = self._get_conn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def log(
        self,
        event_type: str,
        action: str,
        os_user: str | None = None,
        agency_session: str | None = None,
        agency_role: str | None = None,
        cli_command: str | None = None,
        cli_args: dict | None = None,
        cwd: str | None = None,
        task_id: str | None = None,
        details: dict | None = None,
    ) -> int:
        """Log an audit event. Returns the event ID."""
        event = AuditEvent(
            event_type=event_type,
            action=action,
            os_user=os_user or self._get_os_user(),
            agency_session=agency_session or self._get_session(),
            agency_role=agency_role,
            cli_command=cli_command,
            cli_args=cli_args,
            cwd=cwd,
            task_id=task_id,
            details=details,
        )

        with self._transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO events (
                    event_type, action, os_user, agency_session, agency_role,
                    cli_command, cli_args, cwd, task_id, details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_type,
                    event.action,
                    event.os_user,
                    event.agency_session,
                    event.agency_role,
                    event.cli_command,
                    json.dumps(event.cli_args) if event.cli_args else None,
                    event.cwd,
                    event.task_id,
                    json.dumps(event.details) if event.details else None,
                ),
            )
            return cursor.lastrowid or 0

    def log_cli(
        self,
        command: str,
        args: dict | None = None,
        cwd: str | None = None,
    ) -> int:
        """Log a CLI command invocation."""
        return self.log(
            event_type=EVENT_CLI,
            action=command,
            cli_command=command,
            cli_args=args,
            cwd=cwd or os.getcwd(),
        )

    def log_task(
        self,
        action: str,
        task_id: str,
        details: dict | None = None,
    ) -> int:
        """Log a task event."""
        return self.log(
            event_type=EVENT_TASK,
            action=action,
            task_id=task_id,
            details=details,
        )

    def log_session(
        self,
        action: str,
        details: dict | None = None,
    ) -> int:
        """Log a session event."""
        return self.log(
            event_type=EVENT_SESSION,
            action=action,
            details=details,
        )

    def log_agent(
        self,
        action: str,
        agency_role: str,
        details: dict | None = None,
    ) -> int:
        """Log an agent event."""
        return self.log(
            event_type=EVENT_AGENT,
            action=action,
            agency_role=agency_role,
            details=details,
        )

    def _get_os_user(self) -> str | None:
        """Get current OS user."""
        try:
            return os.getlogin()
        except OSError:
            return os.environ.get("USER") or os.environ.get("USERNAME")

    def _get_session(self) -> str | None:
        """Get current agency session from environment."""
        return os.environ.get("AGENCY_PROJECT")

    def query(
        self,
        event_type: str | None = None,
        action: str | None = None,
        task_id: str | None = None,
        session: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEvent]:
        """Query audit events with filters."""
        conn = self._get_conn()
        cursor = conn.cursor()

        conditions = []
        params: list[Any] = []

        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)

        if action:
            conditions.append("action = ?")
            params.append(action)

        if task_id:
            conditions.append("task_id = ?")
            params.append(task_id)

        if session:
            conditions.append("agency_session = ?")
            params.append(session)

        if since:
            conditions.append("timestamp >= ?")
            params.append(since)

        if until:
            conditions.append("timestamp <= ?")
            params.append(until)

        where = " AND ".join(conditions) if conditions else "1=1"
        query = f"""
            SELECT * FROM events
            WHERE {where}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        cursor.execute(query, params)
        return [AuditEvent.from_row(tuple(row)) for row in cursor.fetchall()]

    def stats(self) -> dict[str, Any]:
        """Get audit statistics."""
        conn = self._get_conn()
        cursor = conn.cursor()

        # Total events
        cursor.execute("SELECT COUNT(*) FROM events")
        total = cursor.fetchone()[0]

        # By event type
        cursor.execute("SELECT event_type, COUNT(*) FROM events GROUP BY event_type")
        by_type = dict(cursor.fetchall())

        # By action
        cursor.execute("SELECT action, COUNT(*) FROM events GROUP BY action")
        by_action = dict(cursor.fetchall())

        # Recent activity (last 24h)
        cursor.execute(
            """
            SELECT COUNT(*) FROM events
            WHERE timestamp >= datetime('now', '-1 day')
            """
        )
        last_24h = cursor.fetchone()[0]

        # First and last event
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM events")
        row = cursor.fetchone()
        first_event = row[0]
        last_event = row[1]

        return {
            "total_events": total,
            "by_event_type": by_type,
            "by_action": by_action,
            "last_24h": last_24h,
            "first_event": first_event,
            "last_event": last_event,
        }

    def export(
        self,
        format: str = "json",
        since: str | None = None,
        until: str | None = None,
    ) -> str:
        """Export audit events to JSON or CSV."""
        events = self.query(since=since, until=until, limit=100000)

        if format == "csv":
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow(
                [
                    "id",
                    "timestamp",
                    "event_type",
                    "action",
                    "os_user",
                    "agency_session",
                    "agency_role",
                    "cli_command",
                    "cli_args",
                    "cwd",
                    "task_id",
                    "details",
                ]
            )

            for event in events:
                writer.writerow(
                    [
                        event.id,
                        event.timestamp,
                        event.event_type,
                        event.action,
                        event.os_user,
                        event.agency_session,
                        event.agency_role,
                        event.cli_command,
                        json.dumps(event.cli_args) if event.cli_args else "",
                        event.cwd,
                        event.task_id,
                        json.dumps(event.details) if event.details else "",
                    ]
                )

            return output.getvalue()

        else:  # json
            return json.dumps(
                [e.to_dict() for e in events],
                indent=2,
                default=str,
            )

    def clear(self, before: str | None = None) -> int:
        """Clear old events. Returns count of deleted events."""
        if before is None:
            # Default: keep last 30 days
            before = "datetime('now', '-30 days')"
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM events WHERE timestamp < {before}")
            deleted = cursor.rowcount
            conn.commit()
            return deleted
        else:
            with self._transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM events WHERE timestamp < ?",
                    (before,),
                )
                return cursor.rowcount
