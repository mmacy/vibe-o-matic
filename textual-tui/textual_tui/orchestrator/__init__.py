"""Orchestrator package for the Vibe-O-Matic TUI.

This package implements the headless agent orchestration system that manages
the implement -> review -> iterate workflow using Claude Code and Codex CLIs.
"""

from textual_tui.orchestrator.engine import OrchestrationEngine, RunState
from textual_tui.orchestrator.persistence import RunPersistence
from textual_tui.orchestrator.events import Event, EventType

__all__ = [
    "OrchestrationEngine",
    "RunState",
    "RunPersistence",
    "Event",
    "EventType",
]
