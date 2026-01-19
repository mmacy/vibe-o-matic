"""Tests for the main Textual TUI application."""

import pytest
from textual.widgets import Header, Footer

from textual_tui.app import VibeTUI


@pytest.mark.asyncio
async def test_app_initialization():
    """Test that the app can be instantiated."""
    app = VibeTUI()
    assert app is not None
    assert isinstance(app, VibeTUI)


@pytest.mark.asyncio
async def test_app_composition():
    """Test that the app composes the expected widgets."""
    app = VibeTUI()
    async with app.run_test() as pilot:
        # Verify Header widget is present
        header = app.query_one(Header)
        assert header is not None
        assert isinstance(header, Header)

        # Verify Footer widget is present
        footer = app.query_one(Footer)
        assert footer is not None
        assert isinstance(footer, Footer)


@pytest.mark.asyncio
async def test_app_quit_binding():
    """Test that pressing 'q' quits the application."""
    app = VibeTUI()
    async with app.run_test() as pilot:
        assert app.is_running

        # Press 'q' to quit
        await pilot.press("q")
        await pilot.pause()

        # App should no longer be running
        assert not app.is_running


@pytest.mark.asyncio
async def test_app_has_bindings():
    """Test that the app has the expected key bindings."""
    app = VibeTUI()

    # Check that 'q' binding exists and maps to quit
    # BINDINGS is a list of tuples: (key, action, description)
    bindings = {binding[0]: binding[1] for binding in app.BINDINGS}
    assert "q" in bindings
    assert bindings["q"] == "quit"


@pytest.mark.asyncio
async def test_app_widgets_are_mounted():
    """Test that widgets are properly mounted in the DOM."""
    app = VibeTUI()
    async with app.run_test() as pilot:
        # Wait for app to be fully mounted
        await pilot.pause()

        # Check that Header and Footer widgets exist
        headers = app.query(Header)
        footers = app.query(Footer)
        assert len(headers) == 1
        assert len(footers) == 1

        # Verify they're in the expected order
        all_widgets = list(app.query("*"))
        header_idx = next(i for i, w in enumerate(all_widgets) if isinstance(w, Header))
        footer_idx = next(i for i, w in enumerate(all_widgets) if isinstance(w, Footer))
        assert header_idx < footer_idx
