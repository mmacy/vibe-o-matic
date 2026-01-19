"""Main Textual TUI application module.

This module provides the entry point and main application class for the vibe-o-matic
Textual TUI. The application provides a terminal-based user interface for solo
tabletop RPG tools with keyboard navigation and rich formatting.

The VibeTUI class inherits from Textual's App class and implements the core
application structure. It currently provides a minimal scaffold with header and
footer widgets, ready for feature development.

Typical usage example:

    from textual_tui.app import VibeTUI

    app = VibeTUI()
    app.run()
"""

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header


class VibeTUI(App):
    """Main TUI application class for vibe-o-matic.

    This class represents the primary Textual application for vibe-o-matic's
    terminal user interface. It provides the application structure, widget
    composition, and key bindings for user interaction.

    The app currently implements a minimal interface with a header showing the
    current view and a footer displaying available key bindings. Additional
    widgets and functionality can be added by extending the compose() method
    and adding new screen classes.

    Attributes:
        BINDINGS: List of key binding tuples in the format (key, action, description).
            Currently includes:
            - 'q': Quit the application

    Example:
        Run the application programmatically::

            app = VibeTUI()
            app.run()
    """

    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        """Compose the application's widget tree.

        This method is called by Textual when the app starts to create the
        initial widget hierarchy. Widgets are yielded in the order they should
        appear in the DOM, from top to bottom.

        The current implementation provides a minimal scaffold:
        - Header: Displays the app title and current screen
        - Footer: Shows available key bindings

        Yields:
            Header: Application header widget at the top of the screen.
            Footer: Application footer widget at the bottom of the screen.

        Note:
            This is the starting point for building out the application's UI.
            Additional widgets like containers, input fields, or custom components
            should be yielded here as the application evolves.
        """
        yield Header()
        yield Footer()


def main() -> None:
    """Application entry point.

    This function serves as the main entry point for the vibe-tui command-line
    tool. It instantiates the VibeTUI application and starts the Textual event
    loop, which handles rendering and user input until the application exits.

    The function is registered as a console script entry point in pyproject.toml,
    making it available as the 'vibe-tui' command when the package is installed.

    Example:
        From the command line::

            $ vibe-tui

        Or directly from Python::

            from textual_tui.app import main
            main()
    """
    app = VibeTUI()
    app.run()


if __name__ == "__main__":
    main()
