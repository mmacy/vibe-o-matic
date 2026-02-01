"""Git service for worktree, commit, push, and diff operations.

All git operations are owned by the orchestrator, not the agents.
"""

from __future__ import annotations

from pathlib import Path

from textual_tui.orchestrator.subprocess_runner import run_command_simple


class GitError(Exception):
    """Raised when a git operation fails."""

    pass


GIT_TIMEOUT = 120  # 2 minutes


class GitService:
    """Service for git operations.

    Handles worktree creation, commits, pushes, and diff extraction.
    """

    def __init__(self, timeout: int = GIT_TIMEOUT):
        """Initialize the git service.

        Args:
            timeout: Timeout for git commands in seconds.
        """
        self.timeout = timeout

    async def _run_git(
        self,
        args: list[str],
        cwd: Path | None = None,
    ) -> str:
        """Run a git command and return stdout.

        Args:
            args: Git command arguments (without 'git').
            cwd: Working directory.

        Returns:
            stdout output.

        Raises:
            GitError: If the command fails.
        """
        full_args = ["git"] + args
        exit_code, stdout, stderr = await run_command_simple(
            full_args, cwd=cwd, timeout=self.timeout
        )

        if exit_code != 0:
            raise GitError(f"git {' '.join(args)} failed: {stderr}")

        return stdout

    async def verify_base_branch(self, repo_root: Path, base_branch: str) -> None:
        """Verify the base branch exists locally.

        Args:
            repo_root: Repository root directory.
            base_branch: Branch name to verify.

        Raises:
            GitError: If branch does not exist.
        """
        try:
            await self._run_git(
                ["rev-parse", "--verify", base_branch],
                cwd=repo_root,
            )
        except GitError:
            raise GitError(f"Base branch '{base_branch}' does not exist locally")

    async def verify_remote(self, repo_root: Path, remote: str) -> None:
        """Verify the remote exists.

        Args:
            repo_root: Repository root directory.
            remote: Remote name to verify.

        Raises:
            GitError: If remote does not exist.
        """
        try:
            await self._run_git(
                ["remote", "get-url", remote],
                cwd=repo_root,
            )
        except GitError:
            raise GitError(f"Remote '{remote}' does not exist")

    async def create_worktree(
        self,
        repo_root: Path,
        worktree_path: Path,
        branch: str,
        base_branch: str,
    ) -> None:
        """Create a git worktree for the run.

        Args:
            repo_root: Repository root directory.
            worktree_path: Path for the new worktree.
            branch: Branch name to create.
            base_branch: Base branch to branch from.

        Raises:
            GitError: If worktree creation fails.
        """
        # Ensure parent directory exists
        worktree_path.parent.mkdir(parents=True, exist_ok=True)

        # Create worktree with new branch
        await self._run_git(
            ["worktree", "add", "-b", branch, str(worktree_path), base_branch],
            cwd=repo_root,
        )

    async def has_changes(self, worktree_path: Path) -> bool:
        """Check if worktree has uncommitted changes.

        Args:
            worktree_path: Path to the worktree.

        Returns:
            True if there are uncommitted changes.
        """
        output = await self._run_git(
            ["status", "--porcelain"],
            cwd=worktree_path,
        )
        return bool(output.strip())

    async def commit_all(
        self,
        worktree_path: Path,
        message: str,
    ) -> str:
        """Stage all changes and commit.

        Args:
            worktree_path: Path to the worktree.
            message: Commit message.

        Returns:
            The commit SHA.

        Raises:
            GitError: If commit fails.
        """
        # Stage all changes
        await self._run_git(["add", "-A"], cwd=worktree_path)

        # Commit
        await self._run_git(["commit", "-m", message], cwd=worktree_path)

        # Get the commit SHA
        sha = await self._run_git(
            ["rev-parse", "HEAD"],
            cwd=worktree_path,
        )
        return sha.strip()

    async def push(
        self,
        worktree_path: Path,
        branch: str,
        remote: str = "origin",
    ) -> None:
        """Push branch to remote.

        Args:
            worktree_path: Path to the worktree.
            branch: Branch name to push.
            remote: Remote name (default: origin).

        Raises:
            GitError: If push fails.
        """
        await self._run_git(
            ["push", "-u", remote, branch],
            cwd=worktree_path,
        )

    async def get_diff_stat(
        self,
        worktree_path: Path,
        base_branch: str,
    ) -> str:
        """Get diff --stat output.

        Args:
            worktree_path: Path to the worktree.
            base_branch: Base branch to diff against.

        Returns:
            The diff stat output.
        """
        return await self._run_git(
            ["diff", "--stat", f"{base_branch}...HEAD"],
            cwd=worktree_path,
        )

    async def get_changed_files(
        self,
        worktree_path: Path,
        base_branch: str,
    ) -> list[str]:
        """Get list of changed files.

        Args:
            worktree_path: Path to the worktree.
            base_branch: Base branch to diff against.

        Returns:
            List of changed file paths, sorted.
        """
        output = await self._run_git(
            ["diff", "--name-only", f"{base_branch}...HEAD"],
            cwd=worktree_path,
        )
        files = [f.strip() for f in output.strip().split("\n") if f.strip()]
        return sorted(files)

    async def get_file_diff(
        self,
        worktree_path: Path,
        base_branch: str,
        file_path: str,
    ) -> str:
        """Get unified diff for a single file.

        Args:
            worktree_path: Path to the worktree.
            base_branch: Base branch to diff against.
            file_path: Path to the file.

        Returns:
            The unified diff output.
        """
        return await self._run_git(
            ["diff", "-U3", f"{base_branch}...HEAD", "--", file_path],
            cwd=worktree_path,
        )

    async def get_budgeted_diff(
        self,
        worktree_path: Path,
        base_branch: str,
        max_files: int = 25,
        max_bytes: int = 200_000,
        max_hunks_per_file: int = 8,
    ) -> str:
        """Get budgeted unified diff.

        Applies the diff budget algorithm:
        1. Get at most max_files files
        2. For each file, limit to max_hunks_per_file hunks
        3. Stop accumulating when total bytes would exceed max_bytes

        Args:
            worktree_path: Path to the worktree.
            base_branch: Base branch to diff against.
            max_files: Maximum number of files to include.
            max_bytes: Maximum total diff bytes.
            max_hunks_per_file: Maximum hunks per file.

        Returns:
            The budgeted diff output.
        """
        files = await self.get_changed_files(worktree_path, base_branch)

        result_parts = []
        total_bytes = 0
        files_included = 0
        omitted_files = 0

        if len(files) > max_files:
            omitted_files = len(files) - max_files
            files = files[:max_files]

        for file_path in files:
            diff = await self.get_file_diff(worktree_path, base_branch, file_path)

            # Truncate hunks if needed
            truncated_diff = self._truncate_hunks(diff, max_hunks_per_file)

            # Check if adding this would exceed budget
            diff_bytes = len(truncated_diff.encode("utf-8"))
            if total_bytes + diff_bytes > max_bytes:
                result_parts.append("\n[TRUNCATED_DIFF_BUDGET]\n")
                break

            result_parts.append(truncated_diff)
            total_bytes += diff_bytes
            files_included += 1

        if omitted_files > 0:
            result_parts.insert(0, f"OMITTED_FILES_COUNT={omitted_files}\n\n")

        return "".join(result_parts)

    def _truncate_hunks(self, diff: str, max_hunks: int) -> str:
        """Truncate diff to max_hunks hunks.

        Args:
            diff: The full diff output.
            max_hunks: Maximum number of hunks to keep.

        Returns:
            Truncated diff.
        """
        lines = diff.split("\n")
        result_lines = []
        hunk_count = 0

        for line in lines:
            if line.startswith("@@"):
                hunk_count += 1
                if hunk_count > max_hunks:
                    result_lines.append("[TRUNCATED_HUNKS]")
                    break

            result_lines.append(line)

        return "\n".join(result_lines)
