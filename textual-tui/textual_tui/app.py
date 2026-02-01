"""Main Textual TUI application module for Vibe Orchestrator.

This module provides the entry point and main application class for the
Vibe Orchestrator TUI. The application provides a terminal-based interface
for managing the implement -> review -> iterate workflow using headless
coding agents (Claude Code and OpenAI Codex CLI).

Typical usage example:

    from textual_tui.app import VibeOrchestrator

    app = VibeOrchestrator()
    app.run()
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

from textual_tui.ui.screens import (
    DashboardScreen,
    NewRunScreen,
    RunDetailScreen,
)


class VibeOrchestrator(App):
    """Main TUI application for the Vibe Orchestrator.

    This application manages headless coding agent workflows:
    1. Create a new run with a task description
    2. Implementer agent edits code in an isolated worktree
    3. Orchestrator commits, pushes, and creates/updates a PR
    4. Reviewer agent reviews the changes
    5. Loop until the reviewer approves

    Attributes:
        BINDINGS: Key bindings for the application.
        SCREENS: Named screens for navigation.
        TITLE: Application title.
        SUB_TITLE: Application subtitle.
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "dashboard", "Dashboard"),
    ]

    SCREENS = {
        "dashboard": DashboardScreen,
    }

    TITLE = "Vibe Orchestrator"
    SUB_TITLE = "Headless Agent Workflow Manager"

    def __init__(self, repo_root: Path | None = None, **kwargs: Any) -> None:
        """Initialize the application.

        Args:
            repo_root: Root directory of the repository. Defaults to cwd.
            **kwargs: Additional arguments for the App base class.
        """
        super().__init__(**kwargs)
        self.repo_root = repo_root or Path.cwd()
        self._active_engine: Any = None

    def on_mount(self) -> None:
        """Handle mount event - show dashboard."""
        self.push_screen(DashboardScreen(repo_root=self.repo_root))

    def action_dashboard(self) -> None:
        """Switch to dashboard screen."""
        # Pop all screens and push dashboard
        while len(self.screen_stack) > 1:
            self.pop_screen()
        if not isinstance(self.screen, DashboardScreen):
            self.push_screen(DashboardScreen(repo_root=self.repo_root))

    @on(DashboardScreen.NewRunRequested)
    def on_new_run_requested(self, event: DashboardScreen.NewRunRequested) -> None:
        """Handle new run request from dashboard."""
        self.push_screen(NewRunScreen(repo_root=self.repo_root))

    @on(DashboardScreen.RunSelected)
    def on_run_selected(self, event: DashboardScreen.RunSelected) -> None:
        """Handle run selection from dashboard."""
        self.push_screen(
            RunDetailScreen(run_id=event.run_id, repo_root=self.repo_root)
        )

    @on(NewRunScreen.RunStarted)
    def on_run_started(self, event: NewRunScreen.RunStarted) -> None:
        """Handle run started from new run screen."""
        self.pop_screen()  # Pop NewRunScreen
        self.push_screen(
            RunDetailScreen(run_id=event.run_id, repo_root=self.repo_root)
        )
        # Start the run asynchronously
        asyncio.create_task(self._start_run(event.run_id))

    @on(NewRunScreen.Cancelled)
    def on_new_run_cancelled(self, event: NewRunScreen.Cancelled) -> None:
        """Handle cancellation from new run screen."""
        self.pop_screen()

    @on(RunDetailScreen.BackRequested)
    def on_back_requested(self, event: RunDetailScreen.BackRequested) -> None:
        """Handle back request from run detail screen."""
        self.pop_screen()

    @on(RunDetailScreen.CancelRunRequested)
    def on_cancel_run_requested(
        self, event: RunDetailScreen.CancelRunRequested
    ) -> None:
        """Handle run cancellation request."""
        if self._active_engine:
            self._active_engine.cancel()
            self.notify(f"Cancelling run {event.run_id}...")

    @on(RunDetailScreen.ResumeRunRequested)
    def on_resume_run_requested(
        self, event: RunDetailScreen.ResumeRunRequested
    ) -> None:
        """Handle run resume request."""
        asyncio.create_task(self._resume_run(event.run_id))

    async def _start_run(self, run_id: str) -> None:
        """Start a run asynchronously.

        Args:
            run_id: The run ID to start.
        """
        from textual_tui.orchestrator.engine import OrchestrationEngine, EngineConfig
        from textual_tui.orchestrator.git_service import GitService
        from textual_tui.orchestrator.gh_service import GitHubService
        from textual_tui.orchestrator.agents.claude_driver import ClaudeDriver
        from textual_tui.orchestrator.agents.base import AgentRole

        try:
            config = EngineConfig(repo_root=self.repo_root)
            git_service = GitService()
            github_service = GitHubService(self.repo_root)

            # Create drivers
            implementer = ClaudeDriver(role=AgentRole.IMPLEMENTER)
            reviewer = ClaudeDriver(role=AgentRole.REVIEWER)

            engine = OrchestrationEngine(
                config=config,
                git_service=git_service,
                github_service=github_service,
                implementer_driver=implementer,
                reviewer_driver=reviewer,
                on_event=self._on_engine_event,
            )

            self._active_engine = engine
            await engine.load_run(run_id)
            final_state = await engine.run()

            self.notify(f"Run completed: {final_state.value}")

        except Exception as e:
            self.notify(f"Run failed: {e}", severity="error")
        finally:
            self._active_engine = None

    async def _resume_run(self, run_id: str) -> None:
        """Resume a run asynchronously.

        Args:
            run_id: The run ID to resume.
        """
        # Same as _start_run - engine handles resume internally
        await self._start_run(run_id)

    def _on_engine_event(self, event: Any) -> None:
        """Handle events from the orchestration engine.

        Args:
            event: The event from the engine.
        """
        # The RunDetailScreen will auto-refresh from events.jsonl
        # We can add additional handling here if needed
        pass


# Keep the old class name for backward compatibility
VibeTUI = VibeOrchestrator


def main() -> None:
    """Application entry point.

    This function serves as the main entry point for the vibe-tui command-line
    tool. It instantiates the VibeOrchestrator application and starts the
    Textual event loop.

    Example:
        From the command line::

            $ vibe-tui

        Or directly from Python::

            from textual_tui.app import main
            main()
    """
    app = VibeOrchestrator()
    app.run()


if __name__ == "__main__":
    main()
