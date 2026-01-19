"""Unit tests for the main Textual TUI application.

This test module provides comprehensive testing coverage for the VibeTUI application
class and its core functionality. Tests use Textual's async test harness to verify
widget composition, key bindings, and application lifecycle.

The test suite covers:
- Application initialization and instantiation
- Widget composition and DOM structure
- Key binding configuration and behavior
- Widget mounting and rendering order

All tests are asynchronous and use pytest-asyncio markers to properly handle
Textual's async event loop during testing.

Example:
    Run the test suite::

        $ pytest tests/test_app.py -v

    Run a specific test::

        $ pytest tests/test_app.py::test_app_initialization -v
"""

import pytest
from textual.widgets import Footer, Header

from textual_tui.app import VibeTUI


@pytest.mark.asyncio
async def test_app_initialization():
    """Test that the VibeTUI app can be instantiated.

    Verifies that the VibeTUI class can be successfully instantiated without
    errors and that the resulting object is of the correct type. This is a
    basic smoke test to ensure the application class is properly configured.

    This test does not start the application's event loop, it only verifies
    that the class constructor works correctly.
    """
    app = VibeTUI()
    assert app is not None
    assert isinstance(app, VibeTUI)


@pytest.mark.asyncio
async def test_app_composition():
    """Test that the app composes the expected widgets.

    Verifies that the compose() method yields the correct widgets in the
    application's widget tree. The app should contain exactly one Header
    widget and one Footer widget.

    This test uses Textual's run_test() context manager to start the app
    in test mode, which allows querying the widget tree without requiring
    a real terminal.

    The test validates:
    - Header widget exists and is of correct type
    - Footer widget exists and is of correct type
    - Widgets can be queried from the DOM
    """
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
    """Test that pressing 'q' quits the application.

    Verifies that the key binding for quitting the application works as expected.
    When the user presses 'q', the application should gracefully shut down and
    stop running.

    This test simulates user input using Textual's Pilot interface, which allows
    programmatic interaction with the running app during tests.

    The test validates:
    - App is running after startup
    - Pressing 'q' triggers the quit action
    - App is no longer running after quit
    """
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
    """Test that the app has the expected key bindings configured.

    Verifies that the BINDINGS class attribute is correctly configured with
    the expected key mappings. This test checks the binding configuration
    without actually running the application.

    The BINDINGS attribute is a list of tuples in the format:
    (key, action, description)

    This test validates:
    - The 'q' key is bound
    - The 'q' key maps to the 'quit' action

    Note:
        This test accesses BINDINGS directly as a class attribute. BINDINGS
        is a list of tuples, not binding objects, so we access elements by
        index: binding[0] is key, binding[1] is action, binding[2] is description.
    """
    app = VibeTUI()

    # Check that 'q' binding exists and maps to quit
    # BINDINGS is a list of tuples: (key, action, description)
    bindings = {binding[0]: binding[1] for binding in app.BINDINGS}
    assert "q" in bindings
    assert bindings["q"] == "quit"


@pytest.mark.asyncio
async def test_app_widgets_are_mounted():
    """Test that widgets are properly mounted in the DOM.

    Verifies that all expected widgets are correctly mounted in the application's
    DOM tree and appear in the expected order. This ensures the widget hierarchy
    is properly constructed when the app starts.

    The test validates:
    - Exactly one Header widget is mounted
    - Exactly one Footer widget is mounted
    - Header appears before Footer in the DOM tree

    The widget order matters for both rendering and accessibility, so this test
    ensures the UI structure matches expectations.
    """
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
