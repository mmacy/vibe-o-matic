"""Validation utilities for agent outputs.

Provides JSON Schema validation with support for repair retry.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema
from jsonschema import ValidationError, SchemaError


@dataclass
class ValidationResult:
    """Result of validating agent output."""

    valid: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    raw_output: str | None = None


def validate_json_output(
    raw_output: str,
    schema: dict[str, Any],
) -> ValidationResult:
    """Validate raw output against a JSON schema.

    Args:
        raw_output: Raw string output from agent.
        schema: JSON Schema to validate against.

    Returns:
        ValidationResult with parsed data if valid, error message if not.
    """
    # Try to parse JSON
    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError as e:
        return ValidationResult(
            valid=False,
            error=f"Invalid JSON: {e}",
            raw_output=raw_output,
        )

    # Validate against schema
    try:
        jsonschema.validate(instance=data, schema=schema)
        return ValidationResult(valid=True, data=data)
    except ValidationError as e:
        return ValidationResult(
            valid=False,
            error=f"Schema validation failed: {e.message}",
            raw_output=raw_output,
        )
    except SchemaError as e:
        return ValidationResult(
            valid=False,
            error=f"Invalid schema: {e.message}",
            raw_output=raw_output,
        )


def validate_implementer_output(raw_output: str) -> ValidationResult:
    """Validate implementer agent output.

    Args:
        raw_output: Raw string output from implementer.

    Returns:
        ValidationResult.
    """
    from textual_tui.orchestrator.agents.schemas import IMPLEMENTER_SCHEMA

    return validate_json_output(raw_output, IMPLEMENTER_SCHEMA)


def validate_reviewer_output(raw_output: str) -> ValidationResult:
    """Validate reviewer agent output.

    Also enforces the rule that if verdict is "approved",
    requested_changes must be empty.

    Args:
        raw_output: Raw string output from reviewer.

    Returns:
        ValidationResult.
    """
    from textual_tui.orchestrator.agents.schemas import REVIEWER_SCHEMA

    result = validate_json_output(raw_output, REVIEWER_SCHEMA)

    if result.valid and result.data:
        # Additional validation: approved verdict requires empty requested_changes
        if (
            result.data.get("verdict") == "approved"
            and result.data.get("requested_changes")
        ):
            return ValidationResult(
                valid=False,
                error="If verdict is 'approved', requested_changes must be empty",
                raw_output=raw_output,
            )

    return result


def build_repair_prompt(
    role: str,
    schema: dict[str, Any],
    raw_output: str,
    error: str,
) -> str:
    """Build a repair prompt for invalid output.

    Args:
        role: Agent role ("implementer" or "reviewer").
        schema: JSON Schema the output must conform to.
        raw_output: The invalid raw output.
        error: The validation error message.

    Returns:
        A prompt instructing the agent to fix the output.
    """
    schema_str = json.dumps(schema, indent=2)

    return f"""REPAIR OUTPUT

Your previous output was invalid. Please fix it and output ONLY valid JSON.

## Error
{error}

## Required Schema
```json
{schema_str}
```

## Your Invalid Output
```
{raw_output}
```

## Instructions
1. Return ONLY valid JSON that conforms to the schema above.
2. Do NOT include any prose, markdown formatting, or explanations.
3. Do NOT wrap the JSON in code blocks.
4. The output must be parseable as JSON directly.

Output the corrected JSON now:"""
