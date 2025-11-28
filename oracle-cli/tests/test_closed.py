"""Tests for the Closed Oracle."""

import pytest

from oracle.core import Likelihood, ask_closed
from oracle.util import OracleRNG


def test_closed_determinism():
    """Test that the same seed produces the same result."""
    rng1 = OracleRNG(seed=123)
    result1 = ask_closed("Is the door locked?", Likelihood.LIKELY, rng1)

    rng2 = OracleRNG(seed=123)
    result2 = ask_closed("Is the door locked?", Likelihood.LIKELY, rng2)

    assert result1 == result2


def test_closed_likelihood_modifiers():
    """Test that likelihood modifiers work correctly."""
    assert Likelihood.VERY_UNLIKELY.modifier() == -2
    assert Likelihood.UNLIKELY.modifier() == -1
    assert Likelihood.EVEN.modifier() == 0
    assert Likelihood.LIKELY.modifier() == 1
    assert Likelihood.VERY_LIKELY.modifier() == 2


def test_closed_clamping():
    """Test that results are clamped to [1, 6]."""
    # Use a seed that will produce a low roll
    rng = OracleRNG(seed=100)
    result = ask_closed("Test?", Likelihood.VERY_UNLIKELY, rng)

    # Final roll should be >= 1
    assert result.roll.final >= 1
    assert result.roll.final <= 6


def test_closed_table_coverage(seeded_rng):
    """Test that all table entries (1-6) can be reached."""
    results = set()

    # Try many rolls to get coverage
    for seed in range(1000):
        rng = OracleRNG(seed=seed)
        result = ask_closed("Test?", Likelihood.EVEN, rng)
        results.add(result.roll.final)

    # We should be able to reach all 6 outcomes
    assert results == {1, 2, 3, 4, 5, 6}


def test_closed_result_structure(seeded_rng):
    """Test that the result has the expected structure."""
    result = ask_closed("Is it safe?", Likelihood.EVEN, seeded_rng)

    assert result.type == "closed"
    assert result.question == "Is it safe?"
    assert result.likelihood == "even"
    assert hasattr(result.roll, "base")
    assert hasattr(result.roll, "modifier")
    assert hasattr(result.roll, "final")
    assert hasattr(result.result, "answer")
    assert hasattr(result.result, "detail")
    assert hasattr(result.result, "scenario")
    assert hasattr(result.result, "tone")
