"""Unit tests for core roll logic."""

import pytest

from oracle.core.roll import roll_dice
from oracle.util.rng import OracleRNG


def test_roll_dice_simple():
    """Test rolling a simple die."""
    rng = OracleRNG(seed=42)
    result = roll_dice("1d20", rng)

    assert result.type == "roll"
    assert result.notation == "1d20"
    assert result.count == 1
    assert result.sides == 20
    assert result.modifier == 0
    assert len(result.rolls) == 1
    assert 1 <= result.rolls[0].roll <= 20
    assert result.total == result.rolls[0].roll


def test_roll_dice_multiple():
    """Test rolling multiple dice."""
    rng = OracleRNG(seed=42)
    result = roll_dice("2d6", rng)

    assert result.count == 2
    assert result.sides == 6
    assert len(result.rolls) == 2
    assert all(1 <= r.roll <= 6 for r in result.rolls)
    assert result.total == sum(r.roll for r in result.rolls)


def test_roll_dice_with_positive_modifier():
    """Test rolling with positive modifier."""
    rng = OracleRNG(seed=42)
    result = roll_dice("2d6+3", rng)

    assert result.modifier == 3
    dice_sum = sum(r.roll for r in result.rolls)
    assert result.total == dice_sum + 3


def test_roll_dice_with_negative_modifier():
    """Test rolling with negative modifier."""
    rng = OracleRNG(seed=42)
    result = roll_dice("1d8-1", rng)

    assert result.modifier == -1
    dice_sum = result.rolls[0].roll
    assert result.total == dice_sum - 1


def test_roll_dice_deterministic():
    """Test that same seed produces same output."""
    rng1 = OracleRNG(seed=42)
    rng2 = OracleRNG(seed=42)

    result1 = roll_dice("2d6+3", rng1)
    result2 = roll_dice("2d6+3", rng2)

    assert result1.total == result2.total
    assert result1.rolls[0].roll == result2.rolls[0].roll
    assert result1.rolls[1].roll == result2.rolls[1].roll


def test_roll_dice_all_polyhedrals():
    """Test all common polyhedral dice."""
    rng = OracleRNG(seed=42)

    for sides in [4, 6, 8, 10, 12, 20, 100]:
        result = roll_dice(f"1d{sides}", rng)
        assert result.sides == sides
        assert 1 <= result.rolls[0].roll <= sides


def test_roll_dice_invalid_notation():
    """Test that invalid notation raises ValueError."""
    rng = OracleRNG(seed=42)

    with pytest.raises(ValueError):
        roll_dice("invalid", rng)

    with pytest.raises(ValueError):
        roll_dice("2d", rng)
