"""Utilities for loading and formatting oracle tables."""

from importlib.resources import files
from typing import Any

import yaml


def load_table(filename: str) -> dict[str, Any]:
    """Load a YAML table from the oracle.tables package.

    Args:
        filename: Name of the YAML file (e.g., "closed.yaml").

    Returns:
        Parsed YAML data as a dictionary.

    Raises:
        FileNotFoundError: If the table file doesn't exist.
        yaml.YAMLError: If the YAML is malformed.
    """
    content = files("oracle.tables").joinpath(filename).read_text(encoding="utf-8")
    return yaml.safe_load(content)
