"""Typed event helpers for the orchestrator.

Events are the source of truth for run audit trails. Every significant action
emits an event that is appended to events.jsonl.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """Types of events emitted by the orchestrator."""

    # State machine events
    RUN_CREATED = "run_created"
    STATE_CHANGED = "state_changed"

    # Process events
    PROCESS_STARTED = "process_started"
    PROCESS_LINE = "process_line"
    PROCESS_EXITED = "process_exited"

    # Agent events
    AGENT_OUTPUT_RECEIVED = "agent_output_received"
    AGENT_OUTPUT_VALIDATED = "agent_output_validated"
    AGENT_OUTPUT_INVALID = "agent_output_invalid"
    AGENT_REPAIR_REQUESTED = "agent_repair_requested"

    # Git events
    WORKTREE_CREATED = "worktree_created"
    COMMIT_CREATED = "commit_created"
    PUSH_COMPLETED = "push_completed"

    # GitHub events
    PR_CREATED = "pr_created"
    PR_UPDATED = "pr_updated"
    COMMENT_CREATED = "comment_created"
    COMMENT_UPDATED = "comment_updated"

    # Error events
    ERROR_OCCURRED = "error_occurred"
    TIMEOUT_OCCURRED = "timeout_occurred"

    # Terminal events
    RUN_APPROVED = "run_approved"
    RUN_FAILED = "run_failed"
    RUN_CANCELLED = "run_cancelled"


@dataclass
class Event:
    """A single event in the orchestrator audit trail.

    Attributes:
        type: The event type.
        ts: ISO 8601 timestamp when the event occurred.
        data: Event-specific payload data.
    """

    type: EventType
    ts: str = field(default_factory=lambda: datetime.now().isoformat())
    data: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Serialize the event to a JSON string."""
        return json.dumps(
            {"type": self.type.value, "ts": self.ts, "data": self.data},
            separators=(",", ":"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> Event:
        """Deserialize an event from a JSON string."""
        obj = json.loads(json_str)
        return cls(
            type=EventType(obj["type"]),
            ts=obj["ts"],
            data=obj.get("data", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a dictionary representation."""
        return {"type": self.type.value, "ts": self.ts, "data": self.data}


def run_created_event(
    run_id: str,
    task: str,
    slug: str,
    branch: str,
    implementer_agent: str,
    reviewer_agent: str,
) -> Event:
    """Create a run_created event."""
    return Event(
        type=EventType.RUN_CREATED,
        data={
            "run_id": run_id,
            "task": task,
            "slug": slug,
            "branch": branch,
            "implementer_agent": implementer_agent,
            "reviewer_agent": reviewer_agent,
        },
    )


def state_changed_event(
    run_id: str,
    from_state: str,
    to_state: str,
    reason: str | None = None,
) -> Event:
    """Create a state_changed event."""
    data = {
        "run_id": run_id,
        "from_state": from_state,
        "to_state": to_state,
    }
    if reason:
        data["reason"] = reason
    return Event(type=EventType.STATE_CHANGED, data=data)


def process_started_event(
    run_id: str,
    role: str,
    command: list[str],
    pid: int,
) -> Event:
    """Create a process_started event."""
    return Event(
        type=EventType.PROCESS_STARTED,
        data={
            "run_id": run_id,
            "role": role,
            "command": command,
            "pid": pid,
        },
    )


def process_line_event(
    run_id: str,
    role: str,
    stream: str,
    line: str,
) -> Event:
    """Create a process_line event."""
    return Event(
        type=EventType.PROCESS_LINE,
        data={
            "run_id": run_id,
            "role": role,
            "stream": stream,
            "line": line,
        },
    )


def process_exited_event(
    run_id: str,
    role: str,
    exit_code: int,
    duration_seconds: float,
) -> Event:
    """Create a process_exited event."""
    return Event(
        type=EventType.PROCESS_EXITED,
        data={
            "run_id": run_id,
            "role": role,
            "exit_code": exit_code,
            "duration_seconds": duration_seconds,
        },
    )


def agent_output_received_event(
    run_id: str,
    role: str,
    raw_output: str,
) -> Event:
    """Create an agent_output_received event."""
    return Event(
        type=EventType.AGENT_OUTPUT_RECEIVED,
        data={
            "run_id": run_id,
            "role": role,
            "raw_output": raw_output,
        },
    )


def agent_output_validated_event(
    run_id: str,
    role: str,
    parsed_output: dict[str, Any],
) -> Event:
    """Create an agent_output_validated event."""
    return Event(
        type=EventType.AGENT_OUTPUT_VALIDATED,
        data={
            "run_id": run_id,
            "role": role,
            "parsed_output": parsed_output,
        },
    )


def agent_output_invalid_event(
    run_id: str,
    role: str,
    raw_output: str,
    error: str,
) -> Event:
    """Create an agent_output_invalid event."""
    return Event(
        type=EventType.AGENT_OUTPUT_INVALID,
        data={
            "run_id": run_id,
            "role": role,
            "raw_output": raw_output,
            "error": error,
        },
    )


def agent_repair_requested_event(
    run_id: str,
    role: str,
    attempt: int,
) -> Event:
    """Create an agent_repair_requested event."""
    return Event(
        type=EventType.AGENT_REPAIR_REQUESTED,
        data={
            "run_id": run_id,
            "role": role,
            "attempt": attempt,
        },
    )


def worktree_created_event(
    run_id: str,
    worktree_path: str,
    branch: str,
) -> Event:
    """Create a worktree_created event."""
    return Event(
        type=EventType.WORKTREE_CREATED,
        data={
            "run_id": run_id,
            "worktree_path": worktree_path,
            "branch": branch,
        },
    )


def commit_created_event(
    run_id: str,
    commit_sha: str,
    message: str,
) -> Event:
    """Create a commit_created event."""
    return Event(
        type=EventType.COMMIT_CREATED,
        data={
            "run_id": run_id,
            "commit_sha": commit_sha,
            "message": message,
        },
    )


def push_completed_event(
    run_id: str,
    branch: str,
) -> Event:
    """Create a push_completed event."""
    return Event(
        type=EventType.PUSH_COMPLETED,
        data={
            "run_id": run_id,
            "branch": branch,
        },
    )


def pr_created_event(
    run_id: str,
    pr_number: int,
    pr_url: str,
) -> Event:
    """Create a pr_created event."""
    return Event(
        type=EventType.PR_CREATED,
        data={
            "run_id": run_id,
            "pr_number": pr_number,
            "pr_url": pr_url,
        },
    )


def pr_updated_event(
    run_id: str,
    pr_number: int,
) -> Event:
    """Create a pr_updated event."""
    return Event(
        type=EventType.PR_UPDATED,
        data={
            "run_id": run_id,
            "pr_number": pr_number,
        },
    )


def comment_created_event(
    run_id: str,
    comment_id: int,
    pr_number: int,
) -> Event:
    """Create a comment_created event."""
    return Event(
        type=EventType.COMMENT_CREATED,
        data={
            "run_id": run_id,
            "comment_id": comment_id,
            "pr_number": pr_number,
        },
    )


def comment_updated_event(
    run_id: str,
    comment_id: int,
) -> Event:
    """Create a comment_updated event."""
    return Event(
        type=EventType.COMMENT_UPDATED,
        data={
            "run_id": run_id,
            "comment_id": comment_id,
        },
    )


def error_occurred_event(
    run_id: str,
    error_type: str,
    message: str,
    context: dict[str, Any] | None = None,
) -> Event:
    """Create an error_occurred event."""
    data = {
        "run_id": run_id,
        "error_type": error_type,
        "message": message,
    }
    if context:
        data["context"] = context
    return Event(type=EventType.ERROR_OCCURRED, data=data)


def timeout_occurred_event(
    run_id: str,
    operation: str,
    timeout_seconds: int,
) -> Event:
    """Create a timeout_occurred event."""
    return Event(
        type=EventType.TIMEOUT_OCCURRED,
        data={
            "run_id": run_id,
            "operation": operation,
            "timeout_seconds": timeout_seconds,
        },
    )


def run_approved_event(run_id: str, iteration: int) -> Event:
    """Create a run_approved event."""
    return Event(
        type=EventType.RUN_APPROVED,
        data={
            "run_id": run_id,
            "iteration": iteration,
        },
    )


def run_failed_event(run_id: str, reason: str) -> Event:
    """Create a run_failed event."""
    return Event(
        type=EventType.RUN_FAILED,
        data={
            "run_id": run_id,
            "reason": reason,
        },
    )


def run_cancelled_event(run_id: str) -> Event:
    """Create a run_cancelled event."""
    return Event(
        type=EventType.RUN_CANCELLED,
        data={
            "run_id": run_id,
        },
    )
