"""Unit and integration tests for the Vibe Orchestrator.

Tests cover:
- JSON Schema validation for implementer and reviewer outputs
- State machine transitions
- Diff budgeting/truncation behavior
- Agent driver integration with fixtures
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path

import pytest

from textual_tui.orchestrator.events import (
    Event,
    EventType,
    run_created_event,
    state_changed_event,
    process_line_event,
)
from textual_tui.orchestrator.persistence import (
    RunState,
    RunPersistence,
    RunRegistry,
    RunSnapshot,
    Artifacts,
    generate_run_id,
    generate_slug,
)
from textual_tui.orchestrator.agents.schemas import (
    IMPLEMENTER_SCHEMA,
    REVIEWER_SCHEMA,
)
from textual_tui.orchestrator.agents.validation import (
    validate_implementer_output,
    validate_reviewer_output,
    validate_json_output,
    build_repair_prompt,
)


# ============================================================================
# Schema Validation Tests
# ============================================================================


class TestImplementerSchemaValidation:
    """Tests for implementer output schema validation."""

    def test_valid_implementer_output(self):
        """Test validation of valid implementer output."""
        output = json.dumps({
            "type": "implementer_result",
            "summary": "Added new feature",
            "commit_message": "feat: add new feature",
            "tests": [
                {"command": "pytest", "result": "pass"},
                {"command": "npm test", "result": "pass", "notes": "All passed"},
            ],
            "notes": ["Everything works"],
        })

        result = validate_implementer_output(output)
        assert result.valid
        assert result.data is not None
        assert result.data["type"] == "implementer_result"

    def test_invalid_json(self):
        """Test validation of invalid JSON."""
        result = validate_implementer_output("not valid json")
        assert not result.valid
        assert "Invalid JSON" in result.error

    def test_missing_required_field(self):
        """Test validation with missing required field."""
        output = json.dumps({
            "type": "implementer_result",
            "summary": "Added new feature",
            # Missing commit_message
            "tests": [],
            "notes": [],
        })

        result = validate_implementer_output(output)
        assert not result.valid
        assert "commit_message" in result.error.lower() or "required" in result.error.lower()

    def test_invalid_test_result_value(self):
        """Test validation with invalid test result enum value."""
        output = json.dumps({
            "type": "implementer_result",
            "summary": "Added new feature",
            "commit_message": "feat: add new feature",
            "tests": [
                {"command": "pytest", "result": "invalid_value"},
            ],
            "notes": [],
        })

        result = validate_implementer_output(output)
        assert not result.valid

    def test_wrong_type_value(self):
        """Test validation with wrong type field value."""
        output = json.dumps({
            "type": "wrong_type",
            "summary": "Added new feature",
            "commit_message": "feat: add new feature",
            "tests": [],
            "notes": [],
        })

        result = validate_implementer_output(output)
        assert not result.valid


class TestReviewerSchemaValidation:
    """Tests for reviewer output schema validation."""

    def test_valid_approved_output(self):
        """Test validation of valid approved reviewer output."""
        output = json.dumps({
            "type": "reviewer_result",
            "verdict": "approved",
            "requested_changes": [],
            "notes": ["Code looks good"],
        })

        result = validate_reviewer_output(output)
        assert result.valid
        assert result.data is not None
        assert result.data["verdict"] == "approved"

    def test_valid_changes_requested_output(self):
        """Test validation of valid changes_requested reviewer output."""
        output = json.dumps({
            "type": "reviewer_result",
            "verdict": "changes_requested",
            "requested_changes": [
                {
                    "id": "C1",
                    "path": "src/main.py",
                    "description": "Add error handling",
                    "acceptance": "Try/except around API calls",
                },
            ],
            "notes": ["Needs some improvements"],
        })

        result = validate_reviewer_output(output)
        assert result.valid
        assert result.data is not None
        assert len(result.data["requested_changes"]) == 1

    def test_approved_with_changes_is_invalid(self):
        """Test that approved verdict with requested_changes is invalid."""
        output = json.dumps({
            "type": "reviewer_result",
            "verdict": "approved",
            "requested_changes": [
                {
                    "id": "C1",
                    "path": "*",
                    "description": "Something",
                    "acceptance": "Something",
                },
            ],
            "notes": [],
        })

        result = validate_reviewer_output(output)
        assert not result.valid
        assert "approved" in result.error.lower() or "empty" in result.error.lower()

    def test_invalid_verdict_value(self):
        """Test validation with invalid verdict value."""
        output = json.dumps({
            "type": "reviewer_result",
            "verdict": "maybe",
            "requested_changes": [],
            "notes": [],
        })

        result = validate_reviewer_output(output)
        assert not result.valid


class TestRepairPrompt:
    """Tests for repair prompt generation."""

    def test_repair_prompt_contains_schema(self):
        """Test that repair prompt includes the schema."""
        prompt = build_repair_prompt(
            role="implementer",
            schema=IMPLEMENTER_SCHEMA,
            raw_output="invalid output",
            error="Schema validation failed",
        )

        assert "REPAIR OUTPUT" in prompt
        assert "implementer_result" in prompt
        assert "invalid output" in prompt
        assert "Schema validation failed" in prompt


# ============================================================================
# State Machine Tests
# ============================================================================


class TestRunState:
    """Tests for run state properties."""

    def test_terminal_states(self):
        """Test that terminal states are correctly identified."""
        assert RunState.APPROVED.is_terminal
        assert RunState.FAILED.is_terminal
        assert RunState.CANCELLED.is_terminal

    def test_non_terminal_states(self):
        """Test that non-terminal states are correctly identified."""
        assert not RunState.CREATED.is_terminal
        assert not RunState.PREPARE_WORKSPACE.is_terminal
        assert not RunState.IMPLEMENTER_RUNNING.is_terminal
        assert not RunState.COMMIT_PUSH_PR.is_terminal
        assert not RunState.REVIEWER_RUNNING.is_terminal
        assert not RunState.CHANGES_REQUESTED.is_terminal


class TestRunId:
    """Tests for run ID generation."""

    def test_run_id_format(self):
        """Test that run ID follows expected format."""
        run_id = generate_run_id()

        # Format: YYYYMMDD-HHMMSS-<8hex>
        parts = run_id.split("-")
        assert len(parts) == 3
        assert len(parts[0]) == 8  # YYYYMMDD
        assert len(parts[1]) == 6  # HHMMSS
        assert len(parts[2]) == 8  # 8 hex chars

    def test_run_ids_are_unique(self):
        """Test that generated run IDs are unique."""
        ids = {generate_run_id() for _ in range(100)}
        assert len(ids) == 100


class TestSlugGeneration:
    """Tests for slug generation from tasks."""

    def test_simple_task(self):
        """Test slug generation from simple task."""
        slug = generate_slug("Add user authentication")
        assert slug == "add-user-authentication"

    def test_task_with_special_chars(self):
        """Test slug generation strips special characters."""
        slug = generate_slug("Fix bug #123: handle errors!")
        # Truncated to 24 chars: "fix-bug-123-handle-error"
        assert slug == "fix-bug-123-handle-error"
        assert len(slug) <= 24

    def test_long_task_truncated(self):
        """Test slug generation truncates to 24 chars."""
        slug = generate_slug("This is a very long task description that should be truncated")
        assert len(slug) <= 24
        assert not slug.endswith("-")

    def test_empty_task(self):
        """Test slug generation for empty task."""
        slug = generate_slug("")
        assert slug == "task"

    def test_multiline_task(self):
        """Test slug generation uses first line only."""
        slug = generate_slug("First line\nSecond line\nThird line")
        assert "second" not in slug
        assert "third" not in slug


# ============================================================================
# Persistence Tests
# ============================================================================


class TestRunPersistence:
    """Tests for run persistence."""

    def test_create_directories(self, tmp_path):
        """Test directory creation."""
        persistence = RunPersistence(tmp_path, "test-run-id")
        persistence.ensure_directories()

        assert persistence.run_dir.exists()
        assert persistence.prompts_dir.exists()
        assert persistence.schemas_dir.exists()

    def test_append_and_read_events(self, tmp_path):
        """Test event appending and reading."""
        persistence = RunPersistence(tmp_path, "test-run-id")
        persistence.ensure_directories()

        event1 = run_created_event(
            run_id="test-run-id",
            task="Test task",
            slug="test-task",
            branch="agent/test",
            implementer_agent="claude",
            reviewer_agent="claude",
        )
        event2 = state_changed_event("test-run-id", "CREATED", "PREPARE_WORKSPACE")

        persistence.append_event(event1)
        persistence.append_event(event2)

        events = persistence.read_events()
        assert len(events) == 2
        assert events[0].type == EventType.RUN_CREATED
        assert events[1].type == EventType.STATE_CHANGED

    def test_save_and_load_snapshot(self, tmp_path):
        """Test snapshot save and load."""
        persistence = RunPersistence(tmp_path, "test-run-id")
        persistence.ensure_directories()

        snapshot = RunSnapshot(
            run_id="test-run-id",
            task="Test task",
            slug="test-task",
            branch="agent/test",
            state=RunState.CREATED,
            iteration=0,
            created_at="2026-01-01T00:00:00",
            updated_at="2026-01-01T00:00:00",
            implementer_agent="claude",
            reviewer_agent="claude",
        )

        persistence.save_snapshot(snapshot)
        loaded = persistence.load_snapshot()

        assert loaded is not None
        assert loaded.run_id == "test-run-id"
        assert loaded.state == RunState.CREATED


class TestRunRegistry:
    """Tests for run registry."""

    def test_create_run(self, tmp_path):
        """Test run creation."""
        registry = RunRegistry(tmp_path)
        run_id, persistence = registry.create_run("Test task")

        assert run_id
        assert persistence.run_json_path.exists()
        assert persistence.artifacts_json_path.exists()

    def test_list_runs_empty(self, tmp_path):
        """Test listing runs when empty."""
        registry = RunRegistry(tmp_path)
        runs = registry.list_runs()
        assert runs == []

    def test_list_runs_after_create(self, tmp_path):
        """Test listing runs after creation."""
        registry = RunRegistry(tmp_path)
        registry.create_run("Task 1")
        registry.create_run("Task 2")

        runs = registry.list_runs()
        assert len(runs) == 2


# ============================================================================
# Event Tests
# ============================================================================


class TestEvents:
    """Tests for event creation and serialization."""

    def test_event_to_json(self):
        """Test event JSON serialization."""
        event = run_created_event(
            run_id="test",
            task="Test task",
            slug="test",
            branch="agent/test",
            implementer_agent="claude",
            reviewer_agent="claude",
        )

        json_str = event.to_json()
        parsed = json.loads(json_str)

        assert parsed["type"] == "run_created"
        assert "ts" in parsed
        assert parsed["data"]["run_id"] == "test"

    def test_event_from_json(self):
        """Test event JSON deserialization."""
        event = Event(
            type=EventType.PROCESS_LINE,
            data={"stream": "stdout", "line": "test line"},
        )

        json_str = event.to_json()
        restored = Event.from_json(json_str)

        assert restored.type == EventType.PROCESS_LINE
        assert restored.data["stream"] == "stdout"


# ============================================================================
# Diff Budgeting Tests
# ============================================================================


class TestDiffBudgeting:
    """Tests for diff budgeting and truncation."""

    def test_truncate_hunks(self):
        """Test hunk truncation."""
        from textual_tui.orchestrator.git_service import GitService

        service = GitService()

        diff = """diff --git a/file.py b/file.py
--- a/file.py
+++ b/file.py
@@ -1,3 +1,3 @@
-old line 1
+new line 1
@@ -10,3 +10,3 @@
-old line 2
+new line 2
@@ -20,3 +20,3 @@
-old line 3
+new line 3
"""

        truncated = service._truncate_hunks(diff, max_hunks=2)
        # Should have 2 hunks (each @@ line is a hunk header)
        # The third hunk should be truncated
        assert "[TRUNCATED_HUNKS]" in truncated
        # Count hunk headers by looking for lines starting with @@
        hunk_headers = [line for line in truncated.split("\n") if line.startswith("@@")]
        assert len(hunk_headers) == 2


# ============================================================================
# Agent Driver Tests (Integration)
# ============================================================================


class TestAgentDrivers:
    """Integration tests for agent drivers using fixtures."""

    @pytest.fixture
    def fixtures_dir(self):
        """Get the fixtures directory."""
        return Path(__file__).parent / "fixtures"

    @pytest.mark.asyncio
    async def test_codex_driver_implementer(self, fixtures_dir, tmp_path):
        """Test Codex driver for implementer role."""
        from textual_tui.orchestrator.agents.codex_driver import CodexDriver
        from textual_tui.orchestrator.agents.base import AgentRole

        driver = CodexDriver(
            executable=str(fixtures_dir / "codex"),
            role=AgentRole.IMPLEMENTER,
        )

        schema_path = tmp_path / "schema.json"
        output_path = tmp_path / "output.json"

        with open(schema_path, "w") as f:
            json.dump(IMPLEMENTER_SCHEMA, f)

        result = await driver.run(
            worktree_path=tmp_path,
            prompt="Implement a new feature",
            schema=IMPLEMENTER_SCHEMA,
            schema_path=schema_path,
            output_path=output_path,
            timeout=30,
            on_line=None,
        )

        assert result["type"] == "implementer_result"
        assert "summary" in result
        assert "commit_message" in result

    @pytest.mark.asyncio
    async def test_claude_driver_reviewer(self, fixtures_dir, tmp_path):
        """Test Claude driver for reviewer role."""
        from textual_tui.orchestrator.agents.claude_driver import ClaudeDriver
        from textual_tui.orchestrator.agents.base import AgentRole

        driver = ClaudeDriver(
            executable=str(fixtures_dir / "claude"),
            role=AgentRole.REVIEWER,
        )

        schema_path = tmp_path / "schema.json"
        output_path = tmp_path / "output.json"

        with open(schema_path, "w") as f:
            json.dump(REVIEWER_SCHEMA, f)

        result = await driver.run(
            worktree_path=tmp_path,
            prompt="Review the changes as a reviewer",
            schema=REVIEWER_SCHEMA,
            schema_path=schema_path,
            output_path=output_path,
            timeout=30,
            on_line=None,
        )

        assert result["type"] == "reviewer_result"
        assert result["verdict"] == "approved"


# ============================================================================
# Subprocess Runner Tests
# ============================================================================


class TestSubprocessRunner:
    """Tests for subprocess runner."""

    @pytest.mark.asyncio
    async def test_run_simple_command(self):
        """Test running a simple command."""
        from textual_tui.orchestrator.subprocess_runner import run_command_simple

        exit_code, stdout, stderr = await run_command_simple(
            ["echo", "hello"],
            timeout=5,
        )

        assert exit_code == 0
        assert "hello" in stdout

    @pytest.mark.asyncio
    async def test_run_with_timeout(self):
        """Test command timeout."""
        from textual_tui.orchestrator.subprocess_runner import run_command

        result = await run_command(
            ["sleep", "10"],
            timeout=1,
        )

        assert result.timed_out

    @pytest.mark.asyncio
    async def test_capture_stderr(self):
        """Test stderr capture."""
        from textual_tui.orchestrator.subprocess_runner import run_command_simple

        exit_code, stdout, stderr = await run_command_simple(
            ["python3", "-c", "import sys; print('error', file=sys.stderr)"],
            timeout=5,
        )

        assert exit_code == 0
        assert "error" in stderr
