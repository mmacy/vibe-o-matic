"""Shared test fixtures."""

import pytest

from oracle.util import OracleRNG


@pytest.fixture
def seeded_rng():
    """Provide a seeded RNG for deterministic tests."""
    return OracleRNG(seed=42)
