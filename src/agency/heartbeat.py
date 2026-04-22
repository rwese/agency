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
        "unassigned": 0,
        "pending_approval": 0,
    }

    for task in get_all_tasks(agency_dir):
        status = task.get("status", "")
        assigned = task.get("assigned_to")
        if status == "pending" or status == "in_progress":
            counts["pending"] += 1
            if not assigned:
                counts["unassigned"] += 1
        elif status == "pending_approval":
            counts["pending_approval"] += 1

    return counts


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


def manager_heartbeat(agency_dir: Path, socket_name: str, manager_name: str, poll_interval: int, chunk_size: int = 1):
    """Heartbeat loop for manager."""
    window_ref = f"{socket_name}:[MGR] {manager_name}"

    print(f"[HEARTBEAT] Starting heartbeat for manager '{manager_name}'")
    print(f"[HEARTBEAT] Agency dir: {agency_dir}")
    print(f"[HEARTBEAT] Poll interval: {poll_interval}s, chunk size: {chunk_size}")

    last_unassigned = 0
    last_approval = 0
    last_notification_time = 0

    while True:
        try:
            counts = get_task_count(agency_dir)
            available_agents = get_available_agents(agency_dir, chunk_size)
            current_time = time.time()

            print(
                f"[HEARTBEAT] Tasks: {counts['unassigned']} unassigned, "
                f"{len(available_agents)} agents available: {available_agents}"
            )

            if counts["unassigned"] > 0 and available_agents:
                should_notify = counts["unassigned"] != last_unassigned and (current_time - last_notification_time) > 30
                if should_notify:
                    agent_list = ", ".join(available_agents)
                    msg = (
                        f"📋 {counts['unassigned']} unassigned task(s), "
                        f"{len(available_agents)} agent(s) available ({agent_list}). "
                        f"Run 'agency tasks list' to review and assign."
                    )
                    if send_notification(window_ref, msg):
                        print(f"[HEARTBEAT] Notified manager: {msg}")
                        last_unassigned = counts["unassigned"]
                        last_notification_time = current_time

            if counts["pending_approval"] > 0 and counts["pending_approval"] != last_approval:
                msg = (
                    f"👀 {counts['pending_approval']} task(s) pending your approval - run 'agency tasks list' to review"
                )
                if send_notification(window_ref, msg):
                    print(f"[HEARTBEAT] Notified manager: {msg}")
                    last_approval = counts["pending_approval"]

            time.sleep(poll_interval)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[HEARTBEAT] Error: {e}", file=sys.stderr)
            time.sleep(poll_interval)


def agent_heartbeat(agency_dir: Path, socket_name: str, agent_name: str, poll_interval: int):
    """Heartbeat loop for agent.

    Only ONE notification at a time. Waits until agent marks task as in_progress
    before sending notification for next task.
    """
    window_ref = f"{socket_name}:{agent_name}"

    print(f"[HEARTBEAT] Starting heartbeat for agent '{agent_name}'")
    print(f"[HEARTBEAT] Agency dir: {agency_dir}")
    print(f"[HEARTBEAT] Poll interval: {poll_interval}s")

    # Track the task we notified about (and are waiting to be picked up)
    pending_notification_task_id: str | None = None

    while True:
        try:
            tasks = get_agent_tasks(agency_dir, agent_name)
            pending_tasks = [t for t in tasks if t.get("status") == "pending"]
            in_progress_tasks = [t for t in tasks if t.get("status") == "in_progress"]

            # If agent picked up the pending task, clear and wait for next
            if in_progress_tasks:
                if pending_notification_task_id:
                    print(f"[HEARTBEAT] Agent picked up: {pending_notification_task_id}")
                pending_notification_task_id = None

            # If we have a pending task and agent is free, notify
            elif pending_tasks and not pending_notification_task_id:
                next_task = pending_tasks[0]
                task_id = next_task.get("task_id")

                msg = f"📌 New task: {task_id} - run 'agency tasks show {task_id}' to view"
                if send_notification(window_ref, msg):
                    print(f"[HEARTBEAT] Notified agent about: {task_id}")
                    pending_notification_task_id = task_id

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

    if not role:
        print("[HEARTBEAT] Error: AGENCY_ROLE must be set (MANAGER or AGENT)")
        print("[HEARTBEAT] Usage: Run via agency launch scripts, not directly")
        sys.exit(1)

    if role == "MANAGER":
        manager_name = os.environ.get("AGENCY_MANAGER", "coordinator")
        manager_heartbeat(agency_dir, socket_name, manager_name, poll_interval, chunk_size)
    elif role == "AGENT":
        agent_name = os.environ.get("AGENCY_AGENT", "")
        if not agent_name:
            print("[HEARTBEAT] Error: AGENCY_AGENT must be set when role is AGENT")
            sys.exit(1)
        agent_heartbeat(agency_dir, socket_name, agent_name, poll_interval)
    else:
        print(f"[HEARTBEAT] Error: Unknown role '{role}'. Must be MANAGER or AGENT")
        sys.exit(1)


def main():
    run_heartbeat()


if __name__ == "__main__":
    main()
