"""Custom widgets for the Vibe Orchestrator TUI.

Provides specialized widgets for:
- Log viewing (streaming from events.jsonl)
- Artifacts display
- Requested changes checklist
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static, Label, RichLog, DataTable


class LogView(Widget):
    """A widget for displaying streaming log output.

    Reads from events.jsonl and displays process output lines.
    """

    DEFAULT_CSS = """
    LogView {
        height: 100%;
        border: solid $primary;
    }

    LogView > RichLog {
        height: 100%;
    }

    LogView > .log-header {
        dock: top;
        height: 1;
        background: $primary;
        color: $text;
        padding: 0 1;
    }
    """

    def __init__(
        self,
        run_id: str = "",
        events_path: Path | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the log view.

        Args:
            run_id: The run ID for display.
            events_path: Path to events.jsonl file.
            **kwargs: Additional widget arguments.
        """
        super().__init__(**kwargs)
        self.run_id = run_id
        self.events_path = events_path
        self._last_line = 0

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Label(f"Logs: {self.run_id}", classes="log-header")
        yield RichLog(highlight=True, markup=True, wrap=True, id="log-content")

    def add_line(self, line: str, style: str = "") -> None:
        """Add a line to the log.

        Args:
            line: The line to add.
            style: Optional style (e.g., "bold red").
        """
        log = self.query_one("#log-content", RichLog)
        if style:
            log.write(f"[{style}]{line}[/{style}]")
        else:
            log.write(line)

    def add_event(self, event: dict[str, Any]) -> None:
        """Add an event to the log.

        Formats the event appropriately based on type.

        Args:
            event: Event dictionary.
        """
        event_type = event.get("type", "unknown")
        data = event.get("data", {})
        ts = event.get("ts", "")

        # Format timestamp for display
        ts_short = ts.split("T")[-1].split(".")[0] if "T" in ts else ts

        if event_type == "process_line":
            stream = data.get("stream", "stdout")
            line = data.get("line", "")
            style = "dim" if stream == "stderr" else ""
            self.add_line(f"[{ts_short}] {line}", style)

        elif event_type == "state_changed":
            from_state = data.get("from_state", "")
            to_state = data.get("to_state", "")
            self.add_line(f"[{ts_short}] State: {from_state} -> {to_state}", "bold cyan")

        elif event_type.startswith("agent_"):
            role = data.get("role", "agent")
            self.add_line(f"[{ts_short}] [{role}] {event_type}", "yellow")

        elif event_type.startswith("error") or event_type == "run_failed":
            message = data.get("message", data.get("reason", "Unknown error"))
            self.add_line(f"[{ts_short}] ERROR: {message}", "bold red")

        else:
            self.add_line(f"[{ts_short}] {event_type}", "dim")

    def refresh_from_file(self) -> None:
        """Refresh the log from the events file."""
        if not self.events_path or not self.events_path.exists():
            return

        import json

        with open(self.events_path, "r") as f:
            lines = f.readlines()

        for i, line in enumerate(lines[self._last_line:], start=self._last_line):
            try:
                event = json.loads(line.strip())
                self.add_event(event)
            except json.JSONDecodeError:
                pass

        self._last_line = len(lines)


class ArtifactsPanel(Widget):
    """A widget for displaying run artifacts.

    Shows branch, PR URL, commit SHA, etc.
    """

    DEFAULT_CSS = """
    ArtifactsPanel {
        height: auto;
        border: solid $secondary;
        padding: 1;
    }

    ArtifactsPanel > .artifact-header {
        text-style: bold;
        margin-bottom: 1;
    }

    ArtifactsPanel > .artifact-row {
        height: 1;
    }
    """

    branch: reactive[str] = reactive("")
    pr_url: reactive[str] = reactive("")
    pr_number: reactive[int | None] = reactive(None)
    last_commit: reactive[str] = reactive("")
    verdict: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Label("Artifacts", classes="artifact-header")
        yield Static(id="artifacts-content")

    def watch_branch(self, value: str) -> None:
        """Update display when branch changes."""
        self._update_content()

    def watch_pr_url(self, value: str) -> None:
        """Update display when PR URL changes."""
        self._update_content()

    def watch_verdict(self, value: str) -> None:
        """Update display when verdict changes."""
        self._update_content()

    def _update_content(self) -> None:
        """Update the content display."""
        lines = []

        if self.branch:
            lines.append(f"Branch: {self.branch}")

        if self.pr_url:
            lines.append(f"PR: {self.pr_url}")
        elif self.pr_number:
            lines.append(f"PR: #{self.pr_number}")

        if self.last_commit:
            lines.append(f"Commit: {self.last_commit[:8]}")

        if self.verdict:
            verdict_style = "green" if self.verdict == "approved" else "yellow"
            lines.append(f"Verdict: [{verdict_style}]{self.verdict}[/{verdict_style}]")

        content = self.query_one("#artifacts-content", Static)
        content.update("\n".join(lines) if lines else "No artifacts yet")

    def update_from_snapshot(self, snapshot: Any) -> None:
        """Update from a RunSnapshot.

        Args:
            snapshot: RunSnapshot object.
        """
        self.branch = snapshot.branch or ""
        self.pr_url = snapshot.pr_url or ""
        self.pr_number = snapshot.pr_number
        self.last_commit = ""  # Would need to load from artifacts
        self.verdict = snapshot.last_reviewer_verdict or ""


class RequestedChangesPanel(Widget):
    """A widget for displaying requested changes checklist.

    Shows changes requested by the reviewer (read-only).
    """

    DEFAULT_CSS = """
    RequestedChangesPanel {
        height: auto;
        min-height: 5;
        border: solid $warning;
        padding: 1;
    }

    RequestedChangesPanel > .changes-header {
        text-style: bold;
        margin-bottom: 1;
    }

    RequestedChangesPanel DataTable {
        height: auto;
        max-height: 15;
    }
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the panel."""
        super().__init__(**kwargs)
        self._changes: list[dict[str, str]] = []

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Label("Requested Changes", classes="changes-header")
        table = DataTable(id="changes-table")
        table.add_columns("ID", "Path", "Description")
        yield table

    def set_changes(self, changes: list[Any]) -> None:
        """Set the requested changes.

        Args:
            changes: List of RequestedChange objects or dicts.
        """
        table = self.query_one("#changes-table", DataTable)
        table.clear()

        for change in changes:
            if hasattr(change, "id"):
                # RequestedChange object
                table.add_row(change.id, change.path, change.description)
            else:
                # Dict
                table.add_row(
                    change.get("id", ""),
                    change.get("path", ""),
                    change.get("description", ""),
                )


class StateTimeline(Widget):
    """A widget for displaying the state timeline.

    Shows the progression of states for a run.
    """

    DEFAULT_CSS = """
    StateTimeline {
        height: 3;
        padding: 0 1;
    }

    StateTimeline > Horizontal {
        height: 100%;
        align: center middle;
    }

    StateTimeline .state-item {
        padding: 0 1;
        margin: 0 1;
    }

    StateTimeline .state-current {
        background: $primary;
        text-style: bold;
    }

    StateTimeline .state-completed {
        color: $success;
    }

    StateTimeline .state-pending {
        color: $text-muted;
    }

    StateTimeline .state-failed {
        color: $error;
    }
    """

    STATES = [
        "CREATED",
        "PREPARE_WORKSPACE",
        "IMPLEMENTER_RUNNING",
        "COMMIT_PUSH_PR",
        "REVIEWER_RUNNING",
    ]

    current_state: reactive[str] = reactive("CREATED")

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        with Horizontal():
            for state in self.STATES:
                short_name = self._short_state_name(state)
                yield Label(short_name, classes="state-item state-pending", id=f"state-{state}")

    def _short_state_name(self, state: str) -> str:
        """Get a short display name for a state."""
        names = {
            "CREATED": "Created",
            "PREPARE_WORKSPACE": "Prep",
            "IMPLEMENTER_RUNNING": "Impl",
            "COMMIT_PUSH_PR": "Push",
            "REVIEWER_RUNNING": "Review",
            "CHANGES_REQUESTED": "Changes",
            "APPROVED": "Done",
            "FAILED": "Failed",
            "CANCELLED": "Cancelled",
        }
        return names.get(state, state[:6])

    def watch_current_state(self, value: str) -> None:
        """Update display when current state changes."""
        # Find position of current state
        try:
            current_idx = self.STATES.index(value)
        except ValueError:
            current_idx = -1

        for i, state in enumerate(self.STATES):
            try:
                label = self.query_one(f"#state-{state}", Label)
                label.remove_class("state-current", "state-completed", "state-pending", "state-failed")

                if i < current_idx:
                    label.add_class("state-completed")
                elif i == current_idx:
                    label.add_class("state-current")
                else:
                    label.add_class("state-pending")
            except Exception:
                pass

        # Handle terminal states
        if value in ("FAILED", "CANCELLED"):
            # Mark last visible state as failed
            for state in reversed(self.STATES):
                try:
                    label = self.query_one(f"#state-{state}", Label)
                    if "state-current" in label.classes or "state-completed" in label.classes:
                        label.remove_class("state-current", "state-completed")
                        label.add_class("state-failed")
                        break
                except Exception:
                    pass


class RunListItem(Widget):
    """A widget for displaying a single run in the dashboard list."""

    DEFAULT_CSS = """
    RunListItem {
        height: 3;
        padding: 0 1;
        border-bottom: solid $surface;
    }

    RunListItem:hover {
        background: $surface;
    }

    RunListItem > Horizontal {
        height: 100%;
    }

    RunListItem .run-id {
        width: 24;
        color: $primary;
    }

    RunListItem .run-state {
        width: 16;
    }

    RunListItem .run-task {
        width: 1fr;
        overflow: hidden;
    }

    RunListItem .state-approved {
        color: $success;
    }

    RunListItem .state-failed {
        color: $error;
    }

    RunListItem .state-running {
        color: $warning;
    }
    """

    def __init__(
        self,
        run_id: str,
        state: str,
        task: str,
        **kwargs: Any,
    ) -> None:
        """Initialize the run list item.

        Args:
            run_id: Run ID.
            state: Current state.
            task: Task description (first line).
            **kwargs: Additional widget arguments.
        """
        super().__init__(**kwargs)
        self.run_id = run_id
        self.state = state
        self.task = task.split("\n")[0][:50]

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        state_class = self._state_class()
        with Horizontal():
            yield Label(self.run_id, classes="run-id")
            yield Label(self.state, classes=f"run-state {state_class}")
            yield Label(self.task, classes="run-task")

    def _state_class(self) -> str:
        """Get CSS class for current state."""
        if self.state == "APPROVED":
            return "state-approved"
        elif self.state in ("FAILED", "CANCELLED"):
            return "state-failed"
        elif self.state in ("IMPLEMENTER_RUNNING", "REVIEWER_RUNNING"):
            return "state-running"
        return ""
