"""Chaos Dice: Stateless pool tracking."""

from dataclasses import dataclass

from oracle.util import OracleRNG


@dataclass
class ChaosQuery:
    """Complete result of a chaos dice roll."""

    type: str
    input_pool: int
    rolls: list[int]
    sixes: int
    next_pool: int
    triggered: bool


def chaos_roll(dice: int, rng: OracleRNG) -> ChaosQuery:
    """Roll chaos dice and track the pool.

    Args:
        dice: Number of d6s to roll.
        rng: Random number generator.

    Returns:
        Complete query result with rolls, sixes count, and next pool size.
    """
    # Roll N d6s
    rolls = [rng.d6() for _ in range(dice)]

    # Count sixes
    sixes = sum(1 for roll in rolls if roll == 6)

    # Calculate next pool (total - sixes)
    next_pool = dice - sixes

    # Event triggers if pool reaches 0
    triggered = next_pool == 0

    return ChaosQuery(
        type="chaos",
        input_pool=dice,
        rolls=rolls,
        sixes=sixes,
        next_pool=next_pool,
        triggered=triggered,
    )
