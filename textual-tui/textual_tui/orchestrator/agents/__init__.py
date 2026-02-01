"""Agent drivers for the Vibe-O-Matic orchestrator.

This package provides drivers for interacting with headless agent CLIs:
- Claude Code CLI (claude -p)
- OpenAI Codex CLI (codex exec)
"""

from textual_tui.orchestrator.agents.base import AgentDriver, AgentRole
from textual_tui.orchestrator.agents.codex_driver import CodexDriver
from textual_tui.orchestrator.agents.claude_driver import ClaudeDriver
from textual_tui.orchestrator.agents.schemas import (
    IMPLEMENTER_SCHEMA,
    REVIEWER_SCHEMA,
)
from textual_tui.orchestrator.agents.validation import (
    validate_implementer_output,
    validate_reviewer_output,
)

__all__ = [
    "AgentDriver",
    "AgentRole",
    "CodexDriver",
    "ClaudeDriver",
    "IMPLEMENTER_SCHEMA",
    "REVIEWER_SCHEMA",
    "validate_implementer_output",
    "validate_reviewer_output",
]
