"""Tests for the Chaos Dice Oracle."""

from oracle.core import chaos_roll
from oracle.util import OracleRNG


def test_chaos_determinism():
    """Test that the same seed produces the same result."""
    rng1 = OracleRNG(seed=123)
    result1 = chaos_roll(5, rng1)

    rng2 = OracleRNG(seed=123)
    result2 = chaos_roll(5, rng2)

    assert result1 == result2


def test_chaos_pool_calculation():
    """Test that next pool is correctly calculated."""
    # Test with many seeds to find cases with different numbers of sixes
    for seed in range(200):
        rng = OracleRNG(seed=seed)
        result = chaos_roll(6, rng)

        # Verify the calculation
        assert result.next_pool == result.input_pool - result.sixes
        assert len(result.rolls) == result.input_pool


def test_chaos_trigger_on_zero():
    """Test that event triggers when pool reaches 0."""
    # Find a case where all dice are sixes
    found_trigger = False

    for seed in range(10000):
        rng = OracleRNG(seed=seed)
        result = chaos_roll(3, rng)

        if result.sixes == result.input_pool:
            # All dice were sixes, pool should be 0
            assert result.next_pool == 0
            assert result.triggered is True
            found_trigger = True
            break

    # We should find at least one case where all dice are sixes
    assert found_trigger, "Could not find a seed that produces all sixes"


def test_chaos_no_trigger():
    """Test that event doesn't trigger when pool > 0."""
    rng = OracleRNG(seed=42)
    result = chaos_roll(5, rng)

    if result.next_pool > 0:
        assert result.triggered is False


def test_chaos_structure(seeded_rng):
    """Test that the result has the expected structure."""
    result = chaos_roll(4, seeded_rng)

    assert result.type == "chaos"
    assert result.input_pool == 4
    assert len(result.rolls) == 4
    assert result.sixes >= 0
    assert result.next_pool >= 0
    assert isinstance(result.triggered, bool)

    # All rolls should be valid d6 results
    for roll in result.rolls:
        assert 1 <= roll <= 6


def test_chaos_sixes_count():
    """Test that sixes are counted correctly."""
    rng = OracleRNG(seed=42)
    result = chaos_roll(10, rng)

    # Manually count sixes
    manual_count = sum(1 for r in result.rolls if r == 6)
    assert result.sixes == manual_count
