"""Async subprocess runner with cancellation support.

Provides utilities for running external processes with:
- Concurrent stdout/stderr reading
- Process group management on POSIX
- Graceful cancellation (SIGTERM, wait, SIGKILL)
- Timeout support
"""

from __future__ import annotations

import asyncio
import os
import signal
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass
class ProcessResult:
    """Result of running a subprocess."""

    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False


class SubprocessRunner:
    """Runs subprocesses with cancellation and streaming support."""

    def __init__(
        self,
        on_stdout_line: Callable[[str], None] | None = None,
        on_stderr_line: Callable[[str], None] | None = None,
    ):
        """Initialize the runner.

        Args:
            on_stdout_line: Callback for each stdout line.
            on_stderr_line: Callback for each stderr line.
        """
        self.on_stdout_line = on_stdout_line
        self.on_stderr_line = on_stderr_line
        self._process: asyncio.subprocess.Process | None = None
        self._cancelled = False

    def cancel(self) -> None:
        """Request cancellation of the running process."""
        self._cancelled = True

    async def run(
        self,
        args: list[str],
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
        timeout: int | None = None,
        stdin_data: str | None = None,
    ) -> ProcessResult:
        """Run a subprocess.

        Args:
            args: Command and arguments.
            cwd: Working directory.
            env: Environment variables (merged with current env).
            timeout: Timeout in seconds.
            stdin_data: Data to write to stdin.

        Returns:
            ProcessResult with exit code and captured output.

        Raises:
            TimeoutError: If the process exceeds the timeout.
        """
        self._cancelled = False

        # Merge environment
        process_env = os.environ.copy()
        if env:
            process_env.update(env)

        # Prepare kwargs for subprocess creation
        kwargs: dict = {
            "stdout": asyncio.subprocess.PIPE,
            "stderr": asyncio.subprocess.PIPE,
            "stdin": asyncio.subprocess.PIPE if stdin_data else None,
            "env": process_env,
        }

        if cwd:
            kwargs["cwd"] = str(cwd)

        # On POSIX, start in a new process group for clean termination
        if sys.platform != "win32":
            kwargs["start_new_session"] = True

        self._process = await asyncio.create_subprocess_exec(*args, **kwargs)

        stdout_lines: list[str] = []
        stderr_lines: list[str] = []

        async def read_stream(
            stream: asyncio.StreamReader | None,
            lines: list[str],
            callback: Callable[[str], None] | None,
        ) -> None:
            """Read lines from a stream."""
            if not stream:
                return
            while True:
                try:
                    line = await stream.readline()
                    if not line:
                        break
                    decoded = line.decode("utf-8", errors="replace").rstrip("\n\r")
                    lines.append(decoded)
                    if callback:
                        callback(decoded)
                except Exception:
                    break

        async def write_stdin() -> None:
            """Write data to stdin."""
            if stdin_data and self._process and self._process.stdin:
                try:
                    self._process.stdin.write(stdin_data.encode("utf-8"))
                    await self._process.stdin.drain()
                    self._process.stdin.close()
                    await self._process.stdin.wait_closed()
                except Exception:
                    pass

        async def wait_with_timeout() -> int:
            """Wait for process with timeout and cancellation support."""
            if not self._process:
                return -1

            # Start reading and writing tasks
            tasks = [
                asyncio.create_task(
                    read_stream(
                        self._process.stdout, stdout_lines, self.on_stdout_line
                    )
                ),
                asyncio.create_task(
                    read_stream(
                        self._process.stderr, stderr_lines, self.on_stderr_line
                    )
                ),
            ]

            if stdin_data:
                tasks.append(asyncio.create_task(write_stdin()))

            try:
                # Wait for process with timeout
                if timeout:
                    exit_code = await asyncio.wait_for(
                        self._process.wait(), timeout=timeout
                    )
                else:
                    exit_code = await self._process.wait()

                # Wait for stream readers to finish
                await asyncio.gather(*tasks, return_exceptions=True)

                return exit_code

            except asyncio.TimeoutError:
                await self._terminate_process()
                raise TimeoutError(f"Process timed out after {timeout}s")

            except asyncio.CancelledError:
                await self._terminate_process()
                raise

        try:
            exit_code = await wait_with_timeout()
            return ProcessResult(
                exit_code=exit_code,
                stdout="\n".join(stdout_lines),
                stderr="\n".join(stderr_lines),
                timed_out=False,
            )
        except TimeoutError:
            return ProcessResult(
                exit_code=-1,
                stdout="\n".join(stdout_lines),
                stderr="\n".join(stderr_lines),
                timed_out=True,
            )

    async def _terminate_process(self) -> None:
        """Terminate the process gracefully, then forcefully if needed."""
        if not self._process:
            return

        # Send SIGTERM (or terminate on Windows)
        try:
            if sys.platform == "win32":
                self._process.terminate()
            else:
                # Kill the entire process group
                os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
        except (ProcessLookupError, OSError):
            return

        # Wait up to 5 seconds for graceful termination
        try:
            await asyncio.wait_for(self._process.wait(), timeout=5.0)
            return
        except asyncio.TimeoutError:
            pass

        # Force kill
        try:
            if sys.platform == "win32":
                self._process.kill()
            else:
                os.killpg(os.getpgid(self._process.pid), signal.SIGKILL)
        except (ProcessLookupError, OSError):
            pass

        # Wait for process to die
        try:
            await asyncio.wait_for(self._process.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            pass


async def run_command(
    args: list[str],
    cwd: Path | None = None,
    timeout: int = 120,
    on_stdout: Callable[[str], None] | None = None,
    on_stderr: Callable[[str], None] | None = None,
    stdin_data: str | None = None,
) -> ProcessResult:
    """Convenience function to run a command.

    Args:
        args: Command and arguments.
        cwd: Working directory.
        timeout: Timeout in seconds (default 120).
        on_stdout: Callback for stdout lines.
        on_stderr: Callback for stderr lines.
        stdin_data: Data to write to stdin.

    Returns:
        ProcessResult with exit code and captured output.
    """
    runner = SubprocessRunner(on_stdout_line=on_stdout, on_stderr_line=on_stderr)
    return await runner.run(args, cwd=cwd, timeout=timeout, stdin_data=stdin_data)


async def run_command_simple(
    args: list[str],
    cwd: Path | None = None,
    timeout: int = 120,
) -> tuple[int, str, str]:
    """Run a command and return (exit_code, stdout, stderr).

    Args:
        args: Command and arguments.
        cwd: Working directory.
        timeout: Timeout in seconds.

    Returns:
        Tuple of (exit_code, stdout, stderr).
    """
    result = await run_command(args, cwd=cwd, timeout=timeout)
    return result.exit_code, result.stdout, result.stderr
