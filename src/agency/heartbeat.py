#!/usr/bin/env python3
"""
Agency v2.0 - Heartbeat

Background process that monitors tasks and notifies the manager or agent.
Can be run standalone or as a CLI command.

Role-based behavior:
- MANAGER: Notifies about unassigned tasks when agents have capacity
- AGENT: Notifies about ONE task at a time - the agent picks one and works on it
"""

import json
import os
import sys
import time
from pathlib import Path

import yaml


# Lazy audit store
_audit_store = None


def _get_audit_store(agency_dir: Path):
    """Get audit store lazily."""
    global _audit_store
    if _audit_store is None:
        try:
            from agency.audit import AuditStore
            _audit_store = AuditStore(agency_dir)
        except Exception:
            _audit_store = False
    return _audit_store if _audit_store else None


def get_all_tasks(agency_dir: Path) -> list[dict]:
    """Get all tasks as a list."""
    tasks_json = agency_dir / "tasks.json"
    tasks = []

    if tasks_json.exists():
        try:
            data = json.loads(tasks_json.read_text())
            tasks_data = data.get("tasks", {})

            if isinstance(tasks_data, dict):
                tasks_items = tasks_data.values()
            else:
                tasks_items = tasks_data

            for task in tasks_items:
                if isinstance(task, dict):
                    tasks.append(task)
        except (json.JSONDecodeError, OSError):
            pass

    return tasks


def get_task_count(agency_dir: Path) -> dict:
    """Get task counts by status."""
    counts = {
        "pending": 0,
        "in_progress": 0,
        "unassigned": 0,
        "pending_approval": 0,
    }

    for task in get_all_tasks(agency_dir):
        status = task.get("status", "")
        assigned = task.get("assigned_to")
        if status == "pending":
            counts["pending"] += 1
            if not assigned:
                counts["unassigned"] += 1
        elif status == "in_progress":
            counts["in_progress"] += 1
        elif status == "pending_approval":
            counts["pending_approval"] += 1

    return counts

def get_active_task_count(agency_dir: Path) -> int:
    """Get count of active tasks (pending + in_progress)."""
    counts = get_task_count(agency_dir)
    return counts["pending"] + counts["in_progress"]


def get_agent_workload(agency_dir: Path) -> dict[str, int]:
    """Get workload per agent (count of pending + in_progress tasks)."""
    workload = {}

    for task in get_all_tasks(agency_dir):
        status = task.get("status", "")
        if status in ("pending", "in_progress"):
            agent = task.get("assigned_to")
            if agent:
                workload[agent] = workload.get(agent, 0) + 1

    return workload


def get_available_agents(agency_dir: Path, chunk_size: int = 1) -> list[str]:
    """Get list of agents that have capacity for more work."""
    agents_yaml = agency_dir / "agents.yaml"
    agents = []

    if agents_yaml.exists():
        try:
            data = yaml.safe_load(agents_yaml.read_text()) or {}
            for agent_data in data.get("agents", []):
                agents.append(agent_data.get("name", ""))
        except Exception:
            pass

    workload = get_agent_workload(agency_dir)

    available = []
    for agent in agents:
        current_load = workload.get(agent, 0)
        if current_load < chunk_size:
            available.append(agent)

    return available


def get_agent_tasks(agency_dir: Path, agent_name: str) -> list[dict]:
    """Get tasks assigned to a specific agent."""
    return [t for t in get_all_tasks(agency_dir) if t.get("assigned_to") == agent_name]


def write_notification(agency_dir: Path, role: str, agent_name: str, message: str):
    """Write notification to files that pi can read."""
    import json

    notifications_file = agency_dir / "notifications.json"

    # Load existing notifications
    notifications = []
    if notifications_file.exists():
        try:
            notifications = json.loads(notifications_file.read_text())
        except json.JSONDecodeError:
            notifications = []

    # Add new notification
    notification = {
        "role": role,
        "agent": agent_name,
        "message": message,
        "timestamp": time.time(),
    }
    notifications.append(notification)

    # Keep only last 10 notifications
    notifications = notifications[-10:]

    # Write to notifications file
    notifications_file.write_text(json.dumps(notifications, indent=2))

    # Also write to a system prompt file that can be loaded
    system_hint_file = agency_dir / "system_hint.txt"
    system_hint_file.write_text(f"\n## NEW NOTIFICATION\n{message}\n")


def send_notification(window_ref: str, message: str) -> bool:
    """Send a notification via pi-inject Unix socket."""
    agency_dir = os.environ.get("AGENCY_DIR", "")
    role = os.environ.get("AGENCY_ROLE", "")
    agent_name = os.environ.get("AGENCY_AGENT", os.environ.get("AGENCY_MANAGER", ""))

    # Write to notifications file for debugging
    if agency_dir:
        write_notification(Path(agency_dir), role, agent_name, message)

    # Get socket path from env (defaults to PI_INJECTOR_SOCKET or ~/.pi/injector.sock)
    socket_path = os.environ.get("PI_INJECTOR_SOCKET")

    # Import here to avoid circular imports and use module directly
    import sys

    sys.path.insert(0, str(Path(__file__).parent))
    from pi_inject import get_client

    try:
        client = get_client(socket_path)

        # Extract command from message if it's a task notification
        cmd = "agency tasks list"
        if "New task:" in message:
            # Extract task ID
            parts = message.split()
            for part in parts:
                if "-" in part and len(part) > 5:  # Likely a task ID
                    cmd = f"agency tasks show {part}"
                    break

        # Send as steer message
        resp = client.steer(cmd)

        if resp.is_ok:
            print(f"[HEARTBEAT] Injected: {cmd}")
            return True
        else:
            print(f"[HEARTBEAT] Inject error: {resp.message}")
            return False

    except Exception as e:
        print(f"[HEARTBEAT] pi-inject error: {e}")
        return False


def manager_heartbeat(
    agency_dir: Path,
    socket_name: str,
    manager_name: str,
    poll_interval: int,
    chunk_size: int = 1,
    parallel_limit: int | None = None,
):
    """Heartbeat loop for manager.
    
    Args:
        agency_dir: Path to .agency/ directory
        socket_name: Tmux socket name
        manager_name: Name of the manager window
        poll_interval: Seconds between checks
        chunk_size: Max tasks per agent (per-agent limit)
        parallel_limit: Max total parallel tasks (None = unlimited)
    """
    window_ref = f"{socket_name}:[MGR] {manager_name}"

    print(f"[HEARTBEAT] Starting heartbeat for manager '{manager_name}'")
    print(f"[HEARTBEAT] Agency dir: {agency_dir}")
    print(f"[HEARTBEAT] Poll interval: {poll_interval}s, chunk: {chunk_size}, parallel_limit: {parallel_limit}")

    last_unassigned = 0
    last_approval = 0
    last_notification_time = 0

    while True:
        try:
            counts = get_task_count(agency_dir)
            active_count = counts["pending"] + counts["in_progress"]
            available_agents = get_available_agents(agency_dir, chunk_size)
            current_time = time.time()

            # Check parallel limit
            at_parallel_limit = parallel_limit is not None and active_count >= parallel_limit

            print(
                f"[HEARTBEAT] Active: {active_count}/{parallel_limit or '∞'}, "
                f"{counts['unassigned']} unassigned, "
                f"{len(available_agents)} agents available: {available_agents}"
            )

            # Always notify about unassigned tasks, but warn about parallel limit
            if counts["unassigned"] > 0 and available_agents:
                should_notify = counts["unassigned"] != last_unassigned and (current_time - last_notification_time) > 30
                if should_notify:
                    agent_list = ", ".join(available_agents)
                    
                    # Add parallel limit warning if at limit
                    parallel_warning = ""
                    if at_parallel_limit:
                        parallel_warning = f" ⚠️ **Note**: Only {parallel_limit} task(s) will be actively worked on in priority order."
                    
                    msg = (
                        f"📋 {counts['unassigned']} unassigned task(s), "
                        f"{len(available_agents)} agent(s) available ({agent_list}). "
                        f"Run 'agency tasks list' to review and assign.{parallel_warning}"
                    )
                    if send_notification(window_ref, msg):
                        print(f"[HEARTBEAT] Notified manager: {msg}")
                        last_unassigned = counts["unassigned"]
                        last_notification_time = current_time

                        # Audit log
                        audit = _get_audit_store(agency_dir)
                        if audit:
                            audit.log_agent(
                                action="heartbeat",
                                agency_role="manager",
                                details={
                                    "notification": "unassigned_tasks",
                                    "unassigned": counts["unassigned"],
                                    "available_agents": available_agents,
                                    "at_parallel_limit": at_parallel_limit,
                                },
                            )

            if counts["pending_approval"] > 0 and counts["pending_approval"] != last_approval:
                msg = (
                    f"👀 {counts['pending_approval']} task(s) pending your approval - run 'agency tasks list' to review"
                )
                if send_notification(window_ref, msg):
                    print(f"[HEARTBEAT] Notified manager: {msg}")
                    last_approval = counts["pending_approval"]

                    # Audit log
                    audit = _get_audit_store(agency_dir)
                    if audit:
                        audit.log_agent(
                            action="heartbeat",
                            agency_role="manager",
                            details={
                                "notification": "pending_approval",
                                "pending_count": counts["pending_approval"],
                            },
                        )

            time.sleep(poll_interval)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[HEARTBEAT] Error: {e}", file=sys.stderr)
            time.sleep(poll_interval)


def agent_heartbeat(agency_dir: Path, socket_name: str, agent_name: str, poll_interval: int = 30, ping_interval: int = 120):
    """Heartbeat loop for agent.

    Notifies agents about new tasks and periodically pings idle agents
    to keep them working. Pings only sent when tmux pane is idle.

    Args:
        agency_dir: Path to .agency/ directory
        socket_name: Tmux socket name
        agent_name: Name of the agent
        poll_interval: Seconds between checks
        ping_interval: Seconds between idle pings (default: 2 minutes)
    """
    from agency.session import SessionManager

    window_ref = f"{socket_name}:{agent_name}"

    print(f"[HEARTBEAT] Starting heartbeat for agent '{agent_name}'")
    print(f"[HEARTBEAT] Agency dir: {agency_dir}")
    print(f"[HEARTBEAT] Poll interval: {poll_interval}s, ping interval: {ping_interval}s")

    last_ping_time = 0  # Track when we last sent a ping
    sm = SessionManager(session_name, socket_name, socket_name=socket_name)

    while True:
        try:
            tasks = get_agent_tasks(agency_dir, agent_name)
            pending_tasks = [t for t in tasks if t.get("status") == "pending"]
            in_progress_tasks = [t for t in tasks if t.get("status") == "in_progress"]
            current_time = time.time()

            # Check if pane is idle (at least 2 minutes since last change)
            pane_is_idle = sm.is_window_idle(agent_name, idle_seconds=120)

            # If agent has task in progress, check if it needs attention
            if in_progress_tasks:
                task = in_progress_tasks[0]
                task_id = task.get("task_id")
                # Ping every ping_interval ONLY if pane is idle
                if pane_is_idle and current_time - last_ping_time >= ping_interval:
                    msg = f"💡 Still working on {task_id}? Update status or complete the task."
                    if send_notification(window_ref, msg):
                        print(f"[HEARTBEAT] Pinged idle agent about task: {task_id}")
                        last_ping_time = current_time

            # If we have pending tasks, notify agent (only if idle)
            elif pending_tasks and pane_is_idle:
                next_task = pending_tasks[0]
                task_id = next_task.get("task_id")
                desc = next_task.get("description", "")[:50]

                msg = f"📌 Task ready: {task_id} - {desc}... Run 'agency tasks show {task_id}' to start"
                if send_notification(window_ref, msg):
                    print(f"[HEARTBEAT] Notified idle agent about: {task_id}")
                    last_ping_time = current_time

                    # Audit log
                    audit = _get_audit_store(agency_dir)
                    if audit:
                        audit.log_agent(
                            action="heartbeat",
                            agency_role="agent",
                            details={
                                "notification": "new_task",
                                "task_id": task_id,
                            },
                        )

            # Periodic ping even with no tasks (keep agent engaged) - only if idle
            elif pane_is_idle and current_time - last_ping_time >= ping_interval * 2:
                msg = "🏃 No tasks assigned. Check 'agency tasks list' or wait for new assignments."
                if send_notification(window_ref, msg):
                    print(f"[HEARTBEAT] Pinged idle agent")
                    last_ping_time = current_time

            time.sleep(poll_interval)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[HEARTBEAT] Error: {e}", file=sys.stderr)
            time.sleep(poll_interval)


def run_heartbeat():
    """Run heartbeat based on environment variables."""
    agency_dir = Path(os.environ.get("AGENCY_DIR", ""))
    socket_name = os.environ.get("AGENCY_SOCKET", "")
    role = os.environ.get("AGENCY_ROLE", "").upper()
    poll_interval = int(os.environ.get("AGENCY_POLL_INTERVAL", "30"))
    chunk_size = int(os.environ.get("AGENCY_CHUNK_SIZE", "1"))
    parallel_limit_env = os.environ.get("AGENCY_PARALLEL_LIMIT", "")
    parallel_limit = int(parallel_limit_env) if parallel_limit_env else None

    if not role:
        print("[HEARTBEAT] Error: AGENCY_ROLE must be set (MANAGER or AGENT)")
        print("[HEARTBEAT] Usage: Run via agency launch scripts, not directly")
        sys.exit(1)

    if role == "MANAGER":
        manager_name = os.environ.get("AGENCY_MANAGER", "coordinator")
        manager_heartbeat(agency_dir, socket_name, manager_name, poll_interval, chunk_size, parallel_limit)
    elif role == "AGENT":
        agent_name = os.environ.get("AGENCY_AGENT", "")
        if not agent_name:
            print("[HEARTBEAT] Error: AGENCY_AGENT must be set when role is AGENT")
            sys.exit(1)
        ping_interval = int(os.environ.get("AGENCY_PING_INTERVAL", "120"))
        agent_heartbeat(agency_dir, socket_name, agent_name, poll_interval, ping_interval)
    else:
        print(f"[HEARTBEAT] Error: Unknown role '{role}'. Must be MANAGER or AGENT")
        sys.exit(1)


def main():
    run_heartbeat()


if __name__ == "__main__":
    main()
