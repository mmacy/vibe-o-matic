"""Dice notation parser for standard RPG dice notation."""

import re
from dataclasses import dataclass


@dataclass
class DiceNotation:
    """Parsed dice notation.

    Attributes:
        count: Number of dice to roll.
        sides: Number of sides per die.
        modifier: Additive modifier (can be negative).
    """

    count: int
    sides: int
    modifier: int


def parse_dice_notation(notation: str) -> DiceNotation:
    """Parse dice notation like '2d6+3' or '1d20-1'.

    Args:
        notation: Dice string in format [count]d[sides][+/-modifier].
            - count: Number of dice (must be >= 1)
            - sides: Number of sides per die (must be >= 1)
            - modifier: Optional modifier (e.g., +3, -1)

    Returns:
        DiceNotation with parsed values.

    Raises:
        ValueError: If notation is invalid or values are out of range.

    Examples:

        ```python
        parse_dice_notation("1d20")
        DiceNotation(count=1, sides=20, modifier=0)
        parse_dice_notation("2d6+3")
        DiceNotation(count=2, sides=6, modifier=3)
        parse_dice_notation("1d8-1")
        DiceNotation(count=1, sides=8, modifier=-1)
        ```
    """
    # Pattern: [count]d[sides][+/-modifier]
    # Case-insensitive, allows whitespace around input
    pattern = r"^(\d+)d(\d+)([+-]\d+)?$"
    match = re.match(pattern, notation.lower().strip())

    if not match:
        raise ValueError(
            f"Invalid dice notation: '{notation}'. "
            f"Expected format: [count]d[sides] or [count]d[sides]+/-[modifier] "
            f"(e.g., '1d20', '2d6+3', '1d8-1')"
        )

    count = int(match.group(1))
    sides = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0

    if count < 1:
        raise ValueError(f"Must roll at least 1 die, got {count}")
    if sides < 1:
        raise ValueError(f"Die must have at least 1 side, got {sides}")

    return DiceNotation(count=count, sides=sides, modifier=modifier)
