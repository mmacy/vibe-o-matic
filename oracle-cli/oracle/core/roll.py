"""Core dice rolling logic."""

from dataclasses import dataclass

from oracle.util import OracleRNG, parse_dice_notation


@dataclass
class RollResult:
    """Individual die roll result.

    Attributes:
        die: Number of sides on this die.
        roll: The rolled value.
    """

    die: int
    roll: int


@dataclass
class RollQuery:
    """Generic dice roll query and result.

    Attributes:
        type: Always "roll" for roll queries.
        notation: Original dice notation string.
        count: Number of dice rolled.
        sides: Sides per die.
        modifier: Modifier applied to total.
        rolls: Individual die results.
        total: Final sum (dice total + modifier).
    """

    type: str
    notation: str
    count: int
    sides: int
    modifier: int
    rolls: list[RollResult]
    total: int


def roll_dice(notation: str, rng: OracleRNG) -> RollQuery:
    """Roll dice using standard notation.

    Args:
        notation: Dice notation (e.g., "2d6+3", "1d20", "1d8-1").
        rng: OracleRNG instance for rolling.

    Returns:
        RollQuery with complete roll details.

    Raises:
        ValueError: If notation is invalid (propagated from parse_dice_notation).

    Examples:

        ```python
        rng = OracleRNG(seed=42)
        result = roll_dice("2d6+3", rng)
        result.total  # Sum of two d6 rolls plus 3
        12
        result.count
        2
        result.sides
        6
        result.modifier
        3
        ```
    """
    # Parse dice notation
    parsed = parse_dice_notation(notation)

    # Roll each die using OracleRNG
    rolls = [
        RollResult(die=parsed.sides, roll=rng.roll(parsed.sides))
        for _ in range(parsed.count)
    ]

    # Calculate total
    dice_sum = sum(r.roll for r in rolls)
    total = dice_sum + parsed.modifier

    return RollQuery(
        type="roll",
        notation=notation,
        count=parsed.count,
        sides=parsed.sides,
        modifier=parsed.modifier,
        rolls=rolls,
        total=total,
    )
