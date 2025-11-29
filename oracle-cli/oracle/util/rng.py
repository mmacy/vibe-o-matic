"""RNG wrapper for deterministic dice rolls."""

import random


class OracleRNG:
    """Wrapper around random.Random for deterministic dice rolling."""

    def __init__(self, seed: int | None = None):
        """Initialize the RNG with an optional seed.

        Args:
            seed: Optional seed for deterministic output.
        """
        self._rng = random.Random(seed)

    def d6(self) -> int:
        """Roll a six-sided die.

        Returns:
            Integer between 1 and 6 (inclusive).
        """
        return self._rng.randint(1, 6)

    def d20(self) -> int:
        """Roll a twenty-sided die.

        Returns:
            Integer between 1 and 20 (inclusive).
        """
        return self._rng.randint(1, 20)

    def d4(self) -> int:
        """Roll a four-sided die.

        Returns:
            Integer between 1 and 4 (inclusive).
        """
        return self._rng.randint(1, 4)

    def d8(self) -> int:
        """Roll an eight-sided die.

        Returns:
            Integer between 1 and 8 (inclusive).
        """
        return self._rng.randint(1, 8)

    def d10(self) -> int:
        """Roll a ten-sided die.

        Returns:
            Integer between 1 and 10 (inclusive).
        """
        return self._rng.randint(1, 10)

    def d12(self) -> int:
        """Roll a twelve-sided die.

        Returns:
            Integer between 1 and 12 (inclusive).
        """
        return self._rng.randint(1, 12)

    def d100(self) -> int:
        """Roll percentile dice.

        Returns:
            Integer between 1 and 100 (inclusive).
        """
        return self._rng.randint(1, 100)

    def roll(self, sides: int) -> int:
        """Roll a die with arbitrary number of sides.

        Args:
            sides: Number of sides on the die (must be >= 1).

        Returns:
            Random integer from 1 to sides (inclusive).

        Raises:
            ValueError: If sides < 1.

        Examples:

            ```python
            rng = OracleRNG(seed=42)
            rng.roll(7)  # Roll a d7
            4
            rng.roll(30)  # Roll a d30
            23
            ```
        """
        if sides < 1:
            raise ValueError(f"Die must have at least 1 side, got {sides}")
        return self._rng.randint(1, sides)
