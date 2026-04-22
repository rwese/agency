"""
Agency v2.0 - Manager Orchestration

Handles agent lifecycle management based on task state.
Agents are started on-demand and stopped when idle.
"""

from pathlib import Path
from typing import NamedTuple

from agency.config import load_agency_config, load_agents_config


class AgentSlot(NamedTuple):
    """Represents an available slot for an agent to pick up work."""
    agent: str
    available: bool


class Orchestrator:
    """Manages agent lifecycle based on task state."""

    def __init__(self, agency_dir: Path):
        self.agency_dir = agency_dir
        self.config = load_agency_config(agency_dir)
        self.parallel_limit = getattr(self.config, 'parallel_limit', 2)

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


def start_agents_for_work(agency_dir: Path) -> list[str]:
    """Start agents if there's work available for them.

    Args:
        agency_dir: Path to .agency directory

    Returns:
        List of agents that were started
    """
    orchestrator = Orchestrator(agency_dir)
    started = []

    for agent in orchestrator.get_configured_agents():
        if orchestrator.should_start_agent(agent):
            if orchestrator.start_agent(agent):
                started.append(agent)

    return started
