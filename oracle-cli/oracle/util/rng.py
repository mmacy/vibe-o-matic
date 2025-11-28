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
