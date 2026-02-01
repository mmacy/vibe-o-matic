"""Persistence layer for orchestrator runs.

Handles:
- run.json: Derived snapshot for quick UI loading
- events.jsonl: Append-only audit source of truth
- artifacts.json: Run artifacts (branch, PR URL, etc.)
- Prompt and schema files
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from textual_tui.orchestrator.events import Event, EventType


class RunState(str, Enum):
    """States in the orchestration state machine."""

    CREATED = "CREATED"
    PREPARE_WORKSPACE = "PREPARE_WORKSPACE"
    IMPLEMENTER_RUNNING = "IMPLEMENTER_RUNNING"
    COMMIT_PUSH_PR = "COMMIT_PUSH_PR"
    REVIEWER_RUNNING = "REVIEWER_RUNNING"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    APPROVED = "APPROVED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

    @property
    def is_terminal(self) -> bool:
        """Check if this is a terminal state."""
        return self in (RunState.APPROVED, RunState.FAILED, RunState.CANCELLED)


@dataclass
class RequestedChange:
    """A single change requested by the reviewer."""

    id: str
    path: str
    description: str
    acceptance: str


@dataclass
class TestResult:
    """A single test result from the implementer."""

    command: str
    result: str  # "pass" | "fail" | "not_run"
    notes: str = ""


@dataclass
class RunSnapshot:
    """A snapshot of run state for quick UI loading.

    This is derived from events.jsonl and can be rebuilt from it.
    """

    run_id: str
    task: str
    slug: str
    branch: str
    state: RunState
    iteration: int
    created_at: str
    updated_at: str
    implementer_agent: str
    reviewer_agent: str
    worktree_path: str | None = None
    pr_number: int | None = None
    pr_url: str | None = None
    coord_comment_id: int | None = None
    last_implementer_summary: str | None = None
    last_implementer_tests: list[TestResult] = field(default_factory=list)
    last_reviewer_verdict: str | None = None
    last_requested_changes: list[RequestedChange] = field(default_factory=list)
    failure_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "run_id": self.run_id,
            "task": self.task,
            "slug": self.slug,
            "branch": self.branch,
            "state": self.state.value,
            "iteration": self.iteration,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "implementer_agent": self.implementer_agent,
            "reviewer_agent": self.reviewer_agent,
            "worktree_path": self.worktree_path,
            "pr_number": self.pr_number,
            "pr_url": self.pr_url,
            "coord_comment_id": self.coord_comment_id,
            "last_implementer_summary": self.last_implementer_summary,
            "last_implementer_tests": [
                {"command": t.command, "result": t.result, "notes": t.notes}
                for t in self.last_implementer_tests
            ],
            "last_reviewer_verdict": self.last_reviewer_verdict,
            "last_requested_changes": [
                {
                    "id": c.id,
                    "path": c.path,
                    "description": c.description,
                    "acceptance": c.acceptance,
                }
                for c in self.last_requested_changes
            ],
            "failure_reason": self.failure_reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunSnapshot:
        """Create from dictionary."""
        return cls(
            run_id=data["run_id"],
            task=data["task"],
            slug=data["slug"],
            branch=data["branch"],
            state=RunState(data["state"]),
            iteration=data["iteration"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            implementer_agent=data["implementer_agent"],
            reviewer_agent=data["reviewer_agent"],
            worktree_path=data.get("worktree_path"),
            pr_number=data.get("pr_number"),
            pr_url=data.get("pr_url"),
            coord_comment_id=data.get("coord_comment_id"),
            last_implementer_summary=data.get("last_implementer_summary"),
            last_implementer_tests=[
                TestResult(
                    command=t["command"],
                    result=t["result"],
                    notes=t.get("notes", ""),
                )
                for t in data.get("last_implementer_tests", [])
            ],
            last_reviewer_verdict=data.get("last_reviewer_verdict"),
            last_requested_changes=[
                RequestedChange(
                    id=c["id"],
                    path=c["path"],
                    description=c["description"],
                    acceptance=c["acceptance"],
                )
                for c in data.get("last_requested_changes", [])
            ],
            failure_reason=data.get("failure_reason"),
        )


@dataclass
class Artifacts:
    """Artifacts collected during a run."""

    branch: str
    worktree_path: str | None = None
    pr_number: int | None = None
    pr_url: str | None = None
    coord_comment_id: int | None = None
    last_commit_sha: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "branch": self.branch,
            "worktree_path": self.worktree_path,
            "pr_number": self.pr_number,
            "pr_url": self.pr_url,
            "coord_comment_id": self.coord_comment_id,
            "last_commit_sha": self.last_commit_sha,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Artifacts:
        """Create from dictionary."""
        return cls(
            branch=data["branch"],
            worktree_path=data.get("worktree_path"),
            pr_number=data.get("pr_number"),
            pr_url=data.get("pr_url"),
            coord_comment_id=data.get("coord_comment_id"),
            last_commit_sha=data.get("last_commit_sha"),
        )


def generate_run_id() -> str:
    """Generate a unique run ID.

    Format: YYYYMMDD-HHMMSS-<8hex> using local time.
    Example: 20260201-143012-a1b2c3d4
    """
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    hex_suffix = os.urandom(4).hex()
    return f"{timestamp}-{hex_suffix}"


def generate_slug(task: str) -> str:
    """Generate a slug from a task description.

    - Take the first line
    - Lowercase
    - Replace any non [a-z0-9]+ runs with -
    - Trim leading/trailing -
    - Truncate to 24 chars
    - If empty, use "task"
    """
    first_line = task.split("\n")[0].strip()
    lowered = first_line.lower()
    # Replace any non-alphanumeric runs with single dash
    slug = re.sub(r"[^a-z0-9]+", "-", lowered)
    # Trim leading/trailing dashes
    slug = slug.strip("-")
    # Truncate to 24 chars
    slug = slug[:24]
    # Trim trailing dash after truncation
    slug = slug.rstrip("-")
    return slug if slug else "task"


class RunPersistence:
    """Handles persistence for a single run.

    Directory structure:
    .vibe-orchestrator/runs/<run_id>/
        run.json          - Derived snapshot
        artifacts.json    - Run artifacts
        events.jsonl      - Append-only audit log
        prompts/
            implementer.txt
            reviewer.txt
        schemas/
            implementer.json
            reviewer.json
    """

    def __init__(self, repo_root: Path, run_id: str):
        """Initialize persistence for a run.

        Args:
            repo_root: Root directory of the repository.
            run_id: Unique run identifier.
        """
        self.repo_root = repo_root
        self.run_id = run_id
        self.storage_root = repo_root / ".vibe-orchestrator"
        self.run_dir = self.storage_root / "runs" / run_id
        self.worktrees_dir = self.storage_root / "worktrees"

    @property
    def run_json_path(self) -> Path:
        """Path to run.json snapshot."""
        return self.run_dir / "run.json"

    @property
    def artifacts_json_path(self) -> Path:
        """Path to artifacts.json."""
        return self.run_dir / "artifacts.json"

    @property
    def events_jsonl_path(self) -> Path:
        """Path to events.jsonl audit log."""
        return self.run_dir / "events.jsonl"

    @property
    def prompts_dir(self) -> Path:
        """Path to prompts directory."""
        return self.run_dir / "prompts"

    @property
    def schemas_dir(self) -> Path:
        """Path to schemas directory."""
        return self.run_dir / "schemas"

    def worktree_path(self) -> Path:
        """Path to the worktree for this run."""
        return self.worktrees_dir / self.run_id

    def ensure_directories(self) -> None:
        """Create all necessary directories."""
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.prompts_dir.mkdir(exist_ok=True)
        self.schemas_dir.mkdir(exist_ok=True)
        self.worktrees_dir.mkdir(parents=True, exist_ok=True)

    def append_event(self, event: Event) -> None:
        """Append an event to events.jsonl.

        This is the source of truth for the run's audit trail.
        """
        with open(self.events_jsonl_path, "a") as f:
            f.write(event.to_json() + "\n")

    def read_events(self) -> list[Event]:
        """Read all events from events.jsonl."""
        if not self.events_jsonl_path.exists():
            return []
        events = []
        with open(self.events_jsonl_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(Event.from_json(line))
        return events

    def save_snapshot(self, snapshot: RunSnapshot) -> None:
        """Save run.json snapshot."""
        with open(self.run_json_path, "w") as f:
            json.dump(snapshot.to_dict(), f, indent=2)

    def load_snapshot(self) -> RunSnapshot | None:
        """Load run.json snapshot if it exists."""
        if not self.run_json_path.exists():
            return None
        with open(self.run_json_path, "r") as f:
            return RunSnapshot.from_dict(json.load(f))

    def save_artifacts(self, artifacts: Artifacts) -> None:
        """Save artifacts.json."""
        with open(self.artifacts_json_path, "w") as f:
            json.dump(artifacts.to_dict(), f, indent=2)

    def load_artifacts(self) -> Artifacts | None:
        """Load artifacts.json if it exists."""
        if not self.artifacts_json_path.exists():
            return None
        with open(self.artifacts_json_path, "r") as f:
            return Artifacts.from_dict(json.load(f))

    def save_implementer_prompt(self, prompt: str) -> None:
        """Save the implementer prompt."""
        with open(self.prompts_dir / "implementer.txt", "w") as f:
            f.write(prompt)

    def save_reviewer_prompt(self, prompt: str) -> None:
        """Save the reviewer prompt."""
        with open(self.prompts_dir / "reviewer.txt", "w") as f:
            f.write(prompt)

    def save_implementer_schema(self, schema: dict[str, Any]) -> None:
        """Save the implementer JSON schema."""
        with open(self.schemas_dir / "implementer.json", "w") as f:
            json.dump(schema, f, indent=2)

    def save_reviewer_schema(self, schema: dict[str, Any]) -> None:
        """Save the reviewer JSON schema."""
        with open(self.schemas_dir / "reviewer.json", "w") as f:
            json.dump(schema, f, indent=2)

    def load_implementer_schema(self) -> dict[str, Any] | None:
        """Load the implementer JSON schema."""
        path = self.schemas_dir / "implementer.json"
        if not path.exists():
            return None
        with open(path, "r") as f:
            return json.load(f)

    def load_reviewer_schema(self) -> dict[str, Any] | None:
        """Load the reviewer JSON schema."""
        path = self.schemas_dir / "reviewer.json"
        if not path.exists():
            return None
        with open(path, "r") as f:
            return json.load(f)


class RunRegistry:
    """Registry for all runs in the storage directory.

    Used to list runs for the dashboard.
    """

    def __init__(self, repo_root: Path):
        """Initialize the registry.

        Args:
            repo_root: Root directory of the repository.
        """
        self.repo_root = repo_root
        self.storage_root = repo_root / ".vibe-orchestrator"
        self.runs_dir = self.storage_root / "runs"

    def list_runs(self) -> list[RunSnapshot]:
        """List all runs, sorted by created_at descending."""
        if not self.runs_dir.exists():
            return []

        snapshots = []
        for run_dir in self.runs_dir.iterdir():
            if run_dir.is_dir():
                run_json = run_dir / "run.json"
                if run_json.exists():
                    try:
                        with open(run_json, "r") as f:
                            snapshot = RunSnapshot.from_dict(json.load(f))
                            snapshots.append(snapshot)
                    except (json.JSONDecodeError, KeyError):
                        # Skip invalid run.json files
                        continue

        # Sort by created_at descending (newest first)
        snapshots.sort(key=lambda s: s.created_at, reverse=True)
        return snapshots

    def get_persistence(self, run_id: str) -> RunPersistence:
        """Get persistence handler for a specific run."""
        return RunPersistence(self.repo_root, run_id)

    def create_run(
        self,
        task: str,
        implementer_agent: str = "claude",
        reviewer_agent: str = "claude",
    ) -> tuple[str, RunPersistence]:
        """Create a new run with initial files.

        Args:
            task: The task description.
            implementer_agent: Agent to use for implementation ("claude" or "codex").
            reviewer_agent: Agent to use for review ("claude" or "codex").

        Returns:
            Tuple of (run_id, RunPersistence).
        """
        run_id = generate_run_id()
        slug = generate_slug(task)
        branch = f"agent/{run_id}-{slug}"
        now = datetime.now().isoformat()

        persistence = RunPersistence(self.repo_root, run_id)
        persistence.ensure_directories()

        # Create initial snapshot
        snapshot = RunSnapshot(
            run_id=run_id,
            task=task,
            slug=slug,
            branch=branch,
            state=RunState.CREATED,
            iteration=0,
            created_at=now,
            updated_at=now,
            implementer_agent=implementer_agent,
            reviewer_agent=reviewer_agent,
        )
        persistence.save_snapshot(snapshot)

        # Create initial artifacts
        artifacts = Artifacts(branch=branch)
        persistence.save_artifacts(artifacts)

        return run_id, persistence
