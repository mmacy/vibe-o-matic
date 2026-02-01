"""Base agent driver interface.

Defines the common interface for all agent drivers (Claude, Codex).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Callable


class AgentRole(str, Enum):
    """Role of an agent in the orchestration."""

    IMPLEMENTER = "implementer"
    REVIEWER = "reviewer"


class AgentError(Exception):
    """Raised when an agent fails."""

    def __init__(self, message: str, raw_output: str | None = None):
        super().__init__(message)
        self.raw_output = raw_output


class AgentDriver(ABC):
    """Abstract base class for agent drivers.

    An agent driver is responsible for:
    - Building the CLI command for the agent
    - Running the agent subprocess
    - Parsing and validating the output
    - Handling repair retry on validation failure
    """

    def __init__(
        self,
        executable: str | None = None,
        role: AgentRole = AgentRole.IMPLEMENTER,
    ):
        """Initialize the driver.

        Args:
            executable: Path to the CLI executable (uses default if None).
            role: The role this driver is fulfilling.
        """
        self.executable = executable or self.default_executable
        self.role = role

    @property
    @abstractmethod
    def default_executable(self) -> str:
        """Default executable name for this agent."""
        ...

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Human-readable name of the agent."""
        ...

    @abstractmethod
    def build_command(
        self,
        prompt: str,
        schema: dict[str, Any],
        schema_path: Path,
        output_path: Path,
    ) -> tuple[list[str], str | None]:
        """Build the command to run the agent.

        Args:
            prompt: The prompt to send to the agent.
            schema: JSON Schema for output validation.
            schema_path: Path to schema file for CLI.
            output_path: Path for agent to write output.

        Returns:
            Tuple of (command args, stdin data or None).
        """
        ...

    @abstractmethod
    def extract_output(
        self,
        stdout: str,
        stderr: str,
        output_path: Path,
    ) -> str:
        """Extract the agent's output from process results.

        Args:
            stdout: Process stdout.
            stderr: Process stderr.
            output_path: Path where agent may have written output.

        Returns:
            The raw output string to validate.
        """
        ...

    async def run(
        self,
        worktree_path: Path,
        prompt: str,
        schema: dict[str, Any],
        schema_path: Path,
        output_path: Path,
        timeout: int,
        on_line: Callable[[str, str], None] | None = None,
    ) -> dict[str, Any]:
        """Run the agent and return validated output.

        Args:
            worktree_path: Working directory for the agent.
            prompt: The prompt to send to the agent.
            schema: JSON Schema for output validation.
            schema_path: Path to schema file for CLI.
            output_path: Path for agent to write output.
            timeout: Timeout in seconds.
            on_line: Callback for each output line (stream, line).

        Returns:
            Validated output dictionary.

        Raises:
            AgentError: If agent fails or output is invalid after retry.
            TimeoutError: If agent exceeds timeout.
        """
        from textual_tui.orchestrator.subprocess_runner import SubprocessRunner
        from textual_tui.orchestrator.agents.validation import (
            validate_json_output,
            build_repair_prompt,
        )

        # Build command
        args, stdin_data = self.build_command(prompt, schema, schema_path, output_path)

        # Set up line callbacks
        def on_stdout(line: str) -> None:
            if on_line:
                on_line("stdout", line)

        def on_stderr(line: str) -> None:
            if on_line:
                on_line("stderr", line)

        # Run the agent
        runner = SubprocessRunner(
            on_stdout_line=on_stdout,
            on_stderr_line=on_stderr,
        )

        result = await runner.run(
            args=args,
            cwd=worktree_path,
            timeout=timeout,
            stdin_data=stdin_data,
        )

        if result.timed_out:
            raise TimeoutError(f"Agent timed out after {timeout}s")

        if result.exit_code != 0:
            raise AgentError(
                f"Agent exited with code {result.exit_code}: {result.stderr}",
                raw_output=result.stdout,
            )

        # Extract and validate output
        raw_output = self.extract_output(result.stdout, result.stderr, output_path)
        validation = validate_json_output(raw_output, schema)

        if validation.valid and validation.data:
            return validation.data

        # First attempt failed, try repair
        repair_prompt = build_repair_prompt(
            self.role.value,
            schema,
            raw_output,
            validation.error or "Unknown error",
        )

        repair_args, repair_stdin = self.build_command(
            repair_prompt, schema, schema_path, output_path
        )

        repair_result = await runner.run(
            args=repair_args,
            cwd=worktree_path,
            timeout=timeout,
            stdin_data=repair_stdin,
        )

        if repair_result.timed_out:
            raise TimeoutError(f"Agent repair timed out after {timeout}s")

        if repair_result.exit_code != 0:
            raise AgentError(
                f"Agent repair exited with code {repair_result.exit_code}",
                raw_output=repair_result.stdout,
            )

        repair_output = self.extract_output(
            repair_result.stdout, repair_result.stderr, output_path
        )
        repair_validation = validate_json_output(repair_output, schema)

        if repair_validation.valid and repair_validation.data:
            return repair_validation.data

        raise AgentError(
            f"Agent output invalid after repair: {repair_validation.error}",
            raw_output=repair_output,
        )
