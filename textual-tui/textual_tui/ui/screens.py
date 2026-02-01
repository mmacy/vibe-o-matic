"""Screens for the Vibe Orchestrator TUI.

Provides three screens:
- DashboardScreen: List runs and create new ones
- NewRunScreen: Enter task description and start a run
- RunDetailScreen: View run state, logs, artifacts, and changes
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Callable

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.message import Message
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Label,
    Static,
    TextArea,
    ListView,
    ListItem,
)

from textual_tui.ui.widgets import (
    LogView,
    ArtifactsPanel,
    RequestedChangesPanel,
    StateTimeline,
    RunListItem,
)


class DashboardScreen(Screen):
    """Dashboard screen for listing and managing runs."""

    BINDINGS = [
        ("n", "new_run", "New Run"),
        ("r", "refresh", "Refresh"),
        ("q", "quit", "Quit"),
    ]

    DEFAULT_CSS = """
    DashboardScreen {
        layout: vertical;
    }

    DashboardScreen #dashboard-header {
        dock: top;
        height: 3;
        padding: 1;
        background: $surface;
    }

    DashboardScreen #dashboard-title {
        text-style: bold;
        width: 1fr;
    }

    DashboardScreen #runs-container {
        height: 1fr;
        padding: 1;
    }

    DashboardScreen #no-runs {
        text-align: center;
        padding: 2;
        color: $text-muted;
    }

    DashboardScreen .action-button {
        margin: 0 1;
    }
    """

    class RunSelected(Message):
        """Message when a run is selected."""

        def __init__(self, run_id: str) -> None:
            super().__init__()
            self.run_id = run_id

    class NewRunRequested(Message):
        """Message when new run is requested."""

        pass

    def __init__(
        self,
        repo_root: Path | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the dashboard.

        Args:
            repo_root: Repository root directory.
            **kwargs: Additional screen arguments.
        """
        super().__init__(**kwargs)
        self.repo_root = repo_root or Path.cwd()
        self._runs: list[Any] = []

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        yield Header()

        with Horizontal(id="dashboard-header"):
            yield Label("Vibe Orchestrator", id="dashboard-title")
            yield Button("New Run", id="new-run-btn", variant="primary", classes="action-button")
            yield Button("Refresh", id="refresh-btn", classes="action-button")

        with ScrollableContainer(id="runs-container"):
            yield Static("Loading runs...", id="runs-list")

        yield Footer()

    def on_mount(self) -> None:
        """Handle mount event."""
        self.refresh_runs()

    def action_new_run(self) -> None:
        """Handle new run action."""
        self.post_message(self.NewRunRequested())

    def action_refresh(self) -> None:
        """Handle refresh action."""
        self.refresh_runs()

    @on(Button.Pressed, "#new-run-btn")
    def on_new_run_button(self) -> None:
        """Handle new run button."""
        self.post_message(self.NewRunRequested())

    @on(Button.Pressed, "#refresh-btn")
    def on_refresh_button(self) -> None:
        """Handle refresh button."""
        self.refresh_runs()

    def refresh_runs(self) -> None:
        """Refresh the runs list."""
        from textual_tui.orchestrator.persistence import RunRegistry

        registry = RunRegistry(self.repo_root)
        self._runs = registry.list_runs()

        runs_container = self.query_one("#runs-container", ScrollableContainer)
        runs_list = self.query_one("#runs-list", Static)

        if not self._runs:
            runs_list.update("No runs found. Click 'New Run' to start.")
        else:
            # Build runs display
            lines = []
            for run in self._runs:
                state_indicator = self._state_indicator(run.state.value)
                task_preview = run.task.split("\n")[0][:40]
                lines.append(
                    f"{state_indicator} {run.run_id} | {run.state.value:20} | {task_preview}"
                )
            runs_list.update("\n".join(lines))

    def _state_indicator(self, state: str) -> str:
        """Get state indicator character."""
        indicators = {
            "APPROVED": "[green]v[/]",
            "FAILED": "[red]x[/]",
            "CANCELLED": "[yellow]-[/]",
            "IMPLEMENTER_RUNNING": "[yellow]>[/]",
            "REVIEWER_RUNNING": "[yellow]>[/]",
        }
        return indicators.get(state, "[dim]o[/]")


class NewRunScreen(Screen):
    """Screen for creating a new run."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+s", "start_run", "Start Run"),
    ]

    DEFAULT_CSS = """
    NewRunScreen {
        layout: vertical;
        align: center middle;
    }

    NewRunScreen #new-run-container {
        width: 80%;
        height: 80%;
        border: solid $primary;
        padding: 2;
    }

    NewRunScreen #task-label {
        margin-bottom: 1;
        text-style: bold;
    }

    NewRunScreen #task-input {
        height: 1fr;
        margin-bottom: 1;
    }

    NewRunScreen #button-row {
        height: 3;
        align: center middle;
    }

    NewRunScreen .action-button {
        margin: 0 1;
    }
    """

    class RunStarted(Message):
        """Message when a run is started."""

        def __init__(self, run_id: str, task: str) -> None:
            super().__init__()
            self.run_id = run_id
            self.task = task

    class Cancelled(Message):
        """Message when screen is cancelled."""

        pass

    def __init__(
        self,
        repo_root: Path | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the new run screen.

        Args:
            repo_root: Repository root directory.
            **kwargs: Additional screen arguments.
        """
        super().__init__(**kwargs)
        self.repo_root = repo_root or Path.cwd()

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        yield Header()

        with Container(id="new-run-container"):
            yield Label("Enter Task Description", id="task-label")
            yield TextArea(id="task-input", language="markdown")

            with Horizontal(id="button-row"):
                yield Button("Start Run", id="start-btn", variant="primary", classes="action-button")
                yield Button("Cancel", id="cancel-btn", classes="action-button")

        yield Footer()

    def action_cancel(self) -> None:
        """Handle cancel action."""
        self.post_message(self.Cancelled())

    def action_start_run(self) -> None:
        """Handle start run action."""
        self._start_run()

    @on(Button.Pressed, "#start-btn")
    def on_start_button(self) -> None:
        """Handle start button."""
        self._start_run()

    @on(Button.Pressed, "#cancel-btn")
    def on_cancel_button(self) -> None:
        """Handle cancel button."""
        self.post_message(self.Cancelled())

    def _start_run(self) -> None:
        """Start a new run with the entered task."""
        task_input = self.query_one("#task-input", TextArea)
        task = task_input.text.strip()

        if not task:
            self.notify("Please enter a task description", severity="error")
            return

        from textual_tui.orchestrator.persistence import RunRegistry

        registry = RunRegistry(self.repo_root)
        run_id, _ = registry.create_run(task)

        self.post_message(self.RunStarted(run_id=run_id, task=task))


class RunDetailScreen(Screen):
    """Screen for viewing run details."""

    BINDINGS = [
        ("escape", "back", "Back"),
        ("c", "cancel_run", "Cancel Run"),
        ("r", "resume_run", "Resume Run"),
    ]

    DEFAULT_CSS = """
    RunDetailScreen {
        layout: vertical;
    }

    RunDetailScreen #detail-header {
        dock: top;
        height: auto;
        padding: 1;
        background: $surface;
    }

    RunDetailScreen #run-title {
        text-style: bold;
        margin-bottom: 1;
    }

    RunDetailScreen #main-content {
        layout: horizontal;
        height: 1fr;
    }

    RunDetailScreen #left-panel {
        width: 70%;
        height: 100%;
        padding: 1;
    }

    RunDetailScreen #right-panel {
        width: 30%;
        height: 100%;
        padding: 1;
        border-left: solid $surface;
    }

    RunDetailScreen #button-row {
        dock: bottom;
        height: 3;
        padding: 0 1;
        background: $surface;
    }

    RunDetailScreen .action-button {
        margin: 0 1;
    }
    """

    class BackRequested(Message):
        """Message when back is requested."""

        pass

    class CancelRunRequested(Message):
        """Message when run cancellation is requested."""

        def __init__(self, run_id: str) -> None:
            super().__init__()
            self.run_id = run_id

    class ResumeRunRequested(Message):
        """Message when run resume is requested."""

        def __init__(self, run_id: str) -> None:
            super().__init__()
            self.run_id = run_id

    def __init__(
        self,
        run_id: str,
        repo_root: Path | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the run detail screen.

        Args:
            run_id: The run ID to display.
            repo_root: Repository root directory.
            **kwargs: Additional screen arguments.
        """
        super().__init__(**kwargs)
        self.run_id = run_id
        self.repo_root = repo_root or Path.cwd()
        self._snapshot: Any = None
        self._refresh_task: asyncio.Task | None = None

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        yield Header()

        with Container(id="detail-header"):
            yield Label(f"Run: {self.run_id}", id="run-title")
            yield StateTimeline(id="state-timeline")

        with Horizontal(id="main-content"):
            with Vertical(id="left-panel"):
                yield LogView(run_id=self.run_id, id="log-view")

            with Vertical(id="right-panel"):
                yield ArtifactsPanel(id="artifacts-panel")
                yield RequestedChangesPanel(id="changes-panel")

        with Horizontal(id="button-row"):
            yield Button("Back", id="back-btn", classes="action-button")
            yield Button("Cancel Run", id="cancel-btn", variant="error", classes="action-button")
            yield Button("Resume Run", id="resume-btn", variant="primary", classes="action-button")

        yield Footer()

    def on_mount(self) -> None:
        """Handle mount event."""
        self._load_run()
        self._start_refresh()

    def on_unmount(self) -> None:
        """Handle unmount event."""
        self._stop_refresh()

    def _load_run(self) -> None:
        """Load run data."""
        from textual_tui.orchestrator.persistence import RunPersistence

        persistence = RunPersistence(self.repo_root, self.run_id)
        self._snapshot = persistence.load_snapshot()

        if self._snapshot:
            # Update timeline
            timeline = self.query_one("#state-timeline", StateTimeline)
            timeline.current_state = self._snapshot.state.value

            # Update artifacts
            artifacts = self.query_one("#artifacts-panel", ArtifactsPanel)
            artifacts.update_from_snapshot(self._snapshot)

            # Update changes
            changes = self.query_one("#changes-panel", RequestedChangesPanel)
            changes.set_changes(self._snapshot.last_requested_changes)

            # Set up log view
            log_view = self.query_one("#log-view", LogView)
            log_view.events_path = persistence.events_jsonl_path
            log_view.refresh_from_file()

            # Update button states
            self._update_buttons()

    def _update_buttons(self) -> None:
        """Update button states based on run state."""
        if not self._snapshot:
            return

        is_terminal = self._snapshot.state.is_terminal
        is_running = self._snapshot.state.value in (
            "IMPLEMENTER_RUNNING",
            "REVIEWER_RUNNING",
            "PREPARE_WORKSPACE",
            "COMMIT_PUSH_PR",
        )

        cancel_btn = self.query_one("#cancel-btn", Button)
        resume_btn = self.query_one("#resume-btn", Button)

        cancel_btn.disabled = is_terminal
        resume_btn.disabled = is_terminal or is_running

    def _start_refresh(self) -> None:
        """Start auto-refresh task."""
        async def refresh_loop() -> None:
            while True:
                await asyncio.sleep(2)
                self._load_run()

        self._refresh_task = asyncio.create_task(refresh_loop())

    def _stop_refresh(self) -> None:
        """Stop auto-refresh task."""
        if self._refresh_task:
            self._refresh_task.cancel()
            self._refresh_task = None

    def action_back(self) -> None:
        """Handle back action."""
        self.post_message(self.BackRequested())

    def action_cancel_run(self) -> None:
        """Handle cancel run action."""
        if self._snapshot and not self._snapshot.state.is_terminal:
            self.post_message(self.CancelRunRequested(self.run_id))

    def action_resume_run(self) -> None:
        """Handle resume run action."""
        if self._snapshot and not self._snapshot.state.is_terminal:
            self.post_message(self.ResumeRunRequested(self.run_id))

    @on(Button.Pressed, "#back-btn")
    def on_back_button(self) -> None:
        """Handle back button."""
        self.post_message(self.BackRequested())

    @on(Button.Pressed, "#cancel-btn")
    def on_cancel_button(self) -> None:
        """Handle cancel button."""
        self.action_cancel_run()

    @on(Button.Pressed, "#resume-btn")
    def on_resume_button(self) -> None:
        """Handle resume button."""
        self.action_resume_run()
