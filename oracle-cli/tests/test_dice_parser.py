"""Unit tests for dice notation parser."""

import pytest

from oracle.util.dice import parse_dice_notation


def test_parse_simple_notation():
    """Test parsing simple dice notation without modifier."""
    result = parse_dice_notation("1d20")
    assert result.count == 1
    assert result.sides == 20
    assert result.modifier == 0


def test_parse_multiple_dice():
    """Test parsing multiple dice."""
    result = parse_dice_notation("2d6")
    assert result.count == 2
    assert result.sides == 6
    assert result.modifier == 0


def test_parse_with_positive_modifier():
    """Test parsing with positive modifier."""
    result = parse_dice_notation("2d6+3")
    assert result.count == 2
    assert result.sides == 6
    assert result.modifier == 3


def test_parse_with_negative_modifier():
    """Test parsing with negative modifier."""
    result = parse_dice_notation("1d8-1")
    assert result.count == 1
    assert result.sides == 8
    assert result.modifier == -1


def test_parse_case_insensitive():
    """Test that parser is case insensitive."""
    result1 = parse_dice_notation("1D20")
    result2 = parse_dice_notation("1d20")
    assert result1.count == result2.count
    assert result1.sides == result2.sides


def test_parse_strips_whitespace():
    """Test that parser strips whitespace."""
    result = parse_dice_notation("  2d6+3  ")
    assert result.count == 2
    assert result.sides == 6
    assert result.modifier == 3


def test_parse_invalid_notation():
    """Test that invalid notation raises ValueError."""
    with pytest.raises(ValueError, match="Invalid dice notation"):
        parse_dice_notation("2d")

    with pytest.raises(ValueError, match="Invalid dice notation"):
        parse_dice_notation("d6")

    with pytest.raises(ValueError, match="Invalid dice notation"):
        parse_dice_notation("2x6")

    with pytest.raises(ValueError, match="Invalid dice notation"):
        parse_dice_notation("not-dice")


def test_parse_zero_count():
    """Test that zero dice count raises ValueError."""
    with pytest.raises(ValueError, match="Must roll at least 1 die"):
        parse_dice_notation("0d6")


def test_parse_zero_sides():
    """Test that zero sides raises ValueError."""
    with pytest.raises(ValueError, match="Die must have at least 1 side"):
        parse_dice_notation("2d0")


def test_parse_large_numbers():
    """Test parsing large but valid numbers."""
    result = parse_dice_notation("10d100+50")
    assert result.count == 10
    assert result.sides == 100
    assert result.modifier == 50
