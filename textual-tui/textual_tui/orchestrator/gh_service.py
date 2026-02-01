"""GitHub service for PR and comment operations.

All GitHub operations use the `gh` CLI. No direct API calls.
"""

from __future__ import annotations

import json
from pathlib import Path

from textual_tui.orchestrator.subprocess_runner import run_command_simple


class GitHubError(Exception):
    """Raised when a GitHub operation fails."""

    pass


GH_TIMEOUT = 120  # 2 minutes


class GitHubService:
    """Service for GitHub operations via gh CLI.

    Handles PR creation/lookup and coordination comment management.
    """

    def __init__(
        self,
        repo_root: Path,
        timeout: int = GH_TIMEOUT,
    ):
        """Initialize the GitHub service.

        Args:
            repo_root: Repository root directory.
            timeout: Timeout for gh commands in seconds.
        """
        self.repo_root = repo_root
        self.timeout = timeout
        self._name_with_owner: str | None = None

    async def _run_gh(
        self,
        args: list[str],
    ) -> str:
        """Run a gh command and return stdout.

        Args:
            args: gh command arguments (without 'gh').

        Returns:
            stdout output.

        Raises:
            GitHubError: If the command fails.
        """
        full_args = ["gh"] + args
        exit_code, stdout, stderr = await run_command_simple(
            full_args, cwd=self.repo_root, timeout=self.timeout
        )

        if exit_code != 0:
            raise GitHubError(f"gh {' '.join(args)} failed: {stderr}")

        return stdout

    async def get_repo_name_with_owner(self) -> str:
        """Get the repository name with owner (e.g., 'owner/repo').

        Returns:
            The nameWithOwner string.

        Raises:
            GitHubError: If unable to determine repo.
        """
        if self._name_with_owner:
            return self._name_with_owner

        output = await self._run_gh(
            ["repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"]
        )
        self._name_with_owner = output.strip()
        return self._name_with_owner

    async def find_pr(self, branch: str) -> tuple[int, str] | None:
        """Find an existing PR for a branch.

        Args:
            branch: Branch name to search for.

        Returns:
            Tuple of (pr_number, pr_url) or None if not found.
        """
        try:
            output = await self._run_gh(
                [
                    "pr",
                    "list",
                    "--head",
                    branch,
                    "--state",
                    "open",
                    "--json",
                    "number,url",
                    "--jq",
                    ".[0]",
                ]
            )
        except GitHubError:
            return None

        output = output.strip()
        if not output:
            return None

        try:
            data = json.loads(output)
            if data and "number" in data and "url" in data:
                return (data["number"], data["url"])
        except json.JSONDecodeError:
            pass

        return None

    async def create_pr(
        self,
        branch: str,
        base_branch: str,
        title: str,
        body: str,
    ) -> tuple[int, str]:
        """Create a pull request.

        Args:
            branch: Head branch.
            base_branch: Base branch.
            title: PR title.
            body: PR body.

        Returns:
            Tuple of (pr_number, pr_url).

        Raises:
            GitHubError: If PR creation fails.
        """
        output = await self._run_gh(
            [
                "pr",
                "create",
                "--head",
                branch,
                "--base",
                base_branch,
                "--title",
                title,
                "--body",
                body,
                "--json",
                "number,url",
            ]
        )

        try:
            data = json.loads(output.strip())
            return (data["number"], data["url"])
        except (json.JSONDecodeError, KeyError) as e:
            raise GitHubError(f"Failed to parse PR creation response: {e}")

    async def create_comment(
        self,
        pr_number: int,
        body: str,
    ) -> int:
        """Create a comment on a PR.

        Uses the GitHub Issues Comment API via gh api for reliable comment IDs.

        Args:
            pr_number: PR number.
            body: Comment body.

        Returns:
            The comment ID.

        Raises:
            GitHubError: If comment creation fails.
        """
        name_with_owner = await self.get_repo_name_with_owner()

        output = await self._run_gh(
            [
                "api",
                "-X",
                "POST",
                f"repos/{name_with_owner}/issues/{pr_number}/comments",
                "-f",
                f"body={body}",
            ]
        )

        try:
            data = json.loads(output.strip())
            return data["id"]
        except (json.JSONDecodeError, KeyError) as e:
            raise GitHubError(f"Failed to parse comment creation response: {e}")

    async def update_comment(
        self,
        comment_id: int,
        body: str,
    ) -> None:
        """Update an existing comment.

        Args:
            comment_id: Comment ID to update.
            body: New comment body.

        Raises:
            GitHubError: If comment update fails.
        """
        name_with_owner = await self.get_repo_name_with_owner()

        await self._run_gh(
            [
                "api",
                "-X",
                "PATCH",
                f"repos/{name_with_owner}/issues/comments/{comment_id}",
                "-f",
                f"body={body}",
            ]
        )


class FakeGitHubService:
    """Fake GitHub service for testing.

    Simulates GitHub operations without making real API calls.
    """

    def __init__(self):
        """Initialize the fake service."""
        self.prs: dict[str, tuple[int, str]] = {}  # branch -> (number, url)
        self.comments: dict[int, str] = {}  # comment_id -> body
        self._next_pr_number = 1
        self._next_comment_id = 1

    async def find_pr(self, branch: str) -> tuple[int, str] | None:
        """Find a PR by branch."""
        return self.prs.get(branch)

    async def create_pr(
        self,
        branch: str,
        base_branch: str,
        title: str,
        body: str,
    ) -> tuple[int, str]:
        """Create a fake PR."""
        pr_number = self._next_pr_number
        self._next_pr_number += 1
        pr_url = f"https://github.com/test/repo/pull/{pr_number}"
        self.prs[branch] = (pr_number, pr_url)
        return (pr_number, pr_url)

    async def create_comment(
        self,
        pr_number: int,
        body: str,
    ) -> int:
        """Create a fake comment."""
        comment_id = self._next_comment_id
        self._next_comment_id += 1
        self.comments[comment_id] = body
        return comment_id

    async def update_comment(
        self,
        comment_id: int,
        body: str,
    ) -> None:
        """Update a fake comment."""
        if comment_id not in self.comments:
            raise GitHubError(f"Comment {comment_id} not found")
        self.comments[comment_id] = body
