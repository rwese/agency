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
import socket
import sys
import time
from pathlib import Path

import yaml

# Lazy audit store
_audit_store = None


def _get_audit_store(agency_dir: Path):
    """Get audit store lazily if audit is enabled in config."""
    global _audit_store
    if _audit_store is None:
        try:
            from agency.audit import AuditStore
            from agency.config import load_agency_config

            config = load_agency_config(agency_dir)
            if config.audit_enabled:
                _audit_store = AuditStore(agency_dir)
            else:
                _audit_store = False
        except Exception:
            _audit_store = False
    return _audit_store if _audit_store else None


def get_all_tasks(agency_dir: Path) -> list[dict]:
    """Get all tasks as a list."""
    tasks_json = agency_dir / "var/tasks.json"
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


def process_exists(pid: int) -> bool:
    """Check if a process with the given PID exists.

    Args:
        pid: Process ID to check

    Returns:
        True if process exists, False otherwise
    """
    import subprocess

    try:
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", "pid="],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except (ValueError, OSError):
        return False


def check_stale_tasks(agency_dir: Path) -> list[dict]:
    """Check for crashed agent tasks and revert them to pending.

    Args:
        agency_dir: Path to .agency directory

    Returns:
        List of stale task info dicts with task_id, agent, and reason
    """
    stale = []

    for task in get_all_tasks(agency_dir):
        status = task.get("status", "")
        if status != "in_progress":
            continue

        agent_info = task.get("agent_info")
        if not agent_info:
            continue

        pid = agent_info.get("pid")
        if pid and not process_exists(pid):
            # Process is gone, revert task to pending
            task_id = task.get("task_id")
            session_id = agent_info.get("session_id")
            agent = task.get("assigned_to")

            # Revert the task
            try:
                from agency.tasks import TaskStore

                store = TaskStore(agency_dir)
                store.clear_agent_info(task_id)
                print(f"[CRASH DETECTED] Task {task_id} reverted - agent {agent} process {pid} not found")
                stale.append(
                    {
                        "task_id": task_id,
                        "agent": agent,
                        "session_id": session_id,
                        "reason": "process_not_found",
                        "pid": pid,
                    }
                )
            except Exception as e:
                print(f"[CRASH DETECTED] Failed to revert task {task_id}: {e}")

    return stale


def check_orphan_pending_approval_tasks(agency_dir: Path) -> list[dict]:
    """Check for orphaned pending_approval tasks (no active reviewer).

    Tasks in pending_approval need a reviewer. If no reviewer is assigned
    or the reviewer's process is gone, the task is orphaned.

    Args:
        agency_dir: Path to .agency directory

    Returns:
        List of orphaned task info dicts with task_id and reason
    """
    orphans = []

    for task in get_all_tasks(agency_dir):
        status = task.get("status", "")
        if status != "pending_approval":
            continue

        task_id = task.get("task_id")
        reviewer = task.get("reviewer_assigned")

        # If no reviewer assigned, it's orphaned
        if not reviewer:
            orphans.append(
                {
                    "task_id": task_id,
                    "reviewer": None,
                    "reason": "no_reviewer_assigned",
                }
            )
            continue

        # Check if reviewer process exists
        agent_info = task.get("reviewer_agent_info")
        if agent_info:
            pid = agent_info.get("pid")
            if pid and not process_exists(pid):
                orphans.append(
                    {
                        "task_id": task_id,
                        "reviewer": reviewer,
                        "reason": "reviewer_process_not_found",
                        "pid": pid,
                    }
                )
                continue

        # Reviewer assigned but we need to check if it's running in tmux
        # This is handled by the review spawning logic in heartbeat

    return orphans


def is_agent_idle() -> bool:
    """Check if agent is idle via pi-status socket.

    Queries the PI_STATUS_SOCKET for health status.
    Returns True if agent is idle (not actively working).
    Returns True if socket unavailable (conservative - allows notifications).
    """
    socket_path = os.environ.get("PI_STATUS_SOCKET", "")

    if socket_path:
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(2)  # 2 second timeout
            sock.connect(socket_path)

            # Send health query
            sock.sendall(b'{"action":"health"}\n')

            # Read response
            data = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                data += chunk
                break  # Single response expected

            sock.close()
            if data:
                response = json.loads(data.decode("utf-8"))
                if response.get("type") == "ok" and "data" in response:
                    return response["data"].get("idle", True)

        except (json.JSONDecodeError, OSError):
            # Socket error - assume idle to allow notifications through
            pass

    return True  # Default to idle if we can't check


def write_notification(agency_dir: Path, role: str, agent_name: str, message: str):
    """Write notification to files that pi can read."""
    import json

    notifications_file = agency_dir / "var/notifications.json"

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
    system_hint_file = agency_dir / "var/system_hint.txt"
    system_hint_file.write_text(f"\n## NEW NOTIFICATION\n{message}\n")


def send_notification(window_ref: str, message: str) -> bool:
    """Send a notification via pi-inject Unix socket.

    IMPORTANT: Only sends to pi-inject sockets that belong to this agency.
    Sockets outside the agency directory are ignored to prevent cross-talk.
    """
    agency_dir = os.environ.get("AGENCY_DIR", "")
    role = os.environ.get("AGENCY_ROLE", "")
    agent_name = os.environ.get("AGENCY_AGENT", os.environ.get("AGENCY_MANAGER", ""))
    project_name = os.environ.get("AGENCY_PROJECT", "")

    # Write to notifications file for debugging
    if agency_dir:
        write_notification(Path(agency_dir), role, agent_name, message)

    # Get socket path from env
    socket_path = os.environ.get("PI_INJECTOR_SOCKET", "")

    # CRITICAL: Validate socket path belongs to this agency
    # If socket is not set, empty, or points outside agency_dir, skip injection
    # This prevents accidental cross-talk with other pi instances
    if not socket_path:
        print("[HEARTBEAT] No PI_INJECTOR_SOCKET set, skipping injection")
        return False

    # Security check: socket path must be within agency directory
    # This ensures we only talk to our own pi-inject instance
    socket_path_obj = Path(socket_path)
    if agency_dir and not str(socket_path_obj).startswith(str(Path(agency_dir).absolute())):
        print(f"[HEARTBEAT] Socket {socket_path} outside agency dir, skipping injection")
        return False

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

        # Send as steer message with correct format for pi-inject
        resp = client.steer(cmd)

        if resp.is_ok:
            print(f"[HEARTBEAT] Injected to {project_name}: {cmd}")
            return True
        else:
            print(f"[HEARTBEAT] Inject error: {resp.message}")
            return False

    except FileNotFoundError:
        print(f"[HEARTBEAT] pi-inject socket not found: {socket_path}")
        return False
    except ConnectionRefusedError:
        print(f"[HEARTBEAT] pi-inject not ready: {socket_path}")
        return False
    except Exception as e:
        print(f"[HEARTBEAT] pi-inject error: {e}")
        return False


def _check_pid_file(agency_dir: Path, member_name: str) -> bool:
    """Check if a heartbeat is already running for this member.

    Returns True if we should exit (another instance is running).
    Returns False if we should continue (no other instance).
    """
    import os

    pid_file = agency_dir / "run" / f".heartbeat-{member_name}.pid"
    current_pid = os.getpid()

    if pid_file.exists():
        try:
            old_pid = int(pid_file.read_text().strip())
            # Check if the old process is still running
            if old_pid != current_pid:
                try:
                    os.kill(old_pid, 0)  # Signal 0 just checks if process exists
                    print(f"[HEARTBEAT] Another instance already running (PID: {old_pid})")
                    return True
                except OSError:
                    # Old process is dead, we'll replace it
                    pass
        except (ValueError, OSError):
            pass

    # Write our PID
    pid_file.write_text(str(current_pid))
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
    # Prevent duplicate heartbeats
    if _check_pid_file(agency_dir, f"manager-{manager_name}"):
        return

    window_ref = f"{socket_name}:[MGR] {manager_name}"

    print(f"[HEARTBEAT] Starting heartbeat for manager '{manager_name}'")
    print(f"[HEARTBEAT] Agency dir: {agency_dir}")
    print(f"[HEARTBEAT] Poll interval: {poll_interval}s, chunk: {chunk_size}, parallel_limit: {parallel_limit}")

    last_unassigned = 0
    last_approval = 0
    last_notification_time = 0
    _idle_cycles = 0  # Track cycles with nothing to dispatch

    while True:
        try:
            # CRASH DETECTION: Check for stale tasks and revert them
            stale = check_stale_tasks(agency_dir)
            if stale:
                print(f"[HEARTBEAT] Reverted {len(stale)} stale tasks due to crashed agents")
                # Audit crash events
                audit = _get_audit_store(agency_dir)
                if audit:
                    for event in stale:
                        audit.log_agent(
                            action="crash_detected",
                            agency_role="agent",
                            details={
                                "task_id": event["task_id"],
                                "agent": event["agent"],
                                "pid": event["pid"],
                            },
                        )

            counts = get_task_count(agency_dir)
            active_count = counts["pending"] + counts["in_progress"]
            available_agents = get_available_agents(agency_dir, chunk_size)
            current_time = time.time()

            # Check parallel limit
            at_parallel_limit = parallel_limit is not None and active_count >= parallel_limit

            # Determine if there's anything dispatchable
            has_unassigned = counts["unassigned"] > 0 and available_agents
            has_pending_approval = counts["pending_approval"] > 0
            is_dispatchable = has_unassigned or has_pending_approval

            if not is_dispatchable:
                _idle_cycles += 1
                # Only log every 10 cycles to reduce noise
                if _idle_cycles == 1 or _idle_cycles % 10 == 0:
                    print(
                        f"[HEARTBEAT] Idle: {counts['in_progress']} in progress, "
                        f"{counts['pending']} assigned (not started), "
                        f"{len(available_agents)} agents available. Nothing to dispatch."
                    )
                time.sleep(poll_interval)
                continue

            # Reset idle counter when there's work
            _idle_cycles = 0

            # Only notify about unassigned tasks when nothing is in progress
            if has_unassigned and counts["in_progress"] == 0:
                should_notify = counts["unassigned"] != last_unassigned and (current_time - last_notification_time) > 30
                if should_notify:
                    agent_list = ", ".join(available_agents)

                    # Add parallel limit warning if at limit
                    parallel_warning = ""
                    if at_parallel_limit:
                        parallel_warning = (
                            f" ⚠️ **Note**: Only {parallel_limit} task(s) will be actively worked on in priority order."
                        )

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

            # Only notify about pending approval when nothing is in progress
            elif has_pending_approval and counts["pending_approval"] != last_approval:
                # Get pending task IDs and send approve commands
                from agency.tasks import TaskStore
                store = TaskStore(agency_dir)
                pending_tasks = store.list_tasks(status="pending_approval")

                for task in pending_tasks:
                    task_id = task.task_id
                    # Send approval command directly
                    cmd = f"agency tasks approve {task_id}"
                    if send_notification(window_ref, f"Please review and approve: {task_id}"):
                        # Actually send the approve command
                        import os

                        from agency.pi_inject import get_client
                        socket_path = os.environ.get("PI_INJECTOR_SOCKET", "")
                        if socket_path:
                            try:
                                client = get_client(socket_path)
                                resp = client.steer(cmd)
                                if resp.is_ok:
                                    print(f"[HEARTBEAT] Sent approval for {task_id}")
                                else:
                                    print(f"[HEARTBEAT] Approval error: {resp.message}")
                            except Exception as e:
                                print(f"[HEARTBEAT] Could not send approval: {e}")

                print(f"[HEARTBEAT] Notified manager about {len(pending_tasks)} pending approval tasks")
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


def agent_heartbeat(
    agency_dir: Path, socket_name: str, agent_name: str, poll_interval: int = 30, ping_interval: int = 120
):
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
    # Prevent duplicate heartbeats
    if _check_pid_file(agency_dir, f"agent-{agent_name}"):
        return

    window_ref = f"{socket_name}:{agent_name}"

    print(f"[HEARTBEAT] Starting heartbeat for agent '{agent_name}'")
    print(f"[HEARTBEAT] Agency dir: {agency_dir}")
    print(f"[HEARTBEAT] Poll interval: {poll_interval}s, ping interval: {ping_interval}s")
    print(f"[HEARTBEAT] Status socket: {os.environ.get('PI_STATUS_SOCKET', 'not set')}")

    last_ping_time = 0  # Track when we last sent a ping
    last_notified_task_id = None  # Track last notified task

    while True:
        try:
            tasks = get_agent_tasks(agency_dir, agent_name)

            # Sort pending tasks by priority (high > normal > low) then created_at
            priority_order = {"high": 0, "normal": 1, "low": 2}
            pending_tasks = sorted(
                [t for t in tasks if t.get("status") == "pending"],
                key=lambda t: (priority_order.get(t.get("priority", "normal"), 1), t.get("created_at", "")),
            )
            in_progress_tasks = [t for t in tasks if t.get("status") == "in_progress"]
            current_time = time.time()

            # Check if agent is idle via pi-status socket
            pane_is_idle = is_agent_idle()

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

            # Only notify about pending tasks when nothing is in progress AND pane is idle
            # NEVER interrupt a working agent
            # Stable selection: first task by priority + created_at
            if pending_tasks and not in_progress_tasks and pane_is_idle:
                next_task = pending_tasks[0]
                task_id = next_task.get("task_id")

                # Only notify if new task or been idle since last notify
                should_notify = task_id != last_notified_task_id or current_time - last_ping_time >= ping_interval

                if should_notify:
                    desc = next_task.get("description", "")[:50]
                    msg = f"📌 Task ready: {task_id} - {desc}... Run 'agency tasks show {task_id}' to start"
                    if send_notification(window_ref, msg):
                        print(f"[HEARTBEAT] Notified agent about: {task_id}")
                        last_ping_time = current_time
                        last_notified_task_id = task_id

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

            # Periodic ping with no tasks (keep agent engaged) - only if idle
            elif pane_is_idle and current_time - last_ping_time >= ping_interval * 2:
                msg = "🏃 No tasks assigned. Check 'agency tasks list' or wait for new assignments."
                if send_notification(window_ref, msg):
                    print("[HEARTBEAT] Pinged idle agent")
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


def manager_heartbeat_v2(
    agency_dir: Path,
    socket_name: str,
    manager_name: str,
    poll_interval: int = 30,
):
    """Heartbeat loop for manager with orchestration.

    This is the new task-centric heartbeat that:
    1. Detects crashed agents and reverts their tasks
    2. Extends crash detection to orphaned pending_approval tasks
    3. Starts reviewer agents for pending_approval tasks
    4. Assigns pending tasks to available agents
    5. Starts agents only when work is assigned to them (lazy spawning)

    Args:
        agency_dir: Path to .agency/ directory
        socket_name: Tmux socket name
        manager_name: Name of the manager window
        poll_interval: Seconds between checks
    """
    from agency.orchestrator import (
        Orchestrator,
        assign_tasks_to_agents,
        ensure_agent_running_for_task,
        get_assigned_not_running_tasks,
    )
    from agency.reviewer import get_pending_approval_tasks, start_reviewer

    # Prevent duplicate heartbeats
    if _check_pid_file(agency_dir, f"manager-{manager_name}"):
        return

    window_ref = f"{socket_name}:[MGR] {manager_name}"
    orchestrator = Orchestrator(agency_dir)

    # Initialize slot tracking on startup
    orchestrator.init_slots_on_startup()

    print(f"[HEARTBEAT-V2] Starting for manager '{manager_name}'")
    print(f"[HEARTBEAT-V2] Agency dir: {agency_dir}")
    print(f"[HEARTBEAT-V2] Poll interval: {poll_interval}s")

    last_approval_count = 0
    _idle_cycles = 0

    while True:
        try:
            # 1. CRASH DETECTION: Check for stale in_progress tasks
            stale = check_stale_tasks(agency_dir)
            if stale:
                print(f"[HEARTBEAT-V2] Reverted {len(stale)} stale tasks")
                audit = _get_audit_store(agency_dir)
                if audit:
                    for event in stale:
                        audit.log_agent(
                            action="crash_detected",
                            agency_role="agent",
                            details={
                                "task_id": event["task_id"],
                                "agent": event["agent"],
                                "pid": event["pid"],
                            },
                        )

            # 1b. ORPHAN DETECTION: Check for orphaned pending_approval tasks
            orphans = check_orphan_pending_approval_tasks(agency_dir)
            if orphans:
                print(f"[HEARTBEAT-V2] Found {len(orphans)} orphaned pending_approval tasks")
                # Clear reviewer assignment so new reviewer can be spawned
                from agency.tasks import TaskStore

                store = TaskStore(agency_dir)
                for orphan in orphans:
                    task_id = orphan["task_id"]
                    store.update_task(task_id, reviewer_assigned=None)
                    print(f"[HEARTBEAT-V2] Cleared orphan reviewer for {task_id}")

            # 2. REVIEW: Spawn reviewer agents for pending_approval tasks
            pending_approval = get_pending_approval_tasks(agency_dir)
            for task in pending_approval:
                task_id = task.get("task_id")
                reviewer = task.get("reviewer_assigned")
                if not reviewer:
                    # Spawn reviewer for this task
                    if start_reviewer(agency_dir, task_id):
                        print(f"[HEARTBEAT-V2] Spawned reviewer for {task_id}")

            # 3. ASSIGNMENT: Assign pending unblocked tasks to available agents
            assigned = assign_tasks_to_agents(agency_dir)
            if assigned:
                print(f"[HEARTBEAT-V2] Assigned tasks: {assigned}")

            # 4. SPAWN: Start agents for tasks assigned but not running
            # This is the lazy spawning - agents only start when work is assigned
            unstarted_tasks = get_assigned_not_running_tasks(agency_dir)
            spawned = []
            for task in unstarted_tasks:
                if ensure_agent_running_for_task(agency_dir, task):
                    spawned.append(task.assigned_to)
            if spawned:
                print(f"[HEARTBEAT-V2] Spawned agents for assigned tasks: {spawned}")

            # 5. SLOT SIGNALING: Release slots for completed tasks
            # Signal when in_progress tasks complete (moved to pending_approval)
            current_approval_count = len(pending_approval)
            if current_approval_count > last_approval_count:
                # Tasks moved to pending_approval - signal slots
                for task in get_all_tasks(agency_dir):
                    if task.get("status") == "pending_approval":
                        agent = task.get("assigned_to")
                        if agent:
                            orchestrator.signal_task_completed(agent)

            # 6. NOTIFICATION: Notify about pending approvals
            status = orchestrator.get_status_summary()
            if current_approval_count > 0 and current_approval_count != last_approval_count:
                msg = f"👀 {current_approval_count} task(s) pending approval. Reviewers spawned."
                if send_notification(window_ref, msg):
                    print("[HEARTBEAT-V2] Notified about pending approvals")
            last_approval_count = current_approval_count

            # 7. STATUS: Log status summary periodically
            _idle_cycles += 1
            if _idle_cycles % 10 == 0:
                print(
                    f"[HEARTBEAT-V2] Status: {status['total_busy']}/{status['parallel_limit']} busy, "
                    f"{len(status['running_agents'])} running, "
                    f"{status['unblocked_tasks']} unblocked tasks"
                )

            time.sleep(poll_interval)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[HEARTBEAT-V2] Error: {e}", file=sys.stderr)
            import traceback

            traceback.print_exc()
            time.sleep(poll_interval)
