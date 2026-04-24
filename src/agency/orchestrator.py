"""
Agency v2.0 - Manager Orchestration

Handles agent lifecycle management based on task state.
Agents are started on-demand and stopped when idle.

Slot-based spawning:
- Agents are spawned only when work is assigned to them
- A slot represents capacity for one parallel task per agent
- Slots signal availability when tasks complete
"""

import json
import time
from pathlib import Path
from typing import NamedTuple

from agency.config import load_agency_config, load_agents_config


class AgentSlot(NamedTuple):
    """Represents an available slot for an agent to pick up work."""

    agent: str
    available: bool
    busy_count: int = 0
    slot_index: int = 0  # Which slot (0 to parallel_limit-1)


class SlotEvent:
    """File-based slot availability signal.

    Uses a JSON file to track slot events. Heartbeat waits on this file
    for slot availability, avoiding busy polling.

    Files:
    - signals/slots-available.json: List of available (agent, slot_index) tuples
    - signals/slots-waiting.json: List of waiting requestors
    """

    SLOTS_FILE = "signals/slots-available.json"
    WAITING_FILE = "signals/slots-waiting.json"

    def __init__(self, agency_dir: Path):
        self.agency_dir = agency_dir
        self.signals_dir = agency_dir / "signals"
        self.slots_file = self.signals_dir / "slots-available.json"
        self.waiting_file = self.signals_dir / "slots-waiting.json"

    def _ensure_signals_dir(self):
        """Ensure signals directory exists."""
        self.signals_dir.mkdir(parents=True, exist_ok=True)

    def get_available_slots(self) -> list[tuple[str, int]]:
        """Get list of available (agent, slot_index) tuples."""
        self._ensure_signals_dir()

        if not self.slots_file.exists():
            return []

        try:
            data = json.loads(self.slots_file.read_text())
            return [(item["agent"], item["slot_index"]) for item in data]
        except (json.JSONDecodeError, KeyError, TypeError):
            return []

    def claim_slot(self, agent: str, slot_index: int) -> bool:
        """Claim an available slot.

        Args:
            agent: Agent name
            slot_index: Slot index within agent's capacity

        Returns:
            True if claimed, False if not available
        """
        self._ensure_signals_dir()

        available = self.get_available_slots()
        target = (agent, slot_index)

        if target not in available:
            return False

        # Remove from available slots
        available.remove(target)
        self.slots_file.write_text(json.dumps(available, indent=2))
        return True

    def release_slot(self, agent: str, slot_index: int):
        """Release a slot (mark as available).

        Called when a task completes to signal a slot is now available.

        Args:
            agent: Agent name
            slot_index: Slot index
        """
        self._ensure_signals_dir()

        available = self.get_available_slots()
        target = (agent, slot_index)

        if target not in available:
            available.append(target)
            self.slots_file.write_text(json.dumps(available, indent=2))

            # Notify waiting requestors by touching waiting file mtime
            self.waiting_file.touch()

    def wait_for_slot(self, timeout: float = 30.0, poll_interval: float = 1.0) -> tuple[str, int] | None:
        """Wait for an available slot.

        Blocks until a slot becomes available or timeout expires.
        Uses file modification time for efficient waiting.

        Args:
            timeout: Maximum seconds to wait
            poll_interval: How often to check file mtime

        Returns:
            (agent, slot_index) tuple if slot found, None if timeout
        """
        self._ensure_signals_dir()

        # Initialize waiting file if needed
        self.waiting_file.touch()

        start = time.time()

        while True:
            elapsed = time.time() - start
            if elapsed >= timeout:
                return None

            # Check available slots
            available = self.get_available_slots()
            if available:
                # Claim first available
                agent, slot_index = available[0]
                if self.claim_slot(agent, slot_index):
                    return (agent, slot_index)

            # Calculate remaining time and poll interval
            remaining = timeout - elapsed
            wait_time = min(poll_interval, remaining)

            # Wait using file mtime change
            time.sleep(wait_time)

            # Check if waiting file was touched (new slot released)
            if self.waiting_file.exists():
                try:
                    self.waiting_file.stat().st_mtime
                    # File exists, loop will recheck slots
                except OSError:
                    pass

    def init_agent_slots(self, agent: str, capacity: int):
        """Initialize slots for an agent when they start.

        Args:
            agent: Agent name
            capacity: Number of parallel slots (typically parallel_limit)
        """
        self._ensure_signals_dir()

        available = self.get_available_slots()

        # Add all slots for this agent that aren't already tracked
        for i in range(capacity):
            target = (agent, i)
            if target not in available:
                available.append(target)

        self.slots_file.write_text(json.dumps(available, indent=2))

    def remove_agent_slots(self, agent: str):
        """Remove all slots for an agent when they stop.

        Args:
            agent: Agent name
        """
        available = self.get_available_slots()
        available = [(a, s) for a, s in available if a != agent]
        self.slots_file.write_text(json.dumps(available, indent=2))


class Orchestrator:
    """Manages agent lifecycle based on task state."""

    def __init__(self, agency_dir: Path):
        self.agency_dir = agency_dir
        self.config = load_agency_config(agency_dir)
        self.parallel_limit = getattr(self.config, "parallel_limit", 2)

    def get_configured_agents(self) -> list[str]:
        """Get list of configured agent names."""
        agents = load_agents_config(self.agency_dir)
        return [a.name for a in agents]

    def get_agent_busy_count(self, agent: str) -> int:
        """Get count of in_progress tasks for an agent."""
        from agency.tasks import TaskStore

        store = TaskStore(self.agency_dir)
        return store.get_agent_busy_count(agent)

    def get_total_busy_count(self) -> int:
        """Get total count of in_progress tasks across all agents."""
        from agency.tasks import TaskStore

        store = TaskStore(self.agency_dir)
        return len(store.get_in_progress_tasks())

    def get_unblocked_pending_tasks(self) -> list:
        """Get pending tasks that are not blocked by dependencies."""
        from agency.tasks import TaskStore

        store = TaskStore(self.agency_dir)
        return store.get_unblocked_pending_tasks()

    def get_available_slots(self) -> list[AgentSlot]:
        """Get list of agent slots with availability.

        Returns list of (agent_name, available) tuples.
        An agent slot is available if it has fewer tasks than parallel_limit.
        """
        slots = []
        for agent in self.get_configured_agents():
            busy = self.get_agent_busy_count(agent)
            slots.append(AgentSlot(agent=agent, available=(busy < self.parallel_limit)))
        return slots

    def should_start_agent(self, agent: str) -> bool:
        """Check if we should start an agent.

        Returns True if:
        1. Agent has available slots (busy < parallel_limit)
        2. There are unblocked pending tasks
        3. We're not at total parallel limit
        """
        # Check if agent has capacity
        busy = self.get_agent_busy_count(agent)
        if busy >= self.parallel_limit:
            return False

        # Check total parallel limit
        total_busy = self.get_total_busy_count()
        if total_busy >= self.parallel_limit:
            return False

        # Check if there are unblocked tasks
        unblocked = self.get_unblocked_pending_tasks()
        if not unblocked:
            return False

        # Check if agent is already running (has window in tmux)
        if self.is_agent_running(agent):
            return False

        return True

    def is_agent_running(self, agent: str) -> bool:
        """Check if an agent is currently running (has tmux window)."""
        from agency.session import SessionManager

        project = self.config.project
        session_name = f"agency-{project}"
        sm = SessionManager(session_name, socket_name=session_name)

        if not sm.session_exists():
            return False

        return sm.window_exists(agent)

    def get_agent_capacity(self, agent: str) -> int:
        """Get the capacity (parallel limit) for an agent.

        Returns the parallel_limit, representing how many tasks
        an agent can work on simultaneously.

        Args:
            agent: Agent name

        Returns:
            Capacity (parallel_limit)
        """
        return self.parallel_limit

    def get_agent_available_slot_count(self, agent: str) -> int:
        """Get number of available slots for an agent.

        Args:
            agent: Agent name

        Returns:
            Number of slots available (0 to parallel_limit)
        """
        busy = self.get_agent_busy_count(agent)
        return max(0, self.parallel_limit - busy)

    def wait_for_available_slot(self, timeout: float = 30.0) -> tuple[str, int] | None:
        """Wait for any available slot across all agents.

        Uses the SlotEvent mechanism to efficiently wait for slot availability.

        Args:
            timeout: Maximum seconds to wait (default 30s)

        Returns:
            (agent, slot_index) tuple if slot available, None if timeout
        """
        slot_event = SlotEvent(self.agency_dir)
        return slot_event.wait_for_slot(timeout=timeout)

    def signal_task_completed(self, agent: str):
        """Signal that a task completed, releasing a slot.

        Called by the heartbeat when it detects a task completed
        or was approved.

        Args:
            agent: Agent name whose task completed
        """
        slot_event = SlotEvent(self.agency_dir)

        # Release the next slot for this agent
        # We use slot 0 as a simplified model (any slot release works)
        slot_event.release_slot(agent, 0)

    def init_slots_on_startup(self):
        """Initialize slot tracking on startup.

        Should be called when the heartbeat starts to set up
        the slot tracking system.
        """
        slot_event = SlotEvent(self.agency_dir)
        for agent in self.get_configured_agents():
            slot_event.init_agent_slots(agent, self.parallel_limit)

    def get_pending_tasks_for_agent(self, agent: str) -> list:
        """Get pending tasks assigned to or available for an agent."""
        from agency.tasks import TaskStore

        store = TaskStore(self.agency_dir)

        # Get unblocked pending tasks
        unblocked = store.get_unblocked_pending_tasks()

        # Filter for tasks assigned to this agent or unassigned
        result = []
        for task in unblocked:
            # Agent is available for their assigned tasks or any unassigned
            if task.assigned_to == agent or task.assigned_to is None:
                result.append(task)

        return result

    def start_agent(self, agent: str) -> bool:
        """Start an agent window in the session.

        Returns True if started successfully, False otherwise.
        """
        from agency.session import SessionManager, start_agent_window

        project = self.config.project
        session_name = f"agency-{project}"
        work_dir = self.agency_dir.parent

        sm = SessionManager(session_name, socket_name=session_name)

        # Create session if needed
        if not sm.session_exists():
            from agency.session import create_project_session

            create_project_session(session_name, session_name, work_dir)

        # Check if already running
        if sm.window_exists(agent):
            return True

        try:
            start_agent_window(session_name, session_name, agent, self.agency_dir, work_dir)
            print(f"[ORCHESTRATOR] Started agent: {agent}")
            return True
        except Exception as e:
            print(f"[ORCHESTRATOR] Failed to start agent {agent}: {e}")
            return False

    def stop_agent(self, agent: str, force: bool = False) -> bool:
        """Stop an agent window.

        Args:
            agent: Agent name
            force: If True, kill immediately. If False, graceful stop.

        Returns True if stopped successfully.
        """
        from agency.session import SessionManager

        project = self.config.project
        session_name = f"agency-{project}"

        sm = SessionManager(session_name, socket_name=session_name)

        if not sm.window_exists(agent):
            return True  # Already stopped

        if force:
            sm.kill_window(agent)
            print(f"[ORCHESTRATOR] Force killed agent: {agent}")
        else:
            # Send graceful stop signal
            sm.send_keys(agent, "Please wrap up and exit gracefully.")
            print(f"[ORCHESTRATOR] Sent graceful stop to agent: {agent}")

        return True

    def get_agent_workload(self) -> dict[str, int]:
        """Get workload per agent (in_progress task count)."""
        workload = {}
        for agent in self.get_configured_agents():
            workload[agent] = self.get_agent_busy_count(agent)
        return workload

    def get_status_summary(self) -> dict:
        """Get a summary of the current orchestration state."""
        workload = self.get_agent_workload()
        total_busy = sum(workload.values())
        unblocked = self.get_unblocked_pending_tasks()
        configured = self.get_configured_agents()

        running = [a for a in configured if self.is_agent_running(a)]
        idle_agents = [a for a in running if workload.get(a, 0) == 0]

        return {
            "parallel_limit": self.parallel_limit,
            "total_busy": total_busy,
            "at_limit": total_busy >= self.parallel_limit,
            "unblocked_tasks": len(unblocked),
            "configured_agents": configured,
            "running_agents": running,
            "idle_agents": idle_agents,
            "workload": workload,
        }


def assign_tasks_to_agents(agency_dir: Path) -> list[str]:
    """Assign pending unblocked tasks to available agents.

    This is the main orchestration logic called by the manager heartbeat.

    Args:
        agency_dir: Path to .agency directory

    Returns:
        List of task IDs that were assigned
    """
    from agency.tasks import TaskStore

    orchestrator = Orchestrator(agency_dir)
    store = TaskStore(agency_dir)

    assigned = []
    slots = orchestrator.get_available_slots()

    # Sort by current workload (agents with less work first)
    slots.sort(key=lambda s: orchestrator.get_agent_busy_count(s.agent))

    for slot in slots:
        if slot.available:
            # Get unblocked pending tasks not yet assigned
            unblocked = store.get_unblocked_pending_tasks()
            unassigned = [t for t in unblocked if t.assigned_to is None]

            if unassigned:
                task = unassigned[0]  # Pick first
                try:
                    if store.assign_task(task.task_id, slot.agent):
                        assigned.append(task.task_id)
                        print(f"[ORCHESTRATOR] Assigned task {task.task_id} to {slot.agent}")
                except ValueError as e:
                    print(f"[ORCHESTRATOR] Failed to assign {task.task_id}: {e}")

    return assigned


def start_agents_for_work(agency_dir: Path, wait_for_slot: bool = False) -> list[str]:
    """Start agents if there's work available for them.

    Agents are started when:
    1. A task is assigned to them
    2. The agent is not already running
    3. A slot is available (or becomes available if wait_for_slot=True)

    Args:
        agency_dir: Path to .agency directory
        wait_for_slot: If True, block until a slot is available

    Returns:
        List of agents that were started
    """
    from agency.tasks import TaskStore

    orchestrator = Orchestrator(agency_dir)
    store = TaskStore(agency_dir)
    started = []

    for agent in orchestrator.get_configured_agents():
        # Skip if already running
        if orchestrator.is_agent_running(agent):
            continue

        # Get tasks assigned to this agent
        assigned_tasks = [t for t in store.list_tasks(assignee=agent) if t.status in ("pending", "failed")]

        if not assigned_tasks:
            continue

        # Check if agent has capacity
        if orchestrator.get_agent_available_slot_count(agent) <= 0:
            continue

        # Optionally wait for a slot
        if wait_for_slot:
            slot = orchestrator.wait_for_available_slot(timeout=60.0)
            if slot is None:
                print(f"[ORCHESTRATOR] Timeout waiting for slot for {agent}")
                continue
            assigned_agent, _ = slot
            if assigned_agent != agent:
                # Slot went to a different agent
                print(f"[ORCHESTRATOR] Slot went to {assigned_agent}, not {agent}")
                continue

        # Start the agent
        if orchestrator.start_agent(agent):
            started.append(agent)

    return started


def get_assigned_not_running_tasks(agency_dir: Path) -> list:
    """Get tasks that are assigned but their agent is not running.

    Args:
        agency_dir: Path to .agency directory

    Returns:
        List of Task objects
    """
    from agency.tasks import TaskStore

    orchestrator = Orchestrator(agency_dir)
    store = TaskStore(agency_dir)

    # Get tasks that are pending or failed (need work) and assigned
    pending = store.list_tasks(status="pending")
    failed = store.list_tasks(status="failed")
    assigned = pending + failed

    result = []
    for task in assigned:
        if task.assigned_to and not orchestrator.is_agent_running(task.assigned_to):
            result.append(task)

    return result


def ensure_agent_running_for_task(agency_dir: Path, task) -> bool:
    """Ensure the agent assigned to a task is running.

    Args:
        agency_dir: Path to .agency directory
        task: Task object with assigned_to set

    Returns:
        True if agent is now running or was already running
    """
    orchestrator = Orchestrator(agency_dir)

    if not task.assigned_to:
        return False

    if orchestrator.is_agent_running(task.assigned_to):
        return True

    # Check capacity
    if orchestrator.get_agent_available_slot_count(task.assigned_to) <= 0:
        return False

    return orchestrator.start_agent(task.assigned_to)
