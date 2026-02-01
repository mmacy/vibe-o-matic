"""JSON Schemas for agent outputs.

These schemas define the expected structure of outputs from
implementer and reviewer agents.
"""

from __future__ import annotations

from typing import Any

# Implementer output schema
IMPLEMENTER_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "ImplementerResult",
    "description": "Output from the implementer agent",
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "const": "implementer_result",
            "description": "Must be 'implementer_result'",
        },
        "summary": {
            "type": "string",
            "description": "Brief summary of the changes made",
        },
        "commit_message": {
            "type": "string",
            "description": "Commit message for the changes",
        },
        "tests": {
            "type": "array",
            "description": "Test results",
            "items": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Test command that was run",
                    },
                    "result": {
                        "type": "string",
                        "enum": ["pass", "fail", "not_run"],
                        "description": "Test result",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes about the test",
                    },
                },
                "required": ["command", "result"],
                "additionalProperties": False,
            },
        },
        "notes": {
            "type": "array",
            "description": "Additional notes",
            "items": {"type": "string"},
        },
    },
    "required": ["type", "summary", "commit_message", "tests", "notes"],
    "additionalProperties": False,
}

# Reviewer output schema
REVIEWER_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "ReviewerResult",
    "description": "Output from the reviewer agent",
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "const": "reviewer_result",
            "description": "Must be 'reviewer_result'",
        },
        "verdict": {
            "type": "string",
            "enum": ["approved", "changes_requested"],
            "description": "Review verdict",
        },
        "requested_changes": {
            "type": "array",
            "description": "List of requested changes (empty if approved)",
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Unique identifier (e.g., C1, C2)",
                    },
                    "path": {
                        "type": "string",
                        "description": "File path or '*' for global",
                    },
                    "description": {
                        "type": "string",
                        "description": "What needs to change",
                    },
                    "acceptance": {
                        "type": "string",
                        "description": "Objective pass/fail criteria",
                    },
                },
                "required": ["id", "path", "description", "acceptance"],
                "additionalProperties": False,
            },
        },
        "notes": {
            "type": "array",
            "description": "Additional notes",
            "items": {"type": "string"},
        },
    },
    "required": ["type", "verdict", "requested_changes", "notes"],
    "additionalProperties": False,
}


def get_schema_for_role(role: str) -> dict[str, Any]:
    """Get the JSON schema for a given role.

    Args:
        role: Either "implementer" or "reviewer".

    Returns:
        The corresponding JSON schema.

    Raises:
        ValueError: If role is not recognized.
    """
    if role == "implementer":
        return IMPLEMENTER_SCHEMA
    elif role == "reviewer":
        return REVIEWER_SCHEMA
    else:
        raise ValueError(f"Unknown role: {role}")
