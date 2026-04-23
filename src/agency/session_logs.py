"""Parse and analyze pi session logs (JSONL format).

Usage:
    agency logs list                    # List session log files
    agency logs show <session>          # Show session messages
    agency logs search <pattern>        # Search for pattern
    agency logs errors                  # Show errors only
    agency logs timeline                # Show event timeline
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import click


def find_session_logs(agency_dir: Path) -> list[Path]:
    """Find all pi session log files.

    Args:
        agency_dir: Can be the project root or .agency/ directory.
                    Function will find .agency/ if not given directly.
    """
    # Normalize to .agency directory if not already
    if agency_dir.name == ".agency" and agency_dir.is_dir():
        agency_path = agency_dir
    else:
        # Look for .agency in or below the given path
        agency_path = agency_dir / ".agency"
        if not agency_path.is_dir():
            # Try walking up
            current = agency_dir.absolute()
            while current != current.parent:
                candidate = current / ".agency"
                if candidate.is_dir():
                    agency_path = candidate
                    break
                current = current.parent
            else:
                return []

    sessions_dir = agency_path / "pi" / "sessions"
    if not sessions_dir.exists():
        return []

    logs = []
    for member_dir in sessions_dir.iterdir():
        if member_dir.is_dir():
            for log_file in member_dir.glob("*.jsonl"):
                logs.append(log_file)
    return sorted(logs)


def parse_jsonl(file_path: Path) -> list[dict[str, Any]]:
    """Parse a JSONL file into list of dicts."""
    events = []
    for line in file_path.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return events


def format_timestamp(ts: str) -> str:
    """Format ISO timestamp to readable format."""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%H:%M:%S")
    except (ValueError, AttributeError):
        return ts


def extract_text_content(content: list[dict]) -> str:
    """Extract text from message content array."""
    texts = []
    for item in content:
        if isinstance(item, dict):
            if item.get("type") == "text":
                texts.append(item.get("text", ""))
            elif item.get("type") == "tool_use":
                texts.append(f"[TOOL: {item.get('name', 'unknown')}]")
            elif item.get("type") == "tool_result":
                # Truncate tool results
                result = item.get("content", "")
                if len(result) > 200:
                    result = result[:200] + "..."
                texts.append(f"[RESULT: {result}]")
    return " ".join(texts)


@click.group("logs")
def logs_cmd():
    """Session log analysis."""
    pass


@logs_cmd.command("list")
@click.option("--agency-dir", "-d", type=click.Path(exists=True, file_okay=False), default=".")
def list_logs(agency_dir: str):
    """List available session log files."""
    agency_path = Path(agency_dir)
    logs = find_session_logs(agency_path)

    if not logs:
        click.echo("No session logs found")
        return

    click.echo(f"Found {len(logs)} session log file(s):\n")
    for log in logs:
        # Extract agent name from path
        parts = log.relative_to(agency_path).parts
        agent = parts[-2] if len(parts) >= 2 else "unknown"

        # Count events
        events = parse_jsonl(log)
        msg_count = sum(1 for e in events if e.get("type") == "message")

        # Get timestamps
        timestamps = [e.get("timestamp", "") for e in events if e.get("timestamp")]
        start = format_timestamp(timestamps[0]) if timestamps else "?"
        end = format_timestamp(timestamps[-1]) if timestamps else "?"

        click.echo(f"  [{agent}] {log.name}")
        click.echo(f"         {len(events)} events, {msg_count} messages | {start} - {end}")


@logs_cmd.command("show")
@click.argument("session", required=False)
@click.option("--agency-dir", "-d", type=click.Path(exists=True, file_okay=False), default=".")
@click.option("--role", "-r", type=click.Choice(["user", "assistant", "all"]), default="all")
@click.option("--limit", "-l", type=int, default=50, help="Max messages to show")
def show_log(session: str | None, agency_dir: str, role: str, limit: int):
    """Show session log messages.

    SESSION can be a full path, filename, or partial match.
    """
    agency_path = Path(agency_dir)
    logs = find_session_logs(agency_path)

    if not logs:
        click.echo("No session logs found", err=True)
        return

    # Filter by session if provided
    if session:
        logs = [log for log in logs if session in str(log)]
        if not logs:
            click.echo(f"No logs matching: {session}", err=True)
            return

    for log in logs:
        parts = log.relative_to(agency_path).parts
        agent = parts[-2] if len(parts) >= 2 else "unknown"

        click.echo(f"\n=== Session: {log.name} [{agent}] ===\n")

        events = parse_jsonl(log)
        messages = [e for e in events if e.get("type") == "message"]

        shown = 0
        for msg in messages[-limit:]:
            msg_role = msg.get("message", {}).get("role", "?")
            if role != "all" and msg_role != role:
                continue

            ts = format_timestamp(msg.get("timestamp", ""))
            content = msg.get("message", {}).get("content", [])
            text = extract_text_content(content)

            prefix = "👤" if msg_role == "user" else "🤖" if msg_role == "assistant" else "🔧"
            click.echo(f"[{ts}] {prefix} {msg_role.upper()}")

            # Word wrap text
            for line in text.split("\n"):
                for i in range(0, len(line), 100):
                    click.echo(f"    {line[i:i+100]}")
            click.echo("")

            shown += 1

        if shown == 0:
            click.echo("    (no messages)")


@logs_cmd.command("search")
@click.argument("pattern")
@click.option("--agency-dir", "-d", type=click.Path(exists=True, file_okay=False), default=".")
@click.option("--context", "-c", type=int, default=2, help="Lines of context")
def search_logs(pattern: str, agency_dir: str, context: int):
    """Search for pattern in session logs."""
    agency_path = Path(agency_dir)
    logs = find_session_logs(agency_path)

    if not logs:
        click.echo("No session logs found", err=True)
        return

    found = False
    for log in logs:
        parts = log.relative_to(agency_path).parts
        agent = parts[-2] if len(parts) >= 2 else "unknown"

        events = parse_jsonl(log)
        messages = [e for e in events if e.get("type") == "message"]

        for i, msg in enumerate(messages):
            content = msg.get("message", {}).get("content", [])
            text = extract_text_content(content).lower()

            if pattern.lower() in text:
                found = True
                ts = format_timestamp(msg.get("timestamp", ""))
                msg_role = msg.get("message", {}).get("role", "?")

                click.echo(f"[{log.name}] [{agent}] [{ts}] {msg_role.upper()}")

                # Show context before
                for j in range(max(0, i - context), i):
                    ctx_text = extract_text_content(messages[j].get("message", {}).get("content", []))
                    ctx_ts = format_timestamp(messages[j].get("timestamp", ""))
                    ctx_role = messages[j].get("message", {}).get("role", "?")[:3]
                    click.echo(f"  {ctx_ts} {ctx_role}: {ctx_text[:150]}...")

                # Show match
                click.echo(f"  --> MATCH: {text[:200]}")

                # Show context after
                for j in range(i + 1, min(len(messages), i + context + 1)):
                    ctx_text = extract_text_content(messages[j].get("message", {}).get("content", []))
                    ctx_ts = format_timestamp(messages[j].get("timestamp", ""))
                    ctx_role = messages[j].get("message", {}).get("role", "?")[:3]
                    click.echo(f"  {ctx_ts} {ctx_role}: {ctx_text[:150]}...")
                click.echo("---")

    if not found:
        click.echo(f"Pattern '{pattern}' not found in any logs")


@logs_cmd.command("errors")
@click.option("--agency-dir", "-d", type=click.Path(exists=True, file_okay=False), default=".")
def show_errors(agency_dir: str):
    """Show errors and exceptions from session logs."""
    agency_path = Path(agency_dir)
    logs = find_session_logs(agency_path)

    if not logs:
        click.echo("No session logs found", err=True)
        return

    found = False
    for log in logs:
        parts = log.relative_to(agency_path).parts
        agent = parts[-2] if len(parts) >= 2 else "unknown"

        events = parse_jsonl(log)

        for event in events:
            if event.get("type") == "error" or event.get("type") == "exception":
                found = True
                ts = format_timestamp(event.get("timestamp", ""))
                error_type = event.get("error_type", "Error")
                message = event.get("message", str(event))

                click.echo(f"[{log.name}] [{agent}] [{ts}] {error_type}:")
                click.echo(f"  {message[:200]}")
                click.echo("---")

    if not found:
        click.echo("No errors found in logs")


@logs_cmd.command("timeline")
@click.argument("session", required=False)
@click.option("--agency-dir", "-d", type=click.Path(exists=True, file_okay=False), default=".")
def show_timeline(session: str | None, agency_dir: str):
    """Show event timeline for a session."""
    agency_path = Path(agency_dir)
    logs = find_session_logs(agency_path)

    if not logs:
        click.echo("No session logs found", err=True)
        return

    # Filter by session if provided
    if session:
        logs = [log for log in logs if session in str(log)]
        if not logs:
            click.echo(f"No logs matching: {session}", err=True)
            return

    for log in logs:
        parts = log.relative_to(agency_path).parts
        agent = parts[-2] if len(parts) >= 2 else "unknown"

        click.echo(f"\n=== Timeline: {log.name} [{agent}] ===\n")

        events = parse_jsonl(log)

        type_counts: dict[str, int] = {}
        for event in events:
            event_type = event.get("type", "unknown")
            type_counts[event_type] = type_counts.get(event_type, 0) + 1

        click.echo("Event types:")
        for t, count in sorted(type_counts.items()):
            click.echo(f"  {t}: {count}")

        click.echo("\nChronological events:")
        for event in events:
            ts = format_timestamp(event.get("timestamp", ""))
            event_type = event.get("type", "?")

            if event_type == "message":
                msg_role = event.get("message", {}).get("role", "?")[:3]
                content = event.get("message", {}).get("content", [])
                text = extract_text_content(content)[:60]
                click.echo(f"  {ts} {event_type:12} {msg_role}: {text}...")

            elif event_type == "tool_call":
                tool_name = event.get("tool_name", "?")
                click.echo(f"  {ts} {event_type:12} {tool_name}")

            elif event_type == "tool_result":
                click.echo(f"  {ts} {event_type:12} (result)")

            elif event_type == "model_change":
                provider = event.get("provider", "?")
                model = event.get("modelId", "?")
                click.echo(f"  {ts} {event_type:12} {provider}/{model}")

            else:
                click.echo(f"  {ts} {event_type:12}")
