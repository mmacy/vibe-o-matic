"""Claude Code CLI driver.

Implements the agent driver for Anthropic's Claude Code CLI.

CLI invocation:
    claude -p <prompt> --output-format json --json-schema <schema_json_string>

The output is JSON on stdout with a `structured_output` field.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from textual_tui.orchestrator.agents.base import AgentDriver, AgentRole, AgentError


class ClaudeDriver(AgentDriver):
    """Driver for the Claude Code CLI."""

    def __init__(
        self,
        executable: str | None = None,
        role: AgentRole = AgentRole.IMPLEMENTER,
    ):
        """Initialize the Claude driver.

        Args:
            executable: Path to the claude executable (default: "claude").
            role: The role this driver is fulfilling.
        """
        super().__init__(executable, role)

    @property
    def default_executable(self) -> str:
        """Default executable name."""
        return "claude"

    @property
    def agent_name(self) -> str:
        """Human-readable agent name."""
        return "Claude"

    def build_command(
        self,
        prompt: str,
        schema: dict[str, Any],
        schema_path: Path,
        output_path: Path,
    ) -> tuple[list[str], str | None]:
        """Build the Claude CLI command.

        Args:
            prompt: The prompt to send to the agent.
            schema: JSON Schema for output validation.
            schema_path: Path to schema file (not used, schema passed inline).
            output_path: Path for output (not used, output is on stdout).

        Returns:
            Tuple of (command args, None for stdin).
        """
        # Claude CLI takes the schema as a JSON string argument
        schema_json = json.dumps(schema)

        args = [
            self.executable,
            "-p",
            prompt,
            "--output-format",
            "json",
            "--json-schema",
            schema_json,
        ]

        return args, None

    def extract_output(
        self,
        stdout: str,
        stderr: str,
        output_path: Path,
    ) -> str:
        """Extract output from the Claude result.

        Claude outputs JSON on stdout with a `structured_output` field.

        Args:
            stdout: Process stdout containing the JSON response.
            stderr: Process stderr.
            output_path: Path (not used for Claude).

        Returns:
            The raw output string from structured_output.
        """
        try:
            response = json.loads(stdout)
            # Claude CLI wraps the output in a structured_output field
            if "structured_output" in response:
                structured = response["structured_output"]
                # If it's already a dict, serialize it
                if isinstance(structured, dict):
                    return json.dumps(structured)
                return str(structured)
            # Fallback: maybe the whole response is the output
            return stdout.strip()
        except json.JSONDecodeError:
            # If we can't parse, return raw stdout
            return stdout.strip()
