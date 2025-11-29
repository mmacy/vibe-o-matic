"""Unit tests for OracleRNG polyhedral dice methods."""

import pytest

from oracle.util.rng import OracleRNG


def test_d4():
    """Test d4 method."""
    rng = OracleRNG(seed=42)
    for _ in range(100):
        result = rng.d4()
        assert 1 <= result <= 4


def test_d8():
    """Test d8 method."""
    rng = OracleRNG(seed=42)
    for _ in range(100):
        result = rng.d8()
        assert 1 <= result <= 8


def test_d10():
    """Test d10 method."""
    rng = OracleRNG(seed=42)
    for _ in range(100):
        result = rng.d10()
        assert 1 <= result <= 10


def test_d12():
    """Test d12 method."""
    rng = OracleRNG(seed=42)
    for _ in range(100):
        result = rng.d12()
        assert 1 <= result <= 12


def test_d100():
    """Test d100 method."""
    rng = OracleRNG(seed=42)
    for _ in range(100):
        result = rng.d100()
        assert 1 <= result <= 100


def test_roll_generic():
    """Test generic roll method."""
    rng = OracleRNG(seed=42)

    for sides in [4, 6, 8, 10, 12, 20, 100]:
        result = rng.roll(sides)
        assert 1 <= result <= sides


def test_roll_custom_sides():
    """Test roll with custom number of sides."""
    rng = OracleRNG(seed=42)

    # Test uncommon dice
    result = rng.roll(7)
    assert 1 <= result <= 7

    result = rng.roll(30)
    assert 1 <= result <= 30


def test_roll_invalid_sides():
    """Test that roll raises ValueError for invalid sides."""
    rng = OracleRNG(seed=42)

    with pytest.raises(ValueError, match="Die must have at least 1 side"):
        rng.roll(0)

    with pytest.raises(ValueError, match="Die must have at least 1 side"):
        rng.roll(-1)


def test_all_dice_deterministic():
    """Test that all dice methods are deterministic with same seed."""
    rng1 = OracleRNG(seed=42)
    rng2 = OracleRNG(seed=42)

    assert rng1.d4() == rng2.d4()
    assert rng1.d6() == rng2.d6()
    assert rng1.d8() == rng2.d8()
    assert rng1.d10() == rng2.d10()
    assert rng1.d12() == rng2.d12()
    assert rng1.d20() == rng2.d20()
    assert rng1.d100() == rng2.d100()
    assert rng1.roll(7) == rng2.roll(7)
