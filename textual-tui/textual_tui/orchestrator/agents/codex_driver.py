"""Codex CLI driver.

Implements the agent driver for OpenAI's Codex CLI.

CLI invocation:
    codex exec --full-auto --output-schema <schema_path> --output-last-message <out_path> -

The prompt is sent via stdin (the `-` argument reads from stdin).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from textual_tui.orchestrator.agents.base import AgentDriver, AgentRole


class CodexDriver(AgentDriver):
    """Driver for the OpenAI Codex CLI."""

    def __init__(
        self,
        executable: str | None = None,
        role: AgentRole = AgentRole.IMPLEMENTER,
    ):
        """Initialize the Codex driver.

        Args:
            executable: Path to the codex executable (default: "codex").
            role: The role this driver is fulfilling.
        """
        super().__init__(executable, role)

    @property
    def default_executable(self) -> str:
        """Default executable name."""
        return "codex"

    @property
    def agent_name(self) -> str:
        """Human-readable agent name."""
        return "Codex"

    def build_command(
        self,
        prompt: str,
        schema: dict[str, Any],
        schema_path: Path,
        output_path: Path,
    ) -> tuple[list[str], str | None]:
        """Build the Codex CLI command.

        Args:
            prompt: The prompt to send to the agent.
            schema: JSON Schema for output validation.
            schema_path: Path to schema file for CLI.
            output_path: Path for agent to write output.

        Returns:
            Tuple of (command args, stdin data).
        """
        args = [
            self.executable,
            "exec",
            "--full-auto",
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(output_path),
            "-",  # Read prompt from stdin
        ]

        return args, prompt

    def extract_output(
        self,
        stdout: str,
        stderr: str,
        output_path: Path,
    ) -> str:
        """Extract output from the Codex result.

        Codex writes the final JSON to --output-last-message path.

        Args:
            stdout: Process stdout.
            stderr: Process stderr.
            output_path: Path where agent wrote output.

        Returns:
            The raw output string.
        """
        if output_path.exists():
            return output_path.read_text()

        # Fallback to stdout if file doesn't exist
        return stdout.strip()
