"""Main Textual TUI application."""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer


class VibeTUI(App):
    """A Textual TUI application for vibe-o-matic."""

    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()


def main() -> None:
    """Run the application."""
    app = VibeTUI()
    app.run()


if __name__ == "__main__":
    main()
