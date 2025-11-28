"""Tests for the Plot Twist Oracle."""

from oracle.core import ask_twist
from oracle.util import OracleRNG


def test_twist_determinism():
    """Test that the same seed produces the same result."""
    rng1 = OracleRNG(seed=123)
    result1 = ask_twist(rng1)

    rng2 = OracleRNG(seed=123)
    result2 = ask_twist(rng2)

    assert result1 == result2


def test_twist_structure(seeded_rng):
    """Test that the result has the expected structure."""
    result = ask_twist(seeded_rng)

    assert result.type == "twist"
    assert hasattr(result.rolls, "subject")
    assert hasattr(result.rolls, "action")
    assert isinstance(result.result, str)
    assert 1 <= result.rolls.subject <= 6
    assert 1 <= result.rolls.action <= 6


def test_twist_result_format():
    """Test that the result combines subject and action properly."""
    rng = OracleRNG(seed=42)
    result = ask_twist(rng)

    # Result should be in format "Subject action."
    assert isinstance(result.result, str)
    assert len(result.result) > 0

    # Should contain a period (all actions end with one)
    assert "." in result.result


def test_twist_coverage():
    """Test that various subjects and actions can be generated."""
    subjects = set()
    actions = set()

    for seed in range(100):
        rng = OracleRNG(seed=seed)
        result = ask_twist(rng)
        subjects.add(result.rolls.subject)
        actions.add(result.rolls.action)

    # Should get good coverage of possible values
    assert len(subjects) >= 5  # Should see most of the 6 subjects
    assert len(actions) >= 5  # Should see most of the 6 actions
