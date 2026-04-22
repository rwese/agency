"""
Agency v2.0 - Review Flow

Handles the task review process:
1. Start a reviewer agent with fresh context + task info
2. Reviewer approves or rejects the task
3. On rejection, manager restarts the original agent with fix prompt
"""

from pathlib import Path
from typing import NamedTuple

from agency.config import load_agents_config


class ReviewContext(NamedTuple):
    """Context passed to a reviewer agent."""

    task_id: str
    task_description: str
    agent_result: str
    files_changed: list[str]
    diff: str
    agent_name: str
    rejection_reason: str | None = None


def create_reviewer_prompt(ctx: ReviewContext) -> str:
    """Create a prompt for the reviewer agent.

    Args:
        ctx: Review context with task info and agent result

    Returns:
        Reviewer prompt string
    """
    prompt = f"""# Task Review

You are reviewing a completed task for the agency project.

## Task Information
- **Task ID**: {ctx.task_id}
- **Assigned Agent**: {ctx.agent_name}
- **Description**: {ctx.task_description}

## Agent's Result
{ctx.agent_result}

"""

    if ctx.files_changed:
        prompt += """## Files Changed
"""
        for f in ctx.files_changed:
            prompt += f"- {f}\n"
        prompt += "\n"

    if ctx.diff:
        prompt += f"""## Changes (Diff)
```
{ctx.diff}
```

"""

    if ctx.rejection_reason:
        prompt += f"""## Previous Rejection Reason
{ctx.rejection_reason}

The agent has addressed this feedback. Please verify the fix is complete.
"""

    prompt += """## Review Checklist

1. **Requirements Check**: Does the implementation match the task description?
2. **Code Quality**: Is the code clean, well-structured, and maintainable?
3. **Testing**: Are there appropriate tests if required?
4. **Documentation**: Are docs updated if needed?

## Actions

After your review, use one of:

```bash
# If approved
agency tasks approve {ctx.task_id}

# If rejected (with specific feedback)
agency tasks reject {ctx.task_id} --reason "Detailed rejection reason here"
```

Take your time to review thoroughly. Check the actual files and verify the implementation.
"""

    return prompt


def get_task_review_context(agency_dir: Path, task_id: str) -> ReviewContext | None:
    """Get review context for a task.

    Args:
        agency_dir: Path to .agency directory
        task_id: Task ID to review

    Returns:
        ReviewContext or None if task not found
    """
    import json

    from agency.tasks import TaskStore

    store = TaskStore(agency_dir)
    task = store.get_task(task_id)

    if not task:
        return None

    # Read result.json if exists
    result_data = {}
    result_path = agency_dir / "var" / "tasks" / task_id / "result.json"
    if result_path.exists():
        try:
            result_data = json.loads(result_path.read_text())
        except json.JSONDecodeError:
            pass

    files = result_data.get("artifacts", {}).get("files", [])
    diff = result_data.get("artifacts", {}).get("diff", "")

    return ReviewContext(
        task_id=task_id,
        task_description=task.description,
        agent_result=task.result or "No result provided",
        files_changed=files,
        diff=diff,
        agent_name=task.assigned_to or "unknown",
        rejection_reason=task.rejection_reason,
    )


def get_pending_approval_tasks(agency_dir: Path) -> list[dict]:
    """Get all tasks in pending_approval status.

    Args:
        agency_dir: Path to .agency directory

    Returns:
        List of task dicts with status pending_approval
    """
    from agency.tasks import TaskStore

    store = TaskStore(agency_dir)
    return [t.to_dict() for t in store.list_tasks(status="pending_approval", include_blocked=True)]


def start_reviewer(agency_dir: Path, task_id: str) -> bool:
    """Start a reviewer agent for a task.

    Creates a fresh reviewer session with the task context.

    Args:
        agency_dir: Path to .agency directory
        task_id: Task ID to review

    Returns:
        True if reviewer started successfully
    """
    from agency.session import SessionManager, start_agent_window

    ctx = get_task_review_context(agency_dir, task_id)
    if not ctx:
        print(f"[REVIEWER] Task {task_id} not found")
        return False

    # Check if reviewer agent is configured
    agents = load_agents_config(agency_dir)
    reviewer_names = [a.name for a in agents if a.name.startswith("reviewer")]
    reviewer_name = reviewer_names[0] if reviewer_names else "reviewer"

    # Track reviewer assignment in task
    from agency.tasks import TaskStore

    store = TaskStore(agency_dir)
    store.update_task(task_id, reviewer_assigned=reviewer_name)

    if not reviewer_names:
        print("[REVIEWER] No reviewer agent configured")
        return False

    reviewer_name = reviewer_names[0]

    # Get session info
    project = agency_dir.parent.name
    session_name = f"agency-{project}"
    work_dir = agency_dir.parent

    # Create session if needed
    sm = SessionManager(session_name, socket_name=session_name)
    if not sm.session_exists():
        from agency.session import create_project_session

        create_project_session(session_name, session_name, work_dir)

    # Check if reviewer already running
    if sm.window_exists(reviewer_name):
        print(f"[REVIEWER] {reviewer_name} already running")
        # Could send task to existing reviewer instead
        return False

    # Create reviewer prompt
    prompt = create_reviewer_prompt(ctx)

    # TODO: Start reviewer with custom prompt
    # For now, just log the prompt
    print(f"[REVIEWER] Would start {reviewer_name} with prompt:")
    print(prompt[:500] + "...")

    # Start the reviewer window
    try:
        start_agent_window(session_name, session_name, reviewer_name, agency_dir, work_dir)
        print(f"[REVIEWER] Started reviewer: {reviewer_name}")
        return True
    except Exception as e:
        print(f"[REVIEWER] Failed to start reviewer: {e}")
        return False


def restart_agent_for_fix(agency_dir: Path, task_id: str, rejection_reason: str) -> bool:
    """Restart the original agent to fix a rejected task.

    Args:
        agency_dir: Path to .agency directory
        task_id: Task ID to fix
        rejection_reason: The rejection reason from the reviewer

    Returns:
        True if agent restarted successfully
    """
    from agency.tasks import TaskStore

    store = TaskStore(agency_dir)
    task = store.get_task(task_id)

    if not task:
        print(f"[RESTART] Task {task_id} not found")
        return False

    agent_name = task.assigned_to
    if not agent_name:
        print(f"[RESTART] Task {task_id} not assigned")
        return False

    # Check agent_info for session ID
    agent_info = task.agent_info
    if not agent_info:
        print(f"[RESTART] No agent_info for task {task_id}")
        # Need to start a new agent
        return start_fresh_agent(agency_dir, task_id, rejection_reason)

    agent_info.get("session_id")  # Preserve for potential future use
    pid = agent_info.get("pid")

    # Check if the original agent is still running
    if pid:
        import subprocess

        try:
            result = subprocess.run(["ps", "-p", str(pid), "-o", "pid="], capture_output=True)
            if result.returncode == 0:
                # Original agent still running - inject fix prompt
                return inject_fix_to_running_agent(agency_dir, agent_name, task_id, rejection_reason)
        except Exception:
            pass

    # Original agent crashed or exited - start fresh
    print(f"[RESTART] Original agent {agent_name} not running, starting fresh")
    return start_fresh_agent(agency_dir, task_id, rejection_reason)


def inject_fix_to_running_agent(
    agency_dir: Path,
    agent_name: str,
    task_id: str,
    rejection_reason: str,
) -> bool:
    """Inject fix prompt into a running agent's session.

    Args:
        agency_dir: Path to .agency directory
        agent_name: Agent name
        task_id: Task ID to fix
        rejection_reason: The rejection reason

    Returns:
        True if injected successfully
    """
    from agency.pi_inject import get_client

    socket_path = agency_dir / "run" / f"injector-{agent_name}.sock"

    if not socket_path.exists():
        print(f"[RESTART] Socket not found: {socket_path}")
        return False

    try:
        client = get_client(str(socket_path))

        fix_prompt = f"""TASK REJECTED: {task_id}

Reviewer feedback:
{rejection_reason}

Please fix the issues and resubmit when done using:
agency tasks-agent complete {task_id} --result "<summary of changes>"
"""

        resp = client.steer(fix_prompt)
        if resp.is_ok:
            print(f"[RESTART] Injected fix prompt to {agent_name}")
            return True
        else:
            print(f"[RESTART] Failed to inject: {resp.message}")
            return False

    except Exception as e:
        print(f"[RESTART] Error injecting: {e}")
        return False


def start_fresh_agent(
    agency_dir: Path,
    task_id: str,
    rejection_reason: str,
) -> bool:
    """Start a fresh agent to work on a rejected task.

    Args:
        agency_dir: Path to .agency directory
        task_id: Task ID to fix
        rejection_reason: The rejection reason

    Returns:
        True if agent started successfully
    """
    from agency.session import SessionManager, start_agent_window
    from agency.tasks import TaskStore

    store = TaskStore(agency_dir)
    task = store.get_task(task_id)

    if not task:
        print(f"[RESTART] Task {task_id} not found")
        return False

    agent_name = task.assigned_to
    if not agent_name:
        print(f"[RESTART] Task {task_id} not assigned")
        return False

    # Clear old agent info and set rejection reason
    store.set_rejection(task_id, rejection_reason)

    # Reset task to pending so it can be picked up again
    store.clear_agent_info(task_id)

    # Get session info
    project = agency_dir.parent.name
    session_name = f"agency-{project}"
    work_dir = agency_dir.parent

    # Create session if needed
    sm = SessionManager(session_name, socket_name=session_name)
    if not sm.session_exists():
        from agency.session import create_project_session

        create_project_session(session_name, session_name, work_dir)

    # Check if agent already running
    if sm.window_exists(agent_name):
        print(f"[RESTART] {agent_name} already running, injecting fix prompt")
        return inject_fix_to_running_agent(agency_dir, agent_name, task_id, rejection_reason)

    # Start a new agent window
    try:
        start_agent_window(session_name, session_name, agent_name, agency_dir, work_dir)
        print(f"[RESTART] Started fresh agent: {agent_name}")
        return True
    except Exception as e:
        print(f"[RESTART] Failed to start agent: {e}")
        return False


def handle_rejection(agency_dir: Path, task_id: str, reason: str) -> bool:
    """Handle task rejection - restart agent with fix prompt.

    This is the main entry point for handling rejections.

    Args:
        agency_dir: Path to .agency directory
        task_id: Task ID that was rejected
        reason: Rejection reason

    Returns:
        True if handled successfully
    """
    from agency.tasks import TaskStore

    store = TaskStore(agency_dir)

    # Update rejection reason on task
    store.set_rejection(task_id, reason)

    # Restart the agent to fix the task
    return restart_agent_for_fix(agency_dir, task_id, reason)
