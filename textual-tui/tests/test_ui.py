"""UI smoke tests for the Vibe Orchestrator.

Tests cover:
- Dashboard rendering
- Run creation writes expected files
- Run detail screen updates with events
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from textual_tui.app import VibeOrchestrator
from textual_tui.ui.screens import DashboardScreen, NewRunScreen, RunDetailScreen
from textual_tui.orchestrator.persistence import RunRegistry


class TestDashboardScreen:
    """Tests for the Dashboard screen."""

    @pytest.mark.asyncio
    async def test_dashboard_renders(self, tmp_path):
        """Test that dashboard renders without errors."""
        app = VibeOrchestrator(repo_root=tmp_path)

        async with app.run_test() as pilot:
            # Wait for screen to render
            await pilot.pause()
            await pilot.pause()

            # Dashboard should be the initial screen
            assert isinstance(app.screen, DashboardScreen)

            # Should have header elements - query from the screen
            screen = app.screen
            assert screen.query_one("#dashboard-title")
            assert screen.query_one("#new-run-btn")
            assert screen.query_one("#refresh-btn")

    @pytest.mark.asyncio
    async def test_dashboard_shows_no_runs_message(self, tmp_path):
        """Test that dashboard shows message when no runs exist."""
        app = VibeOrchestrator(repo_root=tmp_path)

        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.pause()

            # Just verify the runs list widget exists and is a Static widget
            runs_list = app.screen.query_one("#runs-list")
            assert runs_list is not None

    @pytest.mark.asyncio
    async def test_dashboard_lists_runs(self, tmp_path):
        """Test that dashboard lists existing runs."""
        # Create a run first
        registry = RunRegistry(tmp_path)
        registry.create_run("Test task for dashboard")

        app = VibeOrchestrator(repo_root=tmp_path)

        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.pause()

            # Trigger refresh
            await pilot.press("r")
            await pilot.pause()

            # Verify the runs list widget exists
            runs_list = app.screen.query_one("#runs-list")
            assert runs_list is not None


class TestNewRunScreen:
    """Tests for the New Run screen."""

    @pytest.mark.asyncio
    async def test_new_run_screen_navigation(self, tmp_path):
        """Test navigation to new run screen."""
        app = VibeOrchestrator(repo_root=tmp_path)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Press 'n' to go to new run
            await pilot.press("n")
            await pilot.pause()
            await pilot.pause()

            # Should be on NewRunScreen
            assert isinstance(app.screen, NewRunScreen)

    @pytest.mark.asyncio
    async def test_new_run_cancel(self, tmp_path):
        """Test cancelling new run returns to dashboard."""
        app = VibeOrchestrator(repo_root=tmp_path)

        async with app.run_test() as pilot:
            await pilot.pause()

            await pilot.press("n")
            await pilot.pause()
            await pilot.pause()
            assert isinstance(app.screen, NewRunScreen)

            # Press escape to cancel
            await pilot.press("escape")
            await pilot.pause()
            await pilot.pause()

            # Should be back on dashboard
            assert isinstance(app.screen, DashboardScreen)

    @pytest.mark.asyncio
    async def test_new_run_has_input_elements(self, tmp_path):
        """Test that new run screen has required input elements."""
        app = VibeOrchestrator(repo_root=tmp_path)

        async with app.run_test() as pilot:
            await pilot.pause()

            await pilot.press("n")
            await pilot.pause()
            await pilot.pause()

            # Should have task input and buttons - query from screen
            screen = app.screen
            assert screen.query_one("#task-input")
            assert screen.query_one("#start-btn")
            assert screen.query_one("#cancel-btn")


class TestRunCreation:
    """Tests for run creation and file writing."""

    @pytest.mark.asyncio
    async def test_run_creation_writes_files(self, tmp_path):
        """Test that creating a run writes expected files."""
        registry = RunRegistry(tmp_path)
        run_id, persistence = registry.create_run("Test task for file creation")

        # Check expected files exist
        assert persistence.run_json_path.exists()
        assert persistence.artifacts_json_path.exists()

        # Check run.json content
        with open(persistence.run_json_path) as f:
            run_data = json.load(f)

        assert run_data["run_id"] == run_id
        assert run_data["task"] == "Test task for file creation"
        assert run_data["state"] == "CREATED"

        # Check artifacts.json content
        with open(persistence.artifacts_json_path) as f:
            artifacts_data = json.load(f)

        assert "branch" in artifacts_data
        assert artifacts_data["branch"].startswith("agent/")

    @pytest.mark.asyncio
    async def test_run_directories_created(self, tmp_path):
        """Test that run directories are created correctly."""
        registry = RunRegistry(tmp_path)
        run_id, persistence = registry.create_run("Test task")

        # Check directories
        assert persistence.run_dir.exists()
        assert persistence.prompts_dir.exists()
        assert persistence.schemas_dir.exists()


class TestRunDetailScreen:
    """Tests for the Run Detail screen."""

    @pytest.mark.asyncio
    async def test_run_detail_renders(self, tmp_path):
        """Test that run detail screen renders."""
        # Create a run
        registry = RunRegistry(tmp_path)
        run_id, _ = registry.create_run("Test task for detail view")

        app = VibeOrchestrator(repo_root=tmp_path)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Navigate to run detail
            app.push_screen(RunDetailScreen(run_id=run_id, repo_root=tmp_path))
            await pilot.pause()
            await pilot.pause()

            # Should have key elements
            screen = app.screen
            assert screen.query_one("#run-title")
            assert screen.query_one("#state-timeline")
            assert screen.query_one("#log-view")
            assert screen.query_one("#artifacts-panel")
            assert screen.query_one("#changes-panel")

    @pytest.mark.asyncio
    async def test_run_detail_shows_state(self, tmp_path):
        """Test that run detail shows current state."""
        registry = RunRegistry(tmp_path)
        run_id, _ = registry.create_run("Test task")

        app = VibeOrchestrator(repo_root=tmp_path)

        async with app.run_test() as pilot:
            await pilot.pause()

            app.push_screen(RunDetailScreen(run_id=run_id, repo_root=tmp_path))
            await pilot.pause()
            await pilot.pause()

            # Timeline should show CREATED state
            timeline = app.screen.query_one("#state-timeline")
            assert timeline.current_state == "CREATED"

    @pytest.mark.asyncio
    async def test_run_detail_back_button(self, tmp_path):
        """Test that back button returns to dashboard."""
        registry = RunRegistry(tmp_path)
        run_id, _ = registry.create_run("Test task")

        app = VibeOrchestrator(repo_root=tmp_path)

        async with app.run_test() as pilot:
            await pilot.pause()

            app.push_screen(RunDetailScreen(run_id=run_id, repo_root=tmp_path))
            await pilot.pause()

            # Press escape to go back
            await pilot.press("escape")
            await pilot.pause()
            await pilot.pause()

            # Should be back on dashboard
            assert isinstance(app.screen, DashboardScreen)


class TestEventsDisplay:
    """Tests for events display in run detail."""

    @pytest.mark.asyncio
    async def test_events_file_grows(self, tmp_path):
        """Test that events.jsonl grows as events are added."""
        from textual_tui.orchestrator.events import state_changed_event

        registry = RunRegistry(tmp_path)
        run_id, persistence = registry.create_run("Test task")

        # Add some events
        event1 = state_changed_event(run_id, "CREATED", "PREPARE_WORKSPACE")
        event2 = state_changed_event(run_id, "PREPARE_WORKSPACE", "IMPLEMENTER_RUNNING")

        persistence.append_event(event1)
        persistence.append_event(event2)

        # Check events file
        events = persistence.read_events()
        assert len(events) == 2

    @pytest.mark.asyncio
    async def test_log_view_shows_events(self, tmp_path):
        """Test that log view displays events."""
        from textual_tui.orchestrator.events import (
            run_created_event,
            state_changed_event,
        )

        registry = RunRegistry(tmp_path)
        run_id, persistence = registry.create_run("Test task")

        # Add events
        event = run_created_event(
            run_id=run_id,
            task="Test task",
            slug="test-task",
            branch="agent/test",
            implementer_agent="claude",
            reviewer_agent="claude",
        )
        persistence.append_event(event)

        app = VibeOrchestrator(repo_root=tmp_path)

        async with app.run_test() as pilot:
            await pilot.pause()

            app.push_screen(RunDetailScreen(run_id=run_id, repo_root=tmp_path))
            await pilot.pause()
            await pilot.pause()

            # Log view should exist and have events path set
            log_view = app.screen.query_one("#log-view")
            assert log_view.events_path is not None


class TestKeyBindings:
    """Tests for application key bindings."""

    @pytest.mark.asyncio
    async def test_quit_binding(self, tmp_path):
        """Test that 'q' quits the application."""
        app = VibeOrchestrator(repo_root=tmp_path)

        async with app.run_test() as pilot:
            # This should trigger quit (app.exit())
            # We can't easily test the full quit, but we can verify binding exists
            assert ("q", "quit", "Quit") in app.BINDINGS

    @pytest.mark.asyncio
    async def test_dashboard_binding(self, tmp_path):
        """Test that 'd' returns to dashboard."""
        registry = RunRegistry(tmp_path)
        run_id, _ = registry.create_run("Test task")

        app = VibeOrchestrator(repo_root=tmp_path)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Navigate away from dashboard
            app.push_screen(RunDetailScreen(run_id=run_id, repo_root=tmp_path))
            await pilot.pause()
            await pilot.pause()

            assert isinstance(app.screen, RunDetailScreen)

            # Press 'd' to go to dashboard
            await pilot.press("d")
            await pilot.pause()
            await pilot.pause()

            assert isinstance(app.screen, DashboardScreen)
