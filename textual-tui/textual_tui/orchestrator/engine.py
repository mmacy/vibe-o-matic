"""Orchestration engine: state machine and step runner.

The engine is responsible for:
- Managing state transitions
- Coordinating agents, git, and GitHub operations
- Ensuring idempotent recovery on crash/resume
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Protocol

from textual_tui.orchestrator.events import (
    Event,
    EventType,
    run_created_event,
    state_changed_event,
    run_approved_event,
    run_failed_event,
    run_cancelled_event,
    error_occurred_event,
)
from textual_tui.orchestrator.persistence import (
    RunState,
    RunPersistence,
    RunSnapshot,
    RunRegistry,
    Artifacts,
    RequestedChange,
    TestResult,
)


# Timeouts in seconds
IMPLEMENTER_TIMEOUT = 30 * 60  # 30 minutes
REVIEWER_TIMEOUT = 15 * 60  # 15 minutes
GIT_GH_TIMEOUT = 2 * 60  # 2 minutes


class GitService(Protocol):
    """Protocol for git operations."""

    async def create_worktree(
        self,
        repo_root: Path,
        worktree_path: Path,
        branch: str,
        base_branch: str,
    ) -> None:
        """Create a git worktree."""
        ...

    async def has_changes(self, worktree_path: Path) -> bool:
        """Check if worktree has uncommitted changes."""
        ...

    async def commit_all(
        self, worktree_path: Path, message: str
    ) -> str:
        """Stage all changes and commit, returning commit SHA."""
        ...

    async def push(self, worktree_path: Path, branch: str) -> None:
        """Push branch to origin."""
        ...

    async def get_diff_stat(self, worktree_path: Path, base_branch: str) -> str:
        """Get diff --stat output."""
        ...

    async def get_budgeted_diff(
        self,
        worktree_path: Path,
        base_branch: str,
        max_files: int,
        max_bytes: int,
        max_hunks_per_file: int,
    ) -> str:
        """Get budgeted unified diff."""
        ...


class GitHubService(Protocol):
    """Protocol for GitHub operations."""

    async def find_pr(self, branch: str) -> tuple[int, str] | None:
        """Find existing PR for branch, returns (number, url) or None."""
        ...

    async def create_pr(
        self,
        branch: str,
        base_branch: str,
        title: str,
        body: str,
    ) -> tuple[int, str]:
        """Create a PR, returns (number, url)."""
        ...

    async def create_comment(
        self, pr_number: int, body: str
    ) -> int:
        """Create a comment on a PR, returns comment ID."""
        ...

    async def update_comment(self, comment_id: int, body: str) -> None:
        """Update an existing comment."""
        ...


class AgentDriver(Protocol):
    """Protocol for agent drivers."""

    async def run(
        self,
        worktree_path: Path,
        prompt: str,
        schema: dict[str, Any],
        schema_path: Path,
        output_path: Path,
        timeout: int,
        on_line: Callable[[str, str], None] | None,
    ) -> dict[str, Any]:
        """Run the agent and return validated output.

        Args:
            worktree_path: Working directory for the agent.
            prompt: The prompt to send to the agent.
            schema: JSON Schema for output validation.
            schema_path: Path to schema file for CLI.
            output_path: Path for agent to write output.
            timeout: Timeout in seconds.
            on_line: Callback for each output line (stream, line).

        Returns:
            Validated output dictionary.

        Raises:
            AgentError: If agent fails or output is invalid after retry.
            TimeoutError: If agent exceeds timeout.
        """
        ...


class AgentError(Exception):
    """Raised when an agent fails."""

    pass


@dataclass
class EngineConfig:
    """Configuration for the orchestration engine."""

    repo_root: Path
    base_branch: str = "main"
    remote: str = "origin"
    implementer_timeout: int = IMPLEMENTER_TIMEOUT
    reviewer_timeout: int = REVIEWER_TIMEOUT
    git_gh_timeout: int = GIT_GH_TIMEOUT
    max_diff_files: int = 25
    max_diff_bytes: int = 200_000
    max_hunks_per_file: int = 8


class OrchestrationEngine:
    """The main orchestration engine.

    Manages the implement -> review -> iterate loop using headless agents.
    """

    def __init__(
        self,
        config: EngineConfig,
        git_service: GitService,
        github_service: GitHubService,
        implementer_driver: AgentDriver,
        reviewer_driver: AgentDriver,
        on_event: Callable[[Event], None] | None = None,
    ):
        """Initialize the engine.

        Args:
            config: Engine configuration.
            git_service: Git operations service.
            github_service: GitHub operations service.
            implementer_driver: Driver for the implementer agent.
            reviewer_driver: Driver for the reviewer agent.
            on_event: Callback for each event (for UI updates).
        """
        self.config = config
        self.git_service = git_service
        self.github_service = github_service
        self.implementer_driver = implementer_driver
        self.reviewer_driver = reviewer_driver
        self.on_event = on_event

        self._registry = RunRegistry(config.repo_root)
        self._persistence: RunPersistence | None = None
        self._snapshot: RunSnapshot | None = None
        self._artifacts: Artifacts | None = None
        self._cancelled = False

    def _emit_event(self, event: Event) -> None:
        """Emit an event to persistence and callback."""
        if self._persistence:
            self._persistence.append_event(event)
        if self.on_event:
            self.on_event(event)

    def _transition_to(self, new_state: RunState, reason: str | None = None) -> None:
        """Transition to a new state."""
        if not self._snapshot:
            raise RuntimeError("No active run")

        old_state = self._snapshot.state
        self._snapshot.state = new_state
        self._snapshot.updated_at = datetime.now().isoformat()

        event = state_changed_event(
            self._snapshot.run_id,
            old_state.value,
            new_state.value,
            reason,
        )
        self._emit_event(event)
        self._save_snapshot()

    def _save_snapshot(self) -> None:
        """Save the current snapshot."""
        if self._persistence and self._snapshot:
            self._persistence.save_snapshot(self._snapshot)

    def _save_artifacts(self) -> None:
        """Save the current artifacts."""
        if self._persistence and self._artifacts:
            self._persistence.save_artifacts(self._artifacts)

    async def create_run(
        self,
        task: str,
        implementer_agent: str = "claude",
        reviewer_agent: str = "claude",
    ) -> str:
        """Create a new run.

        Args:
            task: The task description.
            implementer_agent: Agent for implementation ("claude" or "codex").
            reviewer_agent: Agent for review ("claude" or "codex").

        Returns:
            The run ID.
        """
        run_id, persistence = self._registry.create_run(
            task, implementer_agent, reviewer_agent
        )
        self._persistence = persistence
        self._snapshot = persistence.load_snapshot()
        self._artifacts = persistence.load_artifacts()

        if not self._snapshot or not self._artifacts:
            raise RuntimeError("Failed to create run")

        # Emit run_created event
        event = run_created_event(
            run_id=run_id,
            task=task,
            slug=self._snapshot.slug,
            branch=self._snapshot.branch,
            implementer_agent=implementer_agent,
            reviewer_agent=reviewer_agent,
        )
        self._emit_event(event)

        return run_id

    async def load_run(self, run_id: str) -> RunSnapshot | None:
        """Load an existing run.

        Args:
            run_id: The run ID to load.

        Returns:
            The run snapshot, or None if not found.
        """
        self._persistence = self._registry.get_persistence(run_id)
        self._snapshot = self._persistence.load_snapshot()
        self._artifacts = self._persistence.load_artifacts()
        self._cancelled = False
        return self._snapshot

    def cancel(self) -> None:
        """Request cancellation of the current run."""
        self._cancelled = True

    async def run(self) -> RunState:
        """Execute the orchestration loop until terminal state.

        Returns:
            The final state.
        """
        if not self._snapshot:
            raise RuntimeError("No active run")

        while not self._snapshot.state.is_terminal and not self._cancelled:
            await self._step()

        if self._cancelled and not self._snapshot.state.is_terminal:
            self._transition_to(RunState.CANCELLED)
            event = run_cancelled_event(self._snapshot.run_id)
            self._emit_event(event)

        return self._snapshot.state

    async def _step(self) -> None:
        """Execute one step of the state machine."""
        if not self._snapshot:
            raise RuntimeError("No active run")

        state = self._snapshot.state

        try:
            if state == RunState.CREATED:
                self._transition_to(RunState.PREPARE_WORKSPACE)

            elif state == RunState.PREPARE_WORKSPACE:
                await self._prepare_workspace()
                self._transition_to(RunState.IMPLEMENTER_RUNNING)

            elif state == RunState.IMPLEMENTER_RUNNING:
                await self._run_implementer()
                self._transition_to(RunState.COMMIT_PUSH_PR)

            elif state == RunState.COMMIT_PUSH_PR:
                await self._commit_push_pr()
                self._transition_to(RunState.REVIEWER_RUNNING)

            elif state == RunState.REVIEWER_RUNNING:
                verdict = await self._run_reviewer()
                if verdict == "approved":
                    self._transition_to(RunState.APPROVED)
                    event = run_approved_event(
                        self._snapshot.run_id, self._snapshot.iteration
                    )
                    self._emit_event(event)
                else:
                    self._transition_to(RunState.CHANGES_REQUESTED)

            elif state == RunState.CHANGES_REQUESTED:
                self._snapshot.iteration += 1
                self._transition_to(
                    RunState.IMPLEMENTER_RUNNING,
                    reason=f"Iteration {self._snapshot.iteration}: addressing requested changes",
                )

        except Exception as e:
            self._handle_failure(str(e))

    def _handle_failure(self, reason: str) -> None:
        """Handle a failure by transitioning to FAILED state."""
        if not self._snapshot:
            return

        self._snapshot.failure_reason = reason
        self._transition_to(RunState.FAILED, reason=reason)

        event = run_failed_event(self._snapshot.run_id, reason)
        self._emit_event(event)

    async def _prepare_workspace(self) -> None:
        """Prepare the git worktree for the run."""
        if not self._snapshot or not self._artifacts or not self._persistence:
            raise RuntimeError("No active run")

        worktree_path = self._persistence.worktree_path()

        # Idempotent: skip if worktree already exists
        if worktree_path.exists():
            self._artifacts.worktree_path = str(worktree_path)
            self._snapshot.worktree_path = str(worktree_path)
            self._save_artifacts()
            self._save_snapshot()
            return

        await self.git_service.create_worktree(
            self.config.repo_root,
            worktree_path,
            self._snapshot.branch,
            self.config.base_branch,
        )

        self._artifacts.worktree_path = str(worktree_path)
        self._snapshot.worktree_path = str(worktree_path)
        self._save_artifacts()
        self._save_snapshot()

    async def _run_implementer(self) -> None:
        """Run the implementer agent."""
        if not self._snapshot or not self._persistence:
            raise RuntimeError("No active run")

        worktree_path = Path(self._snapshot.worktree_path or "")
        if not worktree_path.exists():
            raise RuntimeError("Worktree does not exist")

        # Import schemas here to avoid circular imports
        from textual_tui.orchestrator.agents.schemas import IMPLEMENTER_SCHEMA

        # Build the prompt
        prompt = self._build_implementer_prompt()
        self._persistence.save_implementer_prompt(prompt)
        self._persistence.save_implementer_schema(IMPLEMENTER_SCHEMA)

        schema_path = self._persistence.schemas_dir / "implementer.json"
        output_path = self._persistence.run_dir / "implementer_output.json"

        def on_line(stream: str, line: str) -> None:
            from textual_tui.orchestrator.events import process_line_event
            event = process_line_event(
                self._snapshot.run_id, "implementer", stream, line
            )
            self._emit_event(event)

        try:
            result = await self.implementer_driver.run(
                worktree_path=worktree_path,
                prompt=prompt,
                schema=IMPLEMENTER_SCHEMA,
                schema_path=schema_path,
                output_path=output_path,
                timeout=self.config.implementer_timeout,
                on_line=on_line,
            )
        except TimeoutError:
            raise RuntimeError(
                f"Implementer timed out after {self.config.implementer_timeout}s"
            )
        except AgentError as e:
            raise RuntimeError(f"Implementer failed: {e}")

        # Update snapshot with implementer results
        self._snapshot.last_implementer_summary = result.get("summary", "")
        self._snapshot.last_implementer_tests = [
            TestResult(
                command=t.get("command", ""),
                result=t.get("result", "not_run"),
                notes=t.get("notes", ""),
            )
            for t in result.get("tests", [])
        ]
        self._save_snapshot()

        # Store commit message for later
        self._commit_message = result.get("commit_message", "Agent changes")

    async def _commit_push_pr(self) -> None:
        """Commit changes, push, and create/update PR."""
        if not self._snapshot or not self._artifacts or not self._persistence:
            raise RuntimeError("No active run")

        worktree_path = Path(self._snapshot.worktree_path or "")

        # Check for changes
        has_changes = await self.git_service.has_changes(worktree_path)
        if not has_changes:
            raise RuntimeError("Implementer made no changes")

        # Commit
        commit_message = getattr(self, "_commit_message", "Agent changes")
        commit_sha = await self.git_service.commit_all(worktree_path, commit_message)
        self._artifacts.last_commit_sha = commit_sha

        # Push
        await self.git_service.push(worktree_path, self._snapshot.branch)

        # Create or find PR
        existing_pr = await self.github_service.find_pr(self._snapshot.branch)
        if existing_pr:
            pr_number, pr_url = existing_pr
        else:
            title = f"Vibe Orchestrator: {self._snapshot.slug}"
            body = f"Run: {self._snapshot.run_id}\n\nTask:\n{self._snapshot.task}"
            pr_number, pr_url = await self.github_service.create_pr(
                branch=self._snapshot.branch,
                base_branch=self.config.base_branch,
                title=title,
                body=body,
            )

        self._artifacts.pr_number = pr_number
        self._artifacts.pr_url = pr_url
        self._snapshot.pr_number = pr_number
        self._snapshot.pr_url = pr_url
        self._save_artifacts()
        self._save_snapshot()

        # Create or update coordination comment
        await self._update_coordination_comment()

    async def _update_coordination_comment(self) -> None:
        """Create or update the canonical coordination comment."""
        if not self._snapshot or not self._artifacts:
            raise RuntimeError("No active run")

        if not self._artifacts.pr_number:
            return

        import json

        body_data = {
            "run_id": self._snapshot.run_id,
            "iteration": self._snapshot.iteration,
            "state": self._snapshot.state.value,
            "implementer_summary": self._snapshot.last_implementer_summary,
            "reviewer_verdict": self._snapshot.last_reviewer_verdict,
            "requested_changes": [
                {
                    "id": c.id,
                    "path": c.path,
                    "description": c.description,
                    "acceptance": c.acceptance,
                }
                for c in self._snapshot.last_requested_changes
            ],
        }

        body = f"[vibe-orch v1][run:{self._snapshot.run_id}]\n\n```json\n{json.dumps(body_data, indent=2)}\n```"

        if self._artifacts.coord_comment_id:
            await self.github_service.update_comment(
                self._artifacts.coord_comment_id, body
            )
        else:
            comment_id = await self.github_service.create_comment(
                self._artifacts.pr_number, body
            )
            self._artifacts.coord_comment_id = comment_id
            self._snapshot.coord_comment_id = comment_id
            self._save_artifacts()
            self._save_snapshot()

    async def _run_reviewer(self) -> str:
        """Run the reviewer agent and return the verdict."""
        if not self._snapshot or not self._persistence:
            raise RuntimeError("No active run")

        worktree_path = Path(self._snapshot.worktree_path or "")
        if not worktree_path.exists():
            raise RuntimeError("Worktree does not exist")

        # Import schemas here to avoid circular imports
        from textual_tui.orchestrator.agents.schemas import REVIEWER_SCHEMA

        # Build the prompt
        prompt = await self._build_reviewer_prompt()
        self._persistence.save_reviewer_prompt(prompt)
        self._persistence.save_reviewer_schema(REVIEWER_SCHEMA)

        schema_path = self._persistence.schemas_dir / "reviewer.json"
        output_path = self._persistence.run_dir / "reviewer_output.json"

        def on_line(stream: str, line: str) -> None:
            from textual_tui.orchestrator.events import process_line_event
            event = process_line_event(
                self._snapshot.run_id, "reviewer", stream, line
            )
            self._emit_event(event)

        try:
            result = await self.reviewer_driver.run(
                worktree_path=worktree_path,
                prompt=prompt,
                schema=REVIEWER_SCHEMA,
                schema_path=schema_path,
                output_path=output_path,
                timeout=self.config.reviewer_timeout,
                on_line=on_line,
            )
        except TimeoutError:
            raise RuntimeError(
                f"Reviewer timed out after {self.config.reviewer_timeout}s"
            )
        except AgentError as e:
            raise RuntimeError(f"Reviewer failed: {e}")

        verdict = result.get("verdict", "changes_requested")
        self._snapshot.last_reviewer_verdict = verdict

        # Parse requested changes
        self._snapshot.last_requested_changes = [
            RequestedChange(
                id=c.get("id", ""),
                path=c.get("path", "*"),
                description=c.get("description", ""),
                acceptance=c.get("acceptance", ""),
            )
            for c in result.get("requested_changes", [])
        ]
        self._save_snapshot()

        # Update coordination comment with reviewer verdict
        await self._update_coordination_comment()

        return verdict

    def _build_implementer_prompt(self) -> str:
        """Build the prompt for the implementer agent."""
        if not self._snapshot:
            raise RuntimeError("No active run")

        prompt_parts = [
            "You are an implementer agent. Your task is to implement changes in a codebase.",
            "",
            "## Task",
            self._snapshot.task,
            "",
            "## Output Requirements",
            "You MUST output a valid JSON object with the following structure:",
            '- type: "implementer_result"',
            "- summary: A brief summary of the changes made",
            "- commit_message: A commit message for the changes",
            "- tests: Array of test results (command, result, notes)",
            "- notes: Array of additional notes",
            "",
            "## Rules",
            "- Do NOT run git or gh commands. The orchestrator handles git operations.",
            "- Make all necessary code changes directly.",
            "- Run relevant tests and report results.",
            "- Output ONLY valid JSON, no markdown or prose.",
        ]

        # Add requested changes if this is an iteration
        if self._snapshot.iteration > 0 and self._snapshot.last_requested_changes:
            prompt_parts.extend([
                "",
                "## Requested Changes to Address",
                "The reviewer has requested the following changes:",
            ])
            for change in self._snapshot.last_requested_changes:
                prompt_parts.extend([
                    f"",
                    f"### {change.id}: {change.path}",
                    f"**Description:** {change.description}",
                    f"**Acceptance criteria:** {change.acceptance}",
                ])

        return "\n".join(prompt_parts)

    async def _build_reviewer_prompt(self) -> str:
        """Build the prompt for the reviewer agent."""
        if not self._snapshot or not self._artifacts:
            raise RuntimeError("No active run")

        worktree_path = Path(self._snapshot.worktree_path or "")

        # Get diff stat
        diff_stat = await self.git_service.get_diff_stat(
            worktree_path, self.config.base_branch
        )

        # Get budgeted diff
        budgeted_diff = await self.git_service.get_budgeted_diff(
            worktree_path,
            self.config.base_branch,
            self.config.max_diff_files,
            self.config.max_diff_bytes,
            self.config.max_hunks_per_file,
        )

        prompt_parts = [
            "You are a code reviewer agent. Review the following changes and provide a verdict.",
            "",
            "## PR Information",
            f"PR URL: {self._artifacts.pr_url or 'Not yet created'}",
            "",
            "## Implementer Summary",
            self._snapshot.last_implementer_summary or "No summary provided",
            "",
            "## Test Results",
        ]

        if self._snapshot.last_implementer_tests:
            for test in self._snapshot.last_implementer_tests:
                prompt_parts.append(f"- {test.command}: {test.result}")
                if test.notes:
                    prompt_parts.append(f"  Notes: {test.notes}")
        else:
            prompt_parts.append("No tests reported")

        prompt_parts.extend([
            "",
            "## Diff Statistics",
            "```",
            diff_stat,
            "```",
            "",
            "## Code Changes",
            "```diff",
            budgeted_diff,
            "```",
            "",
            "## Output Requirements",
            "You MUST output a valid JSON object with the following structure:",
            '- type: "reviewer_result"',
            '- verdict: "approved" or "changes_requested"',
            "- requested_changes: Array of changes (empty if approved)",
            "  - id: Unique ID (e.g., C1, C2)",
            '  - path: File path or "*" for global',
            "  - description: What needs to change",
            "  - acceptance: Objective pass/fail criteria",
            "- notes: Array of additional notes",
            "",
            "## Rules",
            "- Do NOT run git or gh commands.",
            "- If verdict is approved, requested_changes MUST be empty.",
            "- Output ONLY valid JSON, no markdown or prose.",
        ])

        return "\n".join(prompt_parts)
