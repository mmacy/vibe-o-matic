"""UI package for the Vibe-O-Matic Textual TUI.

This package provides the Textual screens and widgets for the orchestrator UI:
- Dashboard: List runs, create new run, open run detail
- NewRun: Text area for task input
- RunDetail: Shows state, logs, artifacts, requested changes
"""

from textual_tui.ui.screens import DashboardScreen, NewRunScreen, RunDetailScreen
from textual_tui.ui.widgets import LogView, ArtifactsPanel, RequestedChangesPanel

__all__ = [
    "DashboardScreen",
    "NewRunScreen",
    "RunDetailScreen",
    "LogView",
    "ArtifactsPanel",
    "RequestedChangesPanel",
]
