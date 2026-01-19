"""Test suite for the textual-tui package.

This package contains the complete test suite for the vibe-o-matic Textual TUI
application. Tests are organized by module and use pytest with async support
for testing Textual applications.

Test modules:
    test_app: Tests for the main VibeTUI application class, including widget
        composition, key bindings, and application lifecycle.

Running tests:
    Run all tests::

        $ pytest tests/

    Run with coverage::

        $ pytest tests/ --cov=textual_tui

    Run in verbose mode::

        $ pytest tests/ -v
"""
