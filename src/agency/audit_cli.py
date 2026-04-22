"""
Agency v2.0 - Audit CLI

Command-line interface for audit trail management.
"""

import argparse
import json
import sys
from pathlib import Path

from agency.audit import EVENT_AGENT, EVENT_CLI, EVENT_SESSION, EVENT_TASK, AuditStore


def handle_audit_command(args: argparse.Namespace, agency_dir: Path) -> int:
    """Handle audit subcommands."""
    store = AuditStore(agency_dir)

    if args.audit_command == "list":
        return cmd_list(store, args)
    elif args.audit_command == "stats":
        return cmd_stats(store, args)
    elif args.audit_command == "export":
        return cmd_export(store, args)
    elif args.audit_command == "clear":
        return cmd_clear(store, args)
    else:
        print(
            "Usage: agency audit <list|stats|export|clear>",
            file=sys.stderr,
        )
        return 1


def cmd_list(store: AuditStore, args: argparse.Namespace) -> int:
    """List audit events."""
    events = store.query(
        event_type=args.type,
        action=args.action,
        task_id=args.task,
        since=args.since,
        until=args.until,
        limit=args.limit,
    )

    if not events:
        print("No audit events found")
        return 0

    type_icon = {
        EVENT_CLI: "⌨️",
        EVENT_TASK: "📋",
        EVENT_SESSION: "🖥️",
        EVENT_AGENT: "🤖",
    }

    for event in events:
        icon = type_icon.get(event.event_type, "?")
        ts = event.timestamp or "unknown"
        user = event.os_user or "unknown"
        session = event.agency_session or "-"

        print(f"{icon} [{ts}] {event.event_type}/{event.action}")
        print(f"   user={user} session={session}")

        if event.cli_command:
            print(f"   cli={event.cli_command}")

        if event.task_id:
            print(f"   task={event.task_id}")

        if event.details:
            # Pretty print details
            details_str = json.dumps(event.details, indent=None)
            if len(details_str) <= 100:
                print(f"   details={details_str}")
            else:
                print(f"   details={details_str[:100]}...")

        print()

    return 0


def cmd_stats(store: AuditStore, args: argparse.Namespace) -> int:
    """Show audit statistics."""
    stats = store.stats()

    print("# Audit Statistics")
    print()
    print(f"- **Total events**: {stats['total_events']}")
    print(f"- **Last 24 hours**: {stats['last_24h']}")
    print(f"- **First event**: {stats['first_event'] or 'none'}")
    print(f"- **Last event**: {stats['last_event'] or 'none'}")
    print()

    if stats["by_event_type"]:
        print("## By Event Type")
        print()
        for etype, count in stats["by_event_type"].items():
            print(f"- {etype}: {count}")
        print()

    if stats["by_action"]:
        print("## By Action")
        print()
        for action, count in stats["by_action"].items():
            print(f"- {action}: {count}")
        print()

    return 0


def cmd_export(store: AuditStore, args: argparse.Namespace) -> int:
    """Export audit events."""
    output = store.export(
        format=args.format,
        since=args.since,
        until=args.until,
    )

    if args.output:
        Path(args.output).write_text(output)
        print(f"[INFO] Exported to {args.output}")
    else:
        print(output)

    return 0


def cmd_clear(store: AuditStore, args: argparse.Namespace) -> int:
    """Clear old audit events."""
    if not args.force:
        # Preview what would be deleted
        if args.before:
            events = store.query(until=args.before, limit=100000)
        else:
            events = store.query(
                until="datetime('now', '-30 days')",
                limit=100000,
            )

        print(f"[INFO] Would delete {len(events)} events")
        print("[INFO] Use --force to confirm")
        return 0

    deleted = store.clear(before=args.before)
    print(f"[INFO] Deleted {deleted} events")
    return 0
